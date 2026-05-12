import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Truck, AlertTriangle, ClipboardList, Package,
  MessageSquare, CheckCircle, TrendingUp, TrendingDown, Minus
} from "lucide-react";

const KPIS = [
  {
    key: "delayed_shipments",
    label: "Gecikmiş Kargo",
    sub: "Tahmini tarihi aşan",
    icon: AlertTriangle,
    color: "red",
    route: "/shipments",
    insight: "Acil müdahale gerekiyor",
  },
  {
    key: "pending_orders",
    label: "Bugünkü Siparişler",
    sub: "Bugün gelen yeni siparişler",
    icon: ClipboardList,
    color: "amber",
    route: "/orders",
    insight: "Öncelikli işleme alın",
  },
  {
    key: "active_shipments",
    label: "Aktif Teslimat",
    sub: "Yolda veya şubede",
    icon: Truck,
    color: "blue",
    route: "/shipments",
    insight: "Lojistik ağında olan sevkiyatlar",
  },
  {
    key: "low_stock_products",
    label: "Stok Uyarısı",
    sub: "Kritik seviyede ürün",
    icon: Package,
    color: "orange",
    route: "/inventory",
    insight: "Yenileme öneriliyor",
  },
  {
    key: "unread_messages",
    label: "Müşteri Mesajı",
    sub: "Okunmamış talepler",
    icon: MessageSquare,
    color: "violet",
    route: "/messages",
    insight: "Yanıt bekleniyor",
  },
  {
    key: "on_time_delivery_rate",
    label: "Zamanında Teslimat",
    sub: "Aktif kargolarda gecikme yok",
    icon: CheckCircle,
    color: "emerald",
    route: null,
    isPercent: true,
    insight: "Operasyonel sağlık",
  },
];

const COLOR = {
  red:     { bg: "bg-red-50",     icon: "bg-red-100 text-red-600",     val: "text-red-600",     badge: "bg-red-100 text-red-600",     border: "border-red-100"     },
  amber:   { bg: "bg-amber-50",   icon: "bg-amber-100 text-amber-600", val: "text-amber-600",   badge: "bg-amber-100 text-amber-600", border: "border-amber-100"   },
  blue:    { bg: "bg-blue-50",    icon: "bg-blue-100 text-blue-600",   val: "text-slate-900",   badge: "bg-blue-100 text-blue-600",   border: "border-slate-100"   },
  orange:  { bg: "bg-orange-50",  icon: "bg-orange-100 text-orange-600", val: "text-orange-600", badge: "bg-orange-100 text-orange-600", border: "border-orange-100" },
  violet:  { bg: "bg-violet-50",  icon: "bg-violet-100 text-violet-600", val: "text-slate-900",  badge: "bg-violet-100 text-violet-600", border: "border-slate-100"  },
  emerald: { bg: "bg-emerald-50", icon: "bg-emerald-100 text-emerald-600", val: "text-emerald-600", badge: "bg-emerald-100 text-emerald-600", border: "border-emerald-100" },
};

function TrendBadge({ value, isPercent }) {
  if (typeof value !== "number") return null;
  const isGood = isPercent ? value >= 90 : value === 0;
  const isWarn = !isPercent && value > 0;
  if (isGood) return (
    <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
      <CheckCircle className="w-3 h-3" /> Normal
    </span>
  );
  if (isWarn) return (
    <span className="flex items-center gap-1 text-[11px] font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
      <TrendingUp className="w-3 h-3" /> Dikkat
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
      <Minus className="w-3 h-3" /> İzleniyor
    </span>
  );
}

function KpiCard({ cfg, value, index }) {
  const navigate = useNavigate();
  const { icon: Icon, label, sub, color, route, isPercent, insight } = cfg;
  const c = COLOR[color];
  const displayValue = typeof value === "number"
    ? isPercent ? `%${value}` : value
    : "—";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      onClick={route ? () => navigate(route) : undefined}
      className={`bg-white border ${c.border} rounded-2xl p-5 flex flex-col gap-4 ${route ? "cursor-pointer hover:shadow-md hover:-translate-y-0.5" : ""} transition-all duration-200`}
      style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}
    >
      <div className="flex items-start justify-between">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${c.icon}`}>
          <Icon className="w-5 h-5" />
        </div>
        <TrendBadge value={value} isPercent={isPercent} />
      </div>
      <div>
        <p className={`text-3xl font-black tabular-nums tracking-tight ${c.val}`}>{displayValue}</p>
        <p className="text-[13px] font-semibold text-slate-700 mt-1">{label}</p>
        <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>
      </div>
      <div className={`text-[11px] font-medium px-2.5 py-1.5 rounded-lg ${c.bg} ${c.val} self-start`}>
        {insight}
      </div>
    </motion.div>
  );
}

function SkeletonKpi() {
  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5 flex flex-col gap-4 animate-shimmer">
      <div className="w-10 h-10 rounded-xl bg-slate-100" />
      <div>
        <div className="h-8 bg-slate-100 rounded-lg w-16 mb-2" />
        <div className="h-4 bg-slate-50 rounded w-28" />
      </div>
    </div>
  );
}

export default function KpiGrid({ data, loading }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {loading
        ? Array.from({ length: 6 }).map((_, i) => <SkeletonKpi key={i} />)
        : KPIS.map((cfg, i) => (
            <KpiCard key={cfg.key} cfg={cfg} value={data?.[cfg.key]} index={i} />
          ))}
    </div>
  );
}
