# Kooperatif Hub — AI-Powered Operations Assistant

Tarım ve gıda kooperatifleri için geliştirilmiş yapay zeka destekli operasyon yönetim platformu. Google Gemini 2.5 Flash ile doğal dil sorgulama, 4 özerk AI ajanı ile sürekli operasyonel analiz ve gerçek zamanlı sipariş/kargo/stok takibi.

---

## Mimari

```
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND  (React 19 + Vite + Tailwind CSS v4)  │
│  Dashboard · Siparişler · Kargolar · Envanter · Mesajlar    │
│  AI Chat Panel · Simülasyon Paneli · Agent Activity Log     │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST API (JWT)
┌──────────────────────────▼──────────────────────────────────┐
│                  BACKEND  (FastAPI + Python 3.11)            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Chat Agent — Gemini 2.5 Flash (tool calling)       │   │
│  │  17 araç: sipariş, kargo, stok, uyarı, SQL...       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Agent Orchestrator  (4 özerk AI ajanı)             │   │
│  │  operational · shipment · inventory · customer_issue │   │
│  │  Gemini 2.5 Flash ile periyodik LLM içgörüsü        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Simulation Engine  (background tasks)              │   │
│  │  Sipariş üretimi, kargo pipeline, şikayet sim.      │   │
│  │  Manuel: sipariş ekle, müşteri ekle, geciktir...    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Data Layer — SQLAlchemy + SQLite                   │   │
│  │  orders · shipments · inventory · messages · alerts │   │
│  │  ai_insights (LLM-generated, pre-cached)            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Özellikler

- **AI Chat Agent** — Türkçe doğal dil sorguları, Gemini 2.5 Flash ile araç çağrısı (tool calling)
- **4 Özerk AI Ajanı** — Operasyon, kargo, envanter ve müşteri ajanları periyodik olarak LLM içgörüsü üretir ve `ai_insights` tablosuna yazar; dashboard bu verileri okur, anlık LLM çağrısı yapmaz
- **Agent Activity Log** — Her ajanın son çalışma zamanı ve ürettiği içgörü sayısı dashboard'da görünür
- **Canlı Dashboard** — Bugünkü siparişler, aktif teslimatlar, stok uyarıları, zamanında teslimat oranı, AI operasyon analizi
- **Simülasyon Paneli** — Sipariş Ekle, Müşteri Ekle, Kargo Geciktir, Stok Düşür, Şikayet Oluştur, Teslimat Yap, Anomali Yarat
- **Kargo Pipeline** — Otomatik durum geçişleri (preparing → in_transit → at_facility → out_for_delivery → delivered)
- **Müşteri Mesajları** — Kategori/öncelik sınıflandırması, AI aksiyon önerisi, yeni mesaj oluşturma
- **Envanter Yönetimi** — Stok seviyeleri, kritik ürün uyarıları, hareket geçmişi

---

## AI Ajanları

| Ajan | Çalışma Sıklığı | Görev |
|---|---|---|
| `operational` | 15 dakikada bir | Gecikmiş kargolar, bekleyen siparişler, düşük stok, şikayet kümeleri, günlük ciro |
| `shipment` | 10 dakikada bir | Kargo pipeline'ı ilerletir, gecikme tespiti, anlık durum analizi |
| `inventory` | 30 dakikada bir | Yeniden sipariş noktası altındaki ürünler, 14 günlük tüketim trendleri |
| `customer_issue` | 30 dakikada bir | Bugünkü mesaj dağılımı, acil okunmamış mesajlar, kategori trendi |

---

## AI Chat Agent Araçları

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
# .env dosyasına GEMINI_API_KEY değerini ekle (Google AI Studio'dan ücretsiz alınır)

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

**Demo giriş:** `admin@demo.com` / `admin123`

---

## Ortam Değişkenleri

```env
GEMINI_API_KEY=...   # Google AI Studio → aistudio.google.com/apikey (ücretsiz)
```

---

## Seed Verisi

| Veri | Detay |
|---|---|
| Müşteriler | 30 kurumsal + 20 bireysel (gerçekçi Türkçe isim/iletişim) |
| Ürünler | 20 ürün: Domates Salçası, Zeytinyağı, Karadut Pekmezi vb. |
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
GET  /insights                        — AI içgörüleri (ajan/severity filtreli)
POST /insights/{id}/dismiss           — İçgörüyü kapat
GET  /insights/agent-status           — Ajan son çalışma zamanları
POST /simulate/event                  — Simülasyon olayı tetikle
GET  /docs                            — Swagger UI
```

---

## Tech Stack

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI (Chat) | Google Gemini 2.5 Flash — tool calling |
| AI (Ajanlar) | Google Gemini 2.5 Flash — periyodik içgörü üretimi |
| Veritabanı | SQLite + SQLAlchemy 2.x |
| Kimlik Doğrulama | JWT (python-jose) |
| Frontend | React 19, Vite, Tailwind CSS v4 |
| Animasyon | Framer Motion |
| Grafikler | Recharts |

---

## Katkıda Bulunanlar

- [kkbradd](https://github.com/kkbradd)
- [Mervegulatly](https://github.com/Mervegulatly)
