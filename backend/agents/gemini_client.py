"""Shared LLM helper for background insight agents. Tries Gemini first, falls back to Groq."""
import os
from datetime import datetime, timedelta

VALID_SEVERITIES = {"critical", "warning", "info", "positive"}
VALID_TYPES = {"summary", "alert", "recommendation", "anomaly"}

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def _is_quota_error(err: str) -> bool:
    lowered = err.lower()
    return any(kw in lowered for kw in ("429", "quota", "rate", "limit", "resourceexhausted", "exhausted"))


def _call_gemini(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY yok")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=max_tokens,
        ),
    )
    response = model.generate_content(user_prompt)
    return response.text.strip()


def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY yok")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def call_gemini_for_insight(system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    """Önce Gemini dener. Kota/rate-limit hatası alırsa Groq'a geçer. Her ikisi de başarısız olursa boş döner."""
    user_prompt = user_prompt[:3000]

    # 1. Gemini denemesi
    try:
        result = _call_gemini(system_prompt, user_prompt, max_tokens)
        print("[LLM] Gemini kullanıldı.")
        return result
    except Exception as e:
        err = str(e)
        if _is_quota_error(err):
            print(f"[LLM] Gemini kota/limit — Groq'a geçiliyor. ({err[:80]})")
        else:
            print(f"[LLM] Gemini hatası — Groq'a geçiliyor. ({err[:80]})")

    # 2. Groq fallback
    try:
        result = _call_groq(system_prompt, user_prompt, max_tokens)
        print("[LLM] Groq kullanıldı (fallback).")
        return result
    except Exception as e:
        err = str(e)
        if _is_quota_error(err):
            print(f"[LLM] Groq da rate limit — bu çalışma atlandı. ({err[:80]})")
        else:
            print(f"[LLM] Groq hatası — bu çalışma atlandı. ({err[:80]})")
        return ""


def _clean_content(text: str) -> str:
    import re
    text = re.sub(r"^(CONTENT|content)\s*:\s*", "", text).strip()
    text = re.sub(r"^[-*•]\s*", "", text).strip()
    return text


def parse_insight_lines(raw: str, max_insights: int = 3) -> list[dict]:
    import re
    results = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"[*_`]", "", line).strip()

        parts = line.split("|", 2)
        if len(parts) != 3:
            continue

        severity = parts[0].strip().lower()
        insight_type = parts[1].strip().lower()
        content = _clean_content(parts[2])

        if severity not in VALID_SEVERITIES:
            severity = "info"
        if insight_type not in VALID_TYPES:
            insight_type = "summary"
        if len(content) < 10:
            continue

        results.append({"severity": severity, "type": insight_type, "content": content})

    if not results and raw.strip():
        cleaned = _clean_content(raw.strip())
        results.append({
            "severity": "info",
            "type": "summary",
            "content": cleaned[:300],
        })
    return results[:max_insights]


def _context_hash(context: str) -> str:
    import hashlib, re
    normalized = re.sub(r"\d{2}:\d{2}", "", context).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def write_insights(db, insights: list[dict], agent_name: str, context_hash: str = "") -> int:
    """Yalnızca operasyonel context değiştiğinde yeni insight yazar."""
    from models import AIInsight

    cutoff = datetime.utcnow() - timedelta(hours=24)
    db.query(AIInsight).filter(
        AIInsight.agent_name == agent_name,
        AIInsight.created_at < cutoff,
    ).delete(synchronize_session=False)

    if context_hash:
        sentinel = (
            db.query(AIInsight)
            .filter(AIInsight.agent_name == agent_name, AIInsight.insight_type == "_hash")
            .order_by(AIInsight.created_at.desc())
            .first()
        )
        if sentinel and sentinel.content == context_hash:
            print(f"[{agent_name}] Durum değişmedi, insight eklenmedi.")
            return 0

    now = datetime.utcnow()

    if context_hash:
        db.query(AIInsight).filter(
            AIInsight.agent_name == agent_name,
            AIInsight.insight_type == "_hash",
        ).delete(synchronize_session=False)
        db.add(AIInsight(
            agent_name=agent_name,
            insight_type="_hash",
            content=context_hash,
            severity="info",
            created_at=now,
            is_dismissed=True,
        ))

    for item in insights:
        db.add(AIInsight(
            agent_name=agent_name,
            insight_type=item["type"],
            content=item["content"],
            severity=item["severity"],
            related_entity_type=item.get("entity_type"),
            related_entity_id=item.get("entity_id"),
            created_at=now,
            is_dismissed=False,
        ))
    return len(insights)
