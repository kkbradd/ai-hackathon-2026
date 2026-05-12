from datetime import datetime, timedelta

from sqlalchemy import text

from agents.gemini_client import call_gemini_for_insight as call_groq_for_insight, parse_insight_lines, write_insights
from database import SessionLocal

SYSTEM_PROMPT = """Sen Anadolu Tarım ve Gıda Kooperatifi'nin Envanter Analiz Ajanısın.
Sana verilen stok ve tüketim verilerini analiz et ve 2-4 tedarik/envanter içgörüsü üret.
Her içgörü ayrı bir satırda, tam olarak şu formatta yaz:
SEVERITY|TYPE|CONTENT
- SEVERITY: critical, warning, info veya positive
- TYPE: summary, alert, recommendation veya anomaly
- CONTENT: Türkçe, hangi ürün için ne yapılması gerektiğini belirten net bir cümle
Formatın dışında hiçbir şey yazma. Sadece içgörü satırları."""


def _build_context(db) -> str:
    now = datetime.utcnow()
    cutoff_14d = now - timedelta(days=14)

    below_reorder = db.execute(text("""
        SELECT p.id, p.name, p.category, i.quantity_kg, i.min_threshold, i.reorder_point
        FROM inventory i JOIN products p ON p.id = i.product_id
        WHERE i.quantity_kg < i.reorder_point
        ORDER BY (i.quantity_kg / NULLIF(i.reorder_point, 0)) ASC
        LIMIT 10
    """)).fetchall()

    critical_stock = db.execute(text("""
        SELECT p.name, i.quantity_kg, i.min_threshold
        FROM inventory i JOIN products p ON p.id = i.product_id
        WHERE i.quantity_kg < i.min_threshold
        ORDER BY i.quantity_kg ASC LIMIT 5
    """)).fetchall()

    consumption_rows = db.execute(text("""
        SELECT im.product_id, p.name,
               ABS(SUM(CASE WHEN im.movement_type = 'order_fulfillment' THEN im.quantity_change ELSE 0 END)) AS consumed_14d,
               COUNT(DISTINCT DATE(im.timestamp)) AS active_days
        FROM inventory_movements im
        JOIN products p ON p.id = im.product_id
        WHERE im.timestamp >= :cutoff AND im.movement_type = 'order_fulfillment'
        GROUP BY im.product_id, p.name
        ORDER BY consumed_14d DESC LIMIT 10
    """), {"cutoff": cutoff_14d}).fetchall()

    total_products = db.execute(text("SELECT COUNT(*) FROM inventory")).scalar() or 0
    healthy = db.execute(text("""
        SELECT COUNT(*) FROM inventory WHERE quantity_kg >= reorder_point
    """)).scalar() or 0

    reorder_str = ""
    if below_reorder:
        for r in below_reorder:
            cons = next((c for c in consumption_rows if c.product_id == r.id), None)
            avg_daily = round(cons.consumed_14d / max(cons.active_days, 1), 1) if cons else 0
            days_left = round(r.quantity_kg / avg_daily) if avg_daily > 0 else 99
            reorder_str += (
                f"- {r.name} ({r.category}): {r.quantity_kg:.0f} kg mevcut, "
                f"min={r.min_threshold:.0f} kg, günlük tüketim≈{avg_daily} kg, "
                f"tahmini {days_left} gün yeterli\n"
            )
    else:
        reorder_str = "Yeniden sipariş gerektiren ürün yok.\n"

    critical_str = ", ".join(f"{r.name} ({r.quantity_kg:.0f} kg)" for r in critical_stock) or "yok"

    consumption_str = "\n".join(
        f"- {r.name}: 14 günde {r.consumed_14d:.0f} kg tüketildi"
        for r in consumption_rows[:5]
    ) or "Tüketim verisi yok."

    return f"""
Envanter Analizi ({now.strftime('%d.%m.%Y %H:%M')}):

Toplam ürün: {total_products}, sağlıklı stok: {healthy}, yeniden sipariş altı: {len(below_reorder)}

Kritik stok altındaki ürünler: {critical_str}

Yeniden Sipariş Gerektiren Ürünler:
{reorder_str}

En Yüksek Tüketim (14 gün):
{consumption_str}
""".strip()


def run_inventory_agent() -> None:
    db = SessionLocal()
    try:
        context = _build_context(db)
        raw = call_groq_for_insight(SYSTEM_PROMPT, context, max_tokens=250)
        if not raw:
            return
        insights = parse_insight_lines(raw)
        for insight in insights:
            insight["entity_type"] = "inventory"
        write_insights(db, insights, "inventory")
        db.commit()
        print(f"[Agent:inventory] {len(insights)} içgörü yazıldı.")
    except Exception as e:
        db.rollback()
        print(f"[Agent:inventory] Hata: {e}")
    finally:
        db.close()
