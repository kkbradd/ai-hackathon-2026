# İşletme Asistanı — AI-Powered SME Operations Assistant

An AI-powered operational assistant for small and medium-sized enterprises (SMEs), built for the AI Hackathon. The system uses Google Gemini 2.0 Flash with function calling to understand natural language queries and take real actions against live business data.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite + Tailwind)  │
│  Chat UI  │  Orders Table  │  Inventory Grid            │
└─────────────────────┬───────────────────────────────────┘
                      │  REST API
┌─────────────────────▼───────────────────────────────────┐
│                  BACKEND (FastAPI + Python)              │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AI Agent Layer — Gemini 2.0 Flash               │   │
│  │  6 tools: order status, stock check, alerts...   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Data Layer — SQLAlchemy + SQLite                │   │
│  │  customers · products · orders · order_items     │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Features

- **AI Chat Agent** — Natural language queries in Turkish or English, powered by Gemini 2.0 Flash with tool calling
- **Order Tracking** — Real-time order status dashboard with status filtering and color-coded badges
- **Inventory Management** — Product stock visualization with red/green stock bars and low-stock alerts
- **Alert Banner** — Auto-refreshing critical stock alert strip with live polling

## AI Tools

| Tool | Description |
|---|---|
| `get_order_status` | Full order detail by ID |
| `list_pending_orders` | All pending/processing orders |
| `check_stock` | Stock level for a product by name |
| `search_product` | Search products by name or category |
| `get_low_stock_alerts` | All products below reorder threshold |
| `get_order_history` | Customer order history by email |

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy google-genai faker python-dotenv

# Configure API key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here

# Seed the database
python seed.py

# Start the server
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Mock Data

The seed script generates:
- **50 customers** with realistic Turkish names, emails, phone numbers
- **30 products** across 3 categories: Gıda (food), El Sanatları (handcrafts), Tekstil (textile)
- **200 orders** spanning the last 30 days with realistic status distribution
- **~8 products** intentionally below reorder threshold for demo purposes

## Demo Script (3 minutes)

1. Open `http://localhost:5173` → Alert banner shows critical stock items
2. **Chat tab** → Type: `"Bekleyen siparişleri göster"` → Agent calls `list_pending_orders`
3. **Chat tab** → Type: `"42 numaralı siparişin durumu nedir?"` → Agent calls `get_order_status`
4. **Chat tab** → Type: `"Domates stoğu ne kadar?"` → Agent calls `check_stock`
5. **Orders tab** → Filter by `"Bekliyor"` → Color-coded status badges
6. **Inventory tab** → Click "Kritik ürün" button → Red-flagged low-stock cards

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+, FastAPI, Uvicorn |
| AI | Google Gemini 2.0 Flash (`google-genai` SDK) |
| Database | SQLite + SQLAlchemy ORM |
| Mock Data | Faker (tr_TR locale) |
| Frontend | React 18, Vite, Tailwind CSS v4 |

## API Endpoints

```
POST /chat                    — AI agent chat
GET  /orders                  — List orders (filter by status)
GET  /orders/{id}             — Order detail
GET  /inventory               — All products with stock levels
GET  /inventory/alerts        — Products below reorder threshold
GET  /docs                    — Swagger UI
```
