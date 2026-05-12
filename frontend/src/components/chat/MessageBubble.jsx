import ReactMarkdown from "react-markdown";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import {
  Brain, Package, ClipboardList, Clock, Truck, MapPin,
  AlertTriangle, MessageSquare, BarChart3, TrendingUp, CheckCircle,
} from "lucide-react";
import { sanitizeChatText } from "../../utils/sanitizeChatText";

const TOOL_LABELS = {
  get_order_status: { label: "Sipariş bilgisi alındı", Icon: Package },
  list_pending_orders: { label: "Bekleyen siparişler listelendi", Icon: ClipboardList },
  get_order_history: { label: "Sipariş geçmişi alındı", Icon: Clock },
  get_shipment_status: { label: "Sevkiyat durumu alındı", Icon: Truck },
  get_shipment_timeline: { label: "Sevkiyat hareketleri alındı", Icon: MapPin },
  get_delayed_shipments: { label: "Geciken sevkiyatlar listelendi", Icon: AlertTriangle },
  get_recent_messages: { label: "Müşteri iletişimleri alındı", Icon: MessageSquare },
  summarize_daily_operations: { label: "Günlük özet hazırlandı", Icon: BarChart3 },
  get_inventory_status: { label: "Stok bilgisi alındı", Icon: Package },
  get_operational_alerts: { label: "Uyarılar listelendi", Icon: AlertTriangle },
  get_demand_trends: { label: "Talep analizi yapıldı", Icon: TrendingUp },
  get_daily_summary_rich: { label: "Operasyon özeti hazırlandı", Icon: BarChart3 },
  resolve_operational_alert: { label: "Uyarı güncellendi", Icon: CheckCircle },
  update_shipment_status: { label: "Sevkiyat güncellendi", Icon: Truck },
  draft_supplier_order: { label: "Tedarik taslağı oluşturuldu", Icon: Package },
  update_order_status: { label: "Sipariş güncellendi", Icon: ClipboardList },
};

function formatTime(iso) {
  try {
    return format(new Date(iso), "HH:mm", { locale: tr });
  } catch {
    return "";
  }
}

function ShipmentWidget({ data }) {
  if (!data?.status) return null;
  const isDelayed = data.is_delayed;
  return (
    <div className="mt-3 bg-slate-50 border border-slate-100 rounded-xl p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Truck className="w-4 h-4 text-indigo-600 shrink-0" />
          <span className="font-bold text-slate-800 text-[12px] truncate">Kargo {data.tracking_number}</span>
        </div>
        <span
          className={`text-[10px] font-bold px-2 py-0.5 rounded-lg shrink-0 ${
            isDelayed
              ? "bg-red-100 text-red-700"
              : data.status === "delivered"
              ? "bg-emerald-100 text-emerald-700"
              : "bg-blue-100 text-blue-700"
          }`}
        >
          {isDelayed ? "GECİKMİŞ" : data.status?.toUpperCase()}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Taşıyıcı</p>
          <p className="text-[12px] font-semibold text-slate-700">{data.carrier}</p>
        </div>
        <div>
          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Alıcı</p>
          <p className="text-[12px] font-semibold text-slate-700">{data.recipient_name || "—"}</p>
        </div>
      </div>
    </div>
  );
}

function InventoryWidget({ data }) {
  if (!data?.items?.length) return null;
  return (
    <div className="mt-3 space-y-2">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">İlgili stok kayıtları</p>
      {data.items.slice(0, 5).map((item, idx) => {
        const name = item.product_name ?? item.product ?? "Ürün";
        const category = item.category ?? "";
        const unit = item.unit ?? "";
        const qtyRaw = item.quantity_kg ?? item.quantity;
        const qty =
          qtyRaw != null && !Number.isNaN(Number(qtyRaw))
            ? Number(qtyRaw).toLocaleString("tr-TR", { maximumFractionDigits: 2 })
            : "—";
        const low = item.is_low_stock ?? item.isLowStock;
        return (
          <div
            key={`${name}-${category}-${idx}`}
            className="bg-slate-50 border border-slate-100 rounded-xl p-3 flex items-center justify-between gap-4"
          >
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <div
                className={`p-1.5 rounded-lg shrink-0 ${low ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-600"}`}
              >
                <Package className="w-3.5 h-3.5" />
              </div>
              <div className="min-w-0">
                <p className="text-[12px] font-bold text-slate-800 truncate">{name}</p>
                {category ? <p className="text-[10px] text-slate-400 truncate">{category}</p> : null}
              </div>
            </div>
            <div className="text-right shrink-0 min-w-[5.5rem]">
              <p className={`text-[15px] font-extrabold tabular-nums ${low ? "text-red-600" : "text-slate-800"}`}>
                {qty}
              </p>
              <p className="text-[10px] font-bold text-slate-500">
                {unit} <span className="text-slate-400 font-semibold">kalan</span>
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  const toolInfo = msg.toolUsed ? TOOL_LABELS[msg.toolUsed] : null;
  const displayText = isUser ? msg.text : sanitizeChatText(msg.text || "");

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.22 }}
        className="flex justify-end mb-4"
      >
        <div className="w-full max-w-[min(28rem,90%)]">
          <div className="bg-indigo-600 text-white px-4 py-3 rounded-2xl rounded-br-md text-[13px] leading-relaxed shadow-sm shadow-indigo-100 font-medium">
            {displayText}
          </div>
          {msg.timestamp && (
            <p className="text-[10px] font-medium text-slate-400 text-right mt-1 px-1">{formatTime(msg.timestamp)}</p>
          )}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22 }}
      className="flex justify-start mb-4 gap-2.5"
    >
      <div className="w-8 h-8 rounded-xl bg-white border border-slate-100 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
        <Brain className="w-4 h-4 text-indigo-600" />
      </div>

      <div className="min-w-0 w-full max-w-[min(36rem,100%)]">
        {toolInfo && (
          <div className="flex items-center gap-2 mb-1.5">
            <span className="inline-flex items-center gap-1.5 text-slate-600 text-[10px] font-semibold px-2 py-1 rounded-lg bg-slate-50 border border-slate-100">
              <toolInfo.Icon className="w-3 h-3 text-indigo-500 shrink-0" />
              {toolInfo.label}
            </span>
          </div>
        )}

        <div
          className={`px-4 py-3.5 rounded-2xl rounded-bl-md text-[13px] leading-relaxed shadow-sm font-medium ${
            msg.isError ? "bg-red-50 border border-red-100 text-red-800" : "bg-white border border-slate-100 text-slate-800"
          }`}
        >
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2.5 last:mb-0 leading-relaxed text-slate-700">{children}</p>,
              ul: ({ children }) => <ul className="pl-4 list-disc space-y-1 mb-3 text-slate-700">{children}</ul>,
              ol: ({ children }) => <ol className="pl-4 list-decimal space-y-1 mb-3 text-slate-700">{children}</ol>,
              li: ({ children }) => <li>{children}</li>,
              strong: ({ children }) => <strong className="font-bold text-slate-900">{children}</strong>,
              code: ({ inline, children }) =>
                inline ? (
                  <code className="bg-slate-100 text-slate-800 px-1.5 py-0.5 rounded text-[12px] font-medium border border-slate-200">
                    {children}
                  </code>
                ) : (
                  <pre className="bg-slate-50 text-slate-800 rounded-xl p-3.5 text-[12px] mt-2 mb-2 overflow-x-auto border border-slate-100">
                    <code>{children}</code>
                  </pre>
                ),
              h3: ({ children }) => (
                <h3 className="font-extrabold text-slate-900 text-[14px] mb-2 mt-3 first:mt-0">{children}</h3>
              ),
            }}
          >
            {displayText}
          </ReactMarkdown>
          {msg.toolData && msg.toolUsed === "get_shipment_status" && <ShipmentWidget data={msg.toolData} />}
          {msg.toolData && msg.toolUsed === "get_inventory_status" && <InventoryWidget data={msg.toolData} />}
        </div>

        {msg.timestamp && (
          <p className="text-[10px] font-medium text-slate-400 mt-1 px-0.5">{formatTime(msg.timestamp)}</p>
        )}
      </div>
    </motion.div>
  );
}
