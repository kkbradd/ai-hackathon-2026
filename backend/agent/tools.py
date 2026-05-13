import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from models import (
    Order, OrderItem, Product, Customer, OrderStatus,
    Shipment, ShipmentUpdate, CustomerMessage,
    Inventory, OperationalAlert, SupplierOrderDraft,
)


# ── Kept from v1 ──────────────────────────────────────────────────────────────

def get_order_status(db: Session, order_id: int) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"{order_id} numaralı sipariş bulunamadı."}

    items = []
    for item in order.items:
        items.append({
            "product": item.product.name,
            "quantity": item.quantity,
            "unit": item.product.unit,
            "unit_price": item.unit_price,
            "subtotal": round(item.quantity * item.unit_price, 2),
        })

    total = sum(i["subtotal"] for i in items)

    # Include shipment info if available
    shipment_info = None
    if order.shipment:
        s = order.shipment
        shipment_info = {
            "carrier": s.carrier,
            "tracking_number": s.tracking_number,
            "status": s.status,
            "estimated_delivery": s.estimated_delivery.strftime("%d.%m.%Y") if s.estimated_delivery else None,
        }

    return {
        "order_id": order.id,
        "customer": order.customer.name,
        "status": order.status,
        "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "shipment": shipment_info,
        "items": items,
        "total": round(total, 2),
    }


def list_pending_orders(db: Session, limit: int = 10) -> dict:
    orders = (
        db.query(Order)
        .filter(Order.status.in_([OrderStatus.pending, OrderStatus.processing]))
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for order in orders:
        item_count = sum(i.quantity for i in order.items)
        total = sum(i.quantity * i.unit_price for i in order.items)
        result.append({
            "order_id": order.id,
            "customer": order.customer.name,
            "status": order.status,
            "item_count": item_count,
            "total": round(total, 2),
            "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),
        })

    return {"count": len(result), "orders": result}


def get_order_history(db: Session, customer_email: str, limit: int = 5) -> dict:
    customer = db.query(Customer).filter(
        func.lower(Customer.email) == customer_email.lower()
    ).first()

    if not customer:
        return {"error": f"'{customer_email}' e-postasına sahip müşteri bulunamadı."}

    orders = (
        db.query(Order)
        .filter(Order.customer_id == customer.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for order in orders:
        total = sum(i.quantity * i.unit_price for i in order.items)
        result.append({
            "order_id": order.id,
            "status": order.status,
            "total": round(total, 2),
            "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),
            "item_count": len(order.items),
        })

    return {
        "customer": customer.name,
        "email": customer.email,
        "order_count": len(result),
        "orders": result,
    }


# ── New shipment tools ────────────────────────────────────────────────────────

def get_shipment_status(db: Session, order_id: int) -> dict:
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
    if not shipment:
        return {"error": f"{order_id} numaralı sipariş için kargo kaydı bulunamadı."}

    now = datetime.utcnow()
    is_delayed = (
        shipment.estimated_delivery is not None
        and shipment.estimated_delivery < now
        and shipment.status not in ("delivered", "failed", "returned")
    )

    last_update = None
    if shipment.updates:
        lu = shipment.updates[-1]
        last_update = {
            "status": lu.status,
            "location": lu.location,
            "timestamp": lu.timestamp.strftime("%d.%m.%Y %H:%M"),
        }

    return {
        "shipment_id": shipment.id,
        "order_id": order_id,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
        "status": shipment.status,
        "estimated_delivery": shipment.estimated_delivery.strftime("%d.%m.%Y") if shipment.estimated_delivery else None,
        "is_delayed": is_delayed,
        "last_update": last_update,
        "recipient": shipment.recipient_name,
    }


def get_shipment_timeline(db: Session, order_id: int) -> dict:
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
    if not shipment:
        return {"error": f"{order_id} numaralı sipariş için kargo kaydı bulunamadı."}

    events = []
    for u in shipment.updates:
        events.append({
            "status": u.status,
            "location": u.location,
            "description": u.description,
            "timestamp": u.timestamp.strftime("%d.%m.%Y %H:%M"),
        })

    now = datetime.utcnow()
    is_delayed = (
        shipment.estimated_delivery is not None
        and shipment.estimated_delivery < now
        and shipment.status not in ("delivered", "failed", "returned")
    )

    return {
        "shipment_id": shipment.id,
        "order_id": order_id,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
        "current_status": shipment.status,
        "estimated_delivery": shipment.estimated_delivery.strftime("%d.%m.%Y") if shipment.estimated_delivery else None,
        "is_delayed": is_delayed,
        "event_count": len(events),
        "timeline": events,
    }


def get_delayed_shipments(db: Session) -> dict:
    now = datetime.utcnow()
    delayed = (
        db.query(Shipment)
        .filter(
            Shipment.estimated_delivery < now,
            Shipment.status.notin_(["delivered", "failed", "returned"]),
        )
        .order_by(Shipment.estimated_delivery.asc())
        .all()
    )

    result = []
    for s in delayed:
        days_overdue = (now - s.estimated_delivery).days
        result.append({
            "shipment_id": s.id,
            "order_id": s.order_id,
            "carrier": s.carrier,
            "tracking_number": s.tracking_number,
            "status": s.status,
            "recipient": s.recipient_name,
            "estimated_delivery": s.estimated_delivery.strftime("%d.%m.%Y"),
            "days_overdue": days_overdue,
        })

    return {"count": len(result), "delayed_shipments": result}


def get_recent_messages(db: Session, limit: int = 5) -> dict:
    messages = (
        db.query(CustomerMessage)
        .filter(CustomerMessage.direction == "inbound")
        .order_by(CustomerMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    unread = (
        db.query(CustomerMessage)
        .filter(CustomerMessage.direction == "inbound", CustomerMessage.is_read == False)
        .count()
    )

    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "customer": m.customer.name,
            "email": m.customer.email,
            "subject": m.subject,
            "body": m.body[:200] + ("..." if len(m.body) > 200 else ""),
            "created_at": m.created_at.strftime("%d.%m.%Y %H:%M"),
            "is_read": m.is_read,
        })

    return {
        "unread_count": unread,
        "shown": len(result),
        "messages": result,
    }


def summarize_daily_operations(db: Session) -> dict:
    pending_count = db.query(Order).filter(
        Order.status.in_([OrderStatus.pending, OrderStatus.processing])
    ).count()

    now = datetime.utcnow()
    active_shipments = db.query(Shipment).filter(
        Shipment.status.notin_(["delivered", "failed", "returned"])
    ).count()

    delayed_count = db.query(Shipment).filter(
        Shipment.estimated_delivery < now,
        Shipment.status.notin_(["delivered", "failed", "returned"]),
    ).count()

    unread_messages = db.query(CustomerMessage).filter(
        CustomerMessage.direction == "inbound",
        CustomerMessage.is_read == False,
    ).count()

    delivered_today = db.query(Shipment).filter(
        Shipment.status == "delivered",
        func.date(Shipment.updated_at) == func.date(now),
    ).count()

    return {
        "summary": {
            "pending_orders": pending_count,
            "active_shipments": active_shipments,
            "delayed_shipments": delayed_count,
            "unread_messages": unread_messages,
            "delivered_today": delivered_today,
        },
        "alerts": [
            f"{delayed_count} gecikmiş kargo tespit edildi." if delayed_count > 0 else None,
            f"{unread_messages} okunmamış müşteri mesajı var." if unread_messages > 0 else None,
            f"{pending_count} sipariş işlem bekliyor." if pending_count > 0 else None,
        ],
    }


# ── New cooperative-specific tools ────────────────────────────────────────────

def get_inventory_status(db: Session, filter: str = "all", low_stock_only: bool = False) -> dict:
    """Return inventory levels for all products, flagging low-stock and critical items."""
    only_low = filter == "low_stock" or low_stock_only
    query = db.query(Inventory).join(Product)
    if only_low:
        query = query.filter(Inventory.quantity_kg < Inventory.min_threshold)
    items = query.all()
    result = []
    for inv in items:
        result.append({
            "product": inv.product.name,
            "category": inv.product.category,
            "unit": inv.product.unit,
            "quantity": inv.quantity_kg,
            "min_threshold": inv.min_threshold,
            "reorder_point": inv.reorder_point,
            "is_low_stock": inv.quantity_kg < inv.min_threshold,
            "is_critical": inv.quantity_kg < inv.min_threshold * 0.5,
            "last_updated": inv.last_updated.strftime("%d.%m.%Y %H:%M"),
        })
    low_count = sum(1 for i in result if i["is_low_stock"])
    critical_count = sum(1 for i in result if i["is_critical"])
    return {
        "count": len(result),
        "low_stock_count": low_count,
        "critical_count": critical_count,
        "items": result,
    }


def get_operational_alerts(db: Session, severity: str = None, resolved=False) -> dict:
    """Retrieve operational alerts filtered by severity and resolution status."""
    if isinstance(resolved, str):
        resolved = resolved.lower() == "true"
    query = db.query(OperationalAlert).filter(OperationalAlert.is_resolved == resolved)
    if severity:
        query = query.filter(OperationalAlert.severity == severity)
    alerts = query.order_by(OperationalAlert.created_at.desc()).limit(15).all()
    result = [{
        "id": a.id,
        "type": a.type,
        "severity": a.severity,
        "title": a.title,
        "description": a.description,
        "created_at": a.created_at.strftime("%d.%m.%Y %H:%M"),
        "is_resolved": a.is_resolved,
    } for a in alerts]
    return {"count": len(result), "alerts": result}


def get_demand_trends(db: Session, days: int = 7) -> dict:
    """Analyse product demand over the last N days using order data."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            OrderItem.product_id,
            Product.name,
            func.sum(OrderItem.quantity).label("total_qty"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
        )
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.created_at >= cutoff)
        .group_by(OrderItem.product_id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .all()
    )
    result = [{
        "product_id": r.product_id,
        "name": r.name,
        "total_quantity": float(r.total_qty or 0),
        "order_count": int(r.order_count or 0),
        "avg_daily_demand": round(float(r.total_qty or 0) / days, 2),
    } for r in rows]
    return {"period_days": days, "count": len(result), "products": result}


def get_daily_summary_rich(db: Session) -> dict:
    """Comprehensive daily summary: operations KPIs + inventory alerts + demand trends."""
    base = summarize_daily_operations(db)
    inventory = get_inventory_status(db, low_stock_only=True)
    alerts = get_operational_alerts(db)
    demand = get_demand_trends(db, days=7)
    return {
        **base,
        "low_stock_items": inventory["items"],
        "critical_alerts": alerts["alerts"],
        "top_demand_products": demand["products"][:5],
        "low_stock_count": inventory["low_stock_count"],
        "unresolved_alert_count": alerts["count"],
    }


# ── Action Tools (Sisteme Müdahale Eden Araçlar) ─────────────────────────────

def resolve_operational_alert(db: Session, alert_id: int) -> dict:
    """Belirtilen operasyonel uyarıyı 'çözüldü' olarak işaretler."""
    alert = db.query(OperationalAlert).filter(OperationalAlert.id == alert_id).first()
    if not alert:
        return {"error": f"{alert_id} ID'li uyarı bulunamadı."}
    
    if alert.is_resolved:
        return {"message": f"{alert_id} ID'li uyarı zaten çözülmüş durumda."}
        
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": f"{alert_id} ID'li uyarı başarıyla çözüldü olarak işaretlendi."}


def update_shipment_status(db: Session, shipment_id: int, new_status: str, location: str, description: str = "") -> dict:
    """Belirtilen kargonun durumunu günceller ve yeni bir kargo hareket kaydı (ShipmentUpdate) ekler."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return {"error": f"{shipment_id} ID'li kargo bulunamadı."}
        
    valid_statuses = ["preparing", "in_transit", "at_facility", "out_for_delivery", "delivered", "failed", "returned"]
    if new_status not in valid_statuses:
        return {"error": f"Geçersiz durum. Geçerli durumlar: {', '.join(valid_statuses)}"}
        
    shipment.status = new_status
    shipment.updated_at = datetime.utcnow()
    
    update_record = ShipmentUpdate(
        shipment_id=shipment.id,
        status=new_status,
        location=location,
        description=description,
        timestamp=datetime.utcnow()
    )
    db.add(update_record)
    
    if new_status == "delivered":
        # Siparişi de teslim edildi yap
        order = db.query(Order).filter(Order.id == shipment.order_id).first()
        if order:
            order.status = OrderStatus.delivered
            
    db.commit()
    return {
        "message": f"Kargo durumu '{new_status}' olarak güncellendi.",
        "shipment_id": shipment.id,
        "new_status": new_status
    }


def draft_supplier_order(db: Session, product_id: int, quantity: float) -> dict:
    """Tedarikçiye gönderilmek üzere AI ile e-posta taslağı oluşturur (gerçekten göndermez)."""
    from email_drafter import draft_supplier_email

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": f"{product_id} ID'li ürün bulunamadı."}

    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    current_stock = inv.quantity_kg if inv else 0.0
    reorder_point = inv.reorder_point if inv else 0.0

    email = draft_supplier_email(
        product_name=product.name,
        category=product.category,
        quantity=quantity,
        unit=product.unit,
        current_stock=current_stock,
        reorder_point=reorder_point,
    )

    draft = SupplierOrderDraft(
        product_id=product.id,
        quantity=quantity,
        unit=product.unit,
        supplier_email=email["supplier_email"],
        supplier_name=email["supplier_name"],
        subject=email["subject"],
        body=email["body"],
        status="draft",
        triggered_by="chat",
    )
    db.add(draft)
    db.commit()

    return {
        "message": f"{product.name} için {quantity} {product.unit} tedarikçi e-posta taslağı oluşturuldu. UI'dan inceleyip 'Gönder' butonuyla iletebilirsiniz.",
        "draft_id": draft.id,
        "supplier": email["supplier_name"],
        "supplier_email": email["supplier_email"],
        "subject": email["subject"],
    }


def update_order_status(db: Session, order_id: int, new_status: str) -> dict:
    """Belirtilen siparişin durumunu günceller."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"{order_id} numaralı sipariş bulunamadı."}

    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        return {"error": f"Geçersiz durum. Geçerli durumlar: {', '.join(valid_statuses)}"}

    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": f"Sipariş {order_id} durumu '{new_status}' olarak güncellendi."
    }


_ALLOWED_SQL = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA)\b",
    re.IGNORECASE,
)


def execute_sql(db: Session, query: str, limit: int = 20) -> dict:
    """Kullanıcının istediği SELECT sorgusunu çalıştırır ve sonuçları döndürür."""
    query = query.strip().rstrip(";")

    if not _ALLOWED_SQL.match(query):
        return {"error": "Yalnızca SELECT sorguları çalıştırılabilir."}
    if _FORBIDDEN_SQL.search(query):
        return {"error": "Veri değiştiren ifadeler (INSERT/UPDATE/DELETE/DROP vb.) yasaktır."}

    limit = max(1, min(int(limit), 100))

    # Wrap in a subquery to enforce LIMIT without touching the user's query structure
    wrapped = f"SELECT * FROM ({query}) AS _q LIMIT {limit}"

    try:
        result = db.execute(text(wrapped))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {
            "columns": columns,
            "row_count": len(rows),
            "rows": rows,
        }
    except Exception as exc:
        return {"error": f"SQL hatası: {exc}"}
