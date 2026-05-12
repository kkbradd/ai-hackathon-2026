from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_token as get_current_user
from models import User
from schemas import ProductDemandTrend, DemandDataPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/demand", response_model=List[ProductDemandTrend])
def demand_trends(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cutoff_14d = datetime.utcnow() - timedelta(days=14)

    rows = db.execute(
        text("""
            SELECT
                oi.product_id,
                p.name,
                DATE(o.created_at)       AS order_date,
                SUM(oi.quantity)         AS total_qty,
                COUNT(DISTINCT o.id)     AS order_count
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            JOIN orders   o ON o.id = oi.order_id
            WHERE o.created_at >= :cutoff
            GROUP BY oi.product_id, p.name, DATE(o.created_at)
            ORDER BY oi.product_id, DATE(o.created_at)
        """),
        {"cutoff": cutoff_14d},
    ).fetchall()

    product_map: dict[int, dict] = {}
    for row in rows:
        pid = row.product_id
        if pid not in product_map:
            product_map[pid] = {"name": row.name, "points": []}
        product_map[pid]["points"].append({
            "date": str(row.order_date),
            "quantity": float(row.total_qty or 0),
            "order_count": int(row.order_count or 0),
        })

    cutoff_7d_str = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    trends: List[ProductDemandTrend] = []
    for pid, data in product_map.items():
        points = data["points"]
        data_14d = [DemandDataPoint(**p) for p in points]
        data_7d = [DemandDataPoint(**p) for p in points if p["date"] >= cutoff_7d_str]

        total_14d = sum(p["quantity"] for p in points)
        total_7d = sum(p["quantity"] for p in points if p["date"] >= cutoff_7d_str)
        prev_7d = total_14d - total_7d
        avg_daily = total_14d / 14

        if prev_7d == 0:
            direction = "up" if total_7d > 0 else "stable"
        elif total_7d > prev_7d * 1.1:
            direction = "up"
        elif total_7d < prev_7d * 0.9:
            direction = "down"
        else:
            direction = "stable"

        trends.append(ProductDemandTrend(
            product_id=pid,
            name=data["name"],
            data_7d=data_7d,
            data_14d=data_14d,
            avg_daily_demand=round(avg_daily, 2),
            trend_direction=direction,
        ))

    trends.sort(key=lambda t: t.avg_daily_demand, reverse=True)
    return trends
