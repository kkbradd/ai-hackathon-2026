# Harman — 1 Dakikalık Tanıtım Videosu

## Sistem Özeti (Hızlı Hatırlatma)

**Harman**, kooperatifler için AI-first operasyon merkezi. İki katmanlı LLM mimarisi (Gemini + Groq fallback), 4 özerk arka plan ajanı, doğal dil + sesli chat, 7 günlük talep tahmini, AI üretip-operatör onaylayan e-posta akışı.

**7 sayfa:** Genel Bakış · AI Asistan · Siparişler · Kargo Takip · Envanter · **Talep Tahmini** · Mesajlar

**Hackathon gereksinim kapsamı:** 6 alanın 6'sı (müşteri iletişimi · sipariş · kargo · stok · iş akışı · analitik & tahmin)

---

## Hazırlık (Çekimden Önce)

1. **Backend** çalışıyor: `cd backend && uvicorn main:app --reload` (port 8000)
2. **Frontend** çalışıyor: `cd frontend && npm run dev` (port 5173)
3. **Tarayıcı:** Chrome, **incognito değil**, mikrofon iznine "İzin ver" demiş olmalı
4. **Pencere:** 1680×1050 (veya 1920×1080), zoom %100, sidebar **expanded**
5. **Demo verisi taze olsun:**
   - Dashboard'da gecikmiş kargo görünüyor mu? Yoksa: **Demo Olayları → Kargo Geciktir** bas (1 kez)
   - Kritik stok var mı? Yoksa: **Demo Olayları → Stok Düşür** bas (1 kez)
   - Bu iki tetik AI taslakları üretir; çekime girmeden 30 sn bekle ki AI yanıtlar gelsin
6. **Login'i çekmeden önce yap:** kredensiyaller dolu otomatik dolduruyorsa video temiz kayar
7. **OBS / SimpleScreenRecorder / QuickTime** ile 60 fps, viewport-area kayıt

---

## 60 Saniyelik Storyboard

| Saniye | Sayfa / Aksiyon | Sesli Anlatım | Görsel Vurgular |
|--------|-----------------|----------------|------------------|
| **0–5s** | **Login → Dashboard** açılışı | "Karşınızda **Harman** — kooperatifin operasyon merkezini yapay zekâ yönetiyor." | Logo, gradient başlık, sayfaya geçiş animasyonu |
| **5–15s** | **Genel Bakış** — 08:00 Günlük Özeti + 4/4 ajan badge | "Sabah sekizde Harman bizden önce işbaşında. Dört yapay zekâ ajanı dakika dakika sipariş, kargo, stok ve müşteri mesajlarını tarıyor; depo, kargo ve operasyon için üç ayrı sabah özeti çıkarıyor." | "4/4 AI ajanı canlı" badge'ine kısa zoom → "08:00 Günlük Özeti" 3 sütununa yatay pan |
| **15–27s** | **AI Asistan** (`/chat`) — empty state → mikrofon → soruyu söyle → cevap | "Operatör doğal dilde — yazarak ya da sesle — sorabilir." *(mikrofona bas)* — *"Bugün kaç sipariş var? Geciken kargo var mı?"* — *(cevap akarken)* "Sistem doğru aracı seçiyor, veriye bakıyor, Türkçe iş diliyle yanıtlıyor." | Mic butonu kırmızı pulse → transcript belirir → Gönder → 2-3 sn'de gerçek cevap akar |
| **27–38s** | **Talep Tahmini** (`/forecast`) — KPI → grafik → top 5 → AI Yorumu | "**Talep Tahmini**, geçmiş doksan günden öğreniyor; önümüzdeki yedi günün cirosunu öngörüyor. En çok satacak beş ürünü, stok risklerini, Gemini'nin yorumuyla önümüze koyuyor." | KPI şeridi → emerald solid → amber kesik tahmin → "BUGÜN" ayırıcı → KRİTİK rozetli satırlar → sağdaki parlak AI Yorumu kartı |
| **38–48s** | **Mesajlar** veya **Tedarikçi Taslakları** — AI taslak → önizle → Gönder | "Kargo geciktiğinde sistem müşteriye özür mailini, stok azaldığında tedarikçiye sipariş mailini yazıyor. **AI üretir, operatör onaylar, sistem iletir** — denetim hep insanda." | Amber "AI Taslak" rozeti → tam Türkçe profesyonel mail → onay tıklaması → ✓ Gönderildi |
| **48–55s** | **Kargo Takip** + **Envanter** (kısa pan) | "Kargo akışı beş aşamada canlı; gecikenler kırmızıyla işaretli. Envanter, kritik ile uyarı eşiklerini ayrı izliyor." | Statü filtreleri → kırmızı şeritli gecikmiş kart → Envanter kritik stok kartlarına yatay pan |
| **55–60s** | **Logo + tagline** kapanış | "**Gemini ve Groq destekli, çoklu-ajan mimarisi. Harman — kooperatifin için otonom operasyon.**" | Dashboard hero card'a zoom → Harman logosu close-up → fade-out |

---

## Tek Parça Konuşma Metni (Kayıt İçin)

> **Hız hedefi:** dakikada ~135 kelime. Vurgu yapılacak kelimeler **kalın**.
> **Nefes / duraklama** noktaları `‖` ile işaretli — burada yarım saniye dur, akış doğal kalsın.

> Karşınızda **Harman** ‖ kooperatifin operasyon merkezini yapay zekâ yönetiyor.
>
> Sabah sekizde Harman bizden önce işbaşında. ‖ Dört yapay zekâ ajanı dakika dakika sipariş, kargo, stok ve müşteri mesajlarını tarıyor; ‖ depo, kargo ve operasyon için **üç ayrı sabah özeti** çıkarıyor.
>
> Operatör doğal dilde ‖ yazarak ya da **sesle** ‖ sorabilir. *"Bugün kaç sipariş var? Geciken kargo var mı?"* ‖ Sistem doğru aracı seçiyor, veriye bakıyor, Türkçe iş diliyle yanıtlıyor.
>
> **Talep Tahmini** ‖ geçmiş doksan günden öğreniyor, önümüzdeki yedi günün cirosunu öngörüyor. ‖ En çok satacak beş ürünü, stok risklerini, Gemini'nin yorumuyla önümüze koyuyor.
>
> Kargo geciktiğinde sistem müşteriye özür mailini, ‖ stok azaldığında tedarikçiye sipariş mailini yazıyor. ‖ **AI üretir, operatör onaylar, sistem iletir** ‖ denetim hep insanda.
>
> Kargo akışı beş aşamada canlı; ‖ gecikenler kırmızıyla işaretli. Envanter, kritik ile uyarı eşiklerini ayrı izliyor.
>
> **Gemini ve Groq destekli, çoklu-ajan mimarisi.** ‖ **Harman — kooperatifin için otonom operasyon.**

**Kelime sayısı:** ~135 (60s @ 135 wpm hedefiyle rahat).

### Akıcılık Notları

- **"Karşınızda Harman"** açılışı kürsü gibi davet edici; vurguyu *Harman* üzerine çek, küçük bir duraklamayla aç.
- **"Dört yapay zekâ ajanı dakika dakika"** — `dakika dakika` ritmiği güçlü, ağır vurguyla söyle.
- **"yazarak ya da sesle"** — `sesle` üzerine yarım vurgu; hemen ardından mikrofona bas, soruyu söyle.
- **"AI üretir, operatör onaylar, sistem iletir"** — videonun *manifesto* cümlesi. Üçlü ritimde, eşit aralıklarla, hafif crescendo ile söyle. Sonra kısa duraklama → "denetim hep insanda" ile bitir.
- **Kapanış** — `Gemini ve Groq destekli` cümlesi olgunlukla, son cümle (`Harman — kooperatifin için otonom operasyon`) yavaşla ve düş.

---

## Ekran Kaydı / Kurgu İpuçları

### Açılış (0–5s)
- Login ekranındaki **atmosferik gradient** ve **yellow→emerald submit** kısa görünsün — login'e tıklamak yerine zaten login olmuş Dashboard'dan başla, ama logo'yu üst-sol köşede 1 saniye highlight et.

### Dashboard / Genel Bakış (5–15s)
- Üstte yeşil pulsing **"4/4 AI ajanı"** badge'ine kısa zoom — canlılık ve AI-first hissini iletir.
- "08:00 Günlük Özeti" kartının 3 sütununa yatay pan (Depo / Kargo / Operasyon).

### AI Asistan (15–27s) — VİDEONUN EN ÖNEMLİ ANI
- **Empty state hero**'yu göster: "Operasyonu doğal dilde sor." gradient başlık + 4 stat row.
- Mikrofon butonuna bas, **kırmızı pulse animasyonunu** çek.
- Yüksek sesle, net Türkçe ile soruyu söyle: *"Bugün kaç sipariş var? Geciken kargo var mı?"*
- Transcript otomatik input'a yazılır, sen Gönder'e bas.
- AI'ın 2–3 saniye içinde tool çağırıp gerçek Türkçe yanıt vermesini çek (hızlandırılmış değil).
- **Demo öncesi 1-2 deneme yap** — mikrofon izni reddedilmiş mi diye kontrol et.

### Talep Tahmini (27–38s)
- Sayfaya sol menüden tıkla — geçişin animasyonu görünsün.
- Üst KPI şeridini (₺1.6M / 67 sipariş / 19 risk) hızlı tara.
- Grafiğe odaklan: emerald solid kısımdan amber kesik kısma geçişi, "BUGÜN" ayırıcısını vurgula.
- Top 5 tablodaki **KRİTİK** rozetli satırları işaret et.
- Sağdaki parlak AI Yorumu kartına 2 saniye dur — gradient şerit + Sparkles ikonu jüriye iyi görünür.

### Onay Akışı (38–48s)
- Mesajlar sayfasındaki **AI Taslak rozetli amber kart**ı tıkla.
- "E-postayı önizle" ile gerçek mail gövdesini aç — gerçekçi Türkçe içerik.
- "Müşteriye Gönder" butonuna bas — ✓ rozeti çıkışını çek.
- Alternatif: aynı şeyi Dashboard'daki **Tedarikçi Taslakları** panelinde yap (zaman varsa).

### Kargo + Envanter (48–55s)
- Kargo Takip → status filtre tıkla → bir gecikmiş kart kırmızı şeritle parlasın.
- Envanter → kritik stok kartlarını yatay pan.

### Kapanış (55–60s)
- Dashboard'a dön, Harman hero card'a zoom — logo close-up.

---

## Ek Çekim Önerileri (Zaman Kalırsa B-roll)

- **Sidebar collapse animasyonu** — Logoya tıkla, sidebar daralır → genişler. UI cilasını gösterir.
- **Hover state'ler** — KPI kartları üzerine hover, indigo highlight çıkışı.
- **Demo Olayları menüsü** — sağ üstteki dropdown'ı aç → 7 olay türü görünsün (sistemin canlılık kanıtı).
- **Genel bakış grafiği** (Analytics) — günlük ciro eğrisi animasyonu (path-length 1.4s).

---

## Süre Kontrolü Tablosu

| Bölüm | Hedef Süre | Birikimli |
|---|---|---|
| Açılış / Logo | 5s | 5s |
| Dashboard / Özet | 10s | 15s |
| Chat / Sesli soru | 12s | 27s |
| Talep Tahmini | 11s | 38s |
| AI Onay Akışı | 10s | 48s |
| Kargo + Envanter | 7s | 55s |
| Kapanış | 5s | 60s |

**Esneklik notu:** Sesli soru anı uzayabilir — gerekirse Kargo + Envanter pan'ını 5 saniyeye sıkıştır, ya da onay akışını yalnızca müşteri mailiyle bitir (tedarikçi'yi atla).

---

## Çıkış Formatı

- **Çözünürlük:** 1080p (1920×1080) — YouTube/jüri panel uyumu için
- **Ses:** Mono, -3 dB peak, arka plan müziği yok ya da çok kısık (jüri konuşmaya odaklanmalı)
- **Format:** MP4, H.264, ~10–15 MB
- **Altyazı:** Türkçe altyazı (`.srt`) ekleyebilirsen jüri ortamında ses olmasa da anlaşılır olur

---

## Kayıt Sırası Önerisi

1. **Önce sesi kaydet** (telefonun voice memo'su yeter, sessiz odada). 60 saniyenin altında 2-3 alma yap, en akıcısını seç.
2. Ekran kaydını **sessiz** çek, hareketleri ses metnine göre senkronize et.
3. DaVinci Resolve / iMovie / CapCut'ta sesi ekran kaydının üstüne bindir.
4. Geçişlerde küçük cross-dissolve (0.2s), abartı yok.
5. Son 2 saniyede logo'ya kısa zoom + fade-out.

İyi şanslar — Harman'ı parlat.
