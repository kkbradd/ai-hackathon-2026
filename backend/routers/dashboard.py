from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from auth import verify_token as get_current_user
from database import get_db
from models import (
    Order,
    OrderItem,
    Shipment,
    CustomerMessage,
    Customer,
    Inventory,
    OperationalAlert,
    Product,
    User,
)
from operational_metrics import (
    week_bounds,
    pending_pipeline_count,
    active_shipments_count,
    delayed_shipments_count,
    unread_inbound_messages_count,
    low_stock_products_count,
    on_time_delivery_rate,
    revenue_today,
    revenue_for_week,
    revenue_sum_query,
    orders_count_in_range,
    shipment_distribution_map,
    shipment_delay_ratio_pct,
    inventory_health_score,
)
from schemas import (
    DashboardResponse,
    DashboardAlertSummary,
    ShipmentDistribution,
    TopProduct,
    OperationalAlertOut,
    WeeklyChartData,
    InboundMessageDigest,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}


def _generate_ai_insights(db: Session) -> List[str]:
    """Rule-based operational intelligence — no LLM call, fast."""
    insights: List[str] = []
    now = datetime.utcnow()

    total_active = db.execute(
        text("SELECT COUNT(*) FROM shipments WHERE status NOT IN ('delivered','failed','returned')")
    ).scalar() or 0
    delayed = delayed_shipments_count(db, now)
    if total_active > 0 and delayed / total_active > 0.12:
        pct = round(delayed / total_active * 100)
        insights.append(
            f"Aktif kargoların yaklaşık %{pct}'i teslim tarihini aştı; "
            f"{delayed} sevkiyat zamanında güncellenmeli."
        )

    low_stock_rows = db.execute(
        text("""
            SELECT p.name
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            WHERE i.quantity_kg < i.min_threshold
            ORDER BY (i.quantity_kg / i.min_threshold) ASC
        """)
    ).fetchall()
    if low_stock_rows:
        names = ", ".join(r.name for r in low_stock_rows[:3])
        extra = f" ve {len(low_stock_rows) - 3} ürün daha" if len(low_stock_rows) > 3 else ""
        insights.append(
            f"Stok uyarısı: {names}{extra} minimum eşiğin altında. "
            "Tedarik veya yeniden sipariş önceliği önerilir."
        )

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    orders_today = orders_count_in_range(db, today_start, now)
    orders_yesterday = orders_count_in_range(db, yesterday_start, today_start)
    if orders_yesterday > 0 and abs((orders_today - orders_yesterday) / orders_yesterday) >= 0.10:
        delta_pct = round((orders_today - orders_yesterday) / orders_yesterday * 100)
        if delta_pct > 0:
            insights.append(
                f"Bugün alınan sipariş sayısı düne göre %{delta_pct} arttı "
                f"({orders_today} işlem)."
            )
        else:
            insights.append(
                f"Bugün alınan sipariş sayısı düne göre %{abs(delta_pct)} azaldı "
                f"({orders_today} işlem)."
            )
    elif orders_yesterday == 0 and orders_today >= 3:
        insights.append(
            "Dün iptal işlem yapılmış veya düşük hacim vardı; "
            f"bugün {orders_today} sipariş alınarak aktivite yükseldi."
        )

    carrier_delay = db.execute(
        text("""
            SELECT carrier, COUNT(*) AS cnt
            FROM shipments
            WHERE estimated_delivery IS NOT NULL
              AND estimated_delivery < :now
              AND status NOT IN ('delivered','failed','returned')
            GROUP BY carrier
            ORDER BY cnt DESC
            LIMIT 1
        """),
        {"now": now},
    ).fetchone()
    if carrier_delay and carrier_delay.cnt >= 2:
        insights.append(
            f"{carrier_delay.carrier} hattında {carrier_delay.cnt} gecikmiş sevkiyat var. "
            "Müşteri iletişiminde taşıyıcı durumu öne çıkarılabilir."
        )

    cutoff_7d = now - timedelta(days=7)
    top = db.execute(
        text("""
            SELECT p.name, SUM(oi.quantity) AS total_qty
            FROM products p
            JOIN order_items oi ON oi.product_id = p.id
            JOIN orders      o  ON o.id = oi.order_id
            WHERE o.created_at >= :cutoff
            GROUP BY p.name
            ORDER BY total_qty DESC
            LIMIT 1
        """),
        {"cutoff": cutoff_7d},
    ).fetchone()
    if top:
        insights.append(
            f"Son 7 günde öne çıkan ürün {top.name} "
            f"({int(top.total_qty)} birim sipariş). Stok görünümü yakından izlenmeli."
        )

    week_start_roll = now - timedelta(days=7)
    orders_weekly = orders_count_in_range(db, week_start_roll, now)
    revenue_7d_scalar = db.execute(
        text("""
            SELECT SUM(oi.unit_price * oi.quantity)
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.created_at >= :cutoff
        """),
        {"cutoff": cutoff_7d},
    ).scalar()
    revenue_7d = round(float(revenue_7d_scalar or 0.0), 2)
    if orders_weekly > 0:
        insights.insert(
            0,
            f"Son 7 günde {orders_weekly} sipariş ve ₺{revenue_7d:,.0f} civarında ciro oluştu.",
        )

    complaint_count = db.execute(
        text("""
            SELECT COUNT(*) FROM operational_alerts
            WHERE type = 'complaint' AND is_resolved = 0
        """)
    ).scalar() or 0
    if complaint_count >= 2:
        insights.append(
            f"{complaint_count} açık müşteri şikayeti çözüm bekliyor; "
            "memnuniyet ve tekrar sipariş riski artabilir."
        )

    urgent_inbox = db.execute(
        text("""
            SELECT COUNT(*) FROM customer_messages
            WHERE direction = 'inbound' AND is_read = 0 AND urgency = 'yüksek'
        """)
    ).scalar() or 0
    if urgent_inbox >= 2:
        insights.append(
            f"Gelen kutuda {urgent_inbox} yüksek öncelikli müşteri bildirimi okunmayı bekliyor; "
            "operasyon ve lojistik ekipleriyle hızlı senkron önerilir."
        )

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    cat_rows = db.execute(
        text("""
            SELECT category, COUNT(*) AS cnt
            FROM customer_messages
            WHERE direction = 'inbound'
              AND created_at >= :today
              AND category IS NOT NULL
            GROUP BY category
            ORDER BY cnt DESC
        """),
        {"today": today_start},
    ).fetchall()
    cat_map = {r.category: r.cnt for r in cat_rows}
    delay_today = cat_map.get("teslimat_gecikmesi", 0)
    if delay_today > 2:
        insights.append(
            f"Bugün {delay_today} müşteri teslimat gecikmesi kategorisinde mesaj gönderdi; "
            "kargo operasyonunda sistematik bir sorun olabilir."
        )

    two_hours_ago = now - timedelta(hours=2)
    recent_urgent = db.execute(
        text("""
            SELECT COUNT(*) FROM customer_messages
            WHERE direction = 'inbound' AND is_read = 0
              AND urgency = 'yüksek' AND created_at >= :cutoff
        """),
        {"cutoff": two_hours_ago},
    ).scalar() or 0
    if recent_urgent >= 1:
        insights.append(
            f"Son 2 saatte {recent_urgent} yüksek öncelikli okunmamış müşteri mesajı geldi; "
            "acil müdahale önerilir."
        )

    return insights[:5]


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    weeks_ago: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    target_week_start, target_week_end = week_bounds(now, weeks_ago)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    pending_orders = pending_pipeline_count(db)
    active_shipments = active_shipments_count(db)
    delayed_shipments = delayed_shipments_count(db, now)
    unread_messages = unread_inbound_messages_count(db)
    low_stock_products = low_stock_products_count(db)
    on_time = on_time_delivery_rate(db)
    delay_ratio = shipment_delay_ratio_pct(db, now)
    inv_health = inventory_health_score(db)

    orders_today = orders_count_in_range(db, today_start, now)
    rev_today = revenue_today(db, today_start)
    rev_total = round(float(revenue_sum_query(db) or 0.0), 2)

    orders_weekly = orders_count_in_range(db, target_week_start, target_week_end)
    rev_week = revenue_for_week(db, target_week_start, target_week_end)

    dm = shipment_distribution_map(db, now)
    shipment_distribution = ShipmentDistribution(
        preparing=dm.get("preparing", 0),
        in_transit=dm.get("in_transit", 0),
        at_facility=dm.get("at_facility", 0),
        out_for_delivery=dm.get("out_for_delivery", 0),
        delivered=dm.get("delivered", 0),
        delayed=delayed_shipments,
    )

    raw_alerts = (
        db.query(OperationalAlert)
        .filter(OperationalAlert.is_resolved == False)
        .order_by(OperationalAlert.created_at.desc())
        .limit(20)
        .all()
    )
    type_groups: dict[str, list] = {}
    for a in raw_alerts:
        type_groups.setdefault(a.type, []).append(a)

    TYPE_MESSAGES = {
        "delayed_shipment":  lambda n: f"{n} kargo tahmini teslimat tarihini aştı.",
        "low_stock":         lambda n: f"{n} ürün minimum stok eşiğinin altında.",
        "carrier_issue":     lambda n: f"{n} taşıyıcı operasyonunda sorun bildirimi.",
        "complaint":         lambda n: f"{n} müşteri şikayeti çözüm bekliyor.",
        "anomaly":           lambda n: f"{n} operasyonel anomali tespit edildi.",
        "pending_orders":    lambda n: f"{n} açık sipariş birikimi bildirimi.",
        "complaint_cluster": lambda n: f"{n} teslimat şikayet kümesi tespit edildi.",
        "overdue_order":     lambda n: f"{n} sipariş 5+ gündür teslim edilmedi.",
        "restock_suggestion":lambda n: f"{n} ürün için yeniden sipariş önerisi.",
    }
    alerts: List[DashboardAlertSummary] = []
    for type_, group in type_groups.items():
        worst_severity = min(group, key=lambda a: SEVERITY_RANK.get(a.severity, 9)).severity
        msg_fn = TYPE_MESSAGES.get(type_, lambda n: f"{n} aktif uyarı.")
        alerts.append(DashboardAlertSummary(
            type=type_,
            severity=worst_severity,
            message=msg_fn(len(group)),
            count=len(group),
        ))
    alerts.sort(key=lambda a: SEVERITY_RANK.get(a.severity, 9))

    ai_insights = _generate_ai_insights(db)

    top_rows = db.execute(
        text("""
            SELECT
                oi.product_id,
                p.name,
                p.category,
                COUNT(DISTINCT oi.order_id)            AS order_count,
                SUM(oi.quantity)                       AS total_qty,
                SUM(oi.unit_price * oi.quantity)       AS revenue
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            GROUP BY oi.product_id, p.name, p.category
            ORDER BY order_count DESC
            LIMIT 5
        """)
    ).fetchall()
    top_products = [
        TopProduct(
            product_id=r.product_id,
            name=r.name,
            category=r.category,
            order_count=r.order_count,
            total_quantity=float(r.total_qty or 0),
            revenue=round(float(r.revenue or 0), 2),
        )
        for r in top_rows
    ]

    recent_raw = (
        db.query(OperationalAlert)
        .order_by(OperationalAlert.created_at.desc())
        .limit(5)
        .all()
    )
    recent_alerts = [
        OperationalAlertOut(
            id=a.id,
            type=a.type,
            severity=a.severity,
            title=a.title,
            description=a.description,
            is_resolved=a.is_resolved,
            created_at=a.created_at.strftime("%d.%m.%Y %H:%M"),
            related_entity_id=a.related_entity_id,
        )
        for a in recent_raw
    ]

    days_tr = ["PZT", "SAL", "ÇAR", "PER", "CUM", "CMT", "PAZ"]
    chart_rows = db.execute(
        text("""
            SELECT
                DATE(o.created_at)                     AS day,
                COUNT(DISTINCT o.id)                   AS order_count,
                SUM(oi.unit_price * oi.quantity)       AS revenue
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.created_at >= :week_start AND o.created_at < :week_end
            GROUP BY DATE(o.created_at)
            ORDER BY day
        """),
        {"week_start": target_week_start, "week_end": target_week_end},
    ).fetchall()

    # Index fetched rows by date string for O(1) lookup
    chart_by_date = {str(r.day): r for r in chart_rows}
    chart_data = []
    for d in range(7):
        day_start = target_week_start + timedelta(days=d)
        day_key = day_start.strftime("%Y-%m-%d")
        row = chart_by_date.get(day_key)
        chart_data.append(WeeklyChartData(
            date=days_tr[day_start.weekday()],
            orders=int(row.order_count) if row else 0,
            revenue=round(float(row.revenue or 0.0), 2) if row else 0.0,
        ))

    inbound_messages_today_count = db.execute(
        text("""
            SELECT COUNT(*) FROM customer_messages
            WHERE direction = 'inbound' AND created_at >= :today
        """),
        {"today": today_start},
    ).scalar() or 0

    msg_today_slice = db.execute(
        text("""
            SELECT cm.id, cm.subject, c.name AS customer_name,
                   cm.related_order_id, cm.category,
                   cm.created_at
            FROM customer_messages cm
            JOIN customers c ON c.id = cm.customer_id
            WHERE cm.direction = 'inbound' AND cm.created_at >= :today
            ORDER BY cm.created_at DESC
            LIMIT 10
        """),
        {"today": today_start},
    ).fetchall()
    inbound_messages_today = [
        InboundMessageDigest(
            id=m.id,
            subject=m.subject,
            customer_name=m.customer_name,
            related_order_id=m.related_order_id,
            category=m.category,
            created_at=datetime.strptime(str(m.created_at)[:16], "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M"),
        )
        for m in msg_today_slice
    ]

    return DashboardResponse(
        pending_orders=orders_today,
        active_shipments=active_shipments,
        delayed_shipments=delayed_shipments,
        unread_messages=unread_messages,
        low_stock_products=low_stock_products,
        on_time_delivery_rate=on_time,
        average_delivery_performance=on_time,
        orders_today=orders_today,
        revenue_today=rev_today,
        revenue_total=rev_total,
        orders_weekly=orders_weekly,
        revenue_weekly=rev_week,
        shipment_delay_ratio=delay_ratio,
        inventory_health_score=inv_health,
        weekly_chart_data=chart_data,
        shipment_distribution=shipment_distribution,
        alerts=alerts,
        ai_insights=ai_insights,
        top_products=top_products,
        recent_alerts=recent_alerts,
        inbound_messages_today_count=inbound_messages_today_count,
        inbound_messages_today=inbound_messages_today,
    )
