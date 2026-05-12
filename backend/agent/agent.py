import json
import os
import re
from typing import Optional

from groq import Groq
from sqlalchemy.orm import Session

from agent.tool_definitions import TOOL_DEFINITIONS
from agent import tools as tool_fns

SYSTEM_PROMPT = """Sen Tarım ve Gıda Kooperatifi için çalışan üst düzey bir AI Operasyon Yöneticisisin.

Kooperatif hakkında:
- Ürünler: Domates Salçası, Zeytinyağı, Kurutulmuş Domates, Vişne Reçeli, Kayısı Reçeli, Ev Makarnası, Acı Sos, Domates Sosu, Organik Bal, Nohut Unu
- Müşteriler: Restoranlar, marketler, dağıtıcılar ve toptan satıcılar
- Taşıyıcılar: Yurtiçi Kargo, Aras Kargo, MNG Kargo, PTT Kargo

Görevlerin:
- Sipariş ve kargo operasyonlarını yönetmek
- Envanter durumunu takip etmek ve stok uyarıları üretmek
- Gecikmiş teslimatları tespit etmek ve önlem önermek
- Operasyonel uyarıları analiz etmek ve önceliklendirmek
- Ürün talep trendlerini analiz etmek
- Günlük operasyon özeti ve stratejik içgörüler sunmak
- AKSİYON ALMAK: Sorunları çözdüğünde veya durumu güncellediğinde ilgili aksiyon araçlarını mutlaka kullan.

SQL aracı (execute_sql):
- Mevcut araçların kapsamadığı özel sorular için doğrudan veritabanına SQL ile sor.
- Tablolar: orders, order_items, products, customers, shipments, shipment_updates, customer_messages, inventory, inventory_movements, operational_alerts
- Yalnızca SELECT kullan. Sonuçları bağlamla birlikte yorumla.

Yanıt formatın:
## [Konu Başlığı]
**Kritik Bulgular:**
- [Acil dikkat gerektiren durumlar]

**Önerilen / Alınan Eylemler:**
- [Spesifik, eyleme geçilebilir öneriler veya alınan kararlar]

**Detaylar:**
[Ek bilgi ve analizler]

Kurallar:
- Yanıt vermeden önce mutlaka uygun aracı çağır, veriyi gör, sonra yorumla veya eylem yap
- Proaktif ol: Kullanıcı sormadan önce kritik sorunları öne çıkar
- Sayısal değerleri Türkçe formatla: ₺45,00 veya 150 kg
- Kısa, net ve eyleme geçilebilir yanıtlar ver
- Türkçe yanıt ver
- ASLA araç adı, JSON, <function>...</function>, SQL veya teknik çağrı metni yazma; araçlar sistem tarafında çalışır, sen sadece iş dilinde özetlersin
"""

# In-memory session history: session_id -> list of contents
_sessions: dict[str, list] = {}

def _build_tools() -> list[dict]:
    tools = []
    for td in TOOL_DEFINITIONS:
        tools.append({
            "type": "function",
            "function": {
                "name": td["name"],
                "description": td["description"],
                "parameters": td.get("parameters", {"type": "object", "properties": {}})
            }
        })
    return tools


def _strip_leaked_tool_syntax(text: str) -> str:
    """Remove pseudo-tool tags some models echo into assistant content."""
    if not text:
        return text
    s = text
    while re.search(r"<function[\s\S]*?</function>", s, re.IGNORECASE):
        s = re.sub(r"<function[\s\S]*?</function>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<function[^>]+\/>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"</?function[^>]*>", "", s, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def _coerce_args(args: dict) -> dict:
    """Coerce stringified booleans and integers."""
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
        "get_order_status":        lambda: tool_fns.get_order_status(db, **args),
        "list_pending_orders":     lambda: tool_fns.list_pending_orders(db, **args),
        "get_order_history":       lambda: tool_fns.get_order_history(db, **args),
        "get_shipment_status":     lambda: tool_fns.get_shipment_status(db, **args),
        "get_shipment_timeline":   lambda: tool_fns.get_shipment_timeline(db, **args),
        "get_delayed_shipments":   lambda: tool_fns.get_delayed_shipments(db),
        "get_recent_messages":     lambda: tool_fns.get_recent_messages(db, **args),
        "summarize_daily_operations": lambda: tool_fns.summarize_daily_operations(db),
        "get_inventory_status":    lambda: tool_fns.get_inventory_status(db, **args),
        "get_operational_alerts":  lambda: tool_fns.get_operational_alerts(db, **args),
        "get_demand_trends":       lambda: tool_fns.get_demand_trends(db, **args),
        "get_daily_summary_rich":  lambda: tool_fns.get_daily_summary_rich(db),
        "resolve_operational_alert": lambda: tool_fns.resolve_operational_alert(db, **args),
        "update_shipment_status":  lambda: tool_fns.update_shipment_status(db, **args),
        "draft_supplier_order":    lambda: tool_fns.draft_supplier_order(db, **args),
        "update_order_status":     lambda: tool_fns.update_order_status(db, **args),
        "execute_sql":             lambda: tool_fns.execute_sql(db, **args),
    }
    fn = fn_map.get(name)
    if fn is None:
        return {"error": f"Bilinmeyen araç: {name}"}
    return fn()


def chat(message: str, session_id: str, db: Session) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY ortam değişkeni ayarlanmamış.")

    client = Groq(api_key=api_key)
    tools = _build_tools()

    history = _sessions.setdefault(session_id, [])

    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})

    # Append new user message
    history.append({"role": "user", "content": message})

    tool_used: Optional[str] = None
    tool_data: Optional[dict] = None

    # Agentic loop: keep calling until no more tool calls
    max_rounds = 6
    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history,
            tools=tools,
            temperature=0.2,
        )

        message_obj = response.choices[0].message
        
        # We need to append the raw dict to history
        # Pydantic dump or custom dict
        msg_dict = message_obj.model_dump(exclude_unset=True)
        history.append(msg_dict)

        if not message_obj.tool_calls:
            # No tool calls — final answer
            break

        # Dispatch all tool calls
        for tool_call in message_obj.tool_calls:
            tool_used = tool_call.function.name
            
            try:
                args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            except json.JSONDecodeError:
                args = {}
                
            result_dict = _dispatch_tool(tool_call.function.name, args, db)
            tool_data = result_dict
            
            history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": json.dumps(result_dict)
            })

    # Extract final text
    final_text = ""
    for entry in reversed(history):
        if entry.get("role") == "assistant" and entry.get("content"):
            final_text = entry["content"]
            break

    # Keep history bounded
    if len(history) > 40:
        _sessions[session_id] = [history[0]] + history[-39:]

    cleaned = _strip_leaked_tool_syntax(final_text.strip())
    return {"reply": cleaned, "tool_used": tool_used, "tool_data": tool_data}


def clear_session(session_id: str):
    _sessions.pop(session_id, None)
