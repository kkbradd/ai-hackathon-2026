from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    tool_data: Optional[dict] = None


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderItemOut(BaseModel):
    product: str
    quantity: int
    unit: str
    unit_price: float
    subtotal: float
    model_config = {"from_attributes": True}


class OrderSummaryItem(BaseModel):
    product: str
    quantity: float
    unit: str
    unit_price: float
    subtotal: float
    model_config = {"from_attributes": True}


class OrderSummary(BaseModel):
    order_id: int
    customer: str
    customer_type: str
    status: str
    item_count: int
    total: float
    created_at: str
    items: List[OrderSummaryItem] = []
    model_config = {"from_attributes": True}


class OrderDetail(BaseModel):
    order_id: int
    customer: str
    customer_type: str
    status: str
    created_at: str
    shipping_address: Optional[str]
    tracking_number: Optional[str]
    items: List[OrderItemOut]
    total: float
    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """count = rows returned; total_matching_filter = SQL rows for current status filter."""

    count: int
    total_matching_filter: int
    counts_by_status: Dict[str, int]
    pending_pipeline: int
    orders: List[OrderSummary]


# ── Shipments ─────────────────────────────────────────────────────────────────

class ShipmentUpdateOut(BaseModel):
    status: str
    location: Optional[str]
    description: Optional[str]
    timestamp: str
    model_config = {"from_attributes": True}


class ShipmentSummary(BaseModel):
    id: int
    order_id: int
    tracking_number: str
    carrier: str
    status: str
    estimated_delivery: Optional[str]
    recipient_name: Optional[str]
    created_at: str
    is_delayed: bool
    model_config = {"from_attributes": True}


class ShipmentDetail(BaseModel):
    id: int
    order_id: int
    tracking_number: str
    carrier: str
    status: str
    estimated_delivery: Optional[str]
    recipient_name: Optional[str]
    recipient_address: Optional[str]
    created_at: str
    is_delayed: bool
    updates: List[ShipmentUpdateOut]
    model_config = {"from_attributes": True}


class ShipmentListResponse(BaseModel):
    count: int
    shipments: List[ShipmentSummary]


class ShipmentAlertOut(BaseModel):
    id: int
    order_id: int
    tracking_number: str
    carrier: str
    recipient_name: Optional[str]
    estimated_delivery: Optional[str]
    days_overdue: int
    model_config = {"from_attributes": True}


class ShipmentAlertListResponse(BaseModel):
    count: int
    alerts: List[ShipmentAlertOut]


# ── Inventory ─────────────────────────────────────────────────────────────────

class InventoryItem(BaseModel):
    id: int
    product_id: int
    product_name: str
    category: str
    unit: str
    package_size: Optional[str]
    price: float
    quantity_kg: float
    min_threshold: float
    reorder_point: float
    is_low_stock: bool
    is_critical: bool
    stock_percentage: float
    last_updated: str
    model_config = {"from_attributes": True}


class InventoryListResponse(BaseModel):
    count: int
    low_stock_count: int
    items: List[InventoryItem]


class InventoryMovementOut(BaseModel):
    id: int
    product_name: str
    quantity_change: float
    movement_type: str
    timestamp: str
    order_id: Optional[int]
    model_config = {"from_attributes": True}


# ── Operational Alerts ────────────────────────────────────────────────────────

class OperationalAlertOut(BaseModel):
    id: int
    type: str
    severity: str
    title: str
    description: str
    is_resolved: bool
    created_at: str
    related_entity_id: Optional[int]
    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    count: int
    unresolved_count: int
    alerts: List[OperationalAlertOut]


# ── Analytics ─────────────────────────────────────────────────────────────────

class DemandDataPoint(BaseModel):
    date: str
    quantity: float
    order_count: int


class ProductDemandTrend(BaseModel):
    product_id: int
    name: str
    data_7d: List[DemandDataPoint]
    data_14d: List[DemandDataPoint]
    avg_daily_demand: float
    trend_direction: str


# ── Simulate ──────────────────────────────────────────────────────────────────

class SimulateEventRequest(BaseModel):
    event_type: str
    target_id: Optional[int] = None


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardAlertSummary(BaseModel):
    type: str
    severity: str
    message: str
    count: int


class ShipmentDistribution(BaseModel):
    preparing: int
    in_transit: int
    at_facility: int
    out_for_delivery: int
    delivered: int
    delayed: int


class TopProduct(BaseModel):
    product_id: int
    name: str
    category: str
    order_count: int
    total_quantity: float
    revenue: float


class WeeklyChartData(BaseModel):
    date: str
    orders: int
    revenue: float


class InboundMessageDigest(BaseModel):
    id: int
    subject: Optional[str]
    customer_name: str
    related_order_id: Optional[int]
    category: Optional[str]
    urgency: Optional[str] = None
    ai_summary: Optional[str] = None
    created_at: str


class TodayDelayedShipment(BaseModel):
    tracking_number: str
    carrier: str
    recipient_name: Optional[str]
    estimated_delivery: Optional[str]
    hours_late: int
    last_status: Optional[str]


class TodayStockAlert(BaseModel):
    name: str
    category: str
    quantity_kg: float
    min_threshold: float
    pct: int


class AIInsightOut(BaseModel):
    id: int
    agent_name: str
    insight_type: str
    content: str
    severity: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: str
    is_dismissed: bool
    model_config = {"from_attributes": True}


class InsightListResponse(BaseModel):
    count: int
    items: List[AIInsightOut]


class DashboardResponse(BaseModel):
    pending_orders: int
    active_shipments: int
    delayed_shipments: int
    unread_messages: int
    low_stock_products: int
    on_time_delivery_rate: float
    average_delivery_performance: float
    orders_today: int
    revenue_today: float
    revenue_total: float
    orders_weekly: int
    revenue_weekly: float
    shipment_delay_ratio: float
    inventory_health_score: float
    weekly_chart_data: List[WeeklyChartData]
    shipment_distribution: ShipmentDistribution
    alerts: List[DashboardAlertSummary]
    ai_insights: List[AIInsightOut]
    top_products: List[TopProduct]
    recent_alerts: List[OperationalAlertOut]
    inbound_messages_today_count: int
    inbound_messages_today: List[InboundMessageDigest]
    today_delayed_shipments: List[TodayDelayedShipment]
    today_stock_alerts: List[TodayStockAlert]


# ── Customer Messages ─────────────────────────────────────────────────────────

class CustomerMessageOut(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    direction: str
    subject: Optional[str]
    body: str
    created_at: str
    is_read: bool
    ai_generated: bool
    category: Optional[str] = None
    urgency: Optional[str] = None
    ai_summary: Optional[str] = None
    related_order_id: Optional[int] = None
    related_shipment_id: Optional[int] = None
    is_draft: bool = False
    sent_at: Optional[str] = None
    model_config = {"from_attributes": True}


class MessageStats(BaseModel):
    unread_inbound: int
    inbound_total: int
    outbound_total: int
    conversation_total: int


class MessageListResponse(BaseModel):
    count: int
    stats: MessageStats
    messages: List[CustomerMessageOut]
