"""Shared Gemini helper for background insight agents."""
import os
from datetime import datetime, timedelta

import google.generativeai as genai

VALID_SEVERITIES = {"critical", "warning", "info", "positive"}
VALID_TYPES = {"summary", "alert", "recommendation", "anomaly"}

GEMINI_MODEL = "gemini-2.5-flash"


def _client() -> genai.GenerativeModel:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY ortam değişkeni ayarlanmamış.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        GEMINI_MODEL,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=300,
        ),
    )


def call_gemini_for_insight(system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
    user_prompt = user_prompt[:1500]
    try:
        model = _client()
        # Gemini doesn't have a system role in the SDK — prepend to user prompt
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status == 429 or "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
            print(f"[Gemini] Rate limit — skipping this agent run. ({e})")
            return ""
        print(f"[Gemini] API error: {e}")
        return ""


def parse_insight_lines(raw: str) -> list[dict]:
    results = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        severity = parts[0].strip().lower()
        insight_type = parts[1].strip().lower()
        content = parts[2].strip()
        if severity not in VALID_SEVERITIES:
            severity = "info"
        if insight_type not in VALID_TYPES:
            insight_type = "summary"
        if len(content) < 10:
            continue
        results.append({"severity": severity, "type": insight_type, "content": content})
    if not results and raw.strip():
        results.append({
            "severity": "info",
            "type": "summary",
            "content": raw.strip()[:300],
        })
    return results[:3]


def write_insights(db, insights: list[dict], agent_name: str) -> None:
    from models import AIInsight
    cutoff = datetime.utcnow() - timedelta(hours=2)
    db.query(AIInsight).filter(
        AIInsight.agent_name == agent_name,
        AIInsight.created_at < cutoff,
        AIInsight.is_dismissed == False,
    ).delete(synchronize_session=False)
    now = datetime.utcnow()
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
