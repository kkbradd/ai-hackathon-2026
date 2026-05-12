from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_token as get_current_user
from models import Customer, User

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
def list_customers(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customers = db.query(Customer).order_by(Customer.name).all()
    return {
        "count": len(customers),
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "customer_type": c.customer_type,
            }
            for c in customers
        ],
    }
