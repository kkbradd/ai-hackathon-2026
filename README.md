# Kooperatif Hub — AI-Powered Operations Assistant

Tarım ve gıda kooperatifleri için geliştirilmiş yapay zeka destekli operasyon yönetim platformu. Google Gemini 2.5 Flash ile doğal dil sorgulama, 4 özerk AI ajanı ile sürekli operasyonel analiz, AI tarafından üretilen tedarikçi/müşteri e-posta taslakları (operatör onayıyla iletilir) ve sabah rol-bazlı brifingleri.

> **v4.1 yenilikleri:** AI artık sadece içgörü üretmiyor — tedarikçi sipariş e-postası taslakları, müşteri gecikme bildirim taslakları ve rol-bazlı (depo/kargo/operasyon) günlük brifingler üretiyor. Tüm aksiyonlar operatör onayıyla iletilir.

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
│  │  AI Action Layer  (yeni — v4.1)                     │   │
│  │  Tedarikçi e-posta taslakları (otomatik + manuel)   │   │
│  │  Müşteri gecikme bildirim taslakları                │   │
│  │  08:00 Brifingi (depo · kargo · operasyon)          │   │
│  │  → Operatör onayı ile gönderim simülasyonu          │   │
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
│  │  ai_insights · supplier_order_drafts (v4.1)         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Özellikler

- **AI Chat Agent** — Türkçe doğal dil sorguları, Gemini 2.5 Flash ile araç çağrısı (tool calling)
- **4 Özerk AI Ajanı** — Operasyon, kargo, envanter ve müşteri ajanları periyodik olarak LLM içgörüsü üretir ve `ai_insights` tablosuna yazar; dashboard bu verileri okur, anlık LLM çağrısı yapmaz
- **🆕 Tedarikçi E-posta Taslakları** — Envanter ajanı kritik stoğu tespit edince otomatik olarak tedarikçi-spesifik Türkçe sipariş e-postası taslağı üretir; chat agent `draft_supplier_order` aracıyla manuel de tetiklenir; operatör dashboard'dan inceler ve "Tedarikçiye Gönder" ile iletir (gönderim simüle edilir)
- **🆕 Müşteri Bildirim Taslakları** — Kargo gecikmesi tespit edildiğinde sistem otomatik olarak müşteri-spesifik özürlü bildirim e-postası taslağı üretir; operatör onayıyla `outbound` mesaja dönüşür
- **🆕 08:00 Brifingi** — `/daily-briefing` endpoint'i 3 rol için ayrıştırılmış AI özet ve liste döndürür: depo sorumlusu (hazırlanacak paketler), kargo görevlisi (bugünkü dağıtım rotaları), operasyon yöneticisi (açık kritik konular)
- **Agent Activity Log** — Her ajanın son çalışma zamanı ve ürettiği içgörü sayısı dashboard'da görünür
- **Canlı Dashboard** — Sabah brifingi, KPI'lar, AI tedarikçi taslakları, bugünkü mesajlar, analitik grafikler, AI içgörüleri, aktivite akışı
- **Simülasyon Paneli** — Sipariş Ekle, Müşteri Ekle, Kargo Geciktir, Stok Düşür, Şikayet Oluştur, Teslimat Yap, Anomali Yarat
- **Kargo Pipeline** — Otomatik durum geçişleri (preparing → in_transit → at_facility → out_for_delivery → delivered)
- **Müşteri Mesajları** — Kategori/öncelik sınıflandırması, AI aksiyon önerisi, yeni mesaj oluşturma, AI taslak yönetimi
- **Envanter Yönetimi** — Stok seviyeleri, kritik ürün uyarıları, hareket geçmişi

---

## AI Aksiyon Akışı (v4.1)

Sistemin merkezindeki tasarım prensibi: **AI içerik üretir, operatör onaylar, sistem iletir**. Hiçbir e-posta otomatik olarak müşteriye/tedarikçiye gitmez — her aksiyon dashboard'da inceleme/onay aşamasından geçer. Bu, hem güvenlik hem de hesap verebilirlik sağlar.

| Tetikleyici | Üretici | Çıktı | Onay arayüzü |
|---|---|---|---|
| Stok < min_threshold | `inventory_agent` (her 30 dk) | `SupplierOrderDraft` (ürün-bazlı tedarikçi e-postası) | Dashboard → "Tedarikçi Taslakları" paneli |
| Chat: *"X için tedarikçiye taslak hazırla"* | `chat_agent` (`draft_supplier_order` tool) | `SupplierOrderDraft` | Aynı panel |
| Kargo gecikme olayı | `simulation._trigger_delayed_shipment` | `CustomerMessage(direction=outbound, is_draft=True)` | Mesajlar sayfası → AI Taslak rozetli kart |
| Sayfa açılışı (her 30 dk) | `daily_briefing` endpoint | `DailyBriefing` (3 rol için özet + liste) | Dashboard → "08:00 Brifingi" kartı |

**Not:** Demoda gerçek SMTP/WhatsApp entegrasyonu yapılmamıştır. "Gönder" butonu taslak durumunu `sent` olarak işaretler ve `sent_at` zamanı kaydeder. Üretim için yalnızca channel adapter eklenmesi yeterlidir (içerik ve akış hazır).

---

## AI Ajanları

| Ajan | Çalışma Sıklığı | Görev | Yan etki |
|---|---|---|---|
| `simulation_tick` | 2 dakikada bir | Yeni sipariş üretir, %10 olasılıkla şikayet üretir | DB |
| `shipment` | 10 dakikada bir | Kargo pipeline'ı ilerletir, gecikme tespiti, anlık durum analizi | `ai_insights` |
| `operational` | 15 dakikada bir | Gecikmiş kargolar, bekleyen siparişler, düşük stok, şikayet kümeleri, günlük ciro | `ai_insights` |
| `inventory` | 30 dakikada bir | Yeniden sipariş noktası altındaki ürünler, 14 günlük tüketim trendleri | `ai_insights` + **`SupplierOrderDraft`** |
| `customer_issue` | 30 dakikada bir | Bugünkü mesaj dağılımı, acil okunmamış mesajlar, kategori trendi | `ai_insights` |

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
| `draft_supplier_order` | Gemini ile tedarikçi e-posta taslağı üretir (operatör onayıyla iletilir) |
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

**Demo giriş:** `admin@demo.com` / `demo123`

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
GET  /messages                        — Müşteri mesajları (gelen + giden + AI taslaklar)
POST /messages                        — Yeni mesaj oluştur
POST /messages/{id}/send              — 🆕 AI taslak müşteri mesajını gönder (sim)
POST /messages/{id}/cancel            — 🆕 AI taslak müşteri mesajını iptal et
GET  /insights                        — AI içgörüleri (ajan/severity filtreli)
POST /insights/{id}/dismiss           — İçgörüyü kapat
GET  /insights/agent-status           — Ajan son çalışma zamanları
GET  /supplier-drafts                 — 🆕 Tedarikçi e-posta taslakları (status filtreli)
POST /supplier-drafts                 — 🆕 Manuel tedarikçi taslağı oluştur
POST /supplier-drafts/{id}/send       — 🆕 Tedarikçi taslağını onayla & gönder (sim)
POST /supplier-drafts/{id}/cancel     — 🆕 Tedarikçi taslağını iptal et
GET  /daily-briefing                  — 🆕 Sabah brifingi (depo · kargo · operasyon)
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
| AI (E-posta üretimi) | Google Gemini 2.5 Flash — tedarikçi/müşteri e-posta gövdesi (template fallback) |
| AI (Brifing özetleri) | Google Gemini 2.5 Flash — rol-bazlı 2 cümlelik özetler, 30 dk in-memory cache |
| Veritabanı | SQLite + SQLAlchemy 2.x — runtime ALTER TABLE migrasyonu |
| Kimlik Doğrulama | JWT (python-jose) + bcrypt (passlib) |
| Frontend | React 19, Vite 8, Tailwind CSS v4 |
| Animasyon | Framer Motion |
| Grafikler | Recharts |
| İkonlar | Lucide React |

---

## Demo Akışı (Jüri için)

1. **Login:** `admin@demo.com` / `demo123`
2. **Dashboard üst kısmı:** "08:00 Brifingi" — depo / kargo / operasyon için 3 sütun, her birinde AI özet + somut liste. Yenile butonuyla brifing yeniden üretilir (30 dk cache).
3. **Simülasyon → Stok Düşür:** Envanter ajanı bir sonraki çalışmasında (veya manuel `draft_supplier_order` chat tool'u ile) **AI tedarikçi e-posta taslağı** üretir → "Tedarikçi Taslakları" panelinde kart olarak görünür → **E-postayı önizle** ile tam Türkçe profesyonel mail görünür → **Tedarikçiye Gönder** ile durum `sent` olur, ✓ rozeti çıkar.
4. **Simülasyon → Kargo Geciktir:** Sistem otomatik olarak ilgili müşteri için **gecikme bildirim e-postası taslağı** üretir → Mesajlar sayfasında "📤 AI Taslak" rozetli amber kartta görünür → **Müşteriye Gönder** / **İptal** butonlarıyla yönetilir.
5. **AI Chat:** *"Karabiber için 80 kg tedarikçi taslağı hazırla"* — chat agent `draft_supplier_order` tool'unu çağırır, taslak üretilir, dashboard'da görünür.

> Tüm AI üretimleri `GEMINI_API_KEY` yoksa profesyonel template fallback'iyle çalışır; gerçek key ile içerikler ürün/müşteri-spesifik olur.
