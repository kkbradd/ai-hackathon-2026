import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, AlertTriangle, Package, MessageSquare, CheckCircle, RefreshCw, ShoppingCart, UserPlus, Sparkles, Sun, Moon, Sunrise, Sunset } from "lucide-react";
import { useDashboard } from "../../hooks/useDashboard";
import { useAuth } from "../../store/authStore";
import { triggerSimulationEvent } from "../../api/client";
import KpiGrid from "./KpiGrid";
import TodayBriefSection from "./TodayBriefSection";
import TodayMessagesCard from "./TodayMessagesCard";
import AnalyticsSection from "./AnalyticsSection";
import AIInsightsSection from "./AIInsightsSection";
import ActivityFeed from "./ActivityFeed";
import SupplierDraftsPanel from "./SupplierDraftsPanel";
import DailyBriefingCard from "./DailyBriefingCard";

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
              <p className="text-[11px] font-bold text-slate-800 uppercase tracking-wider">Demo Olayları</p>
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

function getGreeting(hour) {
  if (hour < 6)  return { label: "İyi geceler",  Icon: Moon,    color: "text-indigo-500" };
  if (hour < 12) return { label: "Günaydın",     Icon: Sunrise, color: "text-amber-500" };
  if (hour < 18) return { label: "İyi günler",   Icon: Sun,     color: "text-yellow-500" };
  if (hour < 22) return { label: "İyi akşamlar", Icon: Sunset,  color: "text-orange-500" };
  return            { label: "İyi geceler",      Icon: Moon,    color: "text-indigo-500" };
}

export default function DashboardPanel() {
  const [weeksAgo, setWeeksAgo] = useState(0);
  const { data, loading, error, refresh } = useDashboard(weeksAgo);
  const { user } = useAuth();
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30 * 1000);
    return () => clearInterval(id);
  }, []);
  const greeting = getGreeting(now.getHours());
  const firstName = user?.full_name?.split(" ")[0] ?? "Operatör";

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-[1400px] mx-auto px-6 py-6 space-y-10">

        {/* Zone 1 — Editorial header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950"
          style={{ padding: "32px 40px", borderRadius: "16px" }}
        >
          {/* Atmospheric orbs */}
          <div className="absolute -top-20 -right-20 w-80 h-80 bg-yellow-500/[0.12] rounded-full blur-[100px] pointer-events-none" />
          <div className="absolute -bottom-24 -left-16 w-96 h-96 bg-emerald-600/[0.10] rounded-full blur-[120px] pointer-events-none" />
          {/* Faint dotted grid */}
          <div
            className="absolute inset-0 opacity-[0.05] pointer-events-none"
            style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "28px 28px" }}
          />

          <div className="relative z-10 flex flex-col sm:flex-row sm:items-end justify-between gap-5">
            <div className="min-w-0">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 mb-4">
                <span className="relative flex w-1.5 h-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400" />
                </span>
                <span className="text-[10px] font-bold text-yellow-300 tracking-[0.22em] uppercase">
                  Canlı · 4/4 ajan
                </span>
              </div>

              <div className="flex items-center gap-3 mb-1">
                <greeting.Icon className={`w-5 h-5 ${greeting.color}`} />
                <span className="text-[18px] font-semibold text-slate-300">{greeting.label}, {firstName}.</span>
              </div>
              <h1 className="text-[32px] sm:text-[38px] lg:text-[42px] font-black text-white tracking-tight leading-[1.05] mt-1">
                <span className="bg-gradient-to-r from-yellow-300 via-amber-200 to-emerald-300 bg-clip-text text-transparent">
                  Harman
                </span>
                <span className="text-white"> · Operasyon Merkezi</span>
              </h1>
              <p className="text-[12.5px] font-medium text-slate-400 mt-3 flex items-center gap-2 flex-wrap">
                <span>Anadolu Tarım ve Gıda Kooperatifi</span>
                <span className="w-1 h-1 rounded-full bg-slate-600 shrink-0" />
                <span className="font-mono">{now.toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long" })}</span>
              </p>
            </div>
            <div className="shrink-0">
              <SimulateButton onEvent={refresh} />
            </div>
          </div>
        </motion.div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl px-4 py-3 text-[12px] font-medium">
            Bağlantı hatası: {error}
          </div>
        )}

        {/* Zone 2 — Today's Operational Brief */}
        <TodayBriefSection data={data} loading={loading} />

        {/* Zone 3 — Sabah özeti (rol-bazlı, AI üretimli) */}
        <DailyBriefingCard />

        {/* Zone 4 — KPIs */}
        <KpiGrid data={data} loading={loading} />

        {/* Zone 5 — AI aksiyon: tedarikçi e-posta taslakları */}
        <SupplierDraftsPanel />

        {/* Zone 6 — Bugünkü mesajlar */}
        <TodayMessagesCard data={data} loading={loading} />

        {/* Zone 7 — Analytics */}
        <div className="pt-6 border-t border-slate-100/80">
          <AnalyticsSection
            data={data}
            loading={loading}
            weeksAgo={weeksAgo}
            setWeeksAgo={setWeeksAgo}
          />
        </div>

        {/* Zone 8 — Activity Feed */}
        <div className="pt-6 border-t border-slate-100/80">
          <ActivityFeed data={data} loading={loading} />
        </div>

        {/* Zone 7 — AI Insights (deep analysis, below charts) */}
        <div className="pt-6 border-t border-slate-100/80">
          <AIInsightsSection loading={loading} />
        </div>

      </div>
    </div>
  );
}
