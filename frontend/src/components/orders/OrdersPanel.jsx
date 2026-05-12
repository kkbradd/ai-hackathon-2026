import { motion } from "framer-motion";
import { Search, ClipboardList } from "lucide-react";
import { format, parse } from "date-fns";
import { tr } from "date-fns/locale";
import { useState } from "react";
import { useOrders } from "../../hooks/useOrders";

const DATE_FILTERS = [
  { value: "today", label: "Bugün" },
  { value: "week",  label: "Bu Hafta" },
  { value: "all",   label: "Tümü" },
];

function getInitials(name = "") {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatDate(dateStr) {
  try {
    const d = parse(dateStr, "dd.MM.yyyy HH:mm", new Date());
    return format(d, "d MMM yyyy", { locale: tr });
  } catch {
    return dateStr ?? "—";
  }
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 px-6 py-4 border-b border-slate-100 animate-pulse">
      <div className="flex items-center gap-3 flex-1">
        <div className="w-8 h-8 rounded-lg bg-slate-100 shrink-0" />
        <div>
          <div className="h-3.5 bg-slate-200 rounded w-32 mb-1.5" />
          <div className="h-3 bg-slate-100 rounded w-20" />
        </div>
      </div>
      <div className="w-20 h-3.5 bg-slate-100 rounded ml-auto" />
      <div className="w-24 h-4 bg-slate-200 rounded" />
      <div className="w-24 h-3 bg-slate-100 rounded hidden sm:block" />
    </div>
  );
}

export default function OrdersPanel() {
  const { orders, meta, loading, error, dateFilter, setDateFilter, search, setSearch } = useOrders();
  const [customerType, setCustomerType] = useState("kurumsal");

  const filteredOrders = orders.filter((o) => o.customer_type === customerType);

  return (
    <div className="flex flex-col h-full bg-transparent">
      {/* Üst araç çubuğu — arama tablo başlığıyla çakışmaz */}
      <div className="bg-white border-b border-slate-200 px-4 sm:px-6 pt-4 pb-3 shrink-0 z-30 shadow-sm relative">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h2 className="text-[18px] font-extrabold text-slate-900 tracking-tight text-center sm:text-left">
            Siparişler
          </h2>
          {!loading && (
            <div className="flex flex-wrap items-center justify-center sm:justify-end gap-2">
              <span className="text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 px-2.5 py-1 rounded-lg tabular-nums">
                Açık hat: {meta.pending_pipeline}
              </span>
              <span className="text-[11px] font-bold bg-slate-100 text-slate-600 border border-slate-200 px-2.5 py-1 rounded-lg tabular-nums">
                Listede: {filteredOrders.length}
              </span>
            </div>
          )}
        </div>

        {/* Kurumsal / Bireysel — ortalanmış, ayrı düğmeler */}
        <div className="flex justify-center w-full mb-4">
          <div
            className="inline-flex items-center gap-4 bg-slate-100 p-1.5 rounded-2xl"
            role="group"
            aria-label="Müşteri tipi"
          >
            <button
              type="button"
              onClick={() => setCustomerType("kurumsal")}
              className={`min-w-[7.5rem] px-4 py-2 text-xs font-bold rounded-xl transition-all ${
                customerType === "kurumsal"
                  ? "bg-white text-indigo-700 shadow-sm border border-slate-200/80"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Kurumsal
            </button>
            <button
              type="button"
              onClick={() => setCustomerType("bireysel")}
              className={`min-w-[7.5rem] px-4 py-2 text-xs font-bold rounded-xl transition-all ${
                customerType === "bireysel"
                  ? "bg-white text-indigo-700 shadow-sm border border-slate-200/80"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Bireysel
            </button>
          </div>
        </div>

        <div className="max-w-md mx-auto w-full mb-4 relative isolate">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10"
            aria-hidden
          />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Müşteri veya sipariş no ara…"
            className="w-full pl-10 pr-4 py-2.5 text-[13px] font-medium bg-white border border-slate-300 text-slate-800 placeholder-slate-400 rounded-xl outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 shadow-sm transition-all"
          />
        </div>

        {!loading && (
          <p className="text-center text-[11px] text-slate-500 mb-3 px-2">
            <span className="font-bold text-slate-700 tabular-nums">{meta.total_matching_filter}</span>{" "}
            sipariş kayıtlı. Liste kurumsal/bireysel ve arama ile süzülür.
          </p>
        )}

        <div className="flex gap-2 flex-wrap justify-center pb-1">
          {DATE_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setDateFilter(f.value)}
              className={`text-[12px] font-semibold px-3 py-1.5 rounded-lg border transition-all ${
                dateFilter === f.value
                  ? "bg-indigo-50 text-indigo-700 border-indigo-200 shadow-sm"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50 shadow-sm"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="sticky top-0 z-20 flex items-center gap-4 px-6 py-3 bg-slate-50 border-b border-slate-200 shrink-0">
        <div className="flex-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider">Müşteri</div>
        <div className="w-20 text-[11px] font-bold text-slate-500 uppercase tracking-wider text-right">Kalem</div>
        <div className="w-28 text-[11px] font-bold text-slate-500 uppercase tracking-wider text-right">Toplam</div>
        <div className="w-28 text-[11px] font-bold text-slate-500 uppercase tracking-wider text-right hidden sm:block">
          Tarih
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-white">
        {error && (
          <div className="p-4 text-[13px] font-medium text-red-700 bg-red-50 border-b border-red-200">{error}</div>
        )}

        {loading && Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)}

        {!loading && !error && (
          <>
            {filteredOrders.map((order) => (
              <motion.div
                key={order.order_id}
                whileHover={{ x: 2 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
                className="flex items-center gap-4 px-6 py-4 border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 border border-indigo-200 flex items-center justify-center text-indigo-700 text-[12px] font-extrabold shrink-0">
                    {getInitials(order.customer)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-[14px] font-bold text-slate-800 truncate">{order.customer}</p>
                    <p className="text-[11px] font-medium text-slate-500 mt-0.5 font-mono">#{order.order_id}</p>
                  </div>
                </div>

                <div className="w-20 text-right shrink-0">
                  <span className="text-[13px] font-semibold text-slate-600 tabular-nums">{order.item_count} kalem</span>
                </div>

                <div className="w-28 text-right shrink-0">
                  <span className="text-[15px] font-extrabold text-slate-900 tabular-nums">
                    ₺{order.total?.toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <div className="w-28 text-right shrink-0 hidden sm:block">
                  <span className="text-[12px] font-medium text-slate-500">{formatDate(order.created_at)}</span>
                </div>
              </motion.div>
            ))}

            {filteredOrders.length === 0 && (
              <div className="flex flex-col items-center justify-center py-24">
                <ClipboardList className="w-12 h-12 text-slate-300 mb-4" />
                <p className="text-[15px] font-medium text-slate-500">Bu filtreye ait sipariş bulunamadı.</p>
              </div>
            )}
          </>
        )}
      </div>

      {!loading && !error && (
        <div className="border-t border-slate-200 bg-slate-50 px-6 py-3 text-[12px] font-semibold text-slate-500 shrink-0 text-center sm:text-left">
          {filteredOrders.length} sipariş gösteriliyor
        </div>
      )}
    </div>
  );
}
