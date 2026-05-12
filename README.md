# Kooperatif Hub — AI-Powered Operations Assistant

Tarım ve gıda kooperatifleri için geliştirilmiş yapay zeka destekli operasyon yönetim platformu. Groq LLM (Llama 3.3 70B) ile doğal dil sorgulama, gerçek zamanlı sipariş/kargo/stok takibi ve otomatik operasyonel tarama.

---

## Mimari

```
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND  (React 19 + Vite + Tailwind CSS v4)  │
│  Dashboard · Siparişler · Kargolar · Envanter · Mesajlar    │
│  AI Chat Panel (streaming tool call görselleştirmesi)       │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST API (JWT)
┌──────────────────────────▼──────────────────────────────────┐
│                  BACKEND  (FastAPI + Python)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AI Agent — Groq Llama 3.3 70B (tool calling)       │   │
│  │  17 araç: sipariş, kargo, stok, uyarı, SQL...       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Simulation Engine  (asyncio background tasks)      │   │
│  │  45s tick: sipariş üretimi + kargo durum geçişleri  │   │
│  │  3600s scan: gecikme · şikayet · stok · yenileme    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Data Layer — SQLAlchemy + SQLite                   │   │
│  │  orders · shipments · inventory · messages · alerts │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Özellikler

- **AI Chat Agent** — Türkçe doğal dil sorguları, Groq Llama 3.3 70B ile araç çağrısı (tool calling)
- **Canlı Dashboard** — Bugünkü siparişler, aktif teslimatlar, stok uyarıları, zamanında teslimat oranı
- **Otomatik Sipariş Üretimi** — Her 45 saniyede %20 olasılıkla yeni sipariş simülasyonu (gerçek + yeni müşteri)
- **Saatlik Operasyonel Tarama** — Gecikmiş kargolar, müşteri şikayet kümeleri, düşük stok, vadesi geçmiş siparişler, yenileme önerileri
- **Müşteri Mesajları** — Kural tabanlı kategori/öncelik sınıflandırması, yeni mesaj oluşturma
- **Kargo Takibi** — Durum geçişleri (preparing → in_transit → at_facility → out_for_delivery → delivered), timeline görünümü
- **Envanter Yönetimi** — Stok seviyeleri, kritik ürün uyarıları, hareket geçmişi

---

## AI Agent Araçları

| Araç | Açıklama |
|---|---|
| `get_order_status` | Sipariş detayı (müşteri, ürünler, kargo) |
| `list_pending_orders` | Bekleyen/işlemdeki siparişler |
| `get_order_history` | Müşteri sipariş geçmişi (e-posta ile) |
| `get_shipment_status` | Kargo durumu ve gecikme bilgisi |
| `get_shipment_timeline` | Kargo hareket zaman çizelgesi |
| `get_delayed_shipments` | Tüm gecikmiş kargolar |
| `get_inventory_status` | Stok seviyeleri, kritik ürünler |
| `get_recent_messages` | Son müşteri mesajları |
| `get_operational_alerts` | Operasyonel uyarılar (önem/çözüm filtreli) |
| `get_demand_trends` | Ürün talep trendleri (N günlük) |
| `get_daily_summary_rich` | Kapsamlı günlük operasyon raporu |
| `summarize_daily_operations` | Hızlı günlük özet |
| `update_shipment_status` | Kargo durumu güncelle + hareket kaydı ekle |
| `update_order_status` | Sipariş durumu güncelle |
| `resolve_operational_alert` | Uyarıyı çözüldü olarak işaretle |
| `draft_supplier_order` | Tedarikçi sipariş taslağı oluştur |
| `execute_sql` | Doğrudan SELECT sorgusu çalıştır (güvenli, sadece okuma) |

---

## Kurulum

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# API anahtarını ayarla
cp .env.example .env
# .env dosyasına GROQ_API_KEY değerini ekle

# Veritabanını oluştur ve seed et
python seed.py

# Sunucuyu başlat
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

**Demo giriş:** `admin@coop.com` / `admin123`

---

## Seed Verisi

| Veri | Detay |
|---|---|
| Müşteriler | 30 kurumsal + 20 bireysel (gerçekçi Türkçe isim/iletişim) |
| Ürünler | 10 ürün: Domates Salçası, Zeytinyağı, Organik Bal vb. |
| Siparişler | 150 sipariş (son 30 gün, bugün dahil aktif siparişler) |
| Kargolar | Her siparişe bağlı kargo + durum geçmişi |
| Müşteri Mesajları | Kategorize edilmiş gelen mesajlar |
| Operasyonel Uyarılar | Gecikme, stok, şikayet türü uyarılar |

---

## API Uç Noktaları

```
POST /auth/login                      — JWT token al
GET  /dashboard                       — KPI'lar, grafikler, AI içgörüleri
POST /chat                            — AI agent sohbet
GET  /orders                          — Sipariş listesi (tarih/durum filtreli)
GET  /orders/{id}                     — Sipariş detayı
GET  /shipments                       — Kargo listesi
GET  /shipments/{id}                  — Kargo detayı
GET  /inventory                       — Stok seviyeleri
GET  /messages                        — Müşteri mesajları
POST /messages                        — Yeni mesaj oluştur
GET  /operational-alerts              — Operasyonel uyarılar
GET  /analytics/demand                — Talep trendleri
GET  /docs                            — Swagger UI
```

---

## Tech Stack

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI | Groq API — Llama 3.3 70B Versatile |
| Veritabanı | SQLite + SQLAlchemy 2.x |
| Kimlik Doğrulama | JWT (python-jose) |
| Frontend | React 19, Vite, Tailwind CSS v4 |
| Animasyon | Framer Motion |
| Grafikler | Recharts |

---

## Katkıda Bulunanlar

- [kkbradd](https://github.com/kkbradd)
- [Mervegulatly](https://github.com/Mervegulatly)
