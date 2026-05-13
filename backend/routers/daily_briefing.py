"""Günlük 08:00 brifingi — depo/kargo/operasyon için rol-bazlı özet ve listeler.

Gereksinim alan 5 (workflow & task management) örnek senaryosunun karşılığı:
'Sabah 08:00'de sistem o güne ait siparişleri analiz ediyor, depo sorumlusuna
hazırlanması gereken paketleri, kargo görevlisine teslim rotasını çıkarıyor.'

AI özet için Gemini kullanır; key yoksa şablon fallback.
30 dakikalık in-memory cache (her isteği LLM'e götürmeyiz).
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import verify_token as get_current_user
from database import get_db
from email_drafter import _gemini_text  # var olan helper'ı tekrar kullan
from models import User

router = APIRouter(prefix="/daily-briefing", tags=["daily-briefing"])

_CACHE: dict = {"key": None, "data": None}
_CACHE_TTL = timedelta(minutes=30)


# ── Schemas ───────────────────────────────────────────────────────────────────

class WarehouseItem(BaseModel):
    order_id: int
    customer_name: str
    line_count: int
    address: Optional[str]


class CourierRoute(BaseModel):
    shipment_id: int
    order_id: int
    tracking_number: str
    carrier: str
    recipient_name: Optional[str]
    district: Optional[str]
    is_delayed: bool


class OperationsItem(BaseModel):
    type: str  # 'alert' | 'insight'
    severity: str
    title: str
    detail: str
    created_at: str


class RoleBriefing(BaseModel):
    ai_summary: str
    item_count: int
    items: list


class DailyBriefingResponse(BaseModel):
    generated_at: str
    date_label: str
    headline: str
    warehouse: RoleBriefing
    courier: RoleBriefing
    operations: RoleBriefing


# ── Helpers ───────────────────────────────────────────────────────────────────

def _district_from_address(addr: Optional[str]) -> Optional[str]:
    if not addr:
        return None
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    return parts[-1] if parts else None


def _fmt_dt(v) -> str:
    if not v:
        return ""
    if isinstance(v, str):
        try:
            v = datetime.fromisoformat(v)
        except ValueError:
            return v[:5]
    return v.strftime("%H:%M")


def _today_window() -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


# ── Data collectors ──────────────────────────────────────────────────────────

def _warehouse_items(db: Session) -> list[WarehouseItem]:
    rows = db.execute(text("""
        SELECT o.id AS order_id,
               c.name AS customer_name,
               COUNT(oi.id) AS line_count,
               o.shipping_address
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        WHERE o.status IN ('pending', 'processing')
        GROUP BY o.id, c.name, o.shipping_address
        ORDER BY o.created_at ASC
        LIMIT 12
    """)).fetchall()
    return [
        WarehouseItem(
            order_id=r.order_id,
            customer_name=r.customer_name,
            line_count=r.line_count or 0,
            address=r.shipping_address,
        )
        for r in rows
    ]


def _courier_routes(db: Session) -> list[CourierRoute]:
    start, end = _today_window()
    rows = db.execute(text("""
        SELECT s.id AS shipment_id,
               s.order_id,
               s.tracking_number,
               s.carrier,
               s.recipient_name,
               s.recipient_address,
               s.estimated_delivery,
               s.status
        FROM shipments s
        WHERE s.status IN ('out_for_delivery', 'at_facility', 'in_transit')
           OR (s.estimated_delivery IS NOT NULL
               AND s.estimated_delivery >= :start
               AND s.estimated_delivery < :end)
        ORDER BY
          CASE s.status WHEN 'out_for_delivery' THEN 0 ELSE 1 END,
          s.estimated_delivery ASC
        LIMIT 12
    """), {"start": start, "end": end}).fetchall()

    now = datetime.utcnow()
    out = []
    for r in rows:
        eta = r.estimated_delivery
        if isinstance(eta, str):
            try:
                eta = datetime.fromisoformat(eta)
            except ValueError:
                eta = None
        is_delayed = bool(eta and eta < now)
        out.append(CourierRoute(
            shipment_id=r.shipment_id,
            order_id=r.order_id,
            tracking_number=r.tracking_number,
            carrier=r.carrier,
            recipient_name=r.recipient_name,
            district=_district_from_address(r.recipient_address),
            is_delayed=is_delayed,
        ))
    return out


def _operations_items(db: Session) -> list[OperationsItem]:
    alerts = db.execute(text("""
        SELECT type, severity, title, description, created_at
        FROM operational_alerts
        WHERE is_resolved = 0
        ORDER BY
          CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
          created_at DESC
        LIMIT 6
    """)).fetchall()

    insights = db.execute(text("""
        SELECT severity, content, created_at, agent_name
        FROM ai_insights
        WHERE is_dismissed = 0
          AND severity IN ('critical', 'warning')
          AND created_at >= :cutoff
        ORDER BY created_at DESC
        LIMIT 3
    """), {"cutoff": datetime.utcnow() - timedelta(hours=24)}).fetchall()

    out: list[OperationsItem] = []
    for a in alerts:
        out.append(OperationsItem(
            type="alert",
            severity=a.severity,
            title=a.title,
            detail=(a.description or "")[:160],
            created_at=_fmt_dt(a.created_at),
        ))
    for i in insights:
        out.append(OperationsItem(
            type="insight",
            severity=i.severity,
            title=f"{i.agent_name} ajan içgörüsü",
            detail=(i.content or "")[:160],
            created_at=_fmt_dt(i.created_at),
        ))
    return out[:8]


# ── AI summary helpers (3 ayrı kısa çağrı, fallback'li) ──────────────────────

def _summary_warehouse(items: list[WarehouseItem]) -> str:
    if not items:
        return "Bugün hazırlanması gereken yeni paket yok. Depo sakin gün geçirebilir."
    sample = ", ".join(f"#{i.order_id} {i.customer_name}" for i in items[:3])
    fallback = (
        f"Bugün depoda {len(items)} paket hazırlanacak. "
        f"İlk öncelikler: {sample}. Müşteri tipine göre paketleme önceliği belirleyin."
    )
    body = "\n".join(
        f"- Sipariş #{i.order_id} ({i.customer_name}): {i.line_count} kalem, {i.address or '—'}"
        for i in items[:8]
    )
    prompt = (
        f"Sen bir kooperatifin depo sorumlusunun sabah brifingini yazıyorsun. "
        f"Aşağıdaki bekleyen siparişlere bakarak 2 cümlelik Türkçe özet üret: "
        f"toplam paket sayısı, hangi siparişlere öncelik verilmeli, dikkat edilecek noktalar. "
        f"Sadece 2 cümle yaz, madde işareti yok.\n\nBekleyen siparişler:\n{body}"
    )
    return _gemini_text(prompt, max_tokens=200) or fallback


def _summary_courier(routes: list[CourierRoute]) -> str:
    if not routes:
        return "Bugün dağıtım için bekleyen kargo yok. Tüm siparişler güncel."
    delayed = sum(1 for r in routes if r.is_delayed)
    districts = sorted({r.district for r in routes if r.district})[:5]
    fallback = (
        f"Bugün {len(routes)} kargo yola çıkacak"
        + (f", {delayed} tanesi gecikmeli durumda" if delayed else "")
        + ". "
        + (f"Dağıtım bölgeleri: {', '.join(districts)}." if districts else "")
    )
    body = "\n".join(
        f"- {r.carrier} {r.tracking_number}: {r.recipient_name or '—'}"
        f" ({r.district or 'bölge belirsiz'}){' [GECİKMELİ]' if r.is_delayed else ''}"
        for r in routes[:8]
    )
    prompt = (
        f"Sen bir kooperatifin kargo görevlisinin sabah brifingini yazıyorsun. "
        f"Aşağıdaki kargolara bakarak 2 cümlelik Türkçe özet üret: "
        f"toplam kargo sayısı, gecikenler varsa vurgu, dağıtım bölgesi yoğunluğu. "
        f"Sadece 2 cümle yaz, madde işareti yok.\n\nBugünkü kargolar:\n{body}"
    )
    return _gemini_text(prompt, max_tokens=200) or fallback


def _summary_operations(items: list[OperationsItem]) -> str:
    if not items:
        return "Açık operasyonel uyarı yok. Operasyon birimi proaktif takipte kalabilir."
    crit = sum(1 for i in items if i.severity == "critical")
    fallback = (
        f"{len(items)} açık konu var"
        + (f", {crit} tanesi kritik öncelikli" if crit else "")
        + ". Operasyon birimi öncelik sırasıyla bunları kapatmalı."
    )
    body = "\n".join(
        f"- [{i.severity.upper()}] {i.title}: {i.detail}"
        for i in items[:6]
    )
    prompt = (
        f"Sen bir kooperatifin operasyon yöneticisinin sabah brifingini yazıyorsun. "
        f"Aşağıdaki açık konulara bakarak 2 cümlelik Türkçe özet üret: "
        f"kritik aksiyonlar, hangi başlığa odaklanılmalı. "
        f"Sadece 2 cümle yaz, madde işareti yok.\n\nAçık konular:\n{body}"
    )
    return _gemini_text(prompt, max_tokens=200) or fallback


def _headline(wh: list, co: list, op: list) -> str:
    bits = []
    if wh:
        bits.append(f"{len(wh)} paket hazırlanacak")
    if co:
        bits.append(f"{len(co)} kargo yola çıkacak")
    if op:
        bits.append(f"{len(op)} açık konu var")
    if not bits:
        return "Bugün için planlanmış aksiyon yok."
    return " · ".join(bits) + "."


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("", response_model=DailyBriefingResponse)
def get_daily_briefing(
    refresh: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cache_key = datetime.utcnow().strftime("%Y-%m-%d-%H%M")[:13]  # 30 dk hassasiyet
    cache_key = cache_key[:11] + ("00" if int(cache_key[11:]) < 30 else "30")
    if not refresh and _CACHE["key"] == cache_key and _CACHE["data"]:
        return _CACHE["data"]

    warehouse = _warehouse_items(db)
    courier = _courier_routes(db)
    operations = _operations_items(db)

    response = DailyBriefingResponse(
        generated_at=datetime.utcnow().strftime("%d.%m.%Y %H:%M"),
        date_label=datetime.utcnow().strftime("%d %B %Y"),
        headline=_headline(warehouse, courier, operations),
        warehouse=RoleBriefing(
            ai_summary=_summary_warehouse(warehouse),
            item_count=len(warehouse),
            items=[w.model_dump() for w in warehouse],
        ),
        courier=RoleBriefing(
            ai_summary=_summary_courier(courier),
            item_count=len(courier),
            items=[c.model_dump() for c in courier],
        ),
        operations=RoleBriefing(
            ai_summary=_summary_operations(operations),
            item_count=len(operations),
            items=[o.model_dump() for o in operations],
        ),
    )

    _CACHE["key"] = cache_key
    _CACHE["data"] = response
    return response
