# Harman — Yapay Zeka Destekli Kooperatif Operasyon Merkezi

Tarım ve gıda kooperatifleri için geliştirilmiş AI-first operasyon yönetim platformu. Gemini ve Groq üzerinde çalışan çift katmanlı LLM mimarisi ile doğal dil sorgulama, 4 özerk AI ajanı ile kesintisiz operasyonel zeka ve gerçek zamanlı sipariş/kargo/stok takibi.

---

## Yapay Zeka Mimarisi

Harman'ın kalbinde iki katmanlı bir AI sistemi çalışır:

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI KATMANI                                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Sohbet Ajanı  (Gemini → Groq fallback · tool calling)  │  │
│  │                                                          │  │
│  │  Kullanıcı sorusu → doğru aracı seç → DB'yi sorgula     │  │
│  │  → sonucu yorumla → Türkçe iş dili ile yanıtla          │  │
│  │                                                          │  │
│  │  17 araç: sipariş, kargo, stok, uyarı, SQL analizi...   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Özerk Ajan Orkestratörü  (4 ajan · 15 dakikada bir)    │  │
│  │                                                          │  │
│  │  operational   → Bugünkü kargo/sipariş/stok/şikayet     │  │
│  │  shipment      → Pipeline ilerleme, gecikme tespiti     │  │
│  │  inventory     → Kritik stok, tüketim trendi, talep     │  │
│  │  customer_issue→ Yüksek öncelikli mesajlar, kümeler     │  │
│  │                                                          │  │
│  │  Context hash dedup: aynı durum → tekrar yazmaz         │  │
│  │  Sadece gerçek değişimde yeni içgörü üretir             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Sohbet Ajanı Nasıl Çalışır?

```
Kullanıcı: "Bugün kaç sipariş geldi, ciro nedir?"
    ↓
Llama 4 Scout → get_daily_summary_rich() aracını çağırır
    ↓
DB sorgusu → {orders: 22, revenue: 260420, ...}
    ↓
"Bugün 22 sipariş alındı, ciro ₺260.420 ile günlük hedefin
 üzerinde seyrediyor. En yüksek hacimli müşteri..."
```

### Özerk Ajanlar Nasıl Çalışır?

```
Her 15 dakikada bir:
    1. Operasyonel context'i DB'den çek (stok, kargolar, mesajlar...)
    2. Context hash'i hesapla
    3. Hash değişmediyse → "Durum değişmedi, atla"
    4. Hash değiştiyse → Llama 4 Scout'a gönder
    5. "critical|alert|..." formatında içgörü üret
    6. Dashboard'a yaz — kullanıcı dashboard'u açtığında anlık LLM çağrısı yapılmaz
```

---

## Platform Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│           FRONTEND  (React 19 + Vite + Tailwind CSS v4)     │
│                                                             │
│  Bugün Ne Oldu  · KPI Grid  · Mesajlar  · AI Analizi       │
│  Grafikler  · Aktivite Akışı  · Sohbet Paneli              │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST API (JWT)
┌──────────────────────────▼──────────────────────────────────┐
│                  BACKEND  (FastAPI + Python 3.11)            │
│                                                             │
│  Sohbet Ajanı · Ajan Orkestratörü · Simülasyon Motoru      │
│  SQLAlchemy ORM · JWT Auth · REST Uç Noktaları             │
│                                                             │
│  Veritabanı: SQLite                                         │
│  orders · shipments · inventory · messages · ai_insights    │
└─────────────────────────────────────────────────────────────┘
```

---

## Özellikler

### Yapay Zeka
- **Türkçe Sohbet Ajanı** — "Gecikmiş kargo var mı?", "Zeytinyağı stoğu kaç gün yeter?" gibi doğal dil sorularını anlayıp DB'yi sorgular ve Türkçe iş diliyle yanıtlar
- **4 Özerk Arka Plan Ajanı** — Sürekli çalışır, operasyonel değişimleri tespit eder, yalnızca yeni durumları dashboard'a yazar
- **Akıllı Dedup Sistemi** — Context hash karşılaştırması ile aynı durum tekrar tekrar raporlanmaz; sadece gerçek değişim insight üretir
- **Otomatik Önem Sınıflandırması** — Kritik / Uyarı / Bilgi / İyi — keyword analizi ile dinamik olarak belirlenir
- **Son 10 Gün Talep Analizi** — En çok sipariş edilen 3 ürünü tespit eder, stok yenileme önerisi üretir

### Operasyon
- **Günlük Brifing Paneli** — Dashboard açıldığında "Bugün Ne Oldu?": geciken kargolar, kritik stok, müşteri mesajları
- **Kargo Pipeline** — Otomatik durum geçişleri: hazırlanıyor → taşımada → şubede → dağıtımda → teslim edildi
- **Stok Yönetimi** — Kritik eşik altı ve yeniden sipariş noktası ayrı ayrı izlenir, "Kritik Stokları Doldur" butonu
- **Müşteri Mesajları** — Kategori/öncelik sınıflandırması, AI özeti, acil mesaj vurgulama
- **Simülasyon Paneli** — Sipariş Ekle, Kargo Geciktir, Stok Düşür, Şikayet Oluştur, Pipeline Yay, Teslimat Yap

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

| Ajan | Sıklık | Odak |
|---|---|---|
| `operational` | 15 dk | Bugünkü sipariş/kargo hareketi, aktif riskler, ciro |
| `shipment` | 15 dk | Pipeline ilerlemesi, gecikme tespiti (kaç saat gecikti) |
| `inventory` | 15 dk | Kritik stok altı ürünler, sipariş önerisi, 10 günlük talep |
| `customer_issue` | 15 dk | Yüksek öncelikli mesajlar, teslimat şikayeti kümeleri |

> Tüm ajanlar context hash dedup kullanır. Durum değişmediği sürece LLM çağrısı yapılmaz.

---

## Sohbet Ajanı Araçları

| Araç | Ne Yapar |
|---|---|
| `get_order_status` | Sipariş detayı: müşteri, ürünler, tutar, kargo durumu |
| `list_pending_orders` | Bekleyen ve işlemdeki siparişlerin listesi |
| `get_order_history` | Müşterinin tüm sipariş geçmişi (e-posta ile arama) |
| `get_shipment_status` | Kargo durumu, taşıyıcı, gecikme bilgisi |
| `get_shipment_timeline` | Kargonun adım adım hareket zaman çizelgesi |
| `get_delayed_shipments` | Şu an gecikmiş tüm kargolar |
| `get_inventory_status` | Stok seviyeleri, kritik ürünler, eşik karşılaştırması |
| `get_recent_messages` | Son müşteri mesajları (kategori/öncelik filtreli) |
| `get_operational_alerts` | Operasyonel uyarılar |
| `get_demand_trends` | Ürün talep trendleri (N günlük) |
| `get_daily_summary_rich` | Kapsamlı günlük operasyon raporu |
| `summarize_daily_operations` | Hızlı günlük özet |
| `update_shipment_status` | Kargo durumunu güncelle, hareket kaydı ekle |
| `update_order_status` | Sipariş durumunu güncelle |
| `resolve_operational_alert` | Uyarıyı çözüldü olarak işaretle |
| `draft_supplier_order` | Tedarikçi sipariş taslağı oluştur |
| `execute_sql` | Doğrudan SELECT sorgusu çalıştır (salt okunur) |

---

## Kurulum

### 1. Backend

```bash
cd backend
python3.11 -m venv venv311
source venv311/bin/activate       # Windows: venv311\Scripts\activate
pip install -r requirements.txt

# API anahtarlarını ayarla
cp .env.example .env
# GEMINI_API_KEY → aistudio.google.com/apikey
# GROQ_API_KEY   → console.groq.com/settings/api-keys

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
GEMINI_API_KEY=...  # aistudio.google.com/apikey (ücretsiz, birincil LLM)
GROQ_API_KEY=...    # console.groq.com → API Keys (ücretsiz, fallback LLM)
SECRET_KEY=...      # JWT imzalama anahtarı (rastgele string)
```

---

## Seed Verisi

| Veri | Detay |
|---|---|
| Müşteriler | 30 kurumsal + 20 bireysel (gerçekçi Türkçe isim/iletişim) |
| Ürünler | 20 ürün: Domates Salçası, Zeytinyağı, Karadut Pekmezi vb. |
| Siparişler | 150+ sipariş (son 30 gün, gerçekçi kargo pipeline dağılımı) |
| Kargolar | Her siparişe bağlı kargo + 5 aşamalı durum geçmişi |
| Müşteri Mesajları | Kategori ve öncelikle sınıflandırılmış gerçekçi mesajlar |
| Envanter | 20 ürün için stok seviyeleri, min eşik, yeniden sipariş noktası |

---

## API Uç Noktaları

```
POST /auth/login                — JWT token al
GET  /dashboard                 — KPI'lar, bugünkü olaylar, AI içgörüleri
POST /chat                      — AI sohbet ajanı
DELETE /chat/{session_id}       — Oturumu temizle
GET  /orders                    — Sipariş listesi (filtreli)
GET  /orders/{id}               — Sipariş detayı
GET  /shipments                 — Kargo listesi
GET  /shipments/{id}            — Kargo detayı
GET  /inventory                 — Stok seviyeleri
GET  /messages                  — Müşteri mesajları
POST /messages                  — Yeni mesaj oluştur
GET  /insights                  — AI içgörüleri (ajan/önem filtreli)
POST /insights/{id}/dismiss     — İçgörüyü kapat
GET  /insights/agent-status     — Ajan son çalışma zamanları ve içgörü sayıları
POST /simulate/event            — Simülasyon olayı tetikle
GET  /docs                      — Swagger UI
```

---

## Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI Modeli | Gemini 2.0 Flash Lite (birincil) · Llama 4 Scout 17B / Groq (fallback) |
| LLM Altyapısı | Önce Gemini dener, kota/hata durumunda Groq'a otomatik geçer |
| Veritabanı | SQLite + SQLAlchemy 2.x |
| Kimlik Doğrulama | JWT (python-jose) |
| Frontend | React 19, Vite, Tailwind CSS v4, Framer Motion |
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
