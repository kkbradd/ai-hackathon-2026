from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import verify_token
from database import get_db
from models import Shipment, User
from schemas import (
    ShipmentDetail, ShipmentListResponse, ShipmentSummary,
    ShipmentUpdateOut, ShipmentAlertListResponse, ShipmentAlertOut,
)

router = APIRouter(prefix="/shipments", tags=["shipments"])


def _is_delayed(shipment: Shipment) -> bool:
    now = datetime.utcnow()
    return (
        shipment.estimated_delivery is not None
        and shipment.estimated_delivery < now
        and shipment.status not in ("delivered", "failed", "returned")
    )


def _fmt(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else None


@router.get("", response_model=ShipmentListResponse)
def list_shipments(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(verify_token),
):
    q = db.query(Shipment)
    if status:
        q = q.filter(Shipment.status == status)
    q = q.order_by(Shipment.created_at.desc())
    total = q.count()
    shipments = q.offset(offset).limit(limit).all()

    result = [
        ShipmentSummary(
            id=s.id,
            order_id=s.order_id,
            tracking_number=s.tracking_number,
            carrier=s.carrier,
            status=s.status,
            estimated_delivery=_fmt(s.estimated_delivery),
            recipient_name=s.recipient_name,
            created_at=_fmt(s.created_at),
            is_delayed=_is_delayed(s),
        )
        for s in shipments
    ]
    return ShipmentListResponse(count=total, shipments=result)


@router.get("/alerts", response_model=ShipmentAlertListResponse)
def shipment_alerts(
    db: Session = Depends(get_db),
    _: User = Depends(verify_token),
):
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

    alerts = [
        ShipmentAlertOut(
            id=s.id,
            order_id=s.order_id,
            tracking_number=s.tracking_number,
            carrier=s.carrier,
            recipient_name=s.recipient_name,
            estimated_delivery=_fmt(s.estimated_delivery),
            days_overdue=max(0, (now - s.estimated_delivery).days),
        )
        for s in delayed
    ]
    return ShipmentAlertListResponse(count=len(alerts), alerts=alerts)


@router.get("/{shipment_id}", response_model=ShipmentDetail)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_token),
):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Kargo kaydı bulunamadı.")

    updates = [
        ShipmentUpdateOut(
            status=u.status,
            location=u.location,
            description=u.description,
            timestamp=u.timestamp.strftime("%d.%m.%Y %H:%M"),
        )
        for u in s.updates
    ]

    return ShipmentDetail(
        id=s.id,
        order_id=s.order_id,
        tracking_number=s.tracking_number,
        carrier=s.carrier,
        status=s.status,
        estimated_delivery=_fmt(s.estimated_delivery),
        recipient_name=s.recipient_name,
        recipient_address=s.recipient_address,
        created_at=_fmt(s.created_at),
        is_delayed=_is_delayed(s),
        updates=updates,
    )


@router.get("/{shipment_id}/timeline", response_model=ShipmentDetail)
def get_shipment_timeline(
    shipment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_token),
):
    return get_shipment(shipment_id, db, _)
