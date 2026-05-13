import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Truck, Package, MessageSquare, ChevronRight, Clock, AlertTriangle, CheckCircle } from "lucide-react";

const CATEGORY_TR = {
  teslimat_gecikmesi: "Teslimat",
  yanlis_urun: "Yanlış ürün",
  siparis_talebi: "Sipariş",
  fatura_duzeltme: "Fatura",
  stok_bilgisi: "Stok",
  genel_destek: "Genel",
};

function ColumnHeader({ icon: Icon, iconBg, iconColor, title, count, countColor, route }) {
  const navigate = useNavigate();
  return (
    <div className="flex items-center justify-between gap-2 mb-3">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${iconBg}`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        <div className="min-w-0">
          <h3 className="text-[13px] font-bold text-slate-900 truncate">{title}</h3>
          <p className={`text-[11px] font-bold tabular-nums ${countColor}`}>
            {typeof count === "number" ? count : "—"} kayıt
          </p>
        </div>
      </div>
      {route && (
        <button
          type="button"
          onClick={() => navigate(route)}
          className="text-[11px] font-bold text-slate-500 hover:text-slate-900 inline-flex items-center gap-0.5 shrink-0"
        >
          Tümü <ChevronRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}

function EmptyState({ text, color = "text-emerald-600" }) {
  return (
    <p className={`text-[12px] font-medium py-1 ${color}`}>
      <CheckCircle className="w-3.5 h-3.5 inline mr-1 mb-0.5" />
      {text}
    </p>
  );
}

function ColumnSkeleton() {
  return (
    <div className="flex flex-col gap-2 animate-pulse">
      <div className="h-9 bg-slate-100 rounded-xl w-2/3" />
      <div className="h-3 bg-slate-100 rounded w-3/4" />
      <div className="h-3 bg-slate-100 rounded w-1/2" />
    </div>
  );
}

export default function TodayBriefSection({ data, loading }) {
  if (loading) {
    return (
      <div
        className="bg-white border border-slate-200/80 shadow-sm"
        style={{ borderRadius: "16px" }}
      >
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.18em]">Bugün ne oldu?</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          <div className="p-5"><ColumnSkeleton /></div>
          <div className="p-5"><ColumnSkeleton /></div>
          <div className="p-5"><ColumnSkeleton /></div>
        </div>
      </div>
    );
  }

  const delayedList = data?.today_delayed_shipments ?? [];
  const stockList = data?.today_stock_alerts ?? [];
  const messages = data?.inbound_messages_today ?? [];
  const unread = data?.unread_messages ?? 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.05 }}
      className="bg-white border border-slate-200/80 shadow-sm overflow-hidden"
      style={{ borderRadius: "16px" }}
    >
      {/* Section header */}
      <div className="px-6 py-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/40">
        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.18em]">
          Bugün ne oldu?
        </p>
        <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          <span className="relative flex w-1.5 h-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
          </span>
          Anlık
        </div>
      </div>

      {/* 3-column grid with vertical dividers */}
      <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">

        {/* Delayed Shipments */}
        <div className="p-5">
          <ColumnHeader
            icon={Truck}
            iconBg="bg-red-50"
            iconColor="text-red-600"
            title="Geciken Kargolar"
            count={delayedList.length}
            countColor={delayedList.length > 0 ? "text-red-600" : "text-emerald-600"}
            route="/shipments"
          />
          {delayedList.length > 0 ? (
            <ul className="space-y-2">
              {delayedList.slice(0, 4).map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-[11.5px]">
                  <Clock className="w-3 h-3 text-red-400 mt-0.5 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <span className="font-semibold text-slate-800 truncate block">{s.tracking_number}</span>
                    <span className="text-slate-400">{s.carrier} · {s.hours_late} saat gecikti</span>
                    {s.recipient_name && (
                      <span className="text-slate-500 block truncate">→ {s.recipient_name}</span>
                    )}
                  </div>
                </li>
              ))}
              {delayedList.length > 4 && (
                <li className="text-[11px] text-slate-400 font-medium pl-5">+{delayedList.length - 4} daha</li>
              )}
            </ul>
          ) : (
            <EmptyState text="Gecikmiş kargo yok" />
          )}
        </div>

        {/* Stock Alerts */}
        <div className="p-5">
          <ColumnHeader
            icon={Package}
            iconBg="bg-orange-50"
            iconColor="text-orange-600"
            title="Kritik Stok"
            count={stockList.length}
            countColor={stockList.length > 0 ? "text-orange-600" : "text-emerald-600"}
            route="/inventory"
          />
          {stockList.length > 0 ? (
            <ul className="space-y-2">
              {stockList.slice(0, 4).map((s, i) => (
                <li key={i} className="flex items-center gap-2 text-[11.5px]">
                  <AlertTriangle className="w-3 h-3 text-orange-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="font-semibold text-slate-800 truncate block">{s.name}</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <div className="flex-1 bg-slate-100 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${s.pct < 30 ? "bg-red-500" : s.pct < 60 ? "bg-orange-400" : "bg-amber-400"}`}
                          style={{ width: `${Math.min(s.pct, 100)}%` }}
                        />
                      </div>
                      <span className="text-slate-400 tabular-nums text-[10px]">%{s.pct}</span>
                    </div>
                  </div>
                </li>
              ))}
              {stockList.length > 4 && (
                <li className="text-[11px] text-slate-400 font-medium pl-5">+{stockList.length - 4} ürün daha</li>
              )}
            </ul>
          ) : (
            <EmptyState text="Tüm stoklar normal seviyede" />
          )}
        </div>

        {/* Today's Messages */}
        <div className="p-5">
          <ColumnHeader
            icon={MessageSquare}
            iconBg="bg-violet-50"
            iconColor="text-violet-600"
            title="Müşteri Mesajları"
            count={data?.inbound_messages_today_count ?? 0}
            countColor="text-violet-600"
            route="/messages"
          />
          {messages.length > 0 ? (
            <ul className="space-y-2">
              {messages.slice(0, 4).map((m, i) => (
                <li key={i} className="flex items-start gap-2 text-[11.5px]">
                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                    m.urgency === "yüksek" ? "bg-red-500" :
                    m.urgency === "orta" ? "bg-amber-400" : "bg-slate-300"
                  }`} />
                  <div className="min-w-0">
                    <span className="font-semibold text-slate-800 truncate block">{m.customer_name}</span>
                    <span className="text-[10px] font-medium text-violet-600 bg-violet-50 px-1.5 py-0.5 rounded">
                      {CATEGORY_TR[m.category] ?? m.category?.replace(/_/g, " ")}
                    </span>
                  </div>
                </li>
              ))}
              {unread > 0 && (
                <li className="text-[11px] font-semibold text-amber-600 pl-3.5">
                  {unread} okunmamış mesaj bekliyor
                </li>
              )}
            </ul>
          ) : (
            <EmptyState text="Bugün mesaj yok" color="text-slate-400" />
          )}
        </div>

      </div>
    </motion.div>
  );
}
