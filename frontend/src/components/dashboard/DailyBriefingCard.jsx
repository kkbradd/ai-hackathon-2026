import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Sun, Package, Truck, AlertTriangle, RefreshCw, Sparkles,
  ChevronRight, Clock, MapPin, CheckCircle2, Loader2,
} from "lucide-react";
import { fetchDailyBriefing } from "../../api/client";

const ROLE_THEME = {
  warehouse: {
    label: "Depo Sorumlusu",
    Icon: Package,
    accent: "amber",
    cardBg: "bg-amber-50/40 border-amber-200/60",
    iconBg: "bg-amber-100 text-amber-700",
    chipBg: "bg-amber-100/70 text-amber-800",
    headerBg: "bg-gradient-to-br from-amber-100/80 to-amber-50",
    link: "/orders",
    linkLabel: "Tüm siparişler",
    emptyMsg: "Bugün hazırlanması gereken paket yok.",
  },
  courier: {
    label: "Kargo Görevlisi",
    Icon: Truck,
    accent: "blue",
    cardBg: "bg-blue-50/40 border-blue-200/60",
    iconBg: "bg-blue-100 text-blue-700",
    chipBg: "bg-blue-100/70 text-blue-800",
    headerBg: "bg-gradient-to-br from-blue-100/80 to-blue-50",
    link: "/shipments",
    linkLabel: "Tüm kargolar",
    emptyMsg: "Bugün dağıtım için bekleyen kargo yok.",
  },
  operations: {
    label: "Operasyon Yöneticisi",
    Icon: AlertTriangle,
    accent: "rose",
    cardBg: "bg-rose-50/40 border-rose-200/60",
    iconBg: "bg-rose-100 text-rose-700",
    chipBg: "bg-rose-100/70 text-rose-800",
    headerBg: "bg-gradient-to-br from-rose-100/80 to-rose-50",
    link: "/",
    linkLabel: "Operasyon merkezi",
    emptyMsg: "Açık operasyonel uyarı yok.",
  },
};

function WarehouseList({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="space-y-1.5">
      {items.slice(0, 5).map((it) => (
        <li key={it.order_id} className="flex items-start gap-2 text-[12px] text-slate-700">
          <span className="font-extrabold text-amber-700 tabular-nums">#{it.order_id}</span>
          <div className="min-w-0 flex-1">
            <p className="font-bold truncate">{it.customer_name}</p>
            <p className="text-[11px] text-slate-500 truncate">
              {it.line_count} kalem · {it.address || "Adres belirtilmemiş"}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}

function CourierList({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="space-y-1.5">
      {items.slice(0, 5).map((it) => (
        <li key={it.shipment_id} className="flex items-start gap-2 text-[12px] text-slate-700">
          <Truck className="w-3 h-3 mt-0.5 text-blue-600 shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-bold truncate">{it.recipient_name || "Alıcı —"}</span>
              {it.is_delayed && (
                <span className="text-[9px] font-black uppercase px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 tracking-wide">
                  Gecikti
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 flex items-center gap-1 truncate">
              <MapPin className="w-2.5 h-2.5" />
              {it.district || "Bölge —"} · {it.carrier} {it.tracking_number}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}

function OpsList({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="space-y-1.5">
      {items.slice(0, 5).map((it, i) => (
        <li key={i} className="flex items-start gap-2 text-[12px] text-slate-700">
          <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
            it.severity === "critical" ? "bg-red-500" : it.severity === "warning" ? "bg-amber-500" : "bg-slate-400"
          }`} />
          <div className="min-w-0 flex-1">
            <p className="font-bold text-[12px] truncate">{it.title}</p>
            <p className="text-[11px] text-slate-500 line-clamp-2 leading-snug">{it.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

function RoleColumn({ roleKey, briefing, listComponent: List, navigate }) {
  const t = ROLE_THEME[roleKey];
  const isEmpty = !briefing.item_count;
  return (
    <div className={`relative rounded-2xl border ${t.cardBg} overflow-hidden`}>
      <div className={`px-4 py-3 ${t.headerBg} border-b border-white/40`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-xl ${t.iconBg} flex items-center justify-center`}>
              <t.Icon className="w-3.5 h-3.5" />
            </div>
            <p className="text-[12px] font-extrabold text-slate-800">{t.label}</p>
          </div>
          <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${t.chipBg} tabular-nums`}>
            {briefing.item_count}
          </span>
        </div>
      </div>

      <div className="px-4 py-3 space-y-3">
        <div className="flex items-start gap-1.5">
          <Sparkles className="w-3 h-3 mt-0.5 text-slate-400 shrink-0" />
          <p className="text-[11.5px] text-slate-600 leading-relaxed font-medium italic">
            {briefing.ai_summary}
          </p>
        </div>

        {isEmpty ? (
          <div className="flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-xl px-2.5 py-1.5 font-semibold">
            <CheckCircle2 className="w-3 h-3" />
            {t.emptyMsg}
          </div>
        ) : (
          <>
            <List items={briefing.items} />
            {briefing.item_count > 5 && (
              <button
                type="button"
                onClick={() => navigate(t.link)}
                className="flex items-center gap-1 text-[11px] font-bold text-slate-600 hover:text-slate-900 transition-colors"
              >
                {t.linkLabel} ({briefing.item_count})
                <ChevronRight className="w-3 h-3" />
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function DailyBriefingCard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (force = false) => {
    if (force) setRefreshing(true);
    else setLoading(true);
    try {
      const d = await fetchDailyBriefing(force);
      setData(d);
      setError(null);
    } catch (e) {
      setError(e?.response?.data?.detail || "Günlük özet yüklenemedi.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(() => load(false), 30 * 60 * 1000); // 30dk
    return () => clearInterval(interval);
  }, [load]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />
          <p className="text-[13px] text-slate-500 font-bold">Sabah özeti hazırlanıyor…</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-44 bg-slate-50 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-[13px] font-bold text-red-700">
        {error}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm"
    >
      {/* Header */}
      <div className="px-6 py-5 border-b border-slate-100 bg-gradient-to-br from-indigo-50/40 to-white">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-sm">
              <Sun className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-[17px] font-black text-slate-900 tracking-tight">
                  08:00 Günlük Özeti
                </h2>
                <span className="inline-flex items-center gap-1 text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full bg-violet-100 text-violet-700 border border-violet-200">
                  <Sparkles className="w-2.5 h-2.5" />
                  AI üretimli
                </span>
              </div>
              <p className="text-[12px] text-slate-500 font-semibold mt-0.5">
                {data.headline}
              </p>
              <p className="text-[11px] text-slate-400 font-medium mt-0.5 flex items-center gap-1">
                <Clock className="w-2.5 h-2.5" />
                {data.generated_at} · 3 rol için ayrıştırıldı
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => load(true)}
            disabled={refreshing}
            className="p-2 rounded-xl hover:bg-slate-100 transition-colors disabled:opacity-50"
            title="Özeti yeniden üret"
          >
            <RefreshCw className={`w-4 h-4 text-slate-500 ${refreshing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* 3 role columns */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <RoleColumn
          roleKey="warehouse"
          briefing={data.warehouse}
          listComponent={WarehouseList}
          navigate={navigate}
        />
        <RoleColumn
          roleKey="courier"
          briefing={data.courier}
          listComponent={CourierList}
          navigate={navigate}
        />
        <RoleColumn
          roleKey="operations"
          briefing={data.operations}
          listComponent={OpsList}
          navigate={navigate}
        />
      </div>
    </motion.div>
  );
}
