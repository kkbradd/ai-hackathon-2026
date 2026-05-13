from datetime import datetime, timedelta

from sqlalchemy import text

from agents.gemini_client import call_gemini_for_insight as call_groq_for_insight, parse_insight_lines, write_insights, _context_hash
from database import SessionLocal

SYSTEM_PROMPT = """Sen Anadolu Tarım ve Gıda Kooperatifi'nin Kargo Takip Analisti'sin.
Sana verilen ANLIK kargo pipeline verilerini analiz et ve tam olarak 3 içgörü üret.

ODAK: Şu an geciken kargolar kimler, kaç saattir gecikmede? Hangi taşıyıcı sorunlu?
Son dakikalarda ne değişti? Somut takip numaraları ve alıcı adlarıyla konuş.

ÇIKTI KURALLARI — KESİNLİKLE UY:
- Her satır tam olarak şu formatta olmalı: SEVERITY|TYPE|CONTENT
- SEVERITY değerleri: critical, warning, info, positive (küçük harf)
- TYPE değerleri: summary, alert, recommendation, anomaly (küçük harf)
- CONTENT: Türkçe, tam ve anlamlı bir cümle (en az 15 kelime). Asla yarım bırakma.
- "CONTENT:" yazma, sadece cümleyi yaz. Tire, yıldız, numara yok.

ÖRNEK (bu formatı birebir kullan):
critical|alert|3 kargo tahmini teslimat tarihini 6 saatten fazla geçti, en kritik durum Aras Kargo'da Mehmet Yılmaz teslimatı.
warning|anomaly|Son 10 dakikada aynı taşıyıcıdan 4 kargonun durumu güncellenmedi, sistem arızası ya da bağlantı sorunu olabilir.
positive|summary|Bugün teslim edilen 12 kargonun tamamı zamanında ulaştı, lojistik pipeline sorunsuz akıyor."""


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
            f"- {r.tracking_number} ({r.carrier}): {r.hours_late} saat gecikti, alıcı: {r.recipient_name}"
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
        chash = _context_hash(context)
        raw = call_groq_for_insight(SYSTEM_PROMPT, context, max_tokens=250)
        if not raw:
            return
        insights = parse_insight_lines(raw)
        # Gecikmiş kargo varsa ilk insight en az warning olsun
        if "Gecikmiş kargo yok" not in context and insights:
            if insights[0]["severity"] == "info":
                insights[0]["severity"] = "warning"
        added = write_insights(db, insights, "shipment", context_hash=chash)
        db.commit()
        if added:
            print(f"[Agent:shipment] {added} yeni içgörü eklendi.")
    except Exception as e:
        db.rollback()
        print(f"[Agent:shipment] Hata: {e}")
    finally:
        db.close()
