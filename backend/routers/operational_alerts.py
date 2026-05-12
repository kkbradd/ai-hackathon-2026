from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_token as get_current_user
from models import OperationalAlert, User
from schemas import AlertListResponse, OperationalAlertOut

router = APIRouter(prefix="/operational-alerts", tags=["operational-alerts"])


def _build_alert_out(a: OperationalAlert) -> OperationalAlertOut:
    return OperationalAlertOut(
        id=a.id,
        type=a.type,
        severity=a.severity,
        title=a.title,
        description=a.description,
        is_resolved=a.is_resolved,
        created_at=a.created_at.strftime("%d.%m.%Y %H:%M"),
        related_entity_id=a.related_entity_id,
    )


@router.get("", response_model=AlertListResponse)
def list_alerts(
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(OperationalAlert)
    if resolved is not None:
        query = query.filter(OperationalAlert.is_resolved == resolved)
    if severity:
        query = query.filter(OperationalAlert.severity == severity)
    alerts = query.order_by(OperationalAlert.created_at.desc()).limit(limit).all()
    unresolved = sum(1 for a in alerts if not a.is_resolved)
    return AlertListResponse(
        count=len(alerts),
        unresolved_count=unresolved,
        alerts=[_build_alert_out(a) for a in alerts],
    )


@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    alert = db.query(OperationalAlert).filter(OperationalAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Uyarı bulunamadı.")
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    return {"detail": "Uyarı çözüldü olarak işaretlendi.", "id": alert_id}
