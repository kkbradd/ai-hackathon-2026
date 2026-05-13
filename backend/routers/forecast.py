"""Talep tahmini — son 90 günlük satışlardan moving average ile 7 günlük öngörü.

Gereksinim alan 6 (analitik & içgörü) örnek senaryosu karşılığı:
'Sistem geçmiş satış verisini analiz ederek önümüzdeki hafta en çok satılması
beklenen 5 ürünü tahmin ediyor ve stok yöneticisini önceden uyarıyor.'

Tahmin yöntemi: son 14 günün günlük ortalaması × 7 (basit moving average).
LLM ile 2-3 paragraf Türkçe analiz üretilir; key yoksa şablon fallback.
30 dakikalık in-memory cache.
"""
from datetime import datetime, timedelta
from typing import Optional
import random

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import verify_token as get_current_user
from database import get_db
from email_drafter import _gemini_text
from models import User

router = APIRouter(prefix="/forecast", tags=["forecast"])

_CACHE: dict = {"key": None, "data": None}


# ── Schemas ───────────────────────────────────────────────────────────────────

class ForecastChartPoint(BaseModel):
    date: str          # ISO YYYY-MM-DD
    revenue: float
    is_forecast: bool


class ForecastTopProduct(BaseModel):
    product_id: int
    name: str
    category: Optional[str]
    unit: Optional[str]
    sales_30d: float
    forecast_7d: float
    current_stock: float
    stock_status: str  # 'yeterli' | 'uyari' | 'kritik'


class ForecastResponse(BaseModel):
    generated_at: str
    period_label: str
    kpi_revenue_7d: float
    kpi_orders_7d: int
    kpi_at_risk_count: int
    chart_points: list[ForecastChartPoint]
    top_products: list[ForecastTopProduct]
    ai_summary: str


# ── Data collectors ──────────────────────────────────────────────────────────

def _daily_sales_90d(db: Session) -> list[tuple[str, float, int]]:
    cutoff = datetime.utcnow() - timedelta(days=90)
    rows = db.execute(text("""
        SELECT DATE(o.created_at) AS d,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue,
               COUNT(DISTINCT o.id) AS order_count
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        WHERE o.created_at >= :cutoff
        GROUP BY DATE(o.created_at)
        ORDER BY d ASC
    """), {"cutoff": cutoff}).fetchall()
    return [(str(r.d), float(r.revenue or 0), int(r.order_count or 0)) for r in rows]


def _top_products_30d(db: Session) -> list[tuple]:
    cutoff = datetime.utcnow() - timedelta(days=30)
    rows = db.execute(text("""
        SELECT p.id AS product_id,
               p.name AS name,
               p.category AS category,
               p.unit AS unit,
               COALESCE(SUM(oi.quantity), 0) AS qty_30d,
               COALESCE(i.quantity_kg, 0) AS stock
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN products p ON p.id = oi.product_id
        LEFT JOIN inventory i ON i.product_id = p.id
        WHERE o.created_at >= :cutoff
        GROUP BY p.id, p.name, p.category, p.unit, i.quantity_kg
        ORDER BY qty_30d DESC
        LIMIT 5
    """), {"cutoff": cutoff}).fetchall()
    return [(r.product_id, r.name, r.category, r.unit, float(r.qty_30d), float(r.stock)) for r in rows]


def _all_products_at_risk(db: Session) -> int:
    """Tahmini 7 günlük talep mevcut stoğun üzerinde olan ürün sayısı."""
    cutoff = datetime.utcnow() - timedelta(days=14)
    rows = db.execute(text("""
        SELECT p.id,
               COALESCE(SUM(oi.quantity), 0) AS qty_14d,
               COALESCE(i.quantity_kg, 0) AS stock
        FROM products p
        LEFT JOIN order_items oi ON oi.product_id = p.id
        LEFT JOIN orders o ON o.id = oi.order_id AND o.created_at >= :cutoff
        LEFT JOIN inventory i ON i.product_id = p.id
        GROUP BY p.id, i.quantity_kg
    """), {"cutoff": cutoff}).fetchall()
    at_risk = 0
    for r in rows:
        forecast_7d = float(r.qty_14d or 0) / 14.0 * 7.0
        if forecast_7d > float(r.stock or 0):
            at_risk += 1
    return at_risk


# ── Forecast logic ───────────────────────────────────────────────────────────

def _stock_status(forecast_7d: float, stock: float) -> str:
    if stock >= forecast_7d:
        return "yeterli"
    if stock >= forecast_7d * 0.5:
        return "uyari"
    return "kritik"


def _build_chart_points(daily: list[tuple[str, float, int]]) -> tuple[list[ForecastChartPoint], float, int]:
    """Son 30 günü gerçek + sonraki 7 günü tahmin olarak dönder. KPI'ları da hesapla."""
    today = datetime.utcnow().date()
    last_30_start = today - timedelta(days=30)

    by_date = {d: (rev, oc) for d, rev, oc in daily}

    chart: list[ForecastChartPoint] = []
    revenue_14d_window: list[float] = []
    orders_14d_window: list[int] = []

    # Gerçek son 30 gün (eksik günleri 0 ile doldur)
    for i in range(30):
        d = last_30_start + timedelta(days=i + 1)
        d_str = d.isoformat()
        rev, oc = by_date.get(d_str, (0.0, 0))
        chart.append(ForecastChartPoint(date=d_str, revenue=round(rev, 2), is_forecast=False))
        if i >= 30 - 14:
            revenue_14d_window.append(rev)
            orders_14d_window.append(oc)

    avg_rev_14 = sum(revenue_14d_window) / max(len(revenue_14d_window), 1)
    avg_orders_14 = sum(orders_14d_window) / max(len(orders_14d_window), 1)

    # Tahmin: sonraki 7 gün, ±%7 jitter
    rng = random.Random(today.toordinal())
    kpi_revenue_7d = 0.0
    kpi_orders_7d = 0
    for i in range(7):
        d = today + timedelta(days=i + 1)
        jitter = 1.0 + (rng.random() - 0.5) * 0.14  # ±7%
        rev_pred = max(avg_rev_14 * jitter, 0)
        kpi_revenue_7d += rev_pred
        kpi_orders_7d += int(round(avg_orders_14 * jitter))
        chart.append(ForecastChartPoint(date=d.isoformat(), revenue=round(rev_pred, 2), is_forecast=True))

    return chart, round(kpi_revenue_7d, 2), kpi_orders_7d


def _build_top_products(rows: list[tuple]) -> list[ForecastTopProduct]:
    out: list[ForecastTopProduct] = []
    for product_id, name, category, unit, qty_30d, stock in rows:
        forecast_7d = round(qty_30d / 30.0 * 7.0, 1)
        out.append(ForecastTopProduct(
            product_id=product_id,
            name=name,
            category=category,
            unit=unit,
            sales_30d=round(qty_30d, 1),
            forecast_7d=forecast_7d,
            current_stock=round(stock, 1),
            stock_status=_stock_status(forecast_7d, stock),
        ))
    return out


# ── AI summary ───────────────────────────────────────────────────────────────

def _ai_summary(
    kpi_revenue: float,
    kpi_orders: int,
    at_risk: int,
    top: list[ForecastTopProduct],
) -> str:
    if not top:
        return (
            "Son 30 günde anlamlı satış verisi oluşmadığı için sağlıklı bir tahmin "
            "üretilemedi. Operasyonun aktifleşmesini bekleyerek tekrar deneyin."
        )

    top_lines = "\n".join(
        f"- {p.name}: son 30 günde {p.sales_30d:g} {p.unit or 'adet'}, "
        f"7 günlük tahmin {p.forecast_7d:g} {p.unit or 'adet'}, "
        f"mevcut stok {p.current_stock:g} ({p.stock_status.upper()})"
        for p in top
    )

    fallback_lines = []
    fallback_lines.append(
        f"Önümüzdeki 7 gün için tahmini ciro ₺{kpi_revenue:,.0f} ve yaklaşık "
        f"{kpi_orders} sipariş bekleniyor."
    )
    risk_products = [p for p in top if p.stock_status in ("uyari", "kritik")]
    if risk_products:
        risk_names = ", ".join(p.name for p in risk_products[:3])
        fallback_lines.append(
            f"Stok yenileme öncelikli ürünler: {risk_names}. "
            f"Toplam {at_risk} üründe tahmini talep mevcut stoğu aşıyor."
        )
    else:
        fallback_lines.append(
            "Top 5 üründe stok seviyeleri 7 günlük talebi karşılıyor görünüyor; "
            f"yine de genelde {at_risk} ürün risk altında."
        )
    fallback_lines.append(
        f"En çok satması beklenen ürün {top[0].name} — bu üründe arz sürekliliğini koruyun."
    )
    fallback = " ".join(fallback_lines)

    prompt = (
        "Sen bir tarım kooperatifinin operasyon analistisin. Aşağıdaki 7 günlük "
        "talep tahminine bakarak 2-3 paragraf, akıcı bir Türkçe analiz yaz. "
        "Vurgu noktaları: (1) genel gidişat ve ciro beklentisi, (2) stok yenileme "
        "gereken ürünler ve aciliyet, (3) öne çıkan trend ürün. Madde işareti veya "
        "başlık kullanma; düz paragraflar yaz. Rakamları kısa tut.\n\n"
        f"7 günlük tahmin: ciro ₺{kpi_revenue:,.0f}, sipariş ~{kpi_orders}, "
        f"risk altında {at_risk} ürün.\n\n"
        f"En çok satması beklenen 5 ürün:\n{top_lines}"
    )
    return _gemini_text(prompt, max_tokens=520) or fallback


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("", response_model=ForecastResponse)
def get_forecast(
    refresh: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cache_key = datetime.utcnow().strftime("%Y-%m-%d-%H%M")[:13]
    cache_key = cache_key[:11] + ("00" if int(cache_key[11:]) < 30 else "30")
    if not refresh and _CACHE["key"] == cache_key and _CACHE["data"]:
        return _CACHE["data"]

    daily = _daily_sales_90d(db)
    top_rows = _top_products_30d(db)
    at_risk = _all_products_at_risk(db)

    chart_points, kpi_revenue_7d, kpi_orders_7d = _build_chart_points(daily)
    top_products = _build_top_products(top_rows)
    summary = _ai_summary(kpi_revenue_7d, kpi_orders_7d, at_risk, top_products)

    today = datetime.utcnow()
    response = ForecastResponse(
        generated_at=today.strftime("%d.%m.%Y %H:%M"),
        period_label=f"{today.strftime('%d %b')} → {(today + timedelta(days=7)).strftime('%d %b %Y')}",
        kpi_revenue_7d=kpi_revenue_7d,
        kpi_orders_7d=kpi_orders_7d,
        kpi_at_risk_count=at_risk,
        chart_points=chart_points,
        top_products=top_products,
        ai_summary=summary,
    )

    _CACHE["key"] = cache_key
    _CACHE["data"] = response
    return response
