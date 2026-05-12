from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class ShipmentStatus(str, enum.Enum):
    preparing = "preparing"
    in_transit = "in_transit"
    at_facility = "at_facility"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    failed = "failed"
    returned = "returned"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="operator")
    created_at = Column(DateTime, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String)
    customer_type = Column(String, default="kurumsal")

    orders = relationship("Order", back_populates="customer")
    messages = relationship("CustomerMessage", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String, default="adet")
    package_size = Column(String, nullable=True)

    order_items = relationship("OrderItem", back_populates="product")
    inventory = relationship("Inventory", back_populates="product", uselist=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String, nullable=False, default=OrderStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shipping_address = Column(String)
    tracking_number = Column(String, nullable=True)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    shipment = relationship("Shipment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    tracking_number = Column(String, nullable=False, index=True)
    carrier = Column(String, nullable=False)
    status = Column(String, nullable=False, default=ShipmentStatus.preparing)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    estimated_delivery = Column(DateTime, nullable=True)
    recipient_name = Column(String)
    recipient_address = Column(String)

    order = relationship("Order", back_populates="shipment")
    updates = relationship("ShipmentUpdate", back_populates="shipment", order_by="ShipmentUpdate.timestamp")


class ShipmentUpdate(Base):
    __tablename__ = "shipment_updates"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    status = Column(String, nullable=False)
    location = Column(String)
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    shipment = relationship("Shipment", back_populates="updates")


class CustomerMessage(Base):
    __tablename__ = "customer_messages"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    direction = Column(String, nullable=False, default="inbound")
    subject = Column(String)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    ai_generated = Column(Boolean, default=False)
    category = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    ai_summary = Column(Text, nullable=True)
    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    related_shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)

    customer = relationship("Customer", back_populates="messages")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    quantity_kg = Column(Float, nullable=False, default=0.0)
    min_threshold = Column(Float, nullable=False, default=50.0)
    reorder_point = Column(Float, nullable=False, default=100.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="inventory")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    quantity_change = Column(Float, nullable=False)
    movement_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    order = relationship("Order")


class OperationalAlert(Base):
    __tablename__ = "operational_alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    related_entity_id = Column(Integer, nullable=True)


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    insight_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    related_entity_type = Column(String, nullable=True)
    related_entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_dismissed = Column(Boolean, default=False)
