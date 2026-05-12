import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_token as get_current_user
from models import CustomerMessage, User, Customer, Order, Shipment
from operational_metrics import message_counts
from schemas import CustomerMessageOut, MessageListResponse, MessageStats
from message_intel import classify_customer_message, brief_summary

router = APIRouter(prefix="/messages", tags=["messages"])

# ── Categories exposed to frontend ───────────────────────────────────────────

CATEGORIES = [
    {"value": "teslimat_gecikmesi", "label": "Teslimat gecikmesi", "urgency": "yüksek"},
    {"value": "yanlis_urun",        "label": "Yanlış ürün",        "urgency": "orta"},
    {"value": "siparis_talebi",     "label": "Sipariş talebi",     "urgency": "orta"},
    {"value": "fatura_duzeltme",    "label": "Fatura",             "urgency": "düşük"},
    {"value": "stok_bilgisi",       "label": "Stok sorusu",        "urgency": "düşük"},
    {"value": "genel_destek",       "label": "Genel",              "urgency": "orta"},
]

URGENCY_DEFAULTS = {c["value"]: c["urgency"] for c in CATEGORIES}


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateMessageRequest(BaseModel):
    customer_id: int
    category: str
    subject: str
    body: str
    related_order_id: Optional[int] = None


class CreateMessageResponse(BaseModel):
    id: int
    customer_name: str
    category: str
    urgency: str
    ai_summary: str
    ai_action: str
    related_order_id: Optional[int] = None
    related_shipment_id: Optional[int] = None


# ── AI action suggestion via Groq ─────────────────────────────────────────────

def _groq_action_suggestion(category: str, subject: str, body: str, customer_name: str) -> str:
    """Call Gemini to get a short actionable suggestion for this message."""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return _fallback_action(category)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction="Sen bir kooperatif operasyon asistanısın. Kısa, net Türkçe aksiyon önerisi ver.",
            generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=120),
        )
        prompt = (
            f"Müşteri: {customer_name}\n"
            f"Konu kategorisi: {category}\n"
            f"Konu başlığı: {subject}\n"
            f"Mesaj içeriği: {body[:400]}\n\n"
            "Bu mesaj için operasyon yöneticisinin alması gereken tek ve en önemli aksiyonu "
            "1-2 cümleyle belirt. Türkçe yaz, eyleme geçilebilir ve net ol."
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception:
        return _fallback_action(category)


def _fallback_action(category: str) -> str:
    return {
        "teslimat_gecikmesi": "Kargo firmasıyla iletişime geçerek güncel teslim tarihini alın ve müşteriyi bilgilendirin.",
        "yanlis_urun":        "Siparişi doğrulayın, doğru ürünü en kısa sürede gönderin.",
        "siparis_talebi":     "Stok durumunu kontrol edin ve müşteriye sipariş onayı gönderin.",
        "fatura_duzeltme":    "Fatura kaydını muhasebe birimiyle kontrol edin ve düzeltme yapın.",
        "stok_bilgisi":       "Envanter sisteminden güncel stok bilgisini alın ve müşteriyle paylaşın.",
        "genel_destek":       "Mesajı inceleyin ve müşteriye 24 saat içinde geri dönüş yapın.",
    }.get(category, "Mesajı inceleyin ve müşteriye en kısa sürede yanıt verin.")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/categories")
def get_categories(_: User = Depends(get_current_user)):
    return {"categories": CATEGORIES}


@router.get("", response_model=MessageListResponse)
def list_messages(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(CustomerMessage).join(Customer)
    if unread_only:
        query = query.filter(CustomerMessage.is_read == False)

    messages = query.order_by(CustomerMessage.created_at.desc()).all()

    result = []
    for m in messages:
        result.append(
            CustomerMessageOut(
                id=m.id,
                customer_name=m.customer.name,
                customer_email=m.customer.email,
                direction=m.direction,
                subject=m.subject,
                body=m.body,
                created_at=m.created_at.strftime("%d.%m.%Y %H:%M"),
                is_read=m.is_read,
                ai_generated=m.ai_generated,
                category=m.category,
                urgency=m.urgency,
                ai_summary=m.ai_summary,
                related_order_id=m.related_order_id,
                related_shipment_id=m.related_shipment_id,
            )
        )

    mc = message_counts(db)
    stats = MessageStats(
        unread_inbound=mc["unread_inbound"],
        inbound_total=mc["inbound_total"],
        outbound_total=mc["outbound_total"],
        conversation_total=mc["conversation_total"],
    )

    return MessageListResponse(count=len(result), stats=stats, messages=result)


@router.post("", response_model=CreateMessageResponse)
def create_message(
    req: CreateMessageRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")

    # Validate category
    valid_cats = {c["value"] for c in CATEGORIES}
    if req.category not in valid_cats:
        raise HTTPException(status_code=422, detail=f"Geçersiz kategori: {req.category}")

    # Determine urgency from category
    urgency = URGENCY_DEFAULTS.get(req.category, "orta")

    # Auto-link shipment if order provided
    related_shipment_id = None
    if req.related_order_id:
        order = db.query(Order).filter(Order.id == req.related_order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
        ship = db.query(Shipment).filter(Shipment.order_id == req.related_order_id).first()
        if ship:
            related_shipment_id = ship.id

    # AI summary (rule-based, fast)
    ai_summary = brief_summary(customer.name, req.category, req.subject)

    # AI action suggestion (Groq call)
    ai_action = _groq_action_suggestion(req.category, req.subject, req.body, customer.name)

    msg = CustomerMessage(
        customer_id=customer.id,
        direction="inbound",
        subject=req.subject,
        body=req.body,
        created_at=datetime.utcnow(),
        is_read=False,
        ai_generated=False,
        category=req.category,
        urgency=urgency,
        ai_summary=ai_summary,
        related_order_id=req.related_order_id,
        related_shipment_id=related_shipment_id,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return CreateMessageResponse(
        id=msg.id,
        customer_name=customer.name,
        category=req.category,
        urgency=urgency,
        ai_summary=ai_summary,
        ai_action=ai_action,
        related_order_id=msg.related_order_id,
        related_shipment_id=related_shipment_id,
    )


@router.post("/{message_id}/read")
def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    msg = db.query(CustomerMessage).filter(CustomerMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.is_read = True
    db.commit()
    return {"status": "ok"}
