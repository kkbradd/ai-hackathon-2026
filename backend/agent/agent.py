import json
import os
import re
from typing import Optional

from sqlalchemy.orm import Session

from agent.tool_definitions import TOOL_DEFINITIONS
from agent import tools as tool_fns

GEMINI_MODEL = "gemini-2.0-flash-lite"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

SYSTEM_PROMPT = """Sen Anadolu Tarım ve Gıda Kooperatifi'nin yapay zeka destekli Operasyon Yöneticisisin.

## Kooperatif Profili
**Ürün Kataloğu (20 ürün):**
Salça grubu: Domates Salçası, Biber Salçası
Yağ/Sos grubu: Zeytinyağı, Nar Ekşisi, Sıvı Sumak, Acı Biber Sosu
Baharat grubu: Karabiber, Kimyon, İsot, Kırmızı Biber, Karışık Baharat Seti
Kurutulmuş: Kuru Domates, Kuru Biber
Pekmez grubu: Karadut Pekmezi, Keçiboynuzu Pekmezi, Üzüm Pekmezi
Öz grubu: Karadut Özü, Yaban Mersini Özü
Diğer: Ev Eriştesi, El Yapımı Kayısı Reçeli

**Müşteri Segmentleri:**
- restoran / lokanta: büyük hacimli düzenli siparişler (10-50 birim/kalem)
- market / organik market: yüksek hacim (20-80 birim/kalem)
- bakkal / büfe / kuruyemişçi: orta hacim (5-25 birim/kalem)
- kafe / pastane: küçük-orta hacim (3-15 birim/kalem)
- butik / doğal ürünler: küçük hacim premium (2-10 birim/kalem)
- bireysel: en küçük hacim (1-5 birim/kalem)
- yerel_isletme / kooperatif satış / çiftlik: orta hacim (5-20 birim/kalem)
- kurumsal / otel / gıda dağıtım: kurumsal hacim (10-40 birim/kalem)

**Kargo Taşıyıcıları:** Yurtiçi Kargo, Aras Kargo, MNG Kargo, PTT Kargo

**Kargo Yaşam Döngüsü:** preparing → in_transit → at_facility → out_for_delivery → delivered

## Veri Modeli
Tablolar: orders, order_items, products, customers, shipments, shipment_updates, customer_messages, inventory, inventory_movements, operational_alerts

Müşteri mesajları (customer_messages): gerçek müşterilerden gelen şikayetler ve geri bildirimler.
- related_order_id: hangi siparişle ilgili olduğu
- related_shipment_id: hangi kargoyla ilgili olduğu
- category: teslimat_gecikmesi, yanlis_urun, siparis_talebi, fatura_duzeltme, stok_bilgisi, genel_destek
- urgency: yüksek / orta / düşük

## Görevlerin
1. **Operasyon İzleme:** Gecikmiş kargolar, düşük stok, şikayet kümeleri, açık uyarılar
2. **Müşteri İletişimi:** Gelen mesajları analiz et, önceliklendir, yanıt öner veya oluştur
3. **Stok Yönetimi:** Minimum eşik altındaki ürünler için tedarik önerisi
4. **Sipariş Takibi:** Spesifik sipariş veya müşteri sorguları
5. **Trend Analizi:** Hangi ürünler daha fazla satıyor, hangi müşteri segmentleri büyüyor
6. **Aksiyon Alma:** Uyarı çözme, kargo güncelleme, sipariş durumu değiştirme

## Araç Kullanım Kuralları
- Her soruya cevap vermeden önce MUTLAKA ilgili aracı çağır
- execute_sql: Araçlarla karşılanamayan özel analizler için — sadece SELECT
- Bir müşteri veya sipariş hakkında soru gelirse önce o müşteriyi/siparişi sorgula
- Mesaj şikayeti varsa ilgili order_id ve shipment_id'yi araştır

## Yanıt Formatı
Kısa, net, eyleme geçilebilir. Kritik durumlar için:

## [Başlık]
**Durum:** [Özet — 1 cümle]
**Bulgular:** [Sayısal veriler]
**Öneri / Alınan Aksiyon:** [Somut adım]

## Kurallar
- Türkçe yanıt ver, iş dilini kullan
- Sayıları Türkçe formatla: ₺1.250,00 — 45 kg — 3 sipariş
- Araç adı, JSON, SQL veya teknik syntax ASLA yazma — sadece iş çıktısı
- Proaktif ol: kullanıcı sormadan kritik sorunları öne çıkar
- Çok uzun listeleri özetle: "5 üründen 3'ü kritik: X, Y, Z..."
"""

# Groq tool format
_GROQ_TOOLS = [{"type": "function", "function": td} for td in TOOL_DEFINITIONS]

# In-memory session history: session_id -> {"backend": "gemini"|"groq", "history": [...]}
_sessions: dict[str, dict] = {}


def _is_quota_error(err: str) -> bool:
    lowered = err.lower()
    return any(kw in lowered for kw in ("429", "quota", "rate", "limit", "resourceexhausted", "exhausted"))


def _strip_leaked_tool_syntax(text: str) -> str:
    if not text:
        return text
    s = text
    while re.search(r"<function[\s\S]*?</function>", s, re.IGNORECASE):
        s = re.sub(r"<function[\s\S]*?</function>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<function[^>]+\/>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"</?function[^>]*>", "", s, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def _coerce_args(args: dict) -> dict:
    if not args:
        return {}
    result = {}
    for k, v in args.items():
        if isinstance(v, str):
            if v.lower() == "true":
                result[k] = True
            elif v.lower() == "false":
                result[k] = False
            else:
                try:
                    result[k] = int(v)
                except ValueError:
                    try:
                        result[k] = float(v)
                    except ValueError:
                        result[k] = v
        else:
            result[k] = v
    return result


def _dispatch_tool(name: str, args: dict, db: Session) -> dict:
    args = _coerce_args(args)
    fn_map = {
        "get_order_status":           lambda: tool_fns.get_order_status(db, **args),
        "list_pending_orders":        lambda: tool_fns.list_pending_orders(db, **args),
        "get_order_history":          lambda: tool_fns.get_order_history(db, **args),
        "get_shipment_status":        lambda: tool_fns.get_shipment_status(db, **args),
        "get_shipment_timeline":      lambda: tool_fns.get_shipment_timeline(db, **args),
        "get_delayed_shipments":      lambda: tool_fns.get_delayed_shipments(db),
        "get_recent_messages":        lambda: tool_fns.get_recent_messages(db, **args),
        "summarize_daily_operations": lambda: tool_fns.summarize_daily_operations(db),
        "get_inventory_status":       lambda: tool_fns.get_inventory_status(db, **args),
        "get_operational_alerts":     lambda: tool_fns.get_operational_alerts(db, **args),
        "get_demand_trends":          lambda: tool_fns.get_demand_trends(db, **args),
        "get_daily_summary_rich":     lambda: tool_fns.get_daily_summary_rich(db),
        "resolve_operational_alert":  lambda: tool_fns.resolve_operational_alert(db, **args),
        "update_shipment_status":     lambda: tool_fns.update_shipment_status(db, **args),
        "draft_supplier_order":       lambda: tool_fns.draft_supplier_order(db, **args),
        "update_order_status":        lambda: tool_fns.update_order_status(db, **args),
        "execute_sql":                lambda: tool_fns.execute_sql(db, **args),
    }
    fn = fn_map.get(name)
    if fn is None:
        return {"error": f"Bilinmeyen araç: {name}"}
    return fn()


# ---------- Gemini chat ----------

def _build_gemini_tools():
    import google.generativeai as genai
    declarations = []
    for td in TOOL_DEFINITIONS:
        params = td.get("parameters", {"type": "object", "properties": {}})
        declarations.append(genai.types.FunctionDeclaration(
            name=td["name"],
            description=td["description"],
            parameters=params,
        ))
    return [genai.types.Tool(function_declarations=declarations)]


def _chat_gemini(message, history: list, db: Session) -> tuple[str, Optional[str], Optional[dict], list]:
    """Returns (reply_text, tool_used, tool_data, updated_history). Raises on quota/error."""
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY yok")

    genai.configure(api_key=api_key)
    tools = _build_gemini_tools()
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        tools=tools,
        generation_config=genai.types.GenerationConfig(temperature=0.2),
    )

    chat_session = model.start_chat(history=history)
    tool_used = None
    tool_data = None
    current_message = message
    final_text = ""

    for _ in range(6):
        response = chat_session.send_message(current_message)
        parts = response.candidates[0].content.parts
        fn_calls = [p.function_call for p in parts if hasattr(p, "function_call") and p.function_call.name]

        if fn_calls:
            fn_response_parts = []
            for fc in fn_calls:
                tool_used = fc.name
                args = dict(fc.args) if fc.args else {}
                result_dict = _dispatch_tool(fc.name, args, db)
                tool_data = result_dict
                fn_response_parts.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fc.name,
                            response={"result": json.dumps(result_dict)},
                        )
                    )
                )
            current_message = genai.protos.Content(role="function", parts=fn_response_parts)
            continue

        text_parts = [p.text for p in parts if hasattr(p, "text") and p.text]
        if text_parts:
            final_text = "".join(text_parts)
        break

    return final_text, tool_used, tool_data, list(chat_session.history)


# ---------- Groq chat ----------

def _chat_groq(message, history: list, db: Session) -> tuple[str, Optional[str], Optional[dict], list]:
    """Returns (reply_text, tool_used, tool_data, updated_history). Raises on quota/error."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY yok")

    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]

    tool_used = None
    tool_data = None
    final_text = ""

    for _ in range(6):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=_GROQ_TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
            temperature=0.2,
            max_tokens=1024,
        )
        msg = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.__dict__ if hasattr(tc, "__dict__") else tc for tc in (msg.tool_calls or [])],
        })

        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_used = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = _dispatch_tool(tc.function.name, args, db)
                tool_data = result
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            continue

        final_text = msg.content or ""
        break

    # Return history without system message
    return final_text, tool_used, tool_data, messages[1:]


# ---------- Public interface ----------

def chat(message: str, session_id: str, db: Session) -> dict:
    session = _sessions.setdefault(session_id, {"backend": "gemini", "history": []})
    history = session["history"]
    current_backend = session["backend"]

    tool_used = None
    tool_data = None
    final_text = ""
    used_backend = current_backend

    # Try preferred backend first, fall back to the other on quota/error
    backends = ["gemini", "groq"] if current_backend == "gemini" else ["groq", "gemini"]

    for backend in backends:
        try:
            if backend == "gemini":
                # Gemini keeps its own history format — pass only if we have Gemini history
                gemini_history = history if current_backend == "gemini" else []
                final_text, tool_used, tool_data, new_history = _chat_gemini(message, gemini_history, db)
            else:
                # Convert to flat message list for Groq
                groq_history = history if current_backend == "groq" else []
                final_text, tool_used, tool_data, new_history = _chat_groq(message, groq_history, db)

            used_backend = backend
            session["backend"] = backend
            session["history"] = new_history

            # Keep history bounded
            if len(session["history"]) > 40:
                session["history"] = session["history"][-40:]

            print(f"[Chat] {backend} kullanıldı.")
            break

        except Exception as e:
            err = str(e)
            if _is_quota_error(err):
                print(f"[Chat] {backend} kota/limit — {'diğerine geçiliyor' if backend != backends[-1] else 'ikisi de dolu'}. ({err[:100]})")
                if backend == backends[-1]:
                    final_text = "Şu anda her iki AI servisi de yoğun. Lütfen birkaç dakika sonra tekrar deneyin."
            else:
                print(f"[Chat] {backend} hatası — {'diğerine geçiliyor' if backend != backends[-1] else 'başarısız'}. ({err[:100]})")
                if backend == backends[-1]:
                    final_text = "AI servisine bağlanırken bir sorun oluştu. Lütfen tekrar deneyin."

    cleaned = _strip_leaked_tool_syntax(final_text.strip())
    return {"reply": cleaned, "tool_used": tool_used, "tool_data": tool_data}


def clear_session(session_id: str):
    _sessions.pop(session_id, None)
