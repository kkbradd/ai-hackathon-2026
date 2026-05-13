"""Tedarikçi sipariş e-posta taslakları (AI üretimli, gönderim simüle).

Demo akışı:
1. Inventory agent stok düşük → otomatik taslak üretir (status='draft')
2. Veya chat agent draft_supplier_order tool'u ile manuel üretir
3. UI taslakları listeler → operatör 'Gönder' der → status='sent', sent_at set
4. 'İptal' → status='cancelled'

Hiçbir gerçek SMTP yok; bu jürilere "kanal hazır, sadece config" mesajı verir.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import verify_token as get_current_user
from database import get_db
from models import SupplierOrderDraft, User, Product, Inventory
from email_drafter import draft_supplier_email

router = APIRouter(prefix="/supplier-drafts", tags=["supplier-drafts"])


class SupplierDraftOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    category: str
    quantity: float
    unit: str
    supplier_name: Optional[str]
    supplier_email: str
    subject: str
    body: str
    status: str
    created_at: str
    sent_at: Optional[str]
    triggered_by: Optional[str]


class SupplierDraftListResponse(BaseModel):
    count: int
    pending_count: int
    drafts: list[SupplierDraftOut]


class CreateDraftRequest(BaseModel):
    product_id: int
    quantity: float


def _serialize(d: SupplierOrderDraft) -> SupplierDraftOut:
    return SupplierDraftOut(
        id=d.id,
        product_id=d.product_id,
        product_name=d.product.name if d.product else "—",
        category=d.product.category if d.product else "—",
        quantity=d.quantity,
        unit=d.unit,
        supplier_name=d.supplier_name,
        supplier_email=d.supplier_email,
        subject=d.subject,
        body=d.body,
        status=d.status,
        created_at=d.created_at.strftime("%d.%m.%Y %H:%M"),
        sent_at=d.sent_at.strftime("%d.%m.%Y %H:%M") if d.sent_at else None,
        triggered_by=d.triggered_by,
    )


@router.get("", response_model=SupplierDraftListResponse)
def list_drafts(
    status: Optional[str] = None,
    limit: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(SupplierOrderDraft)
    if status:
        q = q.filter(SupplierOrderDraft.status == status)
    drafts = q.order_by(SupplierOrderDraft.created_at.desc()).limit(limit).all()
    pending = db.query(SupplierOrderDraft).filter(SupplierOrderDraft.status == "draft").count()
    return SupplierDraftListResponse(
        count=len(drafts),
        pending_count=pending,
        drafts=[_serialize(d) for d in drafts],
    )


@router.post("", response_model=SupplierDraftOut)
def create_draft(
    req: CreateDraftRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    inv = db.query(Inventory).filter(Inventory.product_id == req.product_id).first()
    email = draft_supplier_email(
        product_name=product.name,
        category=product.category,
        quantity=req.quantity,
        unit=product.unit,
        current_stock=inv.quantity_kg if inv else 0.0,
        reorder_point=inv.reorder_point if inv else 0.0,
    )
    draft = SupplierOrderDraft(
        product_id=product.id,
        quantity=req.quantity,
        unit=product.unit,
        supplier_email=email["supplier_email"],
        supplier_name=email["supplier_name"],
        subject=email["subject"],
        body=email["body"],
        status="draft",
        triggered_by="manual",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return _serialize(draft)


@router.post("/{draft_id}/send")
def send_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Gönderim simülasyonu — gerçek SMTP yok, sadece status değişir."""
    draft = db.query(SupplierOrderDraft).filter(SupplierOrderDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı.")
    if draft.status != "draft":
        raise HTTPException(status_code=400, detail=f"Taslak zaten '{draft.status}' durumunda.")
    draft.status = "sent"
    draft.sent_at = datetime.utcnow()
    db.commit()
    return {
        "detail": f"E-posta {draft.supplier_email} adresine gönderildi (simülasyon).",
        "id": draft.id,
        "sent_at": draft.sent_at.strftime("%d.%m.%Y %H:%M"),
    }


@router.post("/{draft_id}/cancel")
def cancel_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    draft = db.query(SupplierOrderDraft).filter(SupplierOrderDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı.")
    if draft.status != "draft":
        raise HTTPException(status_code=400, detail=f"Taslak zaten '{draft.status}' durumunda.")
    draft.status = "cancelled"
    db.commit()
    return {"detail": "Taslak iptal edildi.", "id": draft.id}
