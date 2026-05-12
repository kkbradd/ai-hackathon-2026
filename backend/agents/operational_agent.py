from datetime import datetime, timedelta

from sqlalchemy import text

from agents.gemini_client import call_gemini_for_insight as call_groq_for_insight, parse_insight_lines, write_insights
from database import SessionLocal

SYSTEM_PROMPT = """Sen Anadolu Tarım ve Gıda Kooperatifi'nin Operasyon Zekâ Ajanısın.
Sana verilen güncel operasyonel verileri analiz et ve 3-5 içgörü üret.
Her içgörü ayrı bir satırda, tam olarak şu formatta yaz:
SEVERITY|TYPE|CONTENT
- SEVERITY: critical, warning, info veya positive
- TYPE: summary, alert, recommendation veya anomaly
- CONTENT: Türkçe, net ve eyleme yönelik bir cümle (20-120 kelime arası)
Formatın dışında hiçbir şey yazma. Sadece içgörü satırları."""


def _build_context(db) -> str:
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    delayed = db.execute(text("""
        SELECT COUNT(*) FROM shipments
        WHERE estimated_delivery IS NOT NULL AND estimated_delivery < :now
          AND status NOT IN ('delivered','failed','returned')
    """), {"now": now}).scalar() or 0

    active = db.execute(text("""
        SELECT COUNT(*) FROM shipments WHERE status NOT IN ('delivered','failed','returned')
    """)).scalar() or 0

    pending = db.execute(text("""
        SELECT COUNT(*) FROM orders WHERE status IN ('pending','processing')
    """)).scalar() or 0

    low_stock = db.execute(text("""
        SELECT p.name, i.quantity_kg, i.min_threshold
        FROM inventory i JOIN products p ON p.id = i.product_id
        WHERE i.quantity_kg < i.min_threshold
        ORDER BY (i.quantity_kg / NULLIF(i.min_threshold, 0)) ASC
        LIMIT 5
    """)).fetchall()

    open_complaints = db.execute(text("""
        SELECT COUNT(*) FROM operational_alerts
        WHERE is_resolved = 0 AND type IN ('complaint','complaint_cluster')
    """)).scalar() or 0

    orders_today = db.execute(text("""
        SELECT COUNT(*) FROM orders WHERE created_at >= :today
    """), {"today": today_start}).scalar() or 0

    orders_yesterday = db.execute(text("""
        SELECT COUNT(*) FROM orders WHERE created_at >= :yday AND created_at < :today
    """), {"yday": yesterday_start, "today": today_start}).scalar() or 0

    revenue_today = db.execute(text("""
        SELECT COALESCE(SUM(oi.unit_price * oi.quantity), 0)
        FROM order_items oi JOIN orders o ON o.id = oi.order_id
        WHERE o.created_at >= :today
    """), {"today": today_start}).scalar() or 0

    urgent_unread = db.execute(text("""
        SELECT COUNT(*) FROM customer_messages
        WHERE direction = 'inbound' AND is_read = 0 AND urgency = 'yüksek'
    """)).scalar() or 0

    carrier_issues = db.execute(text("""
        SELECT carrier, COUNT(*) AS cnt
        FROM shipments
        WHERE estimated_delivery < :now AND status NOT IN ('delivered','failed','returned')
        GROUP BY carrier ORDER BY cnt DESC LIMIT 3
    """), {"now": now}).fetchall()

    low_stock_str = ", ".join(
        f"{r.name} ({r.quantity_kg:.0f}/{r.min_threshold:.0f} kg)"
        for r in low_stock
    ) if low_stock else "yok"

    carrier_str = ", ".join(
        f"{r.carrier}: {r.cnt} gecikme" for r in carrier_issues
    ) if carrier_issues else "yok"

    return f"""
Güncel Operasyonel Durum ({now.strftime('%d.%m.%Y %H:%M')}):

Kargo & Lojistik:
- Aktif kargo sayısı: {active}
- Gecikmiş kargo: {delayed} ({round(delayed/active*100) if active else 0}% gecikme oranı)
- Taşıyıcı bazlı gecikme: {carrier_str}

Sipariş Durumu:
- Bekleyen/işlemdeki sipariş: {pending}
- Bugün alınan sipariş: {orders_today}
- Dün alınan sipariş: {orders_yesterday}
- Bugünkü ciro: ₺{revenue_today:,.0f}

Envanter:
- Kritik stok altındaki ürünler: {low_stock_str}

Müşteri İletişimi:
- Açık şikayet uyarıları: {open_complaints}
- Okunmamış yüksek öncelikli mesaj: {urgent_unread}
""".strip()


def run_operational_agent() -> None:
    db = SessionLocal()
    try:
        context = _build_context(db)
        raw = call_groq_for_insight(SYSTEM_PROMPT, context, max_tokens=250)
        if not raw:
            return
        insights = parse_insight_lines(raw)
        write_insights(db, insights, "operational")
        db.commit()
        print(f"[Agent:operational] {len(insights)} içgörü yazıldı.")
    except Exception as e:
        db.rollback()
        print(f"[Agent:operational] Hata: {e}")
    finally:
        db.close()
