from datetime import datetime, timedelta

from sqlalchemy import text

from agents.gemini_client import call_gemini_for_insight as call_groq_for_insight, parse_insight_lines, write_insights
from database import SessionLocal

SYSTEM_PROMPT = """Sen Anadolu Tarım ve Gıda Kooperatifi'nin Müşteri İletişim Ajanısın.
Sana verilen müşteri mesajı verilerini analiz et ve 2-3 öncelik/müdahale içgörüsü üret.
Her içgörü ayrı bir satırda, tam olarak şu formatta yaz:
SEVERITY|TYPE|CONTENT
- SEVERITY: critical, warning, info veya positive
- TYPE: summary, alert, recommendation veya anomaly
- CONTENT: Türkçe, hangi müşteri sorununa nasıl müdahale edilmesi gerektiğini belirten net bir cümle
Formatın dışında hiçbir şey yazma. Sadece içgörü satırları."""

CATEGORY_LABELS = {
    "teslimat_gecikmesi": "Teslimat Gecikmesi",
    "yanlis_urun": "Yanlış Ürün",
    "siparis_talebi": "Sipariş Talebi",
    "fatura_duzeltme": "Fatura",
    "stok_bilgisi": "Stok Sorusu",
    "genel_destek": "Genel",
}


def _build_context(db) -> str:
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    category_counts = db.execute(text("""
        SELECT category, urgency, COUNT(*) AS cnt
        FROM customer_messages
        WHERE direction = 'inbound' AND created_at >= :today AND category IS NOT NULL
        GROUP BY category, urgency
        ORDER BY cnt DESC
    """), {"today": today_start}).fetchall()

    week_category = db.execute(text("""
        SELECT category, COUNT(*) AS cnt
        FROM customer_messages
        WHERE direction = 'inbound' AND created_at >= :week AND category IS NOT NULL
        GROUP BY category ORDER BY cnt DESC LIMIT 5
    """), {"week": week_start}).fetchall()

    urgent_messages = db.execute(text("""
        SELECT cm.subject, c.name AS customer_name, cm.category, cm.created_at,
               SUBSTR(cm.body, 1, 200) AS body_preview
        FROM customer_messages cm
        JOIN customers c ON c.id = cm.customer_id
        WHERE cm.direction = 'inbound' AND cm.is_read = 0 AND cm.urgency = 'yüksek'
        ORDER BY cm.created_at DESC LIMIT 5
    """)).fetchall()

    unread_total = db.execute(text("""
        SELECT COUNT(*) FROM customer_messages WHERE direction = 'inbound' AND is_read = 0
    """)).scalar() or 0

    today_total = db.execute(text("""
        SELECT COUNT(*) FROM customer_messages
        WHERE direction = 'inbound' AND created_at >= :today
    """), {"today": today_start}).scalar() or 0

    cat_str = ""
    for r in category_counts:
        label = CATEGORY_LABELS.get(r.category, r.category)
        cat_str += f"  - {label} ({r.urgency}): {r.cnt} mesaj\n"
    if not cat_str:
        cat_str = "  Bugün gelen mesaj yok.\n"

    week_str = "\n".join(
        f"  - {CATEGORY_LABELS.get(r.category, r.category)}: {r.cnt} mesaj"
        for r in week_category
    ) or "  Haftalık veri yok."

    urgent_str = ""
    for m in urgent_messages:
        urgent_str += (
            f"  - [{m.category}] {m.customer_name}: \"{m.subject}\" — {m.body_preview[:100]}...\n"
        )
    if not urgent_str:
        urgent_str = "  Acil okunmamış mesaj yok."

    return f"""
Müşteri İletişim Analizi ({now.strftime('%d.%m.%Y %H:%M')}):

Bugün toplam gelen mesaj: {today_total}
Okunmamış toplam mesaj: {unread_total}

Bugün Kategori/Aciliyet Dağılımı:
{cat_str}
Haftalık Kategori Trendi:
{week_str}

Acil Okunmamış Mesajlar:
{urgent_str}
""".strip()


def run_customer_issue_agent() -> None:
    db = SessionLocal()
    try:
        context = _build_context(db)
        raw = call_groq_for_insight(SYSTEM_PROMPT, context, max_tokens=250)
        if not raw:
            return
        insights = parse_insight_lines(raw)
        for insight in insights:
            insight["entity_type"] = "message"
        write_insights(db, insights, "customer_issue")
        db.commit()
        print(f"[Agent:customer_issue] {len(insights)} içgörü yazıldı.")
    except Exception as e:
        db.rollback()
        print(f"[Agent:customer_issue] Hata: {e}")
    finally:
        db.close()
