"""
Seed script for the Tarım ve Gıda Kooperatifi operational platform.
Run: python seed.py
Drops and recreates all tables, then inserts realistic cooperative data.
"""
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import (
    User, Customer, Product, Order, OrderItem,
    Shipment, ShipmentUpdate, CustomerMessage,
    Inventory, InventoryMovement, OperationalAlert,
    OrderStatus, ShipmentStatus,
)
from auth import get_password_hash
from message_intel import brief_summary, classify_customer_message

random.seed(42)

# ── Products ──────────────────────────────────────────────────────────────────

PRODUCTS = [
    ("Domates Salçası",      "Salça",    1500.00, "kg",   "5 kg"),
    ("Biber Salçası",        "Salça",    1500.00, "kg",   "5 kg"),
    ("Zeytinyağı",           "Yağ",      2000.00, "L",    "5 Litre"),
    ("Nar Ekşisi",           "Sos",       250.00, "L",    "1 Litre"),
    ("Sıvı Sumak",           "Sos",       250.00, "L",    "1 Litre"),
    ("Karabiber",            "Baharat",   300.00, "kg",   "1 kg"),
    ("Kimyon",               "Baharat",   400.00, "kg",   "1 kg"),
    ("İsot",                 "Baharat",   500.00, "kg",   "1 kg"),
    ("Kırmızı Biber",        "Baharat",   500.00, "kg",   "1 kg"),
    ("Kuru Domates",         "Kurutulmuş", 450.00, "kg",   "1 kg"),
    ("Kuru Biber",           "Kurutulmuş", 450.00, "kg",   "1 kg"),
    ("Karadut Pekmezi",      "Pekmez",    350.00, "L",    "1 Litre"),
    ("Keçiboynuzu Pekmezi",  "Pekmez",    350.00, "L",    "1 Litre"),
    ("Üzüm Pekmezi",         "Pekmez",    300.00, "L",    "1 Litre"),
    ("Karadut Özü",          "Öz",        400.00, "L",    "1 Litre"),
    ("Yaban Mersini Özü",    "Öz",        450.00, "L",    "1 Litre"),
]

# (quantity_kg, min_threshold, reorder_point) per product index
INVENTORY_LEVELS = [
    (500.0,  100.0, 200.0),   # Domates Salçası
    (300.0,   80.0, 150.0),   # Biber Salçası
    (35.0,    50.0, 100.0),   # Zeytinyağı — BELOW THRESHOLD
    (180.0,   50.0, 100.0),   # Nar Ekşisi
    (180.0,   50.0, 100.0),   # Sıvı Sumak
    (45.0,    50.0, 100.0),   # Karabiber — BELOW THRESHOLD
    (150.0,   40.0,  80.0),   # Kimyon
    (200.0,   50.0, 100.0),   # İsot
    (250.0,   60.0, 120.0),   # Kırmızı Biber
    (120.0,   30.0,  60.0),   # Kuru Domates
    (110.0,   30.0,  60.0),   # Kuru Biber
    (90.0,    25.0,  50.0),   # Karadut Pekmezi
    (85.0,    25.0,  50.0),   # Keçiboynuzu Pekmezi
    (100.0,   30.0,  60.0),   # Üzüm Pekmezi
    (70.0,    20.0,  40.0),   # Karadut Özü
    (65.0,    20.0,  40.0),   # Yaban Mersini Özü
]

# ── Customers ─────────────────────────────────────────────────────────────────

BUSINESS_PREFIXES = [
    "Akdeniz", "Güneş", "Anadolu", "Ege", "Karadeniz",
    "Yıldız", "Altın", "Doğa", "Bereket", "Şimşek",
    "Boğaziçi", "Marmara", "Çukurova", "Kızılırmak", "Yeşil",
    "Sarı", "Mavi", "Turuncu", "Kırmızı", "Yeni",
]

BUSINESS_TYPES = [
    "Restoran", "Market", "Gıda Dağıtım", "Toptan Satış", "Otel",
    "Cafe", "Lokanta", "Gıda Ltd", "Ziraat Market", "Gurme",
]

CITIES = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya",
    "Konya", "Gaziantep", "Mersin", "Eskişehir", "Kayseri",
]

DISTRICTS = {
    "İstanbul":   ["Kadıköy", "Beşiktaş", "Şişli", "Üsküdar", "Maltepe"],
    "Ankara":     ["Çankaya", "Keçiören", "Mamak", "Yenimahalle", "Etimesgut"],
    "İzmir":      ["Bornova", "Karşıyaka", "Konak", "Buca", "Bayraklı"],
    "Bursa":      ["Nilüfer", "Osmangazi", "Yıldırım", "Gemlik", "İnegöl"],
    "Antalya":    ["Muratpaşa", "Konyaaltı", "Kepez", "Alanya", "Manavgat"],
    "Konya":      ["Selçuklu", "Meram", "Karatay", "Ereğli", "Akşehir"],
    "Gaziantep":  ["Şahinbey", "Şehitkamil", "Nizip", "İslahiye", "Nurdağı"],
    "Mersin":     ["Yenişehir", "Toroslar", "Akdeniz", "Mezitli", "Tarsus"],
    "Eskişehir":  ["Odunpazarı", "Tepebaşı", "Mihalıccık", "Saricakaya", "Sivrihisar"],
    "Kayseri":    ["Kocasinan", "Melikgazi", "Talas", "Develi", "Pınarbaşı"],
}

CARRIERS = ["Yurtiçi Kargo", "Aras Kargo", "MNG Kargo", "PTT Kargo"]

CARRIER_TRACKING_PREFIXES = {
    "Yurtiçi Kargo": "YK",
    "Aras Kargo":    "AR",
    "MNG Kargo":     "MN",
    "PTT Kargo":     "PT",
}

COMPLAINT_SUBJECTS = [
    "Teslimat gecikmesi",
    "Ürün kalitesi sorunu",
    "Yanlış ürün teslimatı",
    "Hasar görmüş paket",
    "Toplu sipariş talebi",
    "Fatura düzeltme talebi",
    "Stok bilgisi talebi",
    "Acil sipariş bildirimi",
]

COMPLAINT_BODIES = [
    "Sipariş verdiğim ürünler {days} gündür gelmedi. Kargo durumu hakkında bilgi alabilir miyim?",
    "Son teslimatımda {product} ürünleri bozuk geldi. İade veya değişim yapılmasını talep ediyorum.",
    "Siparişimde {product} yerine farklı bir ürün geldi. En kısa sürede düzeltme yapılmasını bekliyorum.",
    "Paketlerimden biri hasar görmüş vaziyette teslim edildi. Fotoğraf gönderebilirim.",
    "{product} için {qty} adetlik acil sipariş vermek istiyorum. Stok durumunuzu öğrenebilir miyim?",
    "Son faturamda hata var gibi görünüyor. Kontrol edilmesini rica ediyorum.",
]

INITIAL_ALERTS = [
    (
        "low_stock", "critical",
        "Zeytinyağı Stok Kritik Seviyede",
        "Zeytinyağı stoku minimum eşiğin altına düştü (35 şişe < 50 şişe eşiği). "
        "Son 7 günlük satış hızına göre 3-4 gün içinde tükenebilir.",
        None,
    ),
    (
        "low_stock", "critical",
        "Karabiber Stok Uyarısı",
        "Karabiber stoku kritik seviyede (45 adet < 50 adet eşiği). "
        "Bekleyen siparişleri karşılamak için yenileme önerilir.",
        None,
    ),
    (
        "delayed_shipment", "critical",
        "3 Kargo 48+ Saat Gecikmede",
        "MNG Kargo operatöründe taşınan 3 kargo, tahmini teslimat tarihini 2 günden fazla aştı. "
        "Müşteri bildirimi ve kargo takibi gerekiyor.",
        None,
    ),
    (
        "carrier_issue", "warning",
        "MNG Kargo Bölgesel Operasyon Gecikmesi",
        "İzmir ve Ankara bölgelerinde MNG Kargo operasyonlarında 24-48 saatlik gecikme bildirimi. "
        "Aktif kargolar için alternatif takip önerilir.",
        None,
    ),
    (
        "complaint", "info",
        "Yeni Müşteri Şikayeti — İnceleme Gerekiyor",
        "Güneş Market hasar görmüş ürün teslimatı bildirdi. "
        "Teslimat fotoğrafları incelenmeli ve müşteri bilgilendirilmeli.",
        None,
    ),
]


def _rand_phone() -> str:
    return f"05{random.randint(30, 59)}{random.randint(1000000, 9999999)}"


def _rand_date(days_ago_max: int, days_ago_min: int = 0) -> datetime:
    delta = random.randint(days_ago_min, days_ago_max)
    return datetime.utcnow() - timedelta(days=delta)


def _tracking_number(carrier: str) -> str:
    prefix = CARRIER_TRACKING_PREFIXES.get(carrier, "KG")
    return f"{prefix}{random.randint(900000000, 999999999)}"


def _slugify(s: str) -> str:
    replacements = {"ş": "s", "ı": "i", "ö": "o", "ü": "u", "ç": "c", "ğ": "g",
                    "Ş": "S", "İ": "I", "Ö": "O", "Ü": "U", "Ç": "C", "Ğ": "G",
                    " ": "", ".": "", "&": ""}
    result = s.lower()
    for k, v in replacements.items():
        result = result.replace(k, v)
    return result


def seed():
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # ── Admin user ────────────────────────────────────────────────────────
        admin = User(
            email="admin@demo.com",
            password_hash=get_password_hash("demo123"),
            full_name="Kooperatif Yöneticisi",
            role="admin",
        )
        db.add(admin)
        db.flush()
        print("✓ Admin user created")

        # ── Products ──────────────────────────────────────────────────────────
        products = []
        for name, category, price, unit, pkg_size in PRODUCTS:
            p = Product(name=name, category=category, price=price, unit=unit, package_size=pkg_size)
            db.add(p)
            products.append(p)
        db.flush()
        print(f"✓ {len(products)} products created")

        # ── Inventory ─────────────────────────────────────────────────────────
        inventories = []
        movements_to_add = []
        for i, product in enumerate(products):
            qty, min_thr, reorder = INVENTORY_LEVELS[i]
            inv = Inventory(
                product_id=product.id,
                quantity_kg=qty,
                min_threshold=min_thr,
                reorder_point=reorder,
                last_updated=datetime.utcnow() - timedelta(hours=random.randint(1, 12)),
            )
            db.add(inv)
            inventories.append(inv)

            # Historical consumption movements (last 14 days)
            for d in range(14, 0, -3):
                consumed = random.uniform(5.0, 30.0)
                movements_to_add.append(InventoryMovement(
                    product_id=product.id,
                    order_id=None,
                    quantity_change=-consumed,
                    movement_type="order_fulfillment",
                    timestamp=datetime.utcnow() - timedelta(days=d),
                ))
        db.flush()
        for m in movements_to_add:
            db.add(m)
        print(f"✓ {len(inventories)} inventory records + {len(movements_to_add)} historical movements")

        # ── Customers ─────────────────────────────────────────────────────────
        INDIVIDUAL_NAMES = [
            "Ahmet Yılmaz", "Ayşe Kaya", "Mehmet Demir", "Fatma Çelik", "Ali Şahin", 
            "Zeynep Yıldız", "Mustafa Öztürk", "Elif Aydın", "Burak Özdemir", "Canan Arslan", 
            "Kemal Doğan", "Sibel Kılıç", "Okan Çetin", "Derya Gür", "Emre Polat", 
            "Gizem Koç", "Hakan Kurt", "İrem Özcan", "Caner Bulut", "Esra Er"
        ]

        customers = []
        used_emails: set = set()
        used_combos: set = set()

        for i in range(20):
            # Kurumsal Customer
            prefix = random.choice(BUSINESS_PREFIXES)
            btype = random.choice(BUSINESS_TYPES)
            combo = (prefix, btype)
            while combo in used_combos:
                prefix = random.choice(BUSINESS_PREFIXES)
                btype = random.choice(BUSINESS_TYPES)
                combo = (prefix, btype)
            used_combos.add(combo)
            name = f"{prefix} {btype}"
            slug = _slugify(name)
            email = f"{slug}{i}@{slug[:8]}.com.tr"
            if email in used_emails:
                email = f"{slug}{i}{random.randint(10, 99)}@mail.com.tr"
            used_emails.add(email)
            c_corp = Customer(name=name, email=email, phone=_rand_phone(), customer_type="kurumsal")
            db.add(c_corp)
            customers.append(c_corp)

            # Bireysel Customer
            name_ind = INDIVIDUAL_NAMES[i % len(INDIVIDUAL_NAMES)]
            slug_ind = _slugify(name_ind)
            email_ind = f"{slug_ind}{i}@mail.com"
            if email_ind in used_emails:
                email_ind = f"{slug_ind}{i}{random.randint(10, 99)}@mail.com"
            used_emails.add(email_ind)
            c_ind = Customer(name=name_ind, email=email_ind, phone=_rand_phone(), customer_type="bireysel")
            db.add(c_ind)
            customers.append(c_ind)
        db.flush()
        print(f"✓ {len(customers)} customers created")

        # ── Orders & Shipments ────────────────────────────────────────────────
        orders = []
        shipments_created = 0
        now = datetime.utcnow()

        # Realistic lifecycle mix for active shipments
        _shipped_statuses = (
            ["preparing"] * 8
            + ["in_transit"] * 14
            + ["at_facility"] * 10
            + ["out_for_delivery"] * 8
        )
        random.shuffle(_shipped_statuses)
        # ~10% delay rate — realistic, not alarming
        _n_active = len(_shipped_statuses)
        _delayed_flags = [True] * max(1, _n_active // 10) + [False] * (_n_active - max(1, _n_active // 10))
        random.shuffle(_delayed_flags)
        _shipped_ix = 0

        # ── Order timing strategy ──────────────────────────────────────────────
        # Today: 2-4 fresh orders (pending/processing)
        # Last 3 days: orders in transit / processing
        # 4-10 days ago: mix of shipped/delivered
        # 11-45 days ago: mostly delivered, some cancelled
        def _order_status_for_age(days_old: int) -> OrderStatus:
            if days_old == 0:
                return random.choice([OrderStatus.pending, OrderStatus.pending, OrderStatus.processing])
            elif days_old <= 1:
                return random.choice([OrderStatus.pending, OrderStatus.processing, OrderStatus.processing])
            elif days_old <= 3:
                return random.choice([OrderStatus.processing, OrderStatus.shipped, OrderStatus.shipped])
            elif days_old <= 7:
                return random.choice([OrderStatus.shipped, OrderStatus.shipped, OrderStatus.delivered])
            elif days_old <= 14:
                return random.choice([OrderStatus.shipped, OrderStatus.delivered, OrderStatus.delivered, OrderStatus.delivered])
            else:
                return random.choice([OrderStatus.delivered, OrderStatus.delivered, OrderStatus.delivered, OrderStatus.cancelled])

        # Build a realistic age distribution for 150 orders
        order_ages = (
            [0] * 3 +           # today: 3 orders
            [1] * 4 +           # yesterday: 4 orders
            [2] * 5 +           # 2 days ago: 5 orders
            [3] * 6 +           # 3 days ago: 6 orders
            list(range(4, 8)) * 4 +    # 4-7 days: 4 per day = 16
            list(range(8, 15)) * 3 +   # 8-14 days: 3 per day = 21
            list(range(15, 46))        # 15-45 days: 1 per day = 31
        )
        # Pad to 150
        while len(order_ages) < 150:
            order_ages.append(random.randint(15, 45))
        order_ages = order_ages[:150]
        random.shuffle(order_ages)

        for age_days in order_ages:
            customer = random.choice(customers)
            city = random.choice(CITIES)
            district = random.choice(DISTRICTS[city])
            # Create time: random hour within that day
            created = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=age_days)
            created += timedelta(hours=random.randint(7, 20), minutes=random.randint(0, 59))
            status = _order_status_for_age(age_days)

            order = Order(
                customer_id=customer.id,
                status=status,
                created_at=created,
                updated_at=created + timedelta(hours=random.randint(1, 48)),
                shipping_address=f"{district} Mah. No:{random.randint(1, 200)}, {city}",
                tracking_number=None,
            )
            db.add(order)
            db.flush()

            # 1–4 items per order
            selected_products = random.sample(products, k=random.randint(1, 4))
            for product in selected_products:
                qty = random.randint(1, 3) if customer.customer_type == "bireysel" else random.randint(5, 20)
                db.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.price,
                ))

            # Shipments for shipped/delivered orders
            if status in (OrderStatus.shipped, OrderStatus.delivered):
                carrier = random.choice(CARRIERS)
                tracking = _tracking_number(carrier)

                ship_created = created + timedelta(hours=random.randint(2, 24))
                if status == OrderStatus.delivered:
                    ship_status = ShipmentStatus.delivered
                    days_since = max(0, (now - created).days)
                    d = random.randint(1, max(1, min(21, days_since))) if days_since > 0 else 1
                    delivered_at = created + timedelta(days=d)
                    if delivered_at > now:
                        delivered_at = now - timedelta(hours=random.randint(4, 72))
                    if delivered_at <= created:
                        delivered_at = created + timedelta(hours=random.randint(12, 96))
                    est_delivery = delivered_at - timedelta(hours=random.randint(18, 96))
                    if est_delivery < created:
                        est_delivery = created + timedelta(hours=2)
                    if est_delivery > now:
                        est_delivery = now - timedelta(days=1)
                    ship_updated = delivered_at
                else:
                    st_key = _shipped_statuses[_shipped_ix] if _shipped_ix < len(_shipped_statuses) else "in_transit"
                    _shipped_ix += 1
                    ship_status = ShipmentStatus(st_key)
                    is_delayed = (
                        _delayed_flags[_shipped_ix - 1]
                        if _shipped_ix - 1 < len(_delayed_flags)
                        else random.random() < 0.10
                    )
                    if is_delayed:
                        # Delayed: est_delivery was 1-3 days ago (not too extreme)
                        est_delivery = now - timedelta(days=random.randint(1, 3))
                    else:
                        # On time: delivery expected in 1-5 days
                        est_delivery = now + timedelta(days=random.randint(1, 5))
                    ship_updated = now - timedelta(hours=random.randint(1, 24))

                origin_city = random.choice(CITIES)
                shipment = Shipment(
                    order_id=order.id,
                    tracking_number=tracking,
                    carrier=carrier,
                    status=ship_status,
                    created_at=ship_created,
                    updated_at=ship_updated,
                    estimated_delivery=est_delivery,
                    recipient_name=customer.name,
                    recipient_address=order.shipping_address,
                )
                db.add(shipment)
                db.flush()
                order.tracking_number = tracking

                # Build shipment timeline up to current status
                all_stages = ["preparing", "in_transit", "at_facility", "out_for_delivery", "delivered"]
                st_val = ship_status.value if hasattr(ship_status, "value") else str(ship_status)
                current_idx = all_stages.index(st_val)
                stage_time = shipment.created_at
                end_cap = ship_updated if status == OrderStatus.delivered else now

                for stage in all_stages[:current_idx + 1]:
                    loc_map = {
                        "preparing":        f"{origin_city} Kooperatif Deposu",
                        "in_transit":       f"{origin_city} Transfer Merkezi",
                        "at_facility":      f"{city} Dağıtım Şubesi",
                        "out_for_delivery": f"{city} {district} Dağıtım Noktası",
                        "delivered":        f"{district}, {city}",
                    }
                    desc_map = {
                        "preparing":        "Ürünler paketlendi, kargo taşıyıcıya hazır.",
                        "in_transit":       f"Kargo {carrier} tarafından teslim alındı.",
                        "at_facility":      f"Kargo {city} şubesine ulaştı.",
                        "out_for_delivery": "Kargo dağıtım aracına yüklendi.",
                        "delivered":        "Kargo başarıyla teslim edildi.",
                    }
                    ts = min(stage_time, end_cap)
                    db.add(ShipmentUpdate(
                        shipment_id=shipment.id,
                        status=stage,
                        location=loc_map[stage],
                        description=desc_map[stage],
                        timestamp=ts,
                    ))
                    stage_time = ts + timedelta(hours=random.randint(4, 18))

                shipments_created += 1

            orders.append(order)

        db.flush()
        print(f"✓ {len(orders)} orders, {shipments_created} shipments with timelines")

        # ── Customer Messages ─────────────────────────────────────────────────
        # Message age distribution: 5 today, 4 yesterday, rest spread over last 5 days
        msg_ages_hours = (
            [random.randint(0, 10) for _ in range(5)] +
            [random.randint(11, 23) for _ in range(4)] +
            [random.randint(24, 48) for _ in range(4)] +
            [random.randint(49, 72) for _ in range(3)] +
            [random.randint(73, 120) for _ in range(4)]
        )
        random.shuffle(msg_ages_hours)

        msg_count = 0
        msg_customers = random.sample(customers, k=len(msg_ages_hours))
        for i, customer in enumerate(msg_customers):
            subject = random.choice(COMPLAINT_SUBJECTS)
            product_name = random.choice(products).name
            body = random.choice(COMPLAINT_BODIES).format(
                days=random.randint(2, 6),
                product=product_name,
                qty=random.randint(10, 50),
            )
            cat, urg = classify_customer_message(subject)
            cust_orders = [o for o in orders if o.customer_id == customer.id]
            co = random.choice(cust_orders) if cust_orders else None
            cid = co.id if co else None
            sh = None
            if cid:
                sh_row = db.query(Shipment).filter(Shipment.order_id == cid).first()
                sh = sh_row.id if sh_row else None
            hours_ago = msg_ages_hours[i] if i < len(msg_ages_hours) else random.randint(0, 120)
            msg_time = now - timedelta(hours=hours_ago)
            # Messages from today/yesterday are unread; older ones are mostly read
            is_recent = hours_ago < 24
            db.add(CustomerMessage(
                customer_id=customer.id,
                direction="inbound",
                subject=subject,
                body=body,
                created_at=msg_time,
                is_read=False if is_recent else (random.random() < 0.5),
                ai_generated=False,
                category=cat,
                urgency=urg,
                ai_summary=brief_summary(customer.name, cat, subject),
                related_order_id=cid,
                related_shipment_id=sh,
            ))
            msg_count += 1

        # A few outbound replies
        for customer in random.sample(customers, k=3):
            db.add(CustomerMessage(
                customer_id=customer.id,
                direction="outbound",
                subject="Re: Sipariş Durumu Hakkında",
                body="Merhaba, siparişinizle ilgili inceleme yaptık. Kargonuz yola çıkmış olup en geç 2 iş günü içinde teslim edilmesi beklenmektedir. Anlayışınız için teşekkür ederiz.",
                created_at=now - timedelta(hours=random.randint(2, 48)),
                is_read=True,
                ai_generated=True,
            ))
            msg_count += 1

        print(f"✓ {msg_count} customer messages created (5 today, 4 yesterday, rest spread)")

        # ── Operational Alerts ────────────────────────────────────────────────
        for type_, severity, title, description, entity_id in INITIAL_ALERTS:
            db.add(OperationalAlert(
                type=type_,
                severity=severity,
                title=title,
                description=description,
                is_resolved=False,
                created_at=_rand_date(days_ago_max=2),
                related_entity_id=entity_id,
            ))
        print(f"✓ {len(INITIAL_ALERTS)} operational alerts seeded")

        db.commit()
        print("\n✅ Database seeded successfully!")
        print("   Login: admin@demo.com / demo123")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
