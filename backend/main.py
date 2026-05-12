import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base
from models import (  # noqa: F401
    User, Customer, Product, Order, OrderItem,
    Shipment, ShipmentUpdate, CustomerMessage,
    Inventory, InventoryMovement, OperationalAlert,
    AIInsight,
)
from agents.orchestrator import AgentOrchestrator
from routers import auth, chat, orders, shipments, dashboard
from routers import inventory, operational_alerts, analytics, simulate, messages, customers
from routers import insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    yield
    await orchestrator.stop()


app = FastAPI(
    title="Kooperatif Operasyon Merkezi API",
    description="AI-powered operational intelligence platform for food and agriculture cooperatives",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(orders.router)
app.include_router(shipments.router)
app.include_router(dashboard.router)
app.include_router(inventory.router)
app.include_router(operational_alerts.router)
app.include_router(analytics.router)
app.include_router(simulate.router)
app.include_router(messages.router)
app.include_router(customers.router)
app.include_router(insights.router)


@app.get("/")
def root():
    return {
        "name": "Kooperatif Operasyon Merkezi",
        "version": "4.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
