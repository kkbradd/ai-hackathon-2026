import json
import os
import re
from typing import Optional

import google.generativeai as genai
from sqlalchemy.orm import Session

from agent.tool_definitions import TOOL_DEFINITIONS
from agent import tools as tool_fns

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

# In-memory session history: session_id -> list of Content dicts
_sessions: dict[str, list] = {}


def _build_gemini_tools() -> list[genai.types.Tool]:
    """Convert TOOL_DEFINITIONS to Gemini FunctionDeclaration format."""
    declarations = []
    for td in TOOL_DEFINITIONS:
        params = td.get("parameters", {"type": "object", "properties": {}})
        declarations.append(
            genai.types.FunctionDeclaration(
                name=td["name"],
                description=td["description"],
                parameters=params,
            )
        )
    return [genai.types.Tool(function_declarations=declarations)]


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


def chat(message: str, session_id: str, db: Session) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY ortam değişkeni ayarlanmamış.")

    genai.configure(api_key=api_key)
    tools = _build_gemini_tools()
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        tools=tools,
        generation_config=genai.types.GenerationConfig(temperature=0.2),
    )

    # Gemini uses a chat session with history
    history = _sessions.setdefault(session_id, [])

    tool_used: Optional[str] = None
    tool_data: Optional[dict] = None

    # Start/resume chat session
    chat_session = model.start_chat(history=history)

    # Agentic loop
    max_rounds = 6
    current_message = message
    final_text = ""

    for _ in range(max_rounds):
        response = chat_session.send_message(current_message)
        parts = response.candidates[0].content.parts

        # Collect all function calls in this response
        fn_calls = [p.function_call for p in parts if hasattr(p, "function_call") and p.function_call.name]

        if fn_calls:
            # Build function response parts for all tool calls
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

            # Send all function responses back in one message
            current_message = genai.protos.Content(
                role="function",
                parts=fn_response_parts,
            )
            continue

        # No function calls — extract text
        text_parts = [p.text for p in parts if hasattr(p, "text") and p.text]
        if text_parts:
            final_text = "".join(text_parts)
        break

    # Persist history for next turn (Gemini chat session tracks it internally)
    _sessions[session_id] = chat_session.history

    # Keep history bounded
    if len(_sessions[session_id]) > 40:
        _sessions[session_id] = _sessions[session_id][-40:]

    cleaned = _strip_leaked_tool_syntax(final_text.strip())
    return {"reply": cleaned, "tool_used": tool_used, "tool_data": tool_data}


def clear_session(session_id: str):
    _sessions.pop(session_id, None)
