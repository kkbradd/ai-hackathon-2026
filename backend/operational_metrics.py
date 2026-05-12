"""
Single source of truth for KPIs backed by SQL. Used by dashboard, orders, messages.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    CustomerMessage,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Shipment,
    ShipmentStatus,
)

_TERMINAL_SHIPMENT = ("delivered", "failed", "returned")


def week_bounds(now: datetime, weeks_ago: int = 0) -> Tuple[datetime, datetime]:
    """Monday 00:00 UTC of target week → end (exclusive after 7 days)."""
    current_week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    target_week_start = current_week_start - timedelta(weeks=weeks_ago)
    target_week_end = target_week_start + timedelta(days=7)
    return target_week_start, target_week_end


def counts_orders_by_status(db: Session) -> Dict[str, int]:
    rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    return {str(row[0]): int(row[1]) for row in rows}


def pending_pipeline_count(db: Session) -> int:
    """Bekleyen + işleniyor — aligns with dashboard KPI pending_orders."""
    return (
        db.query(Order)
        .filter(Order.status.in_([OrderStatus.pending, OrderStatus.processing]))
        .count()
    )


def unread_inbound_messages_count(db: Session) -> int:
    return (
        db.query(CustomerMessage)
        .filter(
            CustomerMessage.direction == "inbound",
            CustomerMessage.is_read.is_(False),
        )
        .count()
    )


def message_counts(db: Session) -> Dict[str, int]:
    inbound_unread = (
        db.query(CustomerMessage)
        .filter(
            CustomerMessage.direction == "inbound",
            CustomerMessage.is_read.is_(False),
        )
        .count()
    )
    inbound_total = (
        db.query(CustomerMessage)
        .filter(CustomerMessage.direction == "inbound")
        .count()
    )
    outbound_total = (
        db.query(CustomerMessage)
        .filter(CustomerMessage.direction == "outbound")
        .count()
    )
    grand_total = db.query(CustomerMessage).count()
    return {
        "unread_inbound": inbound_unread,
        "inbound_total": inbound_total,
        "outbound_total": outbound_total,
        "conversation_total": grand_total,
    }


def active_shipments_count(db: Session) -> int:
    return (
        db.query(Shipment)
        .filter(
            Shipment.status.in_(
                [
                    ShipmentStatus.in_transit,
                    ShipmentStatus.at_facility,
                    ShipmentStatus.out_for_delivery,
                ]
            )
        )
        .count()
    )


def delayed_shipments_count(db: Session, now: datetime) -> int:
    return (
        db.query(Shipment)
        .filter(
            Shipment.estimated_delivery < now,
            Shipment.status.notin_(list(_TERMINAL_SHIPMENT)),
        )
        .count()
    )


def non_terminal_shipments_count(db: Session) -> int:
    """Denominator for delay ratio: shipments still in network."""
    return db.query(Shipment).filter(Shipment.status.notin_(list(_TERMINAL_SHIPMENT))).count()


def shipment_delay_ratio_pct(db: Session, now: datetime) -> float:
    """% of active (non-terminal) shipments that have missed estimated_delivery."""
    total_active = non_terminal_shipments_count(db)
    if total_active <= 0:
        return 0.0
    delayed = delayed_shipments_count(db, now)
    return round(min(delayed / total_active * 100, 100.0), 1)


def low_stock_products_count(db: Session) -> int:
    return (
        db.query(Inventory)
        .filter(Inventory.quantity_kg < Inventory.min_threshold)
        .count()
    )


def inventory_health_score(db: Session) -> float:
    """
    0–100: average of min(100, qty/reorder_point*100) per stocked product.
    Low when many SKUs sit below reorder.
    """
    rows = db.query(Inventory.quantity_kg, Inventory.reorder_point).all()
    if not rows:
        return 100.0
    scores = []
    for qty, reorder in rows:
        rp = max(float(reorder or 1.0), 1e-6)
        scores.append(min(100.0, (float(qty) / rp) * 100.0))
    return round(sum(scores) / len(scores), 1)


def on_time_delivery_rate(db: Session) -> float:
    """% of active (non-terminal) shipments still within their estimated delivery window."""
    now = datetime.utcnow()
    total_active = (
        db.query(Shipment)
        .filter(Shipment.status.notin_(list(_TERMINAL_SHIPMENT)))
        .count()
    )
    if total_active <= 0:
        return 100.0
    delayed = (
        db.query(Shipment)
        .filter(
            Shipment.status.notin_(list(_TERMINAL_SHIPMENT)),
            Shipment.estimated_delivery < now,
        )
        .count()
    )
    on_time = total_active - delayed
    return round(on_time / total_active * 100, 1)


def revenue_sum_query(db: Session):
    return (
        db.query(func.sum(OrderItem.unit_price * OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .scalar()
    )


def revenue_today(db: Session, today_start: datetime) -> float:
    v = (
        db.query(func.sum(OrderItem.unit_price * OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.created_at >= today_start)
        .scalar()
    )
    return round(float(v or 0.0), 2)


def revenue_for_week(db: Session, week_start: datetime, week_end: datetime) -> float:
    v = (
        db.query(func.sum(OrderItem.unit_price * OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.created_at >= week_start,
            Order.created_at < week_end,
        )
        .scalar()
    )
    return round(float(v or 0.0), 2)


def orders_count_in_range(db: Session, start: datetime, end: datetime) -> int:
    return (
        db.query(Order)
        .filter(Order.created_at >= start, Order.created_at < end)
        .count()
    )


def shipment_distribution_map(db: Session, now: datetime) -> Dict[str, int]:
    dist_rows = (
        db.query(Shipment.status, func.count(Shipment.id)).group_by(Shipment.status).all()
    )
    dist_map = {row[0]: row[1] for row in dist_rows}
    dist_map["delayed"] = delayed_shipments_count(db, now)
    return dist_map


def order_list_aggregate_total(db: Session, status_filter: Optional[str]) -> int:
    q = db.query(Order)
    if status_filter:
        q = q.filter(Order.status == status_filter)
    return q.count()

