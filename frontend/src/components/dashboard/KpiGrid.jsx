import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Truck, AlertTriangle, ClipboardList, Package,
  MessageSquare, CheckCircle, TrendingUp, Minus
} from "lucide-react";

const KPIS = [
  {
    key: "delayed_shipments",
    label: "Gecikmiş Kargo",
    sub: "Tahmini tarihi aşan",
    icon: AlertTriangle,
    color: "red",
    route: "/shipments",
  },
  {
    key: "pending_orders",
    label: "Bugünkü Sipariş",
    sub: "Bugün gelen yeni",
    icon: ClipboardList,
    color: "amber",
    route: "/orders",
  },
  {
    key: "active_shipments",
    label: "Aktif Teslimat",
    sub: "Yolda veya şubede",
    icon: Truck,
    color: "blue",
    route: "/shipments",
  },
  {
    key: "low_stock_products",
    label: "Stok Uyarısı",
    sub: "Kritik seviyede",
    icon: Package,
    color: "orange",
    route: "/inventory",
  },
  {
    key: "unread_messages",
    label: "Müşteri Mesajı",
    sub: "Okunmamış",
    icon: MessageSquare,
    color: "violet",
    route: "/messages",
  },
  {
    key: "on_time_delivery_rate",
    label: "Zamanında Teslim",
    sub: "Genel oran",
    icon: CheckCircle,
    color: "emerald",
    route: null,
    isPercent: true,
  },
];

const COLOR = {
  red:     { iconBg: "bg-red-50",     iconText: "text-red-600",     val: "text-red-600"     },
  amber:   { iconBg: "bg-amber-50",   iconText: "text-amber-600",   val: "text-amber-600"   },
  blue:    { iconBg: "bg-blue-50",    iconText: "text-blue-600",    val: "text-slate-900"   },
  orange:  { iconBg: "bg-orange-50",  iconText: "text-orange-600",  val: "text-orange-600"  },
  violet:  { iconBg: "bg-violet-50",  iconText: "text-violet-600",  val: "text-slate-900"   },
  emerald: { iconBg: "bg-emerald-50", iconText: "text-emerald-600", val: "text-emerald-600" },
};

function TrendBadge({ value, isPercent }) {
  if (typeof value !== "number") return null;
  const isGood = isPercent ? value >= 90 : value === 0;
  const isWarn = !isPercent && value > 0;
  if (isGood) return (
    <span className="inline-flex items-center gap-1 text-[9.5px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded uppercase tracking-wide">
      <CheckCircle className="w-2.5 h-2.5" /> Normal
    </span>
  );
  if (isWarn) return (
    <span className="inline-flex items-center gap-1 text-[9.5px] font-bold text-red-700 bg-red-50 px-1.5 py-0.5 rounded uppercase tracking-wide">
      <TrendingUp className="w-2.5 h-2.5" /> Dikkat
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1 text-[9.5px] font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded uppercase tracking-wide">
      <Minus className="w-2.5 h-2.5" /> İzleniyor
    </span>
  );
}

function KpiCell({ cfg, value, index }) {
  const navigate = useNavigate();
  const { icon: Icon, label, sub, color, route, isPercent } = cfg;
  const c = COLOR[color];
  const displayValue = typeof value === "number"
    ? isPercent ? `%${value}` : value
    : "—";

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      onClick={route ? () => navigate(route) : undefined}
      disabled={!route}
      className={`group relative flex flex-col items-start gap-2 p-5 text-left ${route ? "cursor-pointer hover:bg-slate-50/60" : "cursor-default"} transition-colors`}
    >
      <div className="flex items-center gap-2.5 w-full">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${c.iconBg}`}>
          <Icon className={`w-4 h-4 ${c.iconText}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[10.5px] font-bold text-slate-400 uppercase tracking-[0.14em] truncate">{label}</p>
          <p className="text-[10px] text-slate-400 truncate">{sub}</p>
        </div>
      </div>
      <div className="flex items-baseline gap-2 mt-1">
        <p className={`text-[28px] font-black tabular-nums tracking-tight leading-none ${c.val}`}>{displayValue}</p>
        <TrendBadge value={value} isPercent={isPercent} />
      </div>
    </motion.button>
  );
}

function SkeletonCell() {
  return (
    <div className="p-5 animate-pulse">
      <div className="flex items-center gap-2.5 mb-3">
        <div className="w-9 h-9 rounded-xl bg-slate-100" />
        <div className="flex-1 space-y-1">
          <div className="h-2 bg-slate-100 rounded w-2/3" />
          <div className="h-2 bg-slate-100 rounded w-1/2" />
        </div>
      </div>
      <div className="h-7 bg-slate-100 rounded w-12" />
    </div>
  );
}

export default function KpiGrid({ data, loading }) {
  return (
    <div
      className="bg-white border border-slate-200/80 shadow-sm overflow-hidden"
      style={{ borderRadius: "16px" }}
    >
      <div className="px-6 py-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/40">
        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.18em]">
          Operasyon Göstergeleri
        </p>
        <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
          Karta tıkla → detay
        </p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 divide-y md:divide-y-0 md:divide-x divide-slate-100">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <SkeletonCell key={i} />)
          : KPIS.map((cfg, i) => (
              <KpiCell key={cfg.key} cfg={cfg} value={data?.[cfg.key]} index={i} />
            ))}
      </div>
    </div>
  );
}
