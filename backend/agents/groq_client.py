import os
from datetime import datetime, timedelta

from groq import Groq, RateLimitError

VALID_SEVERITIES = {"critical", "warning", "info", "positive"}
VALID_TYPES = {"summary", "alert", "recommendation", "anomaly"}

# Use a smaller, cheaper model to reduce token burn
GROQ_MODEL = "llama-3.1-8b-instant"


def call_groq_for_insight(system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
    # Hard cap input to keep token usage predictable
    user_prompt = user_prompt[:1500]
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except RateLimitError as e:
        print(f"[Groq] Rate limit — skipping this agent run. ({e})")
        return ""
    except Exception as e:
        print(f"[Groq] API error: {e}")
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
