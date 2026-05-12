"""
Background simulation engine — makes the cooperative feel operationally alive.
Runs as an asyncio task via FastAPI lifespan, ticking every 45 seconds.
Each tick advances shipments, drains inventory, and may generate complaints or anomalies.
A second hourly loop runs deterministic operational scans and writes alerts.
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text

from database import SessionLocal
from message_intel import brief_summary, classify_customer_message
from models import (
    Shipment, ShipmentStatus, ShipmentUpdate,
    Inventory, InventoryMovement,
    CustomerMessage, Customer,
    OperationalAlert,
    Order,
    OrderStatus,
    OrderItem,
    Product,
)

TICK_INTERVAL = 45   # seconds
HOURLY_INTERVAL = 3600  # seconds

COMPLAINT_TEMPLATES = [
    ("Teslimat gecikmesi",
     "Siparişim {days} gündür gelmedi, kargo durumu hakkında bilgi alabilir miyim?"),
    ("Ürün kalitesi sorunu",
     "Son teslimatımda {product} ürünleri bozuk geldi, iade yapmam gerekiyor."),
    ("Acil stok talebi",
     "{product} için acil {qty} adetlik sipariş vermek istiyorum, stok var mı?"),
    ("Hasar görmüş paket",
     "Bugün gelen paketlerimden biri hasar görmüş vaziyetteydi, ne yapmalıyım?"),
    ("Fatura sorunu",
     "Son faturamda eksik ürün görünüyor, kontrol edilmesini rica ediyorum."),
]

SHIPMENT_ADVANCE_LOCATIONS = {
    "in_transit":       ("Transfer Merkezi", "Kargo taşıyıcı aktarma merkezine ulaştı."),
    "at_facility":      ("Dağıtım Şubesi",   "Kargo hedef şehirdeki şubeye ulaştı."),
    "out_for_delivery": ("Dağıtım Aracı",    "Kargo dağıtıma çıktı."),
    "delivered":        ("Teslim Noktası",   "Kargo başarıyla teslim edildi."),
}

TRANSITIONS = {
    "preparing":        "in_transit",
    "in_transit":       "at_facility",
    "at_facility":      "out_for_delivery",
    "out_for_delivery": "delivered",
}

TURKISH_FIRST_NAMES = [
    "Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "Hasan", "İbrahim",
    "Ayşe", "Fatma", "Zeynep", "Elif", "Emine", "Hatice", "Büşra",
    "Yusuf", "Ömer", "Murat", "Emre", "Can", "Burak",
    "Selin", "Gizem", "Esra", "Ceren", "Merve",
]
TURKISH_LAST_NAMES = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Doğan", "Kılıç",
    "Yıldız", "Öztürk", "Arslan", "Aydın", "Özdemir", "Bulut", "Er",
    "Polat", "Koç", "Kurt", "Güneş", "Tekin", "Keskin",
    "Aktaş", "Çetin", "Karaca", "Bozkurt", "Demirci",
]
EMAIL_DOMAINS = ["gmail.com", "hotmail.com", "yahoo.com.tr", "yandex.com.tr"]
CITIES = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya",
    "Konya", "Gaziantep", "Mersin", "Eskişehir", "Kayseri",
]
CARRIERS = ["Yurtiçi Kargo", "Aras Kargo", "MNG Kargo", "PTT Kargo"]
CARRIER_TRACKING_PREFIXES = {
    "Yurtiçi Kargo": "YK", "Aras Kargo": "AR",
    "MNG Kargo": "MN", "PTT Kargo": "PT",
}


def _slugify(s: str) -> str:
    replacements = {
        "ş": "s", "ı": "i", "ö": "o", "ü": "u", "ç": "c", "ğ": "g",
        "Ş": "S", "İ": "I", "Ö": "O", "Ü": "U", "Ç": "C", "Ğ": "G",
        " ": "", ".": "", "&": "",
    }
    result = s.lower()
    for k, v in replacements.items():
        result = result.replace(k, v)
    return result


def _new_tracking_number(carrier: str) -> str:
    prefix = CARRIER_TRACKING_PREFIXES.get(carrier, "KG")
    return f"{prefix}{random.randint(900000000, 999999999)}"


async def run_loop():
    """Main simulation loop. Runs forever until cancelled."""
    print(f"[Simulation] Engine started — ticking every {TICK_INTERVAL}s")
    while True:
        await asyncio.sleep(TICK_INTERVAL)
        try:
            _tick()
        except Exception as exc:
            print(f"[Simulation] Tick error: {exc}")


def _tick():
    db = SessionLocal()
    try:
        actions = [
            _advance_shipment_status,
            _advance_shipment_status,   # double-weighted
            _decrease_inventory,
            _maybe_generate_complaint,
            _maybe_create_anomaly,
            _generate_new_order,
        ]
        chosen = random.sample(actions, k=random.randint(1, 2))
        for action in chosen:
            action(db)
        db.commit()
    finally:
        db.close()


def _generate_new_order(db):
    """20% chance per tick: create a new Order + OrderItems + Shipment."""
    if random.random() > 0.20:
        return

    products = db.query(Product).all()
    if not products:
        return

    now = datetime.utcnow()
    customer = None
    use_existing = random.random() < 0.70

    if use_existing:
        cutoff = now - timedelta(days=30)
        recent_rows = db.execute(
            text("""
                SELECT customer_id, COUNT(*) AS cnt
                FROM orders
                WHERE created_at >= :cutoff
                GROUP BY customer_id
                ORDER BY cnt DESC
                LIMIT 20
            """),
            {"cutoff": cutoff},
        ).fetchall()
        if recent_rows:
            weights = [r.cnt for r in recent_rows]
            chosen_row = random.choices(recent_rows, weights=weights, k=1)[0]
            customer = db.query(Customer).filter(Customer.id == chosen_row.customer_id).first()
        if customer is None:
            all_customers = db.query(Customer).all()
            if all_customers:
                customer = random.choice(all_customers)

    if customer is None:
        first = random.choice(TURKISH_FIRST_NAMES)
        last = random.choice(TURKISH_LAST_NAMES)
        full_name = f"{first} {last}"
        slug = _slugify(full_name)
        suffix = random.randint(100, 9999)
        email = f"{slug}{suffix}@{random.choice(EMAIL_DOMAINS)}"
        if db.query(Customer).filter(Customer.email == email).first():
            email = f"{slug}{suffix}{random.randint(10, 99)}@{random.choice(EMAIL_DOMAINS)}"
        customer = Customer(
            name=full_name,
            email=email,
            phone=f"05{random.randint(30, 59)}{random.randint(1000000, 9999999)}",
            customer_type="bireysel",
        )
        db.add(customer)
        db.flush()

    # Build item list based on customer history or random
    past_items = db.execute(
        text("""
            SELECT oi.product_id, AVG(oi.quantity) AS avg_qty
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.customer_id = :cid
            GROUP BY oi.product_id
        """),
        {"cid": customer.id},
    ).fetchall() if customer.id else []

    if past_items:
        n_items = min(len(past_items), random.randint(1, 3))
        selected_rows = random.sample(past_items, k=n_items)
        selected_products, quantities = [], []
        for row in selected_rows:
            p = db.query(Product).filter(Product.id == row.product_id).first()
            if p:
                base_qty = max(1, int(row.avg_qty))
                selected_products.append(p)
                quantities.append(max(1, round(base_qty * random.uniform(0.7, 1.3))))
    else:
        n = random.randint(1, 3)
        selected_products = random.sample(products, k=min(n, len(products)))
        quantities = [random.randint(1, 5) for _ in selected_products]

    if not selected_products:
        return

    city = random.choice(CITIES)
    carrier = random.choice(CARRIERS)
    tracking = _new_tracking_number(carrier)

    order = Order(
        customer_id=customer.id,
        status=OrderStatus.processing,
        created_at=now,
        updated_at=now,
        shipping_address=f"Merkez Mah. No:{random.randint(1, 200)}, {city}",
        tracking_number=tracking,
    )
    db.add(order)
    db.flush()

    for p, qty in zip(selected_products, quantities):
        db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=p.price))

    shipment = Shipment(
        order_id=order.id,
        tracking_number=tracking,
        carrier=carrier,
        status=ShipmentStatus.preparing,
        created_at=now,
        updated_at=now,
        estimated_delivery=now + timedelta(days=5),
        recipient_name=customer.name,
        recipient_address=order.shipping_address,
    )
    db.add(shipment)
    db.flush()

    db.add(ShipmentUpdate(
        shipment_id=shipment.id,
        status="preparing",
        location=f"{city} Kooperatif Deposu",
        description="Ürünler paketlendi, kargo taşıyıcıya hazır.",
        timestamp=now,
    ))

    backlog = db.execute(
        text("SELECT COUNT(*) FROM orders WHERE status IN ('pending','processing')")
    ).scalar() or 0
    if backlog > 15:
        existing_backlog = db.query(OperationalAlert).filter(
            OperationalAlert.type == "pending_orders",
            OperationalAlert.is_resolved == False,
        ).first()
        if not existing_backlog:
            db.add(OperationalAlert(
                type="pending_orders",
                severity="warning",
                title=f"Sipariş Birikimi: {backlog} Açık Sipariş",
                description=(
                    f"Şu anda {backlog} sipariş beklemede veya işleniyor. "
                    "Operasyon kapasitesi gözden geçirilmeli."
                ),
                is_resolved=False,
                created_at=now,
            ))


def _advance_shipment_status(db):
    """Advance one random non-terminal shipment to its next lifecycle stage."""
    candidates = db.query(Shipment).filter(
        Shipment.status.in_(list(TRANSITIONS.keys()))
    ).all()
    if not candidates:
        return

    shipment = random.choice(candidates)
    next_status = TRANSITIONS[shipment.status]
    shipment.status = next_status
    shipment.updated_at = datetime.utcnow()

    loc, desc = SHIPMENT_ADVANCE_LOCATIONS.get(next_status, ("Bilinmeyen Konum", "Kargo hareket etti."))
    db.add(ShipmentUpdate(
        shipment_id=shipment.id,
        status=next_status,
        location=loc,
        description=desc,
        timestamp=datetime.utcnow(),
    ))

    if next_status == "delivered":
        _resolve_alert_for_entity(db, "delayed_shipment", shipment.id)


def _decrease_inventory(db):
    """Consume inventory for a recent processing order, trigger low-stock alerts if needed."""
    recent_orders = (
        db.query(Order)
        .filter(Order.status == OrderStatus.processing)
        .order_by(Order.created_at.desc())
        .limit(20)
        .all()
    )
    if not recent_orders:
        return

    order = random.choice(recent_orders)
    for item in order.items:
        inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
        if not inv:
            continue
        consumed = round(min(item.quantity * random.uniform(0.3, 0.8), inv.quantity_kg), 2)
        if consumed <= 0:
            continue
        inv.quantity_kg = round(max(0.0, inv.quantity_kg - consumed), 2)
        inv.last_updated = datetime.utcnow()
        db.add(InventoryMovement(
            product_id=item.product_id,
            order_id=order.id,
            quantity_change=-consumed,
            movement_type="order_fulfillment",
            timestamp=datetime.utcnow(),
        ))
        if inv.quantity_kg < inv.min_threshold:
            _ensure_low_stock_alert(db, inv)


def _maybe_generate_complaint(db):
    """10% chance per tick: generate an inbound customer complaint message."""
    if random.random() > 0.10:
        return
    customers = db.query(Customer).all()
    products = db.query(Product).all()
    if not customers or not products:
        return
    customer = random.choice(customers)
    product = random.choice(products)
    subject, body_tmpl = random.choice(COMPLAINT_TEMPLATES)
    body = body_tmpl.format(
        days=random.randint(2, 6),
        product=product.name,
        qty=random.randint(10, 50),
    )
    cat, urg = classify_customer_message(subject)
    co_rows = db.query(Order).filter(Order.customer_id == customer.id).all()
    co = random.choice(co_rows) if co_rows else None
    oid = co.id if co else None
    sid = co.shipment.id if co and co.shipment else None

    db.add(CustomerMessage(
        customer_id=customer.id,
        direction="inbound",
        subject=subject,
        body=body,
        created_at=datetime.utcnow(),
        is_read=False,
        ai_generated=False,
        category=cat,
        urgency=urg,
        ai_summary=brief_summary(customer.name, cat, subject),
        related_order_id=oid,
        related_shipment_id=sid,
    ))
    if urg == "yüksek" and random.random() < 0.35:
        db.add(OperationalAlert(
            type="complaint",
            severity="warning",
            title=f"Müşteri iletişimi — {subject}",
            description=f"{customer.name}: {body[:160]}…",
            is_resolved=False,
            created_at=datetime.utcnow(),
            related_entity_id=oid,
        ))


def _maybe_create_anomaly(db):
    """5% chance per tick: detect stuck shipment and create an anomaly alert."""
    if random.random() > 0.05:
        return
    overdue_threshold = datetime.utcnow() - timedelta(days=1)
    stuck = (
        db.query(Shipment)
        .filter(
            Shipment.status == ShipmentStatus.in_transit,
            Shipment.estimated_delivery < overdue_threshold,
        )
        .first()
    )
    if not stuck:
        return
    existing = db.query(OperationalAlert).filter(
        OperationalAlert.type == "anomaly",
        OperationalAlert.related_entity_id == stuck.id,
        OperationalAlert.is_resolved == False,
    ).first()
    if existing:
        return
    db.add(OperationalAlert(
        type="anomaly",
        severity="critical",
        title=f"Kargo {stuck.tracking_number} Beklenmedik Durum",
        description=(
            f"{stuck.carrier} kargosunda sistem anomalisi tespit edildi. "
            f"Tahmini teslimat {stuck.estimated_delivery.strftime('%d.%m.%Y')} "
            f"tarihiydi ve kargo hâlâ yolda. Manuel kontrol gerekiyor."
        ),
        is_resolved=False,
        created_at=datetime.utcnow(),
        related_entity_id=stuck.id,
    ))


def _ensure_low_stock_alert(db, inv):
    """Create a low-stock alert only if no unresolved one exists for this product."""
    existing = db.query(OperationalAlert).filter(
        OperationalAlert.type == "low_stock",
        OperationalAlert.related_entity_id == inv.product_id,
        OperationalAlert.is_resolved == False,
    ).first()
    if existing:
        return
    severity = "critical" if inv.quantity_kg < inv.min_threshold * 0.5 else "warning"
    db.add(OperationalAlert(
        type="low_stock",
        severity=severity,
        title=f"{inv.product.name} Stok Uyarısı",
        description=(
            f"{inv.product.name} stoku {inv.quantity_kg:.1f} {inv.product.unit} "
            f"seviyesine düştü (eşik: {inv.min_threshold} {inv.product.unit}). "
            f"Yenileme noktası: {inv.reorder_point} {inv.product.unit}."
        ),
        is_resolved=False,
        created_at=datetime.utcnow(),
        related_entity_id=inv.product_id,
    ))


# ── Hourly agent scan ─────────────────────────────────────────────────────────

async def run_hourly_loop():
    """Hourly deterministic operational scan — separate asyncio.Task from run_loop."""
    print("[HourlyAgent] Hourly scan loop started")
    while True:
        await asyncio.sleep(HOURLY_INTERVAL)
        try:
            _hourly_scan()
        except Exception as exc:
            print(f"[HourlyAgent] Scan error: {exc}")


def _hourly_scan():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        _scan_delayed_shipments(db, now)
        _scan_message_complaints(db, today_start)
        _scan_low_stock_hourly(db)
        _scan_overdue_orders(db, now)
        _scan_restock_suggestions(db, now)
        db.commit()
        print(f"[HourlyAgent] Scan complete at {now.strftime('%H:%M:%S')}")
    finally:
        db.close()


def _scan_delayed_shipments(db, now):
    rows = db.execute(
        text("""
            SELECT id FROM shipments
            WHERE estimated_delivery < :now
              AND status NOT IN ('delivered','failed','returned')
        """),
        {"now": now},
    ).fetchall()
    for row in rows:
        existing = db.query(OperationalAlert).filter(
            OperationalAlert.type == "delayed_shipment",
            OperationalAlert.related_entity_id == row.id,
            OperationalAlert.is_resolved == False,
        ).first()
        if existing:
            continue
        shipment = db.query(Shipment).filter(Shipment.id == row.id).first()
        if not shipment:
            continue
        db.add(OperationalAlert(
            type="delayed_shipment",
            severity="critical",
            title=f"Kargo {shipment.tracking_number} Gecikti",
            description=(
                f"{shipment.carrier} operatörü tarafından taşınan kargo "
                f"tahmini teslimat tarihini geçti. Müşteri bilgilendirmesi gerekiyor."
            ),
            is_resolved=False,
            created_at=now,
            related_entity_id=shipment.id,
        ))


def _scan_message_complaints(db, today_start):
    rows = db.execute(
        text("""
            SELECT category, COUNT(*) AS cnt
            FROM customer_messages
            WHERE direction = 'inbound'
              AND created_at >= :today
              AND category IS NOT NULL
            GROUP BY category
        """),
        {"today": today_start},
    ).fetchall()
    cat_map = {r.category: r.cnt for r in rows}
    delay_count = cat_map.get("teslimat_gecikmesi", 0)
    if delay_count > 2:
        existing = db.query(OperationalAlert).filter(
            OperationalAlert.type == "complaint_cluster",
            OperationalAlert.is_resolved == False,
            OperationalAlert.created_at >= today_start,
        ).first()
        if not existing:
            db.add(OperationalAlert(
                type="complaint_cluster",
                severity="warning",
                title=f"Teslimat Gecikme Şikayeti Kümesi ({delay_count} Mesaj)",
                description=(
                    f"Bugün {delay_count} müşteri teslimat gecikmesi bildirdi. "
                    "Kargo operatörleriyle iletişim ve müşteri bilgilendirmesi önerilir."
                ),
                is_resolved=False,
                created_at=datetime.utcnow(),
            ))


def _scan_low_stock_hourly(db):
    rows = db.execute(
        text("""
            SELECT i.product_id, i.quantity_kg, i.min_threshold, i.reorder_point,
                   p.name, p.unit
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            WHERE i.quantity_kg < i.min_threshold
        """)
    ).fetchall()
    for row in rows:
        existing = db.query(OperationalAlert).filter(
            OperationalAlert.type == "low_stock",
            OperationalAlert.related_entity_id == row.product_id,
            OperationalAlert.is_resolved == False,
        ).first()
        if existing:
            continue
        severity = "critical" if row.quantity_kg < row.min_threshold * 0.5 else "warning"
        db.add(OperationalAlert(
            type="low_stock",
            severity=severity,
            title=f"{row.name} Stok Uyarısı",
            description=(
                f"{row.name} stoku {row.quantity_kg:.1f} {row.unit} seviyesine düştü "
                f"(eşik: {row.min_threshold} {row.unit}). "
                f"Yenileme noktası: {row.reorder_point} {row.unit}."
            ),
            is_resolved=False,
            created_at=datetime.utcnow(),
            related_entity_id=row.product_id,
        ))


def _scan_overdue_orders(db, now):
    cutoff = now - timedelta(days=5)
    rows = db.execute(
        text("""
            SELECT o.id, c.name AS customer_name
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.created_at <= :cutoff
              AND o.status NOT IN ('delivered','cancelled')
        """),
        {"cutoff": cutoff},
    ).fetchall()
    for row in rows:
        existing = db.query(OperationalAlert).filter(
            OperationalAlert.type == "overdue_order",
            OperationalAlert.related_entity_id == row.id,
            OperationalAlert.is_resolved == False,
        ).first()
        if existing:
            continue
        db.add(OperationalAlert(
            type="overdue_order",
            severity="warning",
            title=f"Sipariş #{row.id} 5+ Gündür Teslim Edilmedi",
            description=(
                f"{row.customer_name} müşterisine ait #{row.id} numaralı sipariş "
                f"5 günden uzun süredir teslim edilmemiş. Manuel kontrol gerekiyor."
            ),
            is_resolved=False,
            created_at=now,
            related_entity_id=row.id,
        ))


def _scan_restock_suggestions(db, now):
    cutoff_14d = now - timedelta(days=14)
    rows = db.execute(
        text("""
            SELECT i.product_id, i.quantity_kg, i.reorder_point, p.name, p.unit
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            WHERE i.quantity_kg < i.reorder_point
        """)
    ).fetchall()
    for row in rows:
        existing = db.query(OperationalAlert).filter(
            OperationalAlert.type == "restock_suggestion",
            OperationalAlert.related_entity_id == row.product_id,
            OperationalAlert.is_resolved == False,
        ).first()
        if existing:
            continue
        total_consumed = db.execute(
            text("""
                SELECT ABS(SUM(quantity_change)) AS total
                FROM inventory_movements
                WHERE product_id = :pid
                  AND quantity_change < 0
                  AND timestamp >= :cutoff
            """),
            {"pid": row.product_id, "cutoff": cutoff_14d},
        ).scalar() or 0.0
        avg_daily = float(total_consumed) / 14.0
        deficit = max(0.0, float(row.reorder_point) - float(row.quantity_kg))
        raw_qty = deficit + avg_daily * 7
        suggest_qty = max(10, round(raw_qty / 10) * 10)
        db.add(OperationalAlert(
            type="restock_suggestion",
            severity="info",
            title=f"{row.name} İçin Sipariş Önerisi: {suggest_qty} {row.unit}",
            description=(
                f"{row.name}: mevcut stok {row.quantity_kg:.1f} {row.unit}, "
                f"yenileme noktası {row.reorder_point} {row.unit}. "
                f"Son 14 günlük ort. tüketim: {avg_daily:.1f} {row.unit}/gün. "
                f"Önerilen sipariş miktarı: {suggest_qty} {row.unit}."
            ),
            is_resolved=False,
            created_at=now,
            related_entity_id=row.product_id,
        ))


def _resolve_alert_for_entity(db, alert_type: str, entity_id: int):
    alert = db.query(OperationalAlert).filter(
        OperationalAlert.type == alert_type,
        OperationalAlert.related_entity_id == entity_id,
        OperationalAlert.is_resolved == False,
    ).first()
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()


# ── Manual simulation trigger (used by /simulate/event endpoint) ──────────────

def trigger_event(event_type: str, target_id: Optional[int] = None):
    """Called synchronously from the simulate router — no asyncio needed."""
    db = SessionLocal()
    try:
        if event_type == "delayed_shipment":
            _trigger_delayed_shipment(db, target_id)
        elif event_type == "stock_drop":
            _trigger_stock_drop(db, target_id)
        elif event_type == "complaint":
            _maybe_generate_complaint.__wrapped__(db) if hasattr(_maybe_generate_complaint, "__wrapped__") else _force_complaint(db)
        elif event_type == "anomaly":
            _trigger_anomaly(db, target_id)
        elif event_type == "delivery":
            _trigger_delivery(db, target_id)
        db.commit()
    finally:
        db.close()


def _trigger_delayed_shipment(db, target_id):
    if target_id:
        shipment = db.query(Shipment).filter(Shipment.id == target_id).first()
    else:
        shipment = (
            db.query(Shipment)
            .filter(Shipment.status.in_(["in_transit", "at_facility"]))
            .order_by(Shipment.updated_at)
            .first()
        )
    if not shipment:
        return
    # Push estimated_delivery into the past so it registers as delayed
    shipment.estimated_delivery = datetime.utcnow() - timedelta(days=2)
    shipment.updated_at = datetime.utcnow()
    db.add(ShipmentUpdate(
        shipment_id=shipment.id,
        status=shipment.status,
        location="Transfer Merkezi",
        description="Kargo beklenmedik operasyonel gecikme nedeniyle tutuldu.",
        timestamp=datetime.utcnow(),
    ))
    db.add(OperationalAlert(
        type="delayed_shipment",
        severity="critical",
        title=f"Kargo {shipment.tracking_number} Gecikti",
        description=(
            f"{shipment.carrier} operatörü tarafından taşınan kargo "
            f"tahmini teslimat tarihini geçti. Müşteri bilgilendirmesi gerekiyor."
        ),
        is_resolved=False,
        created_at=datetime.utcnow(),
        related_entity_id=shipment.id,
    ))


def _trigger_stock_drop(db, target_id):
    if target_id:
        inv = db.query(Inventory).filter(Inventory.product_id == target_id).first()
    else:
        # Pick a random product that is not already at 0
        inv = (
            db.query(Inventory)
            .filter(Inventory.quantity_kg > 10)
            .order_by(Inventory.quantity_kg)
            .first()
        )
    if not inv:
        return
    drop = round(inv.quantity_kg * random.uniform(0.3, 0.6), 2)
    inv.quantity_kg = round(max(0.0, inv.quantity_kg - drop), 2)
    inv.last_updated = datetime.utcnow()
    db.add(InventoryMovement(
        product_id=inv.product_id,
        order_id=None,
        quantity_change=-drop,
        movement_type="simulation",
        timestamp=datetime.utcnow(),
    ))
    if inv.quantity_kg < inv.min_threshold:
        _ensure_low_stock_alert(db, inv)


def _force_complaint(db):
    customers = db.query(Customer).all()
    products = db.query(Product).all()
    if not customers or not products:
        return
    customer = random.choice(customers)
    product = random.choice(products)
    subject, body_tmpl = random.choice(COMPLAINT_TEMPLATES)
    body = body_tmpl.format(
        days=random.randint(2, 6),
        product=product.name,
        qty=random.randint(10, 50),
    )
    cat, urg = classify_customer_message(subject)
    co_rows = db.query(Order).filter(Order.customer_id == customer.id).all()
    co = random.choice(co_rows) if co_rows else None
    oid = co.id if co else None
    sid = co.shipment.id if co and co.shipment else None

    db.add(CustomerMessage(
        customer_id=customer.id,
        direction="inbound",
        subject=subject,
        body=body,
        created_at=datetime.utcnow(),
        is_read=False,
        ai_generated=False,
        category=cat,
        urgency=urg,
        ai_summary=brief_summary(customer.name, cat, subject),
        related_order_id=oid,
        related_shipment_id=sid,
    ))
    db.add(OperationalAlert(
        type="complaint",
        severity="warning" if urg == "yüksek" else "info",
        title=f"Yeni Müşteri Şikayeti: {subject}",
        description=f"{customer.name} müşterisinden yeni şikayet alındı: {body[:120]}",
        is_resolved=False,
        created_at=datetime.utcnow(),
        related_entity_id=oid,
    ))


def _trigger_anomaly(db, target_id):
    if target_id:
        shipment = db.query(Shipment).filter(Shipment.id == target_id).first()
    else:
        shipment = (
            db.query(Shipment)
            .filter(Shipment.status.in_(["in_transit", "at_facility"]))
            .order_by(Shipment.updated_at)
            .first()
        )
    if not shipment:
        return
    shipment.status = ShipmentStatus.failed
    shipment.updated_at = datetime.utcnow()
    db.add(ShipmentUpdate(
        shipment_id=shipment.id,
        status="failed",
        location="Dağıtım Merkezi",
        description="Kargo teslimat hatası. Tekrar deneme veya iade işlemi gerekiyor.",
        timestamp=datetime.utcnow(),
    ))
    db.add(OperationalAlert(
        type="anomaly",
        severity="critical",
        title=f"Kargo Teslimat Hatası — {shipment.tracking_number}",
        description=(
            f"{shipment.carrier} kargosunda teslimat başarısız oldu. "
            f"Müşteri bildirilmeli ve alternatif teslimat planlanmalı."
        ),
        is_resolved=False,
        created_at=datetime.utcnow(),
        related_entity_id=shipment.id,
    ))


def _trigger_delivery(db, target_id):
    if target_id:
        shipment = db.query(Shipment).filter(Shipment.id == target_id).first()
    else:
        shipment = (
            db.query(Shipment)
            .filter(Shipment.status == ShipmentStatus.out_for_delivery)
            .order_by(Shipment.updated_at)
            .first()
        )
    if not shipment:
        # Fall back to at_facility
        shipment = (
            db.query(Shipment)
            .filter(Shipment.status == ShipmentStatus.at_facility)
            .first()
        )
    if not shipment:
        return
    shipment.status = ShipmentStatus.delivered
    shipment.updated_at = datetime.utcnow()
    db.add(ShipmentUpdate(
        shipment_id=shipment.id,
        status="delivered",
        location="Teslim Noktası",
        description="Kargo başarıyla teslim edildi.",
        timestamp=datetime.utcnow(),
    ))
    _resolve_alert_for_entity(db, "delayed_shipment", shipment.id)
