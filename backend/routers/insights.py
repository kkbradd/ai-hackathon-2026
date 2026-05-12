from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import verify_token as get_current_user
from database import get_db
from models import AIInsight, User
from schemas import AIInsightOut, InsightListResponse

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=InsightListResponse)
def list_insights(
    agent_name: Optional[str] = None,
    severity: Optional[str] = None,
    insight_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(AIInsight).filter(AIInsight.is_dismissed == False)
    if agent_name:
        q = q.filter(AIInsight.agent_name == agent_name)
    if severity:
        q = q.filter(AIInsight.severity == severity)
    if insight_type:
        q = q.filter(AIInsight.insight_type == insight_type)
    total = q.count()
    rows = q.order_by(AIInsight.created_at.desc()).offset(offset).limit(limit).all()
    items = [
        AIInsightOut(
            id=r.id,
            agent_name=r.agent_name,
            insight_type=r.insight_type,
            content=r.content,
            severity=r.severity,
            related_entity_type=r.related_entity_type,
            related_entity_id=r.related_entity_id,
            created_at=r.created_at.strftime("%d.%m.%Y %H:%M"),
            is_dismissed=r.is_dismissed,
        )
        for r in rows
    ]
    return InsightListResponse(count=total, items=items)


@router.post("/{insight_id}/dismiss")
def dismiss_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    row = db.query(AIInsight).filter(AIInsight.id == insight_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="İçgörü bulunamadı.")
    row.is_dismissed = True
    db.commit()
    return {"ok": True}


@router.get("/agent-status")
def agent_status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    agent_names = ["operational", "shipment", "inventory", "customer_issue"]
    result = []
    for name in agent_names:
        latest = (
            db.query(AIInsight)
            .filter(AIInsight.agent_name == name)
            .order_by(AIInsight.created_at.desc())
            .first()
        )
        if latest:
            count = (
                db.query(AIInsight)
                .filter(
                    AIInsight.agent_name == name,
                    AIInsight.created_at >= latest.created_at.replace(second=0, microsecond=0),
                )
                .count()
            )
            result.append({
                "agent_name": name,
                "last_run_at": latest.created_at.strftime("%d.%m.%Y %H:%M"),
                "insight_count": count,
            })
        else:
            result.append({
                "agent_name": name,
                "last_run_at": None,
                "insight_count": 0,
            })
    return {"agents": result}
