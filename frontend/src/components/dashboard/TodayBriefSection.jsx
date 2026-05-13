import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Truck, Package, MessageSquare, ChevronRight, Clock, AlertTriangle, CheckCircle } from "lucide-react";

const STATUS_TR = {
  preparing: "Hazırlanıyor",
  in_transit: "Yolda",
  at_facility: "Şubede",
  out_for_delivery: "Dağıtımda",
  delivered: "Teslim edildi",
  failed: "Başarısız",
  returned: "İade",
};

const CATEGORY_TR = {
  teslimat_gecikmesi: "Teslimat",
  yanlis_urun: "Yanlış ürün",
  siparis_talebi: "Sipariş",
  fatura_duzeltme: "Fatura",
  stok_bilgisi: "Stok",
  genel_destek: "Genel",
};

function BriefCard({ icon: Icon, iconBg, iconColor, title, count, countColor, children, emptyText, emptyColor, route }) {
  const navigate = useNavigate();
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-slate-100 rounded-2xl p-5 flex flex-col gap-3 shadow-sm flex-1 min-w-0"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${iconBg}`}>
            <Icon className={`w-4.5 h-4.5 ${iconColor}`} />
          </div>
          <div>
            <h3 className="text-[13px] font-bold text-slate-900">{title}</h3>
            <p className={`text-[11px] font-bold tabular-nums ${countColor}`}>
              {typeof count === "number" ? count : "—"} kayıt
            </p>
          </div>
        </div>
        {route && (
          <button
            onClick={() => navigate(route)}
            className="text-[11px] font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-0.5 shrink-0"
          >
            Tümü <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      <div className="flex-1">
        {children ?? (
          <p className={`text-[12px] font-medium py-1 ${emptyColor ?? "text-emerald-600"}`}>
            <CheckCircle className="w-3.5 h-3.5 inline mr-1 mb-0.5" />
            {emptyText ?? "Sorun yok"}
          </p>
        )}
      </div>
    </motion.div>
  );
}

function SkeletonBrief() {
  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5 flex-1 animate-shimmer h-40" />
  );
}

export default function TodayBriefSection({ data, loading }) {
  if (loading) {
    return (
      <div>
        <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">Bugün Ne Oldu?</p>
        <div className="flex flex-col sm:flex-row gap-4">
          <SkeletonBrief />
          <SkeletonBrief />
          <SkeletonBrief />
        </div>
      </div>
    );
  }

  const delayedList = data?.today_delayed_shipments ?? [];
  const stockList = data?.today_stock_alerts ?? [];
  const messages = data?.inbound_messages_today ?? [];
  const unread = data?.unread_messages ?? 0;

  return (
    <div>
      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">Bugün Ne Oldu?</p>
      <div className="flex flex-col sm:flex-row gap-4">

        {/* Delayed Shipments */}
        <BriefCard
          icon={Truck}
          iconBg="bg-red-50"
          iconColor="text-red-600"
          title="Geciken Kargolar"
          count={delayedList.length}
          countColor={delayedList.length > 0 ? "text-red-600" : "text-emerald-600"}
          route="/shipments"
          emptyText="Gecikmiş kargo yok"
        >
          {delayedList.length > 0 && (
            <ul className="space-y-1.5">
              {delayedList.slice(0, 4).map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-[11.5px]">
                  <Clock className="w-3 h-3 text-red-400 mt-0.5 shrink-0" />
                  <div className="min-w-0">
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
          )}
        </BriefCard>

        {/* Stock Alerts */}
        <BriefCard
          icon={Package}
          iconBg="bg-orange-50"
          iconColor="text-orange-600"
          title="Kritik Stok"
          count={stockList.length}
          countColor={stockList.length > 0 ? "text-orange-600" : "text-emerald-600"}
          route="/inventory"
          emptyText="Tüm stoklar normal seviyede"
        >
          {stockList.length > 0 && (
            <ul className="space-y-1.5">
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
          )}
        </BriefCard>

        {/* Today's Messages */}
        <BriefCard
          icon={MessageSquare}
          iconBg="bg-violet-50"
          iconColor="text-violet-600"
          title="Müşteri Mesajları"
          count={data?.inbound_messages_today_count ?? 0}
          countColor="text-violet-600"
          route="/messages"
          emptyText="Bugün mesaj yok"
          emptyColor="text-slate-400"
        >
          {messages.length > 0 && (
            <ul className="space-y-1.5">
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
          )}
        </BriefCard>

      </div>
    </div>
  );
}
