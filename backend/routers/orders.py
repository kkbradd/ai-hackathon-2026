from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import verify_token
from database import get_db
from operational_metrics import counts_orders_by_status, pending_pipeline_count
from models import Order, OrderItem, User
from schemas import OrderListResponse, OrderDetail, OrderSummary, OrderItemOut, OrderSummaryItem

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderListResponse)
def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    date_filter: Optional[str] = Query(None, description="today | week | all"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(verify_token),
):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if date_filter == "today":
        query = query.filter(Order.created_at >= today_start)
    elif date_filter == "week":
        week_start = today_start - timedelta(days=today_start.weekday())
        query = query.filter(Order.created_at >= week_start)
    # "all" or None: no date filter

    total_for_filter = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()

    status_breakdown = counts_orders_by_status(db)
    pending_pipe = pending_pipeline_count(db)

    result = []
    for order in orders:
        item_count = sum(i.quantity for i in order.items)
        total = round(sum(i.quantity * i.unit_price for i in order.items), 2)
        items = [
            OrderSummaryItem(
                product=i.product.name,
                quantity=i.quantity,
                unit=i.product.unit,
                unit_price=i.unit_price,
                subtotal=round(i.quantity * i.unit_price, 2),
            )
            for i in order.items
        ]
        result.append(
            OrderSummary(
                order_id=order.id,
                customer=order.customer.name,
                customer_type=order.customer.customer_type,
                status=order.status,
                item_count=item_count,
                total=total,
                created_at=order.created_at.strftime("%d.%m.%Y %H:%M"),
                items=items,
            )
        )

    return OrderListResponse(
        count=len(result),
        total_matching_filter=total_for_filter,
        counts_by_status=status_breakdown,
        pending_pipeline=pending_pipe,
        orders=result,
    )


@router.get("/{order_id}", response_model=OrderDetail)
def get_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(verify_token)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    items = [
        OrderItemOut(
            product=item.product.name,
            quantity=item.quantity,
            unit=item.product.unit,
            unit_price=item.unit_price,
            subtotal=round(item.quantity * item.unit_price, 2),
        )
        for item in order.items
    ]
    total = round(sum(i.subtotal for i in items), 2)

    return OrderDetail(
        order_id=order.id,
        customer=order.customer.name,
        customer_type=order.customer.customer_type,
        status=order.status,
        created_at=order.created_at.strftime("%d.%m.%Y %H:%M"),
        shipping_address=order.shipping_address,
        tracking_number=order.tracking_number,
        items=items,
        total=total,
    )
