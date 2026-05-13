from datetime import datetime, timedelta

from sqlalchemy import text

from agents.gemini_client import call_gemini_for_insight as call_groq_for_insight, parse_insight_lines, write_insights, _context_hash
from database import SessionLocal

SYSTEM_PROMPT = """Sen Anadolu Tarım ve Gıda Kooperatifi'nin Envanter ve Tedarik Analisti'sin.
Sana verilen stok, tüketim ve sipariş talebini analiz et ve tam olarak 4 içgörü üret.

İLK 3 IÇGÖRÜ — Stok durumu:
ODAK: Hangi ürünler kritik stok altında? Hangileri sipariş önerisi gerektiriyor?
KRİTİK etiketli ürünler gerçekten eşiğin altında. UYARI etiketliler ise min_threshold'un üstünde sadece sipariş önerisi.

4. IÇGÖRÜ — Talep analizi (SON 10 GÜN):
En çok sipariş edilen 3 ürünü belirt ve stok yenileme önerisi yap.
Format: "Son 10 günde en çok sipariş edilen ürünler [A], [B] ve [C] oldu; stok yenilemeyi değerlendirin."

ÇIKTI KURALLARI — KESİNLİKLE UY:
- Her satır tam olarak şu formatta olmalı: SEVERITY|TYPE|CONTENT
- SEVERITY değerleri: critical, warning, info, positive (küçük harf)
- TYPE değerleri: summary, alert, recommendation, anomaly (küçük harf)
- CONTENT: Türkçe, tam ve anlamlı bir cümle (en az 15 kelime). Asla yarım bırakma.
- "CONTENT:" yazma, sadece cümleyi yaz. Tire, yıldız, numara yok.

ÖRNEK (bu formatı birebir kullan):
critical|alert|Karabiber stoğu yalnızca 2 günlük tüketime yetecek 45 kg kaldı, bugün tedarik siparişi verilmesi zorunlu.
warning|recommendation|İsot ve Kırmızı Biber yeniden sipariş noktasının altına düştü, bu hafta içinde temin edilmezse stok açığı oluşur.
info|summary|Zeytinyağı son 14 günde 320 kg tükenerek en yüksek tüketimli ürün oldu, mevcut stok 18 güne yeterli.
info|recommendation|Son 10 günde en çok sipariş edilen ürünler Biber Salçası, Kırmızı Biber ve İsot oldu; yoğun talebi karşılamak için stok yenilemeyi değerlendirin."""


def _build_context(db) -> str:
    now = datetime.utcnow()
    cutoff_14d = now - timedelta(days=14)
    cutoff_10d = now - timedelta(days=10)

    # Items BELOW min_threshold — truly critical, immediate action needed
    critical_items = db.execute(text("""
        SELECT p.id, p.name, p.category, i.quantity_kg, i.min_threshold, i.reorder_point
        FROM inventory i JOIN products p ON p.id = i.product_id
        WHERE i.quantity_kg < i.min_threshold
        ORDER BY (i.quantity_kg / NULLIF(i.min_threshold, 0)) ASC
        LIMIT 5
    """)).fetchall()

    # Items BELOW reorder_point but ABOVE min_threshold — warning/order recommendation only
    warning_items = db.execute(text("""
        SELECT p.id, p.name, p.category, i.quantity_kg, i.min_threshold, i.reorder_point
        FROM inventory i JOIN products p ON p.id = i.product_id
        WHERE i.quantity_kg >= i.min_threshold AND i.quantity_kg < i.reorder_point
        ORDER BY (i.quantity_kg / NULLIF(i.reorder_point, 0)) ASC
        LIMIT 5
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

    # Top-3 most ordered products in last 10 days (by total quantity ordered)
    top_demand = db.execute(text("""
        SELECT p.name, p.category,
               SUM(oi.quantity) AS total_ordered,
               COUNT(DISTINCT oi.order_id) AS order_count
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        JOIN orders o ON o.id = oi.order_id
        WHERE o.created_at >= :cutoff
        GROUP BY p.id, p.name, p.category
        ORDER BY total_ordered DESC
        LIMIT 3
    """), {"cutoff": cutoff_10d}).fetchall()

    total_products = db.execute(text("SELECT COUNT(*) FROM inventory")).scalar() or 0
    healthy = db.execute(text("""
        SELECT COUNT(*) FROM inventory WHERE quantity_kg >= reorder_point
    """)).scalar() or 0

    def fmt_item(r, threshold_field):
        cons = next((c for c in consumption_rows if c.product_id == r.id), None)
        avg_daily = round(cons.consumed_14d / max(cons.active_days, 1), 1) if cons and cons.active_days else 0
        days_left = round(r.quantity_kg / avg_daily) if avg_daily > 0 else "?"
        threshold = r.min_threshold if threshold_field == "min" else r.reorder_point
        return (
            f"- {r.name} ({r.category}): {r.quantity_kg:.0f} kg mevcut, "
            f"eşik={threshold:.0f} kg, günlük tüketim≈{avg_daily} kg, "
            f"tahmini {days_left} gün yeterli"
        )

    if critical_items:
        critical_str = "\n".join(fmt_item(r, "min") for r in critical_items)
    else:
        critical_str = "Kritik stok altında ürün yok."

    if warning_items:
        warning_str = "\n".join(fmt_item(r, "reorder") for r in warning_items)
    else:
        warning_str = "Yeniden sipariş önerisi gerektiren ürün yok."

    consumption_str = "\n".join(
        f"- {r.name}: 14 günde {r.consumed_14d:.0f} kg tüketildi"
        for r in consumption_rows[:5]
    ) or "Tüketim verisi yok."

    top_demand_str = "\n".join(
        f"- {r.name} ({r.category}): {r.total_ordered:.0f} birim, {r.order_count} siparişte"
        for r in top_demand
    ) or "Sipariş verisi yok."

    return f"""
Envanter Analizi ({now.strftime('%d.%m.%Y %H:%M')}):

Toplam ürün: {total_products}, sağlıklı stok: {healthy}
KRİTİK (min_threshold altı, acil müdahale): {len(critical_items)} ürün
UYARI (reorder_point altı ama min_threshold üstü, sipariş önerisi): {len(warning_items)} ürün

--- KRİTİK STOK (min_threshold altında — bu ürünler gerçekten kritik) ---
{critical_str}

--- UYARI: SİPARİŞ ÖNERİSİ (min_threshold üstünde, sadece sipariş önerisi) ---
{warning_str}

En Yüksek Tüketim (14 gün):
{consumption_str}

--- SON 10 GÜNDE EN ÇOK SİPARİŞ EDİLEN ÜRÜNLER (stok yenileme önerisi için) ---
{top_demand_str}
""".strip()


def _auto_draft_supplier_orders(db) -> int:
    """Kritik stok altındaki ürünler için tedarikçi e-posta taslakları üret."""
    from models import Inventory, Product, SupplierOrderDraft
    from email_drafter import draft_supplier_email

    critical = db.execute(text("""
        SELECT i.product_id, i.quantity_kg, i.min_threshold, i.reorder_point
        FROM inventory i
        WHERE i.quantity_kg < i.min_threshold
        ORDER BY (i.quantity_kg / NULLIF(i.min_threshold, 0)) ASC
        LIMIT 3
    """)).fetchall()

    created = 0
    for row in critical:
        existing = (
            db.query(SupplierOrderDraft)
            .filter(
                SupplierOrderDraft.product_id == row.product_id,
                SupplierOrderDraft.status == "draft",
            )
            .first()
        )
        if existing:
            continue
        product = db.query(Product).filter(Product.id == row.product_id).first()
        if not product:
            continue
        suggested_qty = max(row.reorder_point * 1.5 - row.quantity_kg, 50)
        email = draft_supplier_email(
            product_name=product.name,
            category=product.category,
            quantity=suggested_qty,
            unit=product.unit,
            current_stock=row.quantity_kg,
            reorder_point=row.reorder_point,
        )
        db.add(SupplierOrderDraft(
            product_id=product.id,
            quantity=suggested_qty,
            unit=product.unit,
            supplier_email=email["supplier_email"],
            supplier_name=email["supplier_name"],
            subject=email["subject"],
            body=email["body"],
            status="draft",
            triggered_by="agent",
        ))
        created += 1
    return created


def run_inventory_agent() -> None:
    db = SessionLocal()
    try:
        context = _build_context(db)
        chash = _context_hash(context)
        raw = call_groq_for_insight(SYSTEM_PROMPT, context, max_tokens=400)
        if not raw:
            return
        insights = parse_insight_lines(raw, max_insights=4)
        for insight in insights:
            insight["entity_type"] = "inventory"
        added = write_insights(db, insights, "inventory", context_hash=chash)

        drafts = _auto_draft_supplier_orders(db)
        if drafts:
            print(f"[Agent:inventory] {drafts} tedarikçi e-posta taslağı üretildi.")
        db.commit()
        if added:
            print(f"[Agent:inventory] {added} yeni içgörü eklendi.")
    except Exception as e:
        db.rollback()
        print(f"[Agent:inventory] Hata: {e}")
    finally:
        db.close()
