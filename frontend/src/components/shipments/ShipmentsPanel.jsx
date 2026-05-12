import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Truck, X, Package, MapPin, Calendar } from "lucide-react";
import { useShipments } from "../../hooks/useShipments";
import { fetchShipmentDetail } from "../../api/client";
import ShipmentTimeline from "./ShipmentTimeline";

const STATUS_CONFIG = {
  preparing:        { label: "Hazırlanıyor",    cls: "bg-slate-100 text-slate-700 border border-slate-200" },
  in_transit:       { label: "Taşımada",        cls: "bg-blue-100 text-blue-700 border border-blue-200" },
  at_facility:      { label: "Şubede",          cls: "bg-amber-100 text-amber-700 border border-amber-200" },
  out_for_delivery: { label: "Dağıtımda",       cls: "bg-indigo-100 text-indigo-700 border border-indigo-200" },
  delivered:        { label: "Teslim Edildi",   cls: "bg-emerald-100 text-emerald-700 border border-emerald-200" },
  failed:           { label: "Teslim Edilemedi",cls: "bg-red-100 text-red-700 border border-red-200" },
  returned:         { label: "İade Edildi",     cls: "bg-orange-100 text-orange-700 border border-orange-200" },
};

const CARRIER_COLORS = {
  "Yurtiçi Kargo": "bg-orange-100 text-orange-700 border border-orange-200",
  "Aras Kargo":    "bg-emerald-100 text-emerald-700 border border-emerald-200",
  "MNG Kargo":     "bg-blue-100 text-blue-700 border border-blue-200",
  "PTT Kargo":     "bg-yellow-100 text-yellow-700 border border-yellow-200",
};

const STATUS_FILTERS = [
  { value: "",                 label: "Tümü" },
  { value: "preparing",        label: "Hazırlanıyor" },
  { value: "in_transit",       label: "Taşımada" },
  { value: "at_facility",      label: "Şubede" },
  { value: "out_for_delivery", label: "Dağıtımda" },
  { value: "delivered",        label: "Teslim Edildi" },
];

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, cls: "bg-slate-100 text-slate-600 border border-slate-200" };
  return (
    <span className={`inline-flex px-2.5 py-1 rounded-lg text-[12px] font-bold tracking-wide uppercase ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

function SkeletonRow() {
  return (
    <div className="px-5 py-4 border-b border-slate-100 animate-pulse bg-white">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="h-3.5 bg-slate-200 rounded w-40" />
        <div className="h-6 bg-slate-100 rounded-lg w-24" />
      </div>
      <div className="flex gap-2">
        <div className="h-5 bg-slate-100 rounded-md w-24" />
        <div className="h-5 bg-slate-200 rounded w-28" />
      </div>
    </div>
  );
}

export default function ShipmentsPanel() {
  const { shipments, loading, error, statusFilter, setStatusFilter } = useShipments();
  const [selected, setSelected] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const delayedCount = shipments.filter((s) => s.is_delayed).length;

  async function openDetail(shipmentId) {
    setDetailLoading(true);
    try {
      const data = await fetchShipmentDetail(shipmentId);
      setSelected(data);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className="flex h-full bg-transparent overflow-hidden">
      {/* Left: list */}
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-6 py-4 shrink-0 shadow-sm z-20">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="text-[18px] font-extrabold text-slate-900 tracking-tight">Kargo Takip</h2>
            {delayedCount > 0 && (
              <motion.span
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className="flex items-center gap-1.5 text-[11px] text-red-700 bg-red-100 border border-red-200 px-3 py-1.5 rounded-lg font-bold shadow-sm"
              >
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                {delayedCount} gecikmiş
              </motion.span>
            )}
          </div>
          <div className="flex gap-2 flex-wrap">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={`text-[12px] font-semibold px-3 py-1.5 rounded-lg border transition-all ${
                  statusFilter === f.value
                    ? "bg-indigo-50 text-indigo-700 border-indigo-200 shadow-sm"
                    : "bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50 shadow-sm"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-auto bg-white">
          {loading && Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)}
          {error && <div className="p-4 text-[13px] font-medium text-red-700 bg-red-50 border-b border-red-200">{error}</div>}
          {!loading && !error && (
            <div>
              {shipments.map((s) => (
                <motion.button
                  key={s.id}
                  whileHover={{ x: 2 }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  onClick={() => openDetail(s.id)}
                  className={`w-full text-left px-6 py-4 border-b transition-colors ${
                    s.is_delayed
                      ? `bg-gradient-to-r from-red-50/95 to-white border-red-100/80 shadow-sm border-l-4 border-l-red-300 ${
                          selected?.id === s.id ? "ring-2 ring-inset ring-red-200/70" : ""
                        }`
                      : selected?.id === s.id
                      ? "bg-indigo-50 border-slate-100 border-l-4 border-l-indigo-500"
                      : "hover:bg-slate-50 border-slate-100 border-l-4 border-l-transparent"
                  }`}
                >
                  {/* Row 1 */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex items-center gap-2 flex-wrap">
                      <span className="text-[14px] font-bold text-slate-900 truncate">
                        {s.recipient_name}
                      </span>
                      {s.is_delayed && (
                        <span className="text-[10px] bg-red-100/90 text-red-800 border border-red-200/90 px-2 py-1 rounded-lg font-black shadow-sm shrink-0">
                          Gecikme riski
                        </span>
                      )}
                    </div>
                    <StatusBadge status={s.status} />
                  </div>

                  {/* Row 2 */}
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-md font-bold ${
                        CARRIER_COLORS[s.carrier] ?? "bg-slate-100 text-slate-600 border border-slate-200"
                      }`}
                    >
                      {s.carrier}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-500 font-mono">{s.tracking_number}</span>
                    <div className="flex-1" />
                    <span className="text-[11px] font-medium text-slate-500">#{s.order_id}</span>
                  </div>

                  {/* Row 3 — estimated delivery */}
                  {s.estimated_delivery && (
                    <div className="flex items-center gap-1.5 mt-2">
                      <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span
                        className={`text-[11px] font-medium ${
                          s.is_delayed ? "text-red-600 font-bold" : "text-slate-500"
                        }`}
                      >
                        Tahmini teslimat: {s.estimated_delivery}
                      </span>
                    </div>
                  )}
                </motion.button>
              ))}

              {shipments.length === 0 && (
                <div className="flex flex-col items-center justify-center py-24">
                  <Truck className="w-12 h-12 text-slate-300 mb-4" />
                  <p className="text-[15px] font-medium text-slate-500">Bu filtreye ait kargo bulunamadı.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {!loading && (
          <div className="border-t border-slate-200 bg-slate-50 px-6 py-3 text-[12px] font-semibold text-slate-500 shrink-0">
            {shipments.length} kargo gösteriliyor
          </div>
        )}
      </div>

      {/* Right: detail slide-over */}
      <AnimatePresence>
        {(selected || detailLoading) && (
          <motion.div
            key={selected?.id ?? "loading"}
            initial={{ x: "100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0 }}
            transition={{ type: "spring", stiffness: 350, damping: 38 }}
            className="w-[480px] bg-slate-50 border-l border-slate-200 flex flex-col overflow-hidden shrink-0 shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] z-30"
          >
            {detailLoading ? (
              <div className="flex items-center justify-center h-full">
                <svg className="w-8 h-8 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            ) : selected ? (
              <>
                {/* Panel header */}
                <div className="px-6 py-5 border-b border-slate-200 bg-white flex items-center justify-between shrink-0 shadow-sm z-10">
                  <h3 className="text-[16px] font-extrabold text-slate-900">Kargo Detayı</h3>
                  <button
                    onClick={() => setSelected(null)}
                    className="w-8 h-8 rounded-xl hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Panel content */}
                <div className="flex-1 overflow-auto px-6 py-6">
                  {/* Status hero card */}
                  <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 mb-6">
                    <div className="flex items-center justify-between mb-4">
                      <span
                        className={`text-[11px] px-2.5 py-1 rounded-md font-bold ${
                          CARRIER_COLORS[selected.carrier] ?? "bg-slate-100 text-slate-600 border border-slate-200"
                        }`}
                      >
                        {selected.carrier}
                      </span>
                      <StatusBadge status={selected.status} />
                    </div>
                    <p className="text-[24px] font-extrabold text-slate-900 tracking-tight">
                      {selected.recipient_name}
                    </p>
                    {selected.recipient_address && (
                      <div className="flex items-start gap-2 mt-2">
                        <MapPin className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                        <p className="text-[13px] font-medium text-slate-600 leading-relaxed">
                          {selected.recipient_address}
                        </p>
                      </div>
                    )}
                    {selected.estimated_delivery && (
                      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-100">
                        <Calendar className="w-4 h-4 text-slate-500 shrink-0" />
                        <span
                          className={`text-[13px] font-bold ${
                            selected.is_delayed ? "text-red-600" : "text-slate-600"
                          }`}
                        >
                          Tahmini teslimat: {selected.estimated_delivery}
                          {selected.is_delayed && " — Gecikmiş"}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Info pills */}
                  <div className="flex gap-3 mb-6">
                    <div className="flex-1 bg-white border border-slate-200 shadow-sm rounded-xl px-4 py-3">
                      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Takip No</p>
                      <p className="text-[13px] font-semibold font-mono text-slate-800">{selected.tracking_number}</p>
                    </div>
                    <div className="flex-1 bg-white border border-slate-200 shadow-sm rounded-xl px-4 py-3">
                      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Sipariş No</p>
                      <p className="text-[13px] font-semibold font-mono text-slate-800">#{selected.order_id}</p>
                    </div>
                  </div>

                  {/* Timeline */}
                  <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5">
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-5">
                      Kargo Hareketleri
                    </p>
                    <ShipmentTimeline updates={selected.updates} isDelayed={selected.is_delayed} />
                  </div>
                </div>
              </>
            ) : null}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
