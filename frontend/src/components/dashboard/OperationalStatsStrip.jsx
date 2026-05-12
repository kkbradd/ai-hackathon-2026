import { motion } from "framer-motion";
import { Landmark, Percent, Activity, BadgeTurkishLira } from "lucide-react";

export default function OperationalStatsStrip({ data, loading }) {
  if (loading || !data) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 rounded-2xl bg-white border border-slate-100" />
        ))}
      </div>
    );
  }

  const items = [
    {
      Icon: Landmark,
      label: "Toplam ciro",
      value: `₺${Number(data.revenue_total || 0).toLocaleString("tr-TR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })}`,
      sub: "Tüm zamanlar",
      tone: "text-indigo-600 bg-indigo-50 border-indigo-100",
    },
    {
      Icon: BadgeTurkishLira,
      label: "Bugün ciro",
      value: `₺${Number(data.revenue_today || 0).toLocaleString("tr-TR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })}`,
      sub: `${data.orders_today ?? 0} sipariş`,
      tone: "text-emerald-600 bg-emerald-50 border-emerald-100",
    },
    {
      Icon: Percent,
      label: "Aktif sevkiyatta gecikme",
      value: `%${data.shipment_delay_ratio ?? 0}`,
      sub: "Aktif ağ içindeki pay",
      tone: "text-amber-700 bg-amber-50 border-amber-100",
    },
    {
      Icon: Activity,
      label: "Envanter sağlığı",
      value: `${data.inventory_health_score ?? "—"}`,
      sub: "0–100 · tüm ürün stoklarından",
      tone: "text-violet-600 bg-violet-50 border-violet-100",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {items.map((item, i) => {
        const Icon = item.Icon;
        return (
        <motion.div
          key={item.label}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06, duration: 0.35 }}
          className={`rounded-2xl border px-4 py-3 flex gap-3 items-start ${item.tone}`}
          style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}
        >
          <div className="p-2 rounded-xl bg-white/70 border border-white/80 shrink-0">
            <Icon className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider opacity-85">{item.label}</p>
            <p className="text-lg font-black tabular-nums tracking-tight mt-0.5 text-slate-900">{item.value}</p>
            <p className="text-[10px] font-semibold opacity-75 mt-0.5 truncate">{item.sub}</p>
          </div>
        </motion.div>
        );
      })}
    </div>
  );
}
