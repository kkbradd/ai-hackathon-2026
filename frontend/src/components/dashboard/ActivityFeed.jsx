import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Truck, Star, ChevronRight } from "lucide-react";

const STAGES = [
  { key: "preparing",        label: "Hazırlanıyor",  color: "bg-slate-400",   bar: "from-slate-400 to-slate-300" },
  { key: "in_transit",       label: "Yolda",          color: "bg-blue-500",    bar: "from-blue-500 to-blue-400" },
  { key: "at_facility",      label: "Şubede",         color: "bg-amber-500",   bar: "from-amber-500 to-amber-400" },
  { key: "out_for_delivery", label: "Dağıtımda",      color: "bg-indigo-500",  bar: "from-indigo-500 to-indigo-400" },
  { key: "delivered",        label: "Teslim Edildi",  color: "bg-emerald-500", bar: "from-emerald-500 to-emerald-400" },
  { key: "delayed",          label: "Gecikmiş",       color: "bg-red-500",     bar: "from-red-500 to-red-400" },
];

function ShipmentPipeline({ distribution, loading }) {
  const navigate = useNavigate();
  // `delayed` is a cross-cutting count (duplicate of statuses) — omit from denominator
  const d = distribution || {};
  const delayedOnly = d.delayed ?? 0;
  const total =
    ["preparing", "in_transit", "at_facility", "out_for_delivery", "delivered"].reduce(
      (a, k) => a + (d[k] ?? 0),
      0,
    ) || 1;
  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center">
            <Truck className="w-3.5 h-3.5 text-blue-600" />
          </div>
          <div>
            <p className="text-[13px] font-bold text-slate-900">Lojistik Akışı</p>
            <p className="text-[10px] text-slate-400">Anlık sevkiyat adımları</p>
          </div>
        </div>
        <button onClick={() => navigate("/shipments")} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
          <ChevronRight className="w-4 h-4 text-slate-400" />
        </button>
      </div>
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-5 animate-shimmer rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {STAGES.map((s) => {
            const count = (s.key === "delayed" ? delayedOnly : d[s.key]) ?? 0;
            const pct = (count / total) * 100;
            return (
              <div key={s.key} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full shrink-0 ${s.color}`} />
                <span className="text-[11px] font-semibold text-slate-600 w-24 shrink-0">{s.label}</span>
                <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.9, ease: "easeOut" }}
                    className={`h-full rounded-full bg-gradient-to-r ${s.bar}`}
                  />
                </div>
                <span className="text-[11px] font-bold text-slate-700 tabular-nums w-6 text-right shrink-0">{count}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function TopProducts({ products, loading }) {
  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center">
          <Star className="w-3.5 h-3.5 text-amber-600" />
        </div>
        <div>
          <p className="text-[13px] font-bold text-slate-900">Popüler Ürünler</p>
          <p className="text-[10px] text-slate-400">En yüksek talep görenler</p>
        </div>
      </div>
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-10 animate-shimmer rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="space-y-1">
          {(products || []).map((p, i) => (
            <div key={p.product_id} className="flex items-center gap-3 px-2 py-2.5 rounded-xl hover:bg-slate-50 transition-colors">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-50 to-violet-50 border border-indigo-100 flex items-center justify-center text-[10px] font-black text-indigo-600 shrink-0">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-bold text-slate-800 truncate">{p.name}</p>
                <p className="text-[10px] text-slate-400">{p.category}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-[12px] font-bold text-slate-800">{p.order_count} sipariş</p>
                <p className="text-[10px] text-slate-400">₺{Math.round(p.revenue).toLocaleString("tr-TR")}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ActivityFeed({ data, loading }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="mb-1">
        <h2 className="text-[15px] font-bold text-slate-900">Lojistik ve ürün özeti</h2>
        <p className="text-[11px] text-slate-400 mt-1">Sevkiyat dağılımı ve talep sıralaması</p>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <ShipmentPipeline distribution={data?.shipment_distribution} loading={loading} />
        <TopProducts products={data?.top_products} loading={loading} />
      </div>
    </div>
  );
}
