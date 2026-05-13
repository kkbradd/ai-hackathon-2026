import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Package, AlertTriangle, TrendingDown, RefreshCw,
  CheckCircle, ArrowDown, Info, DollarSign, Box, Zap
} from "lucide-react";
import { useInventory } from "../hooks/useInventory";
import { triggerSimulationEvent } from "../api/client";

function StockBar({ pct, isCritical, isLow }) {
  const color = isCritical
    ? "bg-red-500"
    : isLow
    ? "bg-amber-500"
    : "bg-emerald-500";
  const clamped = Math.min(100, Math.max(0, pct));
  return (
    <div className="h-2 bg-slate-100 rounded-full overflow-hidden mt-3 shadow-inner">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${clamped}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className={`h-full rounded-full ${color}`}
      />
    </div>
  );
}

function StatusBadge({ isCritical, isLow }) {
  if (isCritical) {
    return (
      <span className="flex items-center gap-1.5 text-[10px] font-bold text-red-700 bg-red-100 border border-red-200 px-2.5 py-1 rounded-full shadow-sm">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        KRİTİK
      </span>
    );
  }
  if (isLow) {
    return (
      <span className="flex items-center gap-1.5 text-[10px] font-bold text-amber-700 bg-amber-100 border border-amber-200 px-2.5 py-1 rounded-full shadow-sm">
        <ArrowDown className="w-3 h-3" />
        DÜŞÜK STOK
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-700 bg-emerald-100 border border-emerald-200 px-2.5 py-1 rounded-full shadow-sm">
      <CheckCircle className="w-3 h-3" />
      STOK NORMAL
    </span>
  );
}

function ProductCard({ item, index, view }) {
  const isStockView = view === "stock";
  const borderClass = isStockView && item.is_critical
    ? "border-red-200 bg-white"
    : isStockView && item.is_low_stock
    ? "border-amber-200 bg-white"
    : "border-slate-200 bg-white";

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={`relative border rounded-3xl p-6 shadow-sm hover:shadow-md transition-shadow ${borderClass}`}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-[11px] font-bold text-indigo-600 uppercase tracking-widest mb-1">{item.category}</p>
          <h3 className="text-[16px] font-extrabold text-slate-900 leading-tight">{item.product_name}</h3>
        </div>
        <div className={`p-2 rounded-xl ${item.is_critical ? 'bg-red-50' : item.is_low_stock ? 'bg-amber-50' : 'bg-slate-50'}`}>
          {isStockView ? (
            item.is_critical ? <AlertTriangle className="w-4 h-4 text-red-500" /> : 
            item.is_low_stock ? <TrendingDown className="w-4 h-4 text-amber-500" /> : 
            <Package className="w-4 h-4 text-slate-400" />
          ) : (
            <Info className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {isStockView ? (
          <motion.div
            key="stock"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
          >
            <div className="flex items-baseline gap-2 mb-1">
              <span className={`text-[32px] font-black tabular-nums leading-none ${item.is_critical ? "text-red-600" : item.is_low_stock ? "text-amber-600" : "text-slate-900"}`}>
                {item.quantity_kg}
              </span>
              <span className="text-[14px] font-bold text-slate-500 uppercase">{item.unit}</span>
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">
              Min: {item.min_threshold} {item.unit} · Hedef: {item.reorder_point} {item.unit}
            </p>
            <StockBar pct={item.stock_percentage} isCritical={item.is_critical} isLow={item.is_low_stock} />
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
              <StatusBadge isCritical={item.is_critical} isLow={item.is_low_stock} />
              <p className="text-[10px] font-bold text-slate-400">{item.last_updated}</p>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="info"
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Paketleme</p>
                <div className="flex items-center gap-2">
                  <Box className="w-3.5 h-3.5 text-indigo-500" />
                  <span className="text-[13px] font-extrabold text-slate-700">{item.package_size || "-"}</span>
                </div>
              </div>
              <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Birim Fiyat</p>
                <div className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-[13px] font-extrabold text-slate-700">₺{item.price.toLocaleString("tr-TR")}</span>
                </div>
              </div>
            </div>
            <div className="bg-indigo-50/50 p-3 rounded-2xl border border-indigo-100/50">
              <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-1">Kategori Bazlı Bilgi</p>
              <p className="text-[12px] font-medium text-indigo-900/70">Kooperatif standartlarına uygun {item.category} kategorisindeki ürün.</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function InventorySummaryCard({ count, lowCount, loading }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
      {[
        { label: "Toplam Ürün", value: count, icon: Package, color: "text-indigo-600", bg: "bg-indigo-100" },
        { label: "Stok Uyarısı", value: lowCount, icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-100" },
        { label: "Normal Stok", value: count - lowCount, icon: CheckCircle, color: "text-emerald-600", bg: "bg-emerald-100" },
      ].map(({ label, value, icon: Icon, color, bg }) => (
        <div key={label} className="bg-white border border-slate-200 shadow-sm rounded-3xl p-6 flex items-center gap-5 hover:shadow-md transition-shadow">
          <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${bg}`}>
            <Icon className={`w-6 h-6 ${color}`} />
          </div>
          <div>
            <p className={`text-3xl font-black tabular-nums tracking-tight ${color}`}>
              {loading ? "—" : value}
            </p>
            <p className="text-[11px] font-extrabold text-slate-400 uppercase tracking-widest">{label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function InventoryPage() {
  const { data, loading, error, refresh } = useInventory();
  const [activeTab, setActiveTab] = useState("stock"); // "stock" or "info"
  const [restocking, setRestocking] = useState(false);
  const [restockToast, setRestockToast] = useState(null);

  const handleRestock = async () => {
    setRestocking(true);
    try {
      await triggerSimulationEvent("restock_critical");
      setRestockToast({ ok: true, msg: "Kritik stoklar dolduruldu." });
      refresh();
    } catch {
      setRestockToast({ ok: false, msg: "İşlem başarısız oldu." });
    } finally {
      setRestocking(false);
      setTimeout(() => setRestockToast(null), 3000);
    }
  };

  return (
    <div className="h-full overflow-auto bg-slate-50/30">
      <div className="max-w-6xl mx-auto px-8 py-10">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-8 mb-14">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">Envanter Yönetimi</h1>
            <p className="text-sm font-semibold text-slate-500 mt-2 flex flex-wrap items-center gap-2">
              Kooperatif Stok ve Ürün Kataloğu{" "}
              <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0" />{" "}
              {loading ? "Veriler çekiliyor..." : `${data?.count ?? 0} aktif ürün`}
            </p>
          </div>

          <div className="relative flex flex-wrap items-center gap-3 shrink-0">
            {restockToast && (
              <div className={`absolute -top-10 right-0 text-[11px] font-semibold px-3 py-1.5 rounded-lg shadow-md whitespace-nowrap z-50 ${restockToast.ok ? "bg-emerald-600 text-white" : "bg-red-600 text-white"}`}>
                {restockToast.msg}
              </div>
            )}
            {(data?.low_stock_count ?? 0) > 0 && (
              <button
                onClick={handleRestock}
                disabled={restocking}
                className="flex items-center gap-2 px-4 py-2.5 text-[12px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 rounded-2xl transition-all shadow-sm disabled:opacity-60"
              >
                {restocking
                  ? <RefreshCw className="w-4 h-4 animate-spin" />
                  : <Zap className="w-4 h-4" />}
                Kritik Stokları Doldur
              </button>
            )}
            <button
              onClick={refresh}
              className="p-3 bg-white border border-slate-200 shadow-sm hover:bg-slate-50 rounded-2xl transition-all hover:rotate-180 duration-500"
              title="Yenile"
            >
              <RefreshCw className="w-5 h-5 text-slate-600" />
            </button>
          </div>
        </div>

        <div className="mb-14 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Görünüm seçimi</p>
            <div className="bg-white border border-slate-200 p-1.5 rounded-2xl inline-flex shadow-sm gap-1">
              <button
                type="button"
                onClick={() => setActiveTab("stock")}
                className={`px-6 py-2.5 text-xs font-black rounded-xl transition-all ${activeTab === "stock" ? "bg-slate-900 text-white shadow-lg" : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"}`}
              >
                Stok Durumu
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("info")}
                className={`px-6 py-2.5 text-xs font-black rounded-xl transition-all ${activeTab === "info" ? "bg-slate-900 text-white shadow-lg" : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"}`}
              >
                Ürün Bilgileri
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-3xl p-5 text-sm font-bold mb-10 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            {error}
          </div>
        )}

        {/* Summary cards */}
        <InventorySummaryCard
          count={data?.count ?? 0}
          lowCount={data?.low_stock_count ?? 0}
          loading={loading}
        />

        {/* Low stock alert strip (only in stock view) */}
        {activeTab === "stock" && !loading && (data?.low_stock_count ?? 0) > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-amber-50 to-white border border-amber-200 shadow-sm rounded-3xl p-8 mb-14 flex flex-col sm:flex-row sm:items-center gap-4 mt-10"
          >
            <div className="w-10 h-10 bg-amber-100 rounded-2xl flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            </div>
            <p className="text-sm font-bold text-amber-900">
              <span className="text-xl font-black mr-2">{data.low_stock_count} Ürün</span> 
              kritik seviyenin altında. Tedarik zinciri aksiyonu gerekiyor.
            </p>
          </motion.div>
        )}

        {/* Product grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-4">
          {loading
            ? Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-64 bg-white border border-slate-100 rounded-3xl shadow-sm animate-pulse" />
              ))
            : data?.items?.map((item, i) => (
                <ProductCard key={item.id} item={item} index={i} view={activeTab} />
              ))}
        </div>

        {!loading && !data?.items?.length && (
          <div className="text-center py-32 bg-white border border-slate-200 rounded-[40px] shadow-sm mt-4">
            <Package className="w-16 h-16 text-slate-200 mx-auto mb-4" />
            <p className="text-slate-400 font-black text-xl tracking-tight">Katalog Boş</p>
            <p className="text-slate-400 text-sm font-medium mt-1">Henüz tanımlı ürün bulunmuyor.</p>
          </div>
        )}

      </div>
    </div>
  );
}
