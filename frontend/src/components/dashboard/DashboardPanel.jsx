import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, AlertTriangle, Package, MessageSquare, CheckCircle, RefreshCw, ShoppingCart, UserPlus } from "lucide-react";
import { useDashboard } from "../../hooks/useDashboard";
import { triggerSimulationEvent } from "../../api/client";
import KpiGrid from "./KpiGrid";
import TodayMessagesCard from "./TodayMessagesCard";
import AnalyticsSection from "./AnalyticsSection";
import AIInsightsSection from "./AIInsightsSection";
import ActivityFeed from "./ActivityFeed";

const SIMULATE_EVENTS = [
  { type: "new_order",        label: "Sipariş Ekle",    Icon: ShoppingCart,  color: "text-blue-600 bg-blue-50" },
  { type: "new_customer",     label: "Müşteri Ekle",    Icon: UserPlus,      color: "text-teal-600 bg-teal-50" },
  { type: "delayed_shipment", label: "Kargo Geciktir",  Icon: AlertTriangle, color: "text-red-600 bg-red-50" },
  { type: "stock_drop",       label: "Stok Düşür",      Icon: Package,       color: "text-orange-600 bg-orange-50" },
  { type: "complaint",        label: "Şikayet Oluştur", Icon: MessageSquare, color: "text-violet-600 bg-violet-50" },
  { type: "delivery",         label: "Teslimat Yap",    Icon: CheckCircle,   color: "text-emerald-600 bg-emerald-50" },
  { type: "anomaly",          label: "Anomali Yarat",   Icon: Zap,           color: "text-amber-600 bg-amber-50" },
];

function SimulateButton({ onEvent }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const handle = async (type) => {
    setLoading(true);
    setOpen(false);
    try {
      const res = await triggerSimulationEvent(type);
      setToast({ ok: true, msg: res?.detail ?? "Olay tetiklendi." });
      onEvent?.();
    } catch (err) {
      const msg = err?.response?.data?.detail ?? "Olay tetiklenemedi.";
      setToast({ ok: false, msg });
    } finally {
      setLoading(false);
      setTimeout(() => setToast(null), 3000);
    }
  };

  return (
    <div className="relative">
      {toast && (
        <div className={`absolute -top-10 right-0 text-[11px] font-semibold px-3 py-1.5 rounded-lg shadow-md whitespace-nowrap z-50 ${toast.ok ? "bg-emerald-600 text-white" : "bg-red-600 text-white"}`}>
          {toast.msg}
        </div>
      )}
      <button
        onClick={() => setOpen((o) => !o)}
        disabled={loading}
        className="flex items-center gap-2 text-[12px] font-semibold text-slate-600 bg-white border border-slate-200 hover:border-indigo-300 hover:text-indigo-600 px-3.5 py-2 rounded-xl transition-colors shadow-sm disabled:opacity-60"
      >
        {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 text-amber-500" />}
        Simülasyon
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full right-0 mt-2 bg-white border border-slate-100 rounded-2xl p-2 z-50 min-w-[210px]"
            style={{ boxShadow: "0 8px 32px rgba(0,0,0,0.12)" }}
          >
            <div className="px-3 py-2 mb-1 border-b border-slate-100">
              <p className="text-[11px] font-bold text-slate-800 uppercase tracking-wider">Test Senaryoları</p>
            </div>
            {SIMULATE_EVENTS.map((e) => (
              <button
                key={e.type}
                onClick={() => handle(e.type)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left hover:bg-slate-50 transition-colors"
              >
                <div className={`p-1.5 rounded-lg ${e.color}`}>
                  <e.Icon className="w-3.5 h-3.5" />
                </div>
                <span className="text-[12px] font-semibold text-slate-700">{e.label}</span>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function DashboardPanel() {
  const [weeksAgo, setWeeksAgo] = useState(0);
  const { data, loading, error, refresh } = useDashboard(weeksAgo);

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-[1400px] mx-auto px-6 py-6 space-y-10">

        {/* Zone 1 — Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight mb-1">Operasyon Merkezi</h1>
            <p className="text-[12px] font-medium text-slate-400">
              Tarım ve Gıda Kooperatifi · {new Date().toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
            </p>
          </div>
          <SimulateButton onEvent={refresh} />
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl px-4 py-3 text-[12px] font-medium">
            Bağlantı hatası: {error}
          </div>
        )}

        {/* Zone 2 — KPIs */}
        <KpiGrid data={data} loading={loading} />

        {/* Bugünkü mesajlar */}
        <TodayMessagesCard data={data} loading={loading} />

        {/* Zone 3 — Analytics */}
        <AnalyticsSection
          data={data}
          loading={loading}
          weeksAgo={weeksAgo}
          setWeeksAgo={setWeeksAgo}
        />

        {/* Zone 4 — AI Insights + Alerts */}
        <div className="pt-10 border-t border-slate-100/80 mt-12">
          <AIInsightsSection loading={loading} />
        </div>

        {/* Zone 5 — Activity Feed (başlık kartlara yakın) */}
        <div className="pt-14 border-t border-slate-100/80 mt-4">
          <ActivityFeed data={data} loading={loading} />
        </div>

      </div>
    </div>
  );
}
