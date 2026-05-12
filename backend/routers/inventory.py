from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_token as get_current_user
from models import Inventory, InventoryMovement, Product, User
from schemas import InventoryItem, InventoryListResponse, InventoryMovementOut

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _build_inventory_item(inv: Inventory) -> InventoryItem:
    pct = (inv.quantity_kg / inv.reorder_point * 100) if inv.reorder_point > 0 else 0.0
    return InventoryItem(
        id=inv.id,
        product_id=inv.product_id,
        product_name=inv.product.name,
        category=inv.product.category,
        unit=inv.product.unit,
        package_size=inv.product.package_size,
        price=inv.product.price,
        quantity_kg=inv.quantity_kg,
        min_threshold=inv.min_threshold,
        reorder_point=inv.reorder_point,
        is_low_stock=inv.quantity_kg < inv.min_threshold,
        is_critical=inv.quantity_kg < inv.min_threshold * 0.5,
        stock_percentage=round(pct, 1),
        last_updated=inv.last_updated.strftime("%d.%m.%Y %H:%M"),
    )


@router.get("", response_model=InventoryListResponse)
def list_inventory(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.query(Inventory).join(Product).all()
    # Sort: critical first, then low stock, then healthy
    items.sort(key=lambda i: (
        0 if i.quantity_kg < i.min_threshold * 0.5 else
        1 if i.quantity_kg < i.min_threshold else 2
    ))
    built = [_build_inventory_item(i) for i in items]
    low_count = sum(1 for i in built if i.is_low_stock)
    return InventoryListResponse(count=len(built), low_stock_count=low_count, items=built)


@router.get("/alerts", response_model=InventoryListResponse)
def inventory_alerts(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = (
        db.query(Inventory)
        .join(Product)
        .filter(Inventory.quantity_kg < Inventory.min_threshold)
        .all()
    )
    built = [_build_inventory_item(i) for i in items]
    return InventoryListResponse(count=len(built), low_stock_count=len(built), items=built)


@router.get("/{product_id}/movements", response_model=List[InventoryMovementOut])
def get_movements(
    product_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    movements = (
        db.query(InventoryMovement)
        .filter(InventoryMovement.product_id == product_id)
        .order_by(InventoryMovement.timestamp.desc())
        .limit(limit)
        .all()
    )
    result = []
    for m in movements:
        result.append(InventoryMovementOut(
            id=m.id,
            product_name=m.product.name,
            quantity_change=m.quantity_change,
            movement_type=m.movement_type,
            timestamp=m.timestamp.strftime("%d.%m.%Y %H:%M"),
            order_id=m.order_id,
        ))
    return result
