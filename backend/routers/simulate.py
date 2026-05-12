from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_token as get_current_user
from models import User
from schemas import SimulateEventRequest
import simulation

router = APIRouter(prefix="/simulate", tags=["simulate"])

VALID_EVENTS = {"delayed_shipment", "stock_drop", "complaint", "anomaly", "delivery"}


@router.post("/event")
def trigger_event(
    req: SimulateEventRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if req.event_type not in VALID_EVENTS:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz olay tipi. Geçerli tipler: {', '.join(VALID_EVENTS)}",
        )
    simulation.trigger_event(req.event_type, req.target_id)
    labels = {
        "delayed_shipment": "Kargo gecikme olayı tetiklendi.",
        "stock_drop":       "Stok düşürme olayı tetiklendi.",
        "complaint":        "Müşteri şikayeti oluşturuldu.",
        "anomaly":          "Operasyonel anomali oluşturuldu.",
        "delivery":         "Teslimat tamamlama olayı tetiklendi.",
    }
    return {"detail": labels[req.event_type], "event_type": req.event_type}
