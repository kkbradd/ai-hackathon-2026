import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Sparkles, Brain, AlertTriangle, Package, Truck,
  TrendingDown, MessageSquare, X, ChevronRight, Zap, Activity
} from "lucide-react";

const ALERT_ICONS = {
  delayed_shipment: Truck,
  low_stock: Package,
  complaint: MessageSquare,
  anomaly: Zap,
  carrier_issue: AlertTriangle,
};

const SEVERITY_STYLE = {
  critical: {
    card: "bg-red-50 border-red-100",
    icon: "bg-red-100 text-red-600",
    badge: "bg-red-100 text-red-600",
    dot: "bg-red-500",
    text: "text-red-700",
  },
  warning: {
    card: "bg-amber-50 border-amber-100",
    icon: "bg-amber-100 text-amber-600",
    badge: "bg-amber-100 text-amber-600",
    dot: "bg-amber-400",
    text: "text-amber-700",
  },
  info: {
    card: "bg-blue-50 border-blue-100",
    icon: "bg-blue-100 text-blue-600",
    badge: "bg-blue-100 text-blue-600",
    dot: "bg-blue-500",
    text: "text-blue-700",
  },
};

const INSIGHT_ICONS = [Brain, TrendingDown, Truck, Package, Activity];

function InsightCard({ text, index }) {
  const Icon = INSIGHT_ICONS[index % INSIGHT_ICONS.length];
  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.35 }}
      className="flex gap-3 p-3.5 rounded-xl bg-slate-50 hover:bg-white border border-transparent hover:border-indigo-100 hover:shadow-sm transition-all duration-300 group cursor-default"
    >
      <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-3.5 h-3.5 text-indigo-600" />
      </div>
      <p className="text-[12.5px] text-slate-700 leading-relaxed font-medium flex-1">{text}</p>
    </motion.div>
  );
}

function AlertCard({ alert, onDismiss }) {
  const s = SEVERITY_STYLE[alert.severity] || SEVERITY_STYLE.info;
  const Icon = ALERT_ICONS[alert.type] || AlertTriangle;
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.97, height: 0, marginBottom: 0 }}
      className={`relative flex items-start gap-3 p-3.5 rounded-xl border ${s.card} mb-2.5`}
    >
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${s.icon}`}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${s.dot}`} />
          <span className={`text-[10px] font-bold uppercase tracking-wider ${s.text}`}>{alert.severity}</span>
          {alert.count > 1 && (
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ml-auto ${s.badge}`}>{alert.count}</span>
          )}
        </div>
        <p className={`text-[12px] font-medium leading-relaxed ${s.text}`}>{alert.message}</p>
      </div>
      <button
        onClick={() => onDismiss(alert.type)}
        className="shrink-0 p-0.5 text-slate-300 hover:text-slate-500 transition-colors"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
}

export default function AIInsightsSection({ data, loading }) {
  const navigate = useNavigate();
  const [dismissed, setDismissed] = useState([]);

  const alerts = (data?.alerts || []).filter((a) => !dismissed.includes(a.type));
  const insights = data?.ai_insights || [];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
      {/* AI Insights — wider */}
      <div
        className="xl:col-span-3 bg-white border border-slate-100 rounded-2xl p-5 flex flex-col gap-4 relative overflow-hidden"
        style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}
      >
        <div className="absolute -top-16 -right-16 w-40 h-40 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm shadow-indigo-200">
              <Sparkles className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h3 className="text-[14px] font-bold text-slate-900">AI Operasyon Analizi</h3>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest">Akıllı öngörüler</p>
            </div>
          </div>
          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200">
            Kooperatif verisi
          </span>
        </div>

        {/* Insights */}
        <div className="flex-1 space-y-2 overflow-auto custom-scrollbar">
          {loading
            ? Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-14 animate-shimmer rounded-xl" />
              ))
            : insights.length > 0
            ? insights.map((text, i) => <InsightCard key={i} text={text} index={i} />)
            : (
              <div className="py-10 text-center">
                <Sparkles className="w-8 h-8 text-slate-200 mx-auto mb-2" />
                <p className="text-[12px] text-slate-400 font-medium">Şu an yeni operasyonel içgörü bulunmuyor.</p>
              </div>
            )}
        </div>

        {/* CTA */}
        <button
          onClick={() => navigate("/chat")}
          className="w-full text-[13px] font-bold text-white bg-indigo-600 hover:bg-indigo-700 py-3 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm shadow-indigo-200"
        >
          <Brain className="w-4 h-4" /> AI Asistanını Aç
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Risk Cards — narrower */}
      <div className="xl:col-span-2 flex flex-col gap-0">
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <h3 className="text-[14px] font-bold text-slate-900">Operasyonel Riskler</h3>
          {alerts.length > 0 && (
            <span className="ml-auto text-[10px] font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
              {alerts.length} aktif
            </span>
          )}
        </div>
        <div className="flex-1 overflow-auto custom-scrollbar">
          <AnimatePresence>
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-16 animate-shimmer rounded-xl mb-2.5" />
                ))
              : alerts.length > 0
              ? alerts.map((alert) => (
                  <AlertCard
                    key={alert.type}
                    alert={alert}
                    onDismiss={(type) => setDismissed((d) => [...d, type])}
                  />
                ))
              : (
                <div className="py-10 text-center">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center mx-auto mb-2">
                    <Sparkles className="w-5 h-5 text-emerald-500" />
                  </div>
                  <p className="text-[12px] text-slate-400 font-medium">Aktif risk uyarısı yok.</p>
                </div>
              )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
