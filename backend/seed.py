"""
Seed script — 1 aylık gerçekçi kooperatif verisi.
Her sipariş → kargo lifecycle → ilgili müşteri mesajları zinciri birbiriyle bağlantılı.
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
    ("Domates Salçası",         "Salça",      1500.00, "kg",       "5 kg"),
    ("Biber Salçası",           "Salça",      1500.00, "kg",       "5 kg"),
    ("Zeytinyağı",              "Yağ",        2000.00, "L",        "5 Litre"),
    ("Nar Ekşisi",              "Sos",         250.00, "L",        "1 Litre"),
    ("Sıvı Sumak",              "Sos",         250.00, "L",        "1 Litre"),
    ("Karabiber",               "Baharat",     300.00, "kg",       "1 kg"),
    ("Kimyon",                  "Baharat",     400.00, "kg",       "1 kg"),
    ("İsot",                    "Baharat",     500.00, "kg",       "1 kg"),
    ("Kırmızı Biber",           "Baharat",     500.00, "kg",       "1 kg"),
    ("Kuru Domates",            "Kurutulmuş",  450.00, "kg",       "1 kg"),
    ("Kuru Biber",              "Kurutulmuş",  450.00, "kg",       "1 kg"),
    ("Karadut Pekmezi",         "Pekmez",      350.00, "L",        "1 Litre"),
    ("Keçiboynuzu Pekmezi",     "Pekmez",      350.00, "L",        "1 Litre"),
    ("Üzüm Pekmezi",            "Pekmez",      300.00, "L",        "1 Litre"),
    ("Karadut Özü",             "Öz",          400.00, "L",        "1 Litre"),
    ("Yaban Mersini Özü",       "Öz",          450.00, "L",        "1 Litre"),
    ("Acı Biber Sosu",          "Sos",         180.00, "şişe",     "1 şişe"),
    ("Ev Eriştesi",             "Makarna",      65.00, "kg",       "1 kg"),
    ("Karışık Baharat Seti",    "Baharat",     120.00, "adet",     "1 adet"),
    ("El Yapımı Kayısı Reçeli", "Reçel",        95.00, "kavanoz",  "1 kavanoz"),
]

INVENTORY_LEVELS = [
    (500.0, 100.0, 200.0), (300.0,  80.0, 150.0), (400.0,  50.0, 100.0),
    (180.0,  50.0, 100.0), (180.0,  50.0, 100.0), (150.0,  50.0, 100.0),
    (150.0,  40.0,  80.0), (200.0,  50.0, 100.0), (250.0,  60.0, 120.0),
    (120.0,  30.0,  60.0), (110.0,  30.0,  60.0), ( 90.0,  25.0,  50.0),
    ( 85.0,  25.0,  50.0), (100.0,  30.0,  60.0), ( 70.0,  20.0,  40.0),
    ( 65.0,  20.0,  40.0), (200.0,  40.0,  80.0), (180.0,  50.0, 100.0),
    (150.0,  30.0,  60.0), (120.0,  25.0,  50.0),
]

# ── Customers ─────────────────────────────────────────────────────────────────
BUSINESS_PREFIXES = [
    "Akdeniz", "Güneş", "Anadolu", "Ege", "Karadeniz", "Yıldız", "Altın",
    "Doğa", "Bereket", "Şimşek", "Boğaziçi", "Marmara", "Çukurova",
    "Kızılırmak", "Yeşil", "Sarı", "Mavi", "Turuncu", "Yeni", "Toprak",
    "Hasad", "Öz", "Seçkin", "Ata", "Doğal", "Serin", "Taze", "Mis", "Bahar",
]
BUSINESS_CUSTOMER_TYPES = [
    ("Restoran", "restoran"), ("Market", "market"), ("Gıda Dağıtım", "kurumsal"),
    ("Toptan Satış", "kurumsal"), ("Otel", "kurumsal"), ("Cafe", "kafe"),
    ("Lokanta", "restoran"), ("Gıda Ltd", "kurumsal"), ("Ziraat Market", "market"),
    ("Gurme", "butik"), ("Bakkal", "bakkal"), ("Büfe", "bakkal"),
    ("Pastane", "kafe"), ("Kuruyemişçi", "bakkal"), ("Organik Market", "market"),
    ("Doğal Ürünler", "butik"), ("Yerel Lezzetler", "yerel_isletme"),
    ("Kooperatif Satış", "yerel_isletme"), ("Çiftlik Mağazası", "yerel_isletme"),
    ("El Sanatları Evi", "butik"),
]
INDIVIDUAL_NAMES = [
    "Ahmet Yılmaz", "Ayşe Kaya", "Mehmet Demir", "Fatma Çelik", "Ali Şahin",
    "Zeynep Yıldız", "Mustafa Öztürk", "Elif Aydın", "Burak Özdemir", "Canan Arslan",
    "Kemal Doğan", "Sibel Kılıç", "Okan Çetin", "Derya Gür", "Emre Polat",
    "Gizem Koç", "Hakan Kurt", "İrem Özcan", "Caner Bulut", "Esra Er",
]

CITIES = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Konya", "Gaziantep", "Mersin", "Eskişehir", "Kayseri"]
DISTRICTS = {
    "İstanbul": ["Kadıköy", "Beşiktaş", "Şişli", "Üsküdar", "Maltepe"],
    "Ankara":   ["Çankaya", "Keçiören", "Mamak", "Yenimahalle", "Etimesgut"],
    "İzmir":    ["Bornova", "Karşıyaka", "Konak", "Buca", "Bayraklı"],
    "Bursa":    ["Nilüfer", "Osmangazi", "Yıldırım", "Gemlik", "İnegöl"],
    "Antalya":  ["Muratpaşa", "Konyaaltı", "Kepez", "Alanya", "Manavgat"],
    "Konya":    ["Selçuklu", "Meram", "Karatay", "Ereğli", "Akşehir"],
    "Gaziantep":["Şahinbey", "Şehitkamil", "Nizip", "İslahiye", "Nurdağı"],
    "Mersin":   ["Yenişehir", "Toroslar", "Akdeniz", "Mezitli", "Tarsus"],
    "Eskişehir":["Odunpazarı", "Tepebaşı", "Sivrihisar", "Mihalgazi", "Beylikova"],
    "Kayseri":  ["Kocasinan", "Melikgazi", "Talas", "Develi", "Pınarbaşı"],
}
CARRIERS = ["Yurtiçi Kargo", "Aras Kargo", "MNG Kargo", "PTT Kargo"]
CARRIER_PREFIXES = {"Yurtiçi Kargo": "YK", "Aras Kargo": "AR", "MNG Kargo": "MN", "PTT Kargo": "PT"}

QTY_RANGES = {
    "restoran": (10, 50), "market": (20, 80), "bakkal": (5, 25),
    "kafe": (3, 15), "butik": (2, 10), "bireysel": (1, 5),
    "yerel_isletme": (5, 20), "kurumsal": (10, 40),
}

# ── Mesaj şablonları — kategoriye göre ──────────────────────────────────────

# Her şablon: (subject, body_template, category, urgency)
# body_template değişkenleri: {order_id}, {product}, {tracking}, {carrier}, {days}, {est_date}, {item_count}, {qty}

DELAY_MESSAGES = [
    ("Teslimat gecikmesi",
     "Merhaba, #{order_id} numaralı siparişim {days} gündür yolda görünüyor. "
     "{carrier} üzerinde {tracking} takip numarasıyla takip etmeye çalışıyorum ama güncelleme gelmiyor. "
     "Ne zaman teslim edilebilir?",
     "teslimat_gecikmesi", "yüksek"),

    ("Teslimat gecikmesi",
     "#{order_id} siparişim için tahmini teslimat tarihi {est_date} olarak gösteriyordu, "
     "bugün hâlâ elimde değil. Kargo durumu nedir?",
     "teslimat_gecikmesi", "yüksek"),

    ("Kargo takip sorunu",
     "#{order_id} nolu siparişimin kargosu {carrier} üzerinde {days} gündür hareket etmiyor. "
     "Lütfen araştırır mısınız?",
     "teslimat_gecikmesi", "yüksek"),
]

DELIVERY_COMPLAINT_MESSAGES = [
    ("Ürün kalitesi sorunu",
     "Merhaba, #{order_id} numaralı sipariş teslim edildi ancak içindeki {product} ürünleri "
     "bozuk çıktı. İade veya değişim yapmak istiyorum.",
     "urun_hasari", "yüksek"),

    ("Yanlış ürün teslimatı",
     "#{order_id} siparişimde {product} sipariş ettim fakat gelen pakette farklı ürün çıktı. "
     "Lütfen doğru ürünü gönderir misiniz?",
     "yanlis_urun", "orta"),

    ("Hasar görmüş paket",
     "#{order_id} numaralı kargom teslim edildi ama paket hasar görmüş. "
     "{product} ürünleri dökülmüş, kullanılamaz durumda.",
     "paket_hasari", "orta"),

    ("Eksik ürün bildirimi",
     "#{order_id} siparişimde toplam {item_count} kalem vardı ama teslimatta {product} eksikti. "
     "Gönderimi tamamlar mısınız?",
     "urun_hasari", "orta"),

    ("Memnuniyet bildirimi",
     "#{order_id} siparişim sorunsuz teslim edildi, teşekkür ederim. "
     "{product} kalitesi çok iyiydi, yakında tekrar sipariş vereceğim.",
     "genel_destek", "düşük"),
]

GENERAL_MESSAGES = [
    ("Toplu sipariş talebi",
     "{product} için {qty} adetlik toplu sipariş vermek istiyorum. "
     "Fiyat ve stok durumunu öğrenebilir miyim?",
     "siparis_talebi", "orta"),

    ("Stok bilgisi talebi",
     "{product} ürününüzde stok var mı? Yakında büyük bir etkinliğimiz var, "
     "{qty} adet lazım olacak.",
     "stok_bilgisi", "düşük"),

    ("Fatura düzeltme talebi",
     "#{order_id} numaralı sipariş faturamda hata var gibi görünüyor. "
     "Kontrol edilmesini rica ediyorum.",
     "fatura_duzeltme", "düşük"),

    ("Acil stok talebi",
     "{product} için acil {qty} adetlik sipariş vermek istiyorum. "
     "Stok durumunuzu öğrenebilir miyim?",
     "siparis_talebi", "yüksek"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _rand_phone():
    return f"05{random.randint(30, 59)}{random.randint(1000000, 9999999)}"

def _tracking(carrier):
    return f"{CARRIER_PREFIXES.get(carrier, 'KG')}{random.randint(100000000, 999999999)}"

def _slugify(s):
    for k, v in {"ş":"s","ı":"i","ö":"o","ü":"u","ç":"c","ğ":"g","Ş":"S","İ":"I","Ö":"O","Ü":"U","Ç":"C","Ğ":"G"," ":"",".":"","&":""}.items():
        s = s.replace(k, v)
    return s.lower()

def _dt(base: datetime, **kwargs) -> datetime:
    return base + timedelta(**kwargs)

def _parse_dt(v):
    """Parse datetime from string if SQLite returns string."""
    if isinstance(v, datetime):
        return v
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return datetime.utcnow()


# ── Main seed ──────────────────────────────────────────────────────────────────

def seed():
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ── Admin ─────────────────────────────────────────────────────────────
        db.add(User(
            email="admin@demo.com",
            password_hash=get_password_hash("demo123"),
            full_name="Kooperatif Yöneticisi",
            role="admin",
        ))
        db.flush()
        print("✓ Admin user created")

        # ── Products ──────────────────────────────────────────────────────────
        products = []
        for name, cat, price, unit, pkg in PRODUCTS:
            p = Product(name=name, category=cat, price=price, unit=unit, package_size=pkg)
            db.add(p)
            products.append(p)
        db.flush()
        print(f"✓ {len(products)} products")

        # ── Inventory ─────────────────────────────────────────────────────────
        for i, product in enumerate(products):
            qty, min_thr, reorder = INVENTORY_LEVELS[i]
            db.add(Inventory(
                product_id=product.id,
                quantity_kg=qty,
                min_threshold=min_thr,
                reorder_point=reorder,
                last_updated=now - timedelta(hours=random.randint(1, 6)),
            ))
            for d in range(28, 0, -4):
                db.add(InventoryMovement(
                    product_id=product.id,
                    quantity_change=-random.uniform(5.0, 25.0),
                    movement_type="order_fulfillment",
                    timestamp=now - timedelta(days=d),
                ))
        db.flush()
        print(f"✓ {len(products)} inventory records + historical movements")

        # ── Customers ─────────────────────────────────────────────────────────
        customers = []
        used_emails = set()
        used_combos = set()

        for i in range(40):
            prefix = random.choice(BUSINESS_PREFIXES)
            lbl, ctype = random.choice(BUSINESS_CUSTOMER_TYPES)
            combo = (prefix, lbl)
            attempts = 0
            while combo in used_combos and attempts < 20:
                prefix = random.choice(BUSINESS_PREFIXES)
                lbl, ctype = random.choice(BUSINESS_CUSTOMER_TYPES)
                combo = (prefix, lbl)
                attempts += 1
            used_combos.add(combo)
            name = f"{prefix} {lbl}"
            slug = _slugify(name)
            email = f"{slug}{i}@{slug[:8]}.com.tr"
            if email in used_emails:
                email = f"{slug}{i}{random.randint(10, 99)}@mail.com.tr"
            used_emails.add(email)
            c = Customer(name=name, email=email, phone=_rand_phone(), customer_type=ctype)
            db.add(c)
            customers.append(c)

        for i, iname in enumerate(INDIVIDUAL_NAMES):
            slug = _slugify(iname)
            email = f"{slug}{i}@mail.com"
            if email in used_emails:
                email = f"{slug}{i}{random.randint(10, 99)}@mail.com"
            used_emails.add(email)
            c = Customer(name=iname, email=email, phone=_rand_phone(), customer_type="bireysel")
            db.add(c)
            customers.append(c)

        db.flush()
        print(f"✓ {len(customers)} customers")

        # ── 1 Aylık Sipariş + Kargo + Mesaj Zinciri ───────────────────────────
        #
        # Strateji:
        # - Günlük 6-14 sipariş, 30 gün boyunca
        # - Her siparişin yaşına göre kargo durumu belirlenir
        # - Kargo gecikmeli veya teslim edilmiş siparişlerden mesaj üretilir
        # - Bugünkü mesajlar dashboard'a düşer
        #
        # Kargo lifecycle süreleri (gerçekçi):
        #   preparing    → 4-8 saat sonra in_transit
        #   in_transit   → 24-48 saat sonra at_facility
        #   at_facility  → 4-12 saat sonra out_for_delivery
        #   out_for_delivery → 2-6 saat sonra delivered

        STAGE_HOURS = {
            "preparing":        (4, 8),
            "in_transit":       (24, 48),
            "at_facility":      (4, 12),
            "out_for_delivery": (2, 6),
        }
        ALL_STAGES = ["preparing", "in_transit", "at_facility", "out_for_delivery", "delivered"]

        orders_created = []
        shipments_created = []
        total_orders = 0

        for day_offset in range(30, -1, -1):  # 30 gün önce → bugün
            day_base = today_start - timedelta(days=day_offset)
            daily_count = random.randint(6, 14)

            for _ in range(daily_count):
                customer = random.choice(customers)
                city = random.choice(CITIES)
                district = random.choice(DISTRICTS[city])
                hour = random.randint(7, 21)
                minute = random.randint(0, 59)
                created_at = day_base + timedelta(hours=hour, minutes=minute)

                if created_at > now:
                    created_at = now - timedelta(minutes=random.randint(5, 120))

                # Sipariş durumunu yaşa göre belirle
                age_hours = (now - created_at).total_seconds() / 3600
                age_days = age_hours / 24

                if age_days <= 0.5:
                    order_status = OrderStatus.pending
                elif age_days <= 1.5:
                    order_status = random.choice([OrderStatus.pending, OrderStatus.processing])
                elif age_days <= 3:
                    order_status = OrderStatus.processing
                elif age_days <= 5:
                    order_status = random.choice([OrderStatus.processing, OrderStatus.shipped])
                elif age_days <= 25:
                    # %85 delivered, %10 shipped, %5 cancelled
                    r = random.random()
                    if r < 0.85:
                        order_status = OrderStatus.delivered
                    elif r < 0.95:
                        order_status = OrderStatus.shipped
                    else:
                        order_status = OrderStatus.cancelled
                else:
                    order_status = OrderStatus.delivered

                q_min, q_max = QTY_RANGES.get(customer.customer_type, (1, 10))
                n_items = random.randint(1, 4)
                sel_products = random.sample(products, k=n_items)

                order = Order(
                    customer_id=customer.id,
                    status=order_status,
                    created_at=created_at,
                    updated_at=created_at + timedelta(hours=random.randint(1, 4)),
                    shipping_address=f"{district} Mah. No:{random.randint(1, 200)}, {city}",
                    tracking_number=None,
                )
                db.add(order)
                db.flush()

                order_total = 0.0
                for p in sel_products:
                    qty = random.randint(q_min, q_max)
                    subtotal = qty * p.price
                    order_total += subtotal
                    db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=p.price))

                orders_created.append(order)
                total_orders += 1

                # Kargo oluştur (shipped veya delivered için)
                if order_status in (OrderStatus.shipped, OrderStatus.delivered, OrderStatus.cancelled):
                    carrier = random.choice(CARRIERS)
                    tracking = _tracking(carrier)
                    origin_city = random.choice(CITIES)

                    ship_created = created_at + timedelta(hours=random.randint(2, 8))

                    # Kargo durumunu gerçekçi zaman bazlı hesapla
                    # Her aşama için deterministic süre (sipariş id bazlı)
                    stage_cursor = ship_created
                    stage_times = {"preparing": ship_created}

                    for stage in ["preparing", "in_transit", "at_facility", "out_for_delivery"]:
                        min_h, max_h = STAGE_HOURS[stage]
                        duration = timedelta(hours=min_h + (order.id % max(1, max_h - min_h)))
                        stage_times[stage + "_end"] = stage_cursor + duration
                        stage_cursor = stage_cursor + duration

                    delivered_time = stage_cursor  # gerçek teslim zamanı

                    if order_status == OrderStatus.delivered:
                        ship_status = ShipmentStatus.delivered
                        # est_delivery: teslimden biraz önce veya sonra (bazen geç)
                        on_time = random.random() < 0.88  # %88 zamanında
                        if on_time:
                            est_delivery = delivered_time - timedelta(hours=random.randint(2, 24))
                        else:
                            est_delivery = delivered_time - timedelta(days=random.randint(1, 3))
                        final_time = delivered_time
                    elif order_status == OrderStatus.cancelled:
                        ship_status = ShipmentStatus.preparing
                        est_delivery = ship_created + timedelta(days=5)
                        final_time = ship_created
                    else:
                        # shipped — kargo yolda, nerede olduğunu zamanla hesapla
                        est_delivery = ship_created + timedelta(days=5)
                        # Hangi aşamada?
                        current_stage = "preparing"
                        for stage in ALL_STAGES[:-1]:
                            end_key = stage + "_end"
                            if stage_times.get(end_key, now + timedelta(days=999)) <= now:
                                idx = ALL_STAGES.index(stage)
                                current_stage = ALL_STAGES[min(idx + 1, len(ALL_STAGES) - 2)]
                            else:
                                break
                        ship_status = ShipmentStatus(current_stage)
                        # %12 gecikme
                        if random.random() < 0.12:
                            est_delivery = now - timedelta(hours=random.randint(6, 48))
                        final_time = now - timedelta(hours=random.randint(1, 12))

                    shipment = Shipment(
                        order_id=order.id,
                        tracking_number=tracking,
                        carrier=carrier,
                        status=ship_status,
                        created_at=ship_created,
                        updated_at=final_time,
                        estimated_delivery=est_delivery,
                        recipient_name=customer.name,
                        recipient_address=order.shipping_address,
                    )
                    db.add(shipment)
                    db.flush()
                    order.tracking_number = tracking

                    # Shipment timeline oluştur
                    st_val = ship_status.value if hasattr(ship_status, "value") else str(ship_status)
                    current_idx = ALL_STAGES.index(st_val)
                    stage_cursor = ship_created

                    for stage in ALL_STAGES[:current_idx + 1]:
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
                        ts = stage_cursor
                        if stage == st_val and order_status == OrderStatus.delivered:
                            ts = delivered_time
                        ts = min(ts, now)
                        db.add(ShipmentUpdate(
                            shipment_id=shipment.id,
                            status=stage,
                            location=loc_map[stage],
                            description=desc_map[stage],
                            timestamp=ts,
                        ))
                        if stage in STAGE_HOURS:
                            min_h, max_h = STAGE_HOURS[stage]
                            stage_cursor = ts + timedelta(hours=min_h + (order.id % max(1, max_h - min_h)))
                        else:
                            stage_cursor = ts + timedelta(hours=4)

                    shipments_created.append(shipment)

                    # ── Mesaj üret (kargo durumuna göre) ──────────────────────
                    msg_chance = random.random()

                    # Gecikmiş kargolar → gecikme şikayeti (%70 ihtimal)
                    ship_est = est_delivery if isinstance(est_delivery, datetime) else now
                    is_delayed = (ship_est < now) and (order_status == OrderStatus.shipped)
                    if is_delayed and msg_chance < 0.70:
                        tmpl = random.choice(DELAY_MESSAGES)
                        subj, body_t, cat, urg = tmpl
                        days_late = max(1, int((now - ship_est).total_seconds() / 86400))
                        body = body_t.format(
                            order_id=order.id,
                            tracking=tracking,
                            carrier=carrier,
                            days=days_late,
                            est_date=ship_est.strftime("%d.%m.%Y"),
                            product=sel_products[0].name,
                            item_count=n_items,
                            qty=random.randint(5, 30),
                        )
                        hours_ago = random.randint(0, 36)
                        msg_time = now - timedelta(hours=hours_ago)
                        db.add(CustomerMessage(
                            customer_id=customer.id,
                            direction="inbound",
                            subject=subj,
                            body=body,
                            created_at=msg_time,
                            is_read=hours_ago > 24,
                            ai_generated=False,
                            category=cat,
                            urgency=urg,
                            ai_summary=brief_summary(customer.name, cat, subj),
                            related_order_id=order.id,
                            related_shipment_id=shipment.id,
                        ))

                    # Teslim edilmişlerden geri bildirim (%25 ihtimal)
                    elif order_status == OrderStatus.delivered and msg_chance < 0.25:
                        tmpl = random.choice(DELIVERY_COMPLAINT_MESSAGES)
                        subj, body_t, cat, urg = tmpl
                        body = body_t.format(
                            order_id=order.id,
                            product=sel_products[0].name,
                            item_count=n_items,
                            qty=random.randint(5, 30),
                            tracking=tracking,
                            carrier=carrier,
                            days=1,
                            est_date=(now - timedelta(days=1)).strftime("%d.%m.%Y"),
                        )
                        # Mesaj teslimden 1-72 saat sonra
                        msg_time = delivered_time + timedelta(hours=random.randint(2, 72))
                        if msg_time > now:
                            msg_time = now - timedelta(hours=random.randint(1, 12))
                        hours_ago = (now - msg_time).total_seconds() / 3600
                        db.add(CustomerMessage(
                            customer_id=customer.id,
                            direction="inbound",
                            subject=subj,
                            body=body,
                            created_at=msg_time,
                            is_read=hours_ago > 24,
                            ai_generated=False,
                            category=cat,
                            urgency=urg,
                            ai_summary=brief_summary(customer.name, cat, subj),
                            related_order_id=order.id,
                            related_shipment_id=shipment.id,
                        ))

        db.flush()

        # ── Genel sorgular (siparişten bağımsız) ─────────────────────────────
        general_count = 0
        for _ in range(15):
            customer = random.choice(customers)
            tmpl = random.choice(GENERAL_MESSAGES)
            subj, body_t, cat, urg = tmpl
            product = random.choice(products)
            cust_orders = [o for o in orders_created if o.customer_id == customer.id]
            co = random.choice(cust_orders) if cust_orders else None
            body = body_t.format(
                order_id=co.id if co else "—",
                product=product.name,
                qty=random.randint(10, 50),
                tracking="—", carrier="—", days=2,
                est_date=(now + timedelta(days=3)).strftime("%d.%m.%Y"),
                item_count=2,
            )
            hours_ago = random.randint(0, 96)
            msg_time = now - timedelta(hours=hours_ago)
            db.add(CustomerMessage(
                customer_id=customer.id,
                direction="inbound",
                subject=subj,
                body=body,
                created_at=msg_time,
                is_read=hours_ago > 24,
                ai_generated=False,
                category=cat,
                urgency=urg,
                ai_summary=brief_summary(customer.name, cat, subj),
                related_order_id=co.id if co else None,
            ))
            general_count += 1

        # ── Giden yanıtlar ────────────────────────────────────────────────────
        reply_count = 0
        for customer in random.sample(customers, k=8):
            cust_orders = [o for o in orders_created if o.customer_id == customer.id]
            co = random.choice(cust_orders) if cust_orders else None
            sh = None
            if co:
                from models import Shipment as Sh
                sh_row = db.query(Sh).filter(Sh.order_id == co.id).first()
                if sh_row:
                    sh = sh_row
                    st_val = sh.status.value if hasattr(sh.status, "value") else str(sh.status)
                    est = sh.estimated_delivery
                    est_str = est.strftime("%d.%m.%Y") if isinstance(est, datetime) else str(est)
                    if st_val != "delivered":
                        body = (
                            f"Merhaba {customer.name.split()[0]}, #{co.id} numaralı siparişinizle "
                            f"ilgili inceleme yaptık. Kargonuz ({sh.tracking_number}) şu anda "
                            f"yolda olup tahmini teslimat tarihi {est_str}. "
                            "Gecikme yaşanması durumunda sizi bilgilendireceğiz."
                        )
                    else:
                        body = (
                            f"Merhaba {customer.name.split()[0]}, talebinizi aldık. "
                            "İncelememiz tamamlandıktan sonra en kısa sürede dönüş yapacağız."
                        )
                else:
                    body = "Merhaba, talebinizi aldık. En kısa sürede geri dönüş yapacağız."
            else:
                body = "Merhaba, talebinizi aldık. En kısa sürede geri dönüş yapacağız."

            db.add(CustomerMessage(
                customer_id=customer.id,
                direction="outbound",
                subject="Re: Sipariş Durumu Hakkında",
                body=body,
                created_at=now - timedelta(hours=random.randint(1, 48)),
                is_read=True,
                ai_generated=True,
                related_order_id=co.id if co else None,
                related_shipment_id=sh.id if sh else None,
            ))
            reply_count += 1

        db.flush()

        # Mesaj özeti
        from sqlalchemy import text as sqlt
        msg_stats = db.execute(sqlt("""
            SELECT category, COUNT(*) as cnt FROM customer_messages
            WHERE direction='inbound' GROUP BY category ORDER BY cnt DESC
        """)).fetchall()
        total_msgs = sum(r.cnt for r in msg_stats)
        today_msgs = db.execute(sqlt(
            "SELECT COUNT(*) FROM customer_messages WHERE direction='inbound' AND DATE(created_at)=DATE('now')"
        )).scalar()
        print(f"✓ {total_orders} orders, {len(shipments_created)} shipments")
        print(f"✓ {total_msgs} inbound messages ({today_msgs} today) + {reply_count} outbound")
        print(f"  Kategoriler: {', '.join(f'{r.category}:{r.cnt}' for r in msg_stats)}")

        # ── Operasyonel alertler — gerçek scan ───────────────────────────────
        db.commit()
        import simulation as sim
        scan_db = SessionLocal()
        try:
            scan_now = datetime.utcnow()
            scan_today = scan_now.replace(hour=0, minute=0, second=0, microsecond=0)
            sim._scan_delayed_shipments(scan_db, scan_now)
            sim._scan_low_stock_hourly(scan_db)
            sim._scan_message_complaints(scan_db, scan_today)
            sim._scan_overdue_orders(scan_db, scan_now)
            sim._scan_restock_suggestions(scan_db, scan_now)
            scan_db.commit()
            alert_count = scan_db.query(OperationalAlert).count()
            print(f"✓ {alert_count} operational alerts from real-time scans")
        finally:
            scan_db.close()

        print("\n✅ Database seeded successfully!")
        print("   Login: admin@demo.com / demo123")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        import traceback; traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
