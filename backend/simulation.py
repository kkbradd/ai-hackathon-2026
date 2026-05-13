"""
Background simulation engine — makes the cooperative feel operationally alive.
Generates new orders, advances shipments through their lifecycle, and occasionally
produces complaint messages. Intelligence analysis is handled by the AI agent layer.
"""
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

DAILY_ORDER_TARGET_MIN = 8
DAILY_ORDER_TARGET_MAX = 15

QTY_MULTIPLIERS = {
    "restoran":     (10, 50),
    "market":       (20, 80),
    "bakkal":       (5,  25),
    "kafe":         (3,  15),
    "butik":        (2,  10),
    "bireysel":     (1,   5),
    "yerel_isletme":(5,  20),
    "kurumsal":     (10, 40),
}

PIPELINE_DELAYS = {
    "preparing":        (4,  8),
    "in_transit":       (24, 48),
    "at_facility":      (4,  12),
    "out_for_delivery": (2,  6),
}

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


def _generate_new_order(db):
    """Create a new order based on daily target pacing."""
    now = datetime.utcnow()

    today_count = db.execute(
        text("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now')")
    ).scalar() or 0

    hour = now.hour
    expected_ratio = min(hour / 18.0, 1.0)
    daily_target = random.randint(DAILY_ORDER_TARGET_MIN, DAILY_ORDER_TARGET_MAX)
    expected_count = daily_target * expected_ratio

    if today_count >= expected_count * 1.5 and random.random() > 0.15:
        return
    if today_count >= DAILY_ORDER_TARGET_MAX:
        return
    if random.random() > 0.50:
        return

    products = db.query(Product).all()
    if not products:
        return

    customer = None
    use_existing = random.random() < 0.75

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

    ctype = getattr(customer, "customer_type", "bireysel") or "bireysel"
    qty_min, qty_max = QTY_MULTIPLIERS.get(ctype, (1, 5))

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
                base_qty = max(qty_min, int(row.avg_qty))
                qty = max(qty_min, round(base_qty * random.uniform(0.7, 1.3)))
                selected_products.append(p)
                quantities.append(min(qty, qty_max))
    else:
        n = random.randint(1, 3)
        selected_products = random.sample(products, k=min(n, len(products)))
        quantities = [random.randint(qty_min, qty_max) for _ in selected_products]

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
        inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
        if inv:
            package_size = 1.0
            try:
                pkg = p.package_size or "1"
                package_size = float(pkg.split()[0])
            except (ValueError, AttributeError, IndexError):
                package_size = 1.0
            consumed = round(qty * package_size, 2)
            inv.quantity_kg = round(max(0.0, inv.quantity_kg - consumed), 2)
            inv.last_updated = now
            db.add(InventoryMovement(
                product_id=p.id,
                order_id=order.id,
                quantity_change=-consumed,
                movement_type="order_fulfillment",
                timestamp=now,
            ))
            if inv.quantity_kg < inv.min_threshold:
                _ensure_low_stock_alert(db, inv)

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


def _advance_shipments_pipeline(db):
    """Time-based pipeline: advance ALL shipments that have waited long enough."""
    now = datetime.utcnow()

    for current_status, next_status in TRANSITIONS.items():
        min_h, max_h = PIPELINE_DELAYS[current_status]

        rows = db.execute(
            text("""
                SELECT s.id, MAX(su.timestamp) AS last_update
                FROM shipments s
                JOIN shipment_updates su ON su.shipment_id = s.id
                WHERE s.status = :status
                GROUP BY s.id
            """),
            {"status": current_status},
        ).fetchall()

        for row in rows:
            if row.last_update is None:
                continue
            last_update = row.last_update
            if isinstance(last_update, str):
                for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        last_update = datetime.strptime(last_update, fmt)
                        break
                    except ValueError:
                        continue
            elapsed_hours = (now - last_update).total_seconds() / 3600
            threshold = min_h + (row.id % max(1, max_h - min_h))
            if elapsed_hours < threshold:
                continue

            shipment = db.query(Shipment).filter(Shipment.id == row.id).first()
            if not shipment:
                continue

            shipment.status = next_status
            shipment.updated_at = now
            loc, desc = SHIPMENT_ADVANCE_LOCATIONS.get(next_status, ("Bilinmeyen Konum", "Kargo hareket etti."))
            db.add(ShipmentUpdate(
                shipment_id=shipment.id,
                status=next_status,
                location=loc,
                description=desc,
                timestamp=now,
            ))

            if next_status == "delivered":
                order = db.query(Order).filter(Order.id == shipment.order_id).first()
                if order:
                    order.status = OrderStatus.delivered
                _resolve_alert_for_entity(db, "delayed_shipment", shipment.id)

    overdue = db.execute(
        text("""
            SELECT id FROM shipments
            WHERE status NOT IN ('delivered','failed','returned')
              AND estimated_delivery < :now
        """),
        {"now": now},
    ).fetchall()
    for row in overdue:
        s = db.query(Shipment).filter(Shipment.id == row.id).first()
        if not s:
            continue
        existing = db.query(OperationalAlert).filter(
            OperationalAlert.type == "delayed_shipment",
            OperationalAlert.related_entity_id == s.id,
            OperationalAlert.is_resolved == False,
        ).first()
        if not existing:
            db.add(OperationalAlert(
                type="delayed_shipment",
                severity="critical",
                title=f"Kargo {s.tracking_number} Gecikti",
                description=(
                    f"{s.carrier} tarafından taşınan kargo tahmini teslimat tarihini geçti. "
                    "Müşteri bilgilendirmesi gerekiyor."
                ),
                is_resolved=False,
                created_at=now,
                related_entity_id=s.id,
            ))


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
            _force_complaint(db)
        elif event_type == "anomaly":
            _trigger_anomaly(db, target_id)
        elif event_type == "delivery":
            _trigger_delivery(db, target_id)
        elif event_type == "new_order":
            _trigger_new_order(db)
        elif event_type == "new_customer":
            _trigger_new_customer(db)
        db.commit()
    finally:
        db.close()


def _trigger_delayed_shipment(db, target_id):
    if target_id:
        shipment = db.query(Shipment).filter(Shipment.id == target_id).first()
    else:
        shipment = (
            db.query(Shipment)
            .filter(Shipment.status.in_(["in_transit", "at_facility", "preparing", "out_for_delivery"]))
            .order_by(Shipment.updated_at)
            .first()
        )
    if not shipment:
        return
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

    # AI ile müşteri bildirim taslağı oluştur (gönderim manuel onaylanmalı)
    try:
        from email_drafter import draft_delay_notification
        order = db.query(Order).filter(Order.id == shipment.order_id).first()
        if order and order.customer:
            already_drafted = (
                db.query(CustomerMessage)
                .filter(
                    CustomerMessage.related_shipment_id == shipment.id,
                    CustomerMessage.direction == "outbound",
                    CustomerMessage.is_draft == True,
                )
                .first()
            )
            if not already_drafted:
                draft = draft_delay_notification(
                    customer_name=order.customer.name,
                    tracking_number=shipment.tracking_number,
                    carrier=shipment.carrier,
                    days_overdue=2,
                    order_id=order.id,
                )
                db.add(CustomerMessage(
                    customer_id=order.customer_id,
                    direction="outbound",
                    subject=draft["subject"],
                    body=draft["body"],
                    created_at=datetime.utcnow(),
                    is_read=True,
                    ai_generated=True,
                    is_draft=True,
                    category="teslimat_gecikmesi",
                    urgency="yüksek",
                    ai_summary=f"AI tarafından üretilmiş gecikme bildirimi taslağı (Sipariş #{order.id}).",
                    related_order_id=order.id,
                    related_shipment_id=shipment.id,
                ))
    except Exception as e:
        print(f"[simulation] Gecikme bildirimi taslağı üretilemedi: {e}")


def _trigger_stock_drop(db, target_id):
    if target_id:
        inv = db.query(Inventory).filter(Inventory.product_id == target_id).first()
    else:
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


def _trigger_new_order(db):
    """Force-create a new order, bypassing daily pacing gates."""
    now = datetime.utcnow()
    products = db.query(Product).all()
    if not products:
        return

    all_customers = db.query(Customer).all()
    customer = random.choice(all_customers) if all_customers else None

    if customer is None:
        first = random.choice(TURKISH_FIRST_NAMES)
        last = random.choice(TURKISH_LAST_NAMES)
        full_name = f"{first} {last}"
        slug = _slugify(full_name)
        suffix = random.randint(100, 9999)
        email = f"{slug}{suffix}@{random.choice(EMAIL_DOMAINS)}"
        customer = Customer(
            name=full_name,
            email=email,
            phone=f"05{random.randint(30, 59)}{random.randint(1000000, 9999999)}",
            customer_type="bireysel",
        )
        db.add(customer)
        db.flush()

    ctype = getattr(customer, "customer_type", "bireysel") or "bireysel"
    qty_min, qty_max = QTY_MULTIPLIERS.get(ctype, (1, 5))

    n = random.randint(1, 3)
    selected_products = random.sample(products, k=min(n, len(products)))
    quantities = [random.randint(qty_min, qty_max) for _ in selected_products]

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
        inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
        if inv:
            package_size = 1.0
            try:
                pkg = p.package_size or "1"
                package_size = float(pkg.split()[0])
            except (ValueError, AttributeError, IndexError):
                package_size = 1.0
            consumed = round(qty * package_size, 2)
            inv.quantity_kg = round(max(0.0, inv.quantity_kg - consumed), 2)
            inv.last_updated = now
            db.add(InventoryMovement(
                product_id=p.id,
                order_id=order.id,
                quantity_change=-consumed,
                movement_type="order_fulfillment",
                timestamp=now,
            ))
            if inv.quantity_kg < inv.min_threshold:
                _ensure_low_stock_alert(db, inv)

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


def _trigger_new_customer(db):
    """Create a new customer record, then immediately place one order for them."""
    first = random.choice(TURKISH_FIRST_NAMES)
    last = random.choice(TURKISH_LAST_NAMES)
    full_name = f"{first} {last}"
    slug = _slugify(full_name)
    suffix = random.randint(100, 9999)
    email = f"{slug}{suffix}@{random.choice(EMAIL_DOMAINS)}"
    if db.query(Customer).filter(Customer.email == email).first():
        email = f"{slug}{suffix}{random.randint(10, 99)}@{random.choice(EMAIL_DOMAINS)}"
    ctype = random.choice(list(QTY_MULTIPLIERS.keys()))
    customer = Customer(
        name=full_name,
        email=email,
        phone=f"05{random.randint(30, 59)}{random.randint(1000000, 9999999)}",
        customer_type=ctype,
    )
    db.add(customer)
    db.flush()

    # Place one order for the new customer
    products = db.query(Product).all()
    if not products:
        return

    qty_min, qty_max = QTY_MULTIPLIERS.get(ctype, (1, 5))
    n = random.randint(1, 2)
    selected_products = random.sample(products, k=min(n, len(products)))
    quantities = [random.randint(qty_min, qty_max) for _ in selected_products]

    now = datetime.utcnow()
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
        inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
        if inv:
            package_size = 1.0
            try:
                pkg = p.package_size or "1"
                package_size = float(pkg.split()[0])
            except (ValueError, AttributeError, IndexError):
                package_size = 1.0
            consumed = round(qty * package_size, 2)
            inv.quantity_kg = round(max(0.0, inv.quantity_kg - consumed), 2)
            inv.last_updated = now
            db.add(InventoryMovement(
                product_id=p.id,
                order_id=order.id,
                quantity_change=-consumed,
                movement_type="order_fulfillment",
                timestamp=now,
            ))
            if inv.quantity_kg < inv.min_threshold:
                _ensure_low_stock_alert(db, inv)

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
