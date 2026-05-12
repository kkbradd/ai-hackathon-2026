import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Sparkles, Brain, Package, Truck,
  TrendingDown, X, ChevronRight, Activity,
} from "lucide-react";
import useInsights from "../../hooks/useInsights";
import AgentActivityLog from "./AgentActivityLog";

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
  positive: {
    card: "bg-emerald-50 border-emerald-100",
    icon: "bg-emerald-100 text-emerald-600",
    badge: "bg-emerald-100 text-emerald-600",
    dot: "bg-emerald-500",
    text: "text-emerald-700",
  },
};

const INSIGHT_ICONS = [Brain, TrendingDown, Truck, Package, Activity];

const AGENT_LABELS = {
  operational:    "Operasyon",
  shipment:       "Kargo",
  inventory:      "Envanter",
  customer_issue: "Müşteri",
};

const AGENT_COLORS = {
  operational:    "bg-violet-100 text-violet-600",
  shipment:       "bg-blue-100 text-blue-600",
  inventory:      "bg-amber-100 text-amber-700",
  customer_issue: "bg-rose-100 text-rose-600",
};

function InsightCard({ insight, index, onDismiss }) {
  const Icon = INSIGHT_ICONS[index % INSIGHT_ICONS.length];
  const s = SEVERITY_STYLE[insight.severity] || SEVERITY_STYLE.info;
  const agentLabel = AGENT_LABELS[insight.agent_name] || insight.agent_name;
  const agentColor = AGENT_COLORS[insight.agent_name] || "bg-slate-100 text-slate-500";

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -12, height: 0, marginBottom: 0 }}
      transition={{ delay: index * 0.06, duration: 0.3 }}
      className="flex gap-3 p-3.5 rounded-xl bg-slate-50 hover:bg-white border border-transparent hover:border-indigo-100 hover:shadow-sm transition-all duration-300 group"
    >
      <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-3.5 h-3.5 text-indigo-600" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-1">
          <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full ${s.badge}`}>
            {insight.severity}
          </span>
          <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full ${agentColor}`}>
            {agentLabel}
          </span>
          {insight.created_at && (
            <span className="text-[9px] text-slate-400 ml-auto">{insight.created_at}</span>
          )}
        </div>
        <p className="text-[12.5px] text-slate-700 leading-relaxed font-medium">
          {insight.content}
        </p>
      </div>
      <button
        onClick={() => onDismiss(insight.id)}
        className="shrink-0 p-0.5 text-slate-300 hover:text-slate-500 transition-colors opacity-0 group-hover:opacity-100"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
}

export default function AIInsightsSection({ loading: dashLoading }) {
  const navigate = useNavigate();
  const { insights, loading: insightsLoading, dismiss } = useInsights();

  const loading = dashLoading || insightsLoading;

  return (
    <div>
      <div
        className="bg-white border border-slate-100 rounded-2xl p-5 flex flex-col gap-4 relative overflow-hidden"
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
          <AnimatePresence>
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-14 animate-shimmer rounded-xl" />
                ))
              : insights.length > 0
              ? insights.map((insight, i) => (
                  <InsightCard key={insight.id} insight={insight} index={i} onDismiss={dismiss} />
                ))
              : (
                <div className="py-10 text-center">
                  <Sparkles className="w-8 h-8 text-slate-200 mx-auto mb-2" />
                  <p className="text-[12px] text-slate-400 font-medium">
                    AI ajanları içgörü üretiyor, lütfen bekleyin…
                  </p>
                </div>
              )}
          </AnimatePresence>
        </div>

        {/* Agent Activity Log */}
        <AgentActivityLog />

        {/* CTA */}
        <button
          onClick={() => navigate("/chat")}
          className="w-full text-[13px] font-bold text-white bg-indigo-600 hover:bg-indigo-700 py-3 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm shadow-indigo-200"
        >
          <Brain className="w-4 h-4" /> AI Asistanını Aç
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
