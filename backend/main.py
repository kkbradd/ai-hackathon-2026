import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base
# Import all models so Base.metadata registers them before create_all
from models import (  # noqa: F401
    User, Customer, Product, Order, OrderItem,
    Shipment, ShipmentUpdate, CustomerMessage,
    Inventory, InventoryMovement, OperationalAlert,
)
import simulation
from routers import auth, chat, orders, shipments, dashboard
from routers import inventory, operational_alerts, analytics, simulate, messages, customers


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    sim_task = asyncio.create_task(simulation.run_loop())
    hourly_task = asyncio.create_task(simulation.run_hourly_loop())
    yield
    sim_task.cancel()
    hourly_task.cancel()
    for t in (sim_task, hourly_task):
        try:
            await t
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Kooperatif Operasyon Merkezi API",
    description="AI-powered operational control center for food and agriculture cooperatives",
    version="3.0.0",
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


@app.get("/")
def root():
    return {
        "name": "Kooperatif Operasyon Merkezi",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
