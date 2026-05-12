from datetime import datetime, timedelta

from sqlalchemy import text

from agents.gemini_client import call_gemini_for_insight as call_groq_for_insight, parse_insight_lines, write_insights
from database import SessionLocal

SYSTEM_PROMPT = """Sen Anadolu Tarım ve Gıda Kooperatifi'nin Kargo İzleme Ajanısın.
Sana verilen kargo pipeline verilerini analiz et ve 2-4 içgörü üret.
Her içgörü ayrı bir satırda, tam olarak şu formatta yaz:
SEVERITY|TYPE|CONTENT
- SEVERITY: critical, warning, info veya positive
- TYPE: summary, alert, recommendation veya anomaly
- CONTENT: Türkçe, net ve eyleme yönelik bir cümle
Formatın dışında hiçbir şey yazma. Sadece içgörü satırları."""


def _build_context(db, since: datetime) -> str:
    now = datetime.utcnow()

    recent_updates = db.execute(text("""
        SELECT s.tracking_number, su.status, su.location, su.description
        FROM shipment_updates su
        JOIN shipments s ON s.id = su.shipment_id
        WHERE su.timestamp >= :since
        ORDER BY su.timestamp DESC LIMIT 20
    """), {"since": since}).fetchall()

    status_counts = db.execute(text("""
        SELECT status, COUNT(*) AS cnt FROM shipments
        GROUP BY status
    """)).fetchall()

    delayed_details = db.execute(text("""
        SELECT s.tracking_number, s.carrier, s.recipient_name,
               s.estimated_delivery,
               CAST((julianday(:now) - julianday(s.estimated_delivery)) * 24 AS INTEGER) AS hours_late
        FROM shipments s
        WHERE s.estimated_delivery IS NOT NULL
          AND s.estimated_delivery < :now
          AND s.status NOT IN ('delivered','failed','returned')
        ORDER BY hours_late DESC LIMIT 5
    """), {"now": now}).fetchall()

    status_str = ", ".join(f"{r.status}: {r.cnt}" for r in status_counts)

    updates_str = ""
    if recent_updates:
        updates_str = "\n".join(
            f"- {r.tracking_number} → {r.status} @ {r.location or 'bilinmiyor'}"
            for r in recent_updates[:10]
        )
    else:
        updates_str = "Son 3 dakikada durum değişikliği yok."

    delayed_str = ""
    if delayed_details:
        delayed_str = "\n".join(
            f"- {r.tracking_number} ({r.carrier}): {r.hours_late}s gecikme, alıcı: {r.recipient_name}"
            for r in delayed_details
        )
    else:
        delayed_str = "Gecikmiş kargo yok."

    return f"""
Kargo Pipeline Durumu ({now.strftime('%d.%m.%Y %H:%M')}):

Durum Dağılımı:
{status_str}

Son 3 Dakikada Durum Değişiklikleri:
{updates_str}

En Kritik Gecikmeler:
{delayed_str}
""".strip()


def run_shipment_agent() -> None:
    db = SessionLocal()
    try:
        import simulation as sim
        since = datetime.utcnow() - timedelta(minutes=4)
        sim._advance_shipments_pipeline(db)
        db.commit()

        context = _build_context(db, since)
        raw = call_groq_for_insight(SYSTEM_PROMPT, context, max_tokens=250)
        if not raw:
            return
        insights = parse_insight_lines(raw)
        write_insights(db, insights, "shipment")
        db.commit()
        print(f"[Agent:shipment] pipeline ilerledi, {len(insights)} içgörü yazıldı.")
    except Exception as e:
        db.rollback()
        print(f"[Agent:shipment] Hata: {e}")
    finally:
        db.close()
