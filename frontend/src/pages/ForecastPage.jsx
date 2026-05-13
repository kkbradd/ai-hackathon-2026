import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp, RefreshCcw, AlertTriangle, ShoppingCart, Wallet,
  Sparkles, CheckCircle2, AlertCircle, XCircle,
} from "lucide-react";
import { format, parseISO } from "date-fns";
import { tr } from "date-fns/locale";
import { useForecast } from "../hooks/useForecast";

const STATUS_CFG = {
  yeterli: {
    label: "YETERLİ",
    cls: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    Icon: CheckCircle2,
    iconCls: "text-emerald-600",
  },
  uyari: {
    label: "UYARI",
    cls: "bg-amber-50 text-amber-700 border border-amber-200",
    Icon: AlertCircle,
    iconCls: "text-amber-600",
  },
  kritik: {
    label: "KRİTİK",
    cls: "bg-red-50 text-red-700 border border-red-200",
    Icon: XCircle,
    iconCls: "text-red-600",
  },
};

function formatTL(v) {
  return "₺" + Math.round(v).toLocaleString("tr-TR");
}

function fmtDate(iso) {
  try { return format(parseISO(iso), "d MMM", { locale: tr }); }
  catch { return iso; }
}

function KpiCard({ icon: Icon, iconBg, iconColor, label, value, sub }) {
  return (
    <div
      className="bg-white border border-slate-200 shadow-sm p-5 flex items-start gap-4"
      style={{ borderRadius: "16px" }}
    >
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${iconBg}`}>
        <Icon className={`w-6 h-6 ${iconColor}`} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[10.5px] font-extrabold text-slate-400 uppercase tracking-[0.16em] truncate">
          {label}
        </p>
        <p className="text-[26px] font-black text-slate-900 tracking-tight tabular-nums leading-none mt-1.5">
          {value}
        </p>
        {sub && <p className="text-[11px] font-medium text-slate-500 mt-1 truncate">{sub}</p>}
      </div>
    </div>
  );
}

function ForecastChart({ points }) {
  const layout = useMemo(() => {
    if (!points?.length) return null;
    const W = 1000, H = 280, P = 40;
    const max = Math.max(...points.map((p) => p.revenue), 1);
    const min = Math.min(...points.map((p) => p.revenue));
    const norm = (v) => (max === min ? 0.5 : (v - min) / (max - min));
    const x = (i) => (i / Math.max(points.length - 1, 1)) * (W - P * 2) + P;
    const y = (v) => H - (norm(v) * (H - P * 2) + P);

    const pts = points.map((p, i) => ({ ...p, ix: i, x: x(i), y: y(p.revenue) }));
    const splitIdx = pts.findIndex((p) => p.is_forecast);
    const realPts = splitIdx === -1 ? pts : pts.slice(0, splitIdx);
    const fcPts = splitIdx === -1 ? [] : pts.slice(splitIdx - 1); // include join point

    function smoothPath(arr) {
      if (arr.length < 2) return "";
      let d = `M ${arr[0].x} ${arr[0].y}`;
      for (let i = 0; i < arr.length - 1; i++) {
        const c = arr[i], n = arr[i + 1];
        d += ` C ${c.x + (n.x - c.x) / 3} ${c.y}, ${c.x + (n.x - c.x) * (2 / 3)} ${n.y}, ${n.x} ${n.y}`;
      }
      return d;
    }

    function areaPath(arr) {
      if (arr.length < 2) return "";
      let d = `M ${arr[0].x} ${H - P / 2}`;
      d += ` L ${arr[0].x} ${arr[0].y}`;
      for (let i = 0; i < arr.length - 1; i++) {
        const c = arr[i], n = arr[i + 1];
        d += ` C ${c.x + (n.x - c.x) / 3} ${c.y}, ${c.x + (n.x - c.x) * (2 / 3)} ${n.y}, ${n.x} ${n.y}`;
      }
      d += ` L ${arr[arr.length - 1].x} ${H - P / 2} Z`;
      return d;
    }

    const splitX = splitIdx > 0 ? pts[splitIdx].x : null;

    return {
      W, H, P,
      pts,
      realLine: smoothPath(realPts),
      realArea: areaPath(realPts),
      fcLine: smoothPath(fcPts),
      fcArea: areaPath(fcPts),
      splitX,
    };
  }, [points]);

  if (!layout) return <div className="h-72 animate-pulse bg-slate-100 rounded-2xl" />;
  const { W, H, pts, realLine, realArea, fcLine, fcArea, splitX } = layout;

  const labelEvery = Math.ceil(pts.length / 10);

  return (
    <div className="relative">
      <svg className="w-full h-72" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id="fcRealGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="fcPredGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Forecast region background highlight */}
        {splitX != null && (
          <rect x={splitX} y={0} width={W - splitX} height={H} fill="#fef3c7" opacity="0.25" />
        )}

        {/* Real area + line */}
        {realArea && <path d={realArea} fill="url(#fcRealGrad)" />}
        {realLine && (
          <motion.path
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 1.2, ease: "easeInOut" }}
            d={realLine}
            fill="none"
            stroke="#10b981"
            strokeWidth="3"
            strokeLinecap="round"
          />
        )}

        {/* Forecast area + line */}
        {fcArea && <path d={fcArea} fill="url(#fcPredGrad)" />}
        {fcLine && (
          <motion.path
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 1.4, delay: 0.6, ease: "easeInOut" }}
            d={fcLine}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="8 5"
          />
        )}

        {/* Today divider */}
        {splitX != null && (
          <>
            <line
              x1={splitX} y1={20} x2={splitX} y2={H - 20}
              stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="4 4"
            />
            <text
              x={splitX} y={14}
              textAnchor="middle"
              className="fill-slate-500"
              fontSize="11"
              fontWeight="700"
            >
              BUGÜN
            </text>
          </>
        )}
      </svg>

      {/* Date axis */}
      <div className="flex justify-between px-1 mt-2">
        {pts.map((p, i) =>
          i % labelEvery === 0 || i === pts.length - 1 ? (
            <span
              key={i}
              className={`text-[10px] font-semibold tabular-nums ${
                p.is_forecast ? "text-amber-600" : "text-slate-400"
              }`}
            >
              {fmtDate(p.date)}
            </span>
          ) : null,
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5 mt-3 text-[11px] font-semibold">
        <span className="flex items-center gap-1.5 text-emerald-700">
          <span className="w-3 h-0.5 bg-emerald-500" /> Gerçekleşen (son 30 gün)
        </span>
        <span className="flex items-center gap-1.5 text-amber-700">
          <span className="w-3 h-0.5 bg-amber-500" style={{ borderTop: "2px dashed #f59e0b" }} />
          Tahmin (önümüzdeki 7 gün)
        </span>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const cfg = STATUS_CFG[status] ?? STATUS_CFG.yeterli;
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-[10.5px] font-extrabold tracking-wide px-2 py-1 rounded-lg ${cfg.cls}`}
    >
      <cfg.Icon className={`w-3 h-3 ${cfg.iconCls}`} />
      {cfg.label}
    </span>
  );
}

function TopProductsTable({ rows }) {
  if (!rows?.length) return (
    <div className="text-center py-8 text-[13px] font-medium text-slate-500">
      Henüz yeterli satış verisi yok.
    </div>
  );
  return (
    <div className="overflow-hidden">
      <div className="grid grid-cols-12 gap-2 px-4 py-3 bg-gradient-to-b from-slate-100 to-slate-50 border-b border-slate-200 text-[10.5px] font-extrabold text-slate-500 uppercase tracking-[0.14em]">
        <div className="col-span-4">Ürün</div>
        <div className="col-span-2 text-right">Son 30g Satış</div>
        <div className="col-span-2 text-right">7g Tahmin</div>
        <div className="col-span-2 text-right">Mevcut Stok</div>
        <div className="col-span-2 text-right">Durum</div>
      </div>
      {rows.map((p, i) => (
        <div
          key={p.product_id}
          className={`grid grid-cols-12 gap-2 px-4 py-3.5 border-b border-slate-100/80 items-center ${
            i % 2 === 1 ? "bg-slate-50/40" : "bg-white"
          }`}
        >
          <div className="col-span-4 min-w-0">
            <p className="text-[13px] font-bold text-slate-800 truncate">{p.name}</p>
            <p className="text-[10.5px] font-medium text-slate-400 truncate">{p.category ?? "—"}</p>
          </div>
          <div className="col-span-2 text-right text-[13px] font-semibold text-slate-700 tabular-nums">
            {p.sales_30d.toLocaleString("tr-TR")} <span className="text-[10px] text-slate-400">{p.unit ?? ""}</span>
          </div>
          <div className="col-span-2 text-right text-[13px] font-extrabold text-amber-700 tabular-nums">
            {p.forecast_7d.toLocaleString("tr-TR")} <span className="text-[10px] text-amber-500">{p.unit ?? ""}</span>
          </div>
          <div className="col-span-2 text-right text-[13px] font-semibold text-slate-700 tabular-nums">
            {p.current_stock.toLocaleString("tr-TR")} <span className="text-[10px] text-slate-400">{p.unit ?? ""}</span>
          </div>
          <div className="col-span-2 flex justify-end">
            <StatusBadge status={p.stock_status} />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ForecastPage() {
  const { data, loading, refreshing, error, refresh } = useForecast();
  const [tab] = useState("overview");

  return (
    <div className="flex flex-col h-full bg-transparent overflow-auto">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-6 sm:px-8 pt-6 pb-5 shrink-0 shadow-sm z-20">
        <div className="flex items-end justify-between gap-3">
          <div className="flex items-start gap-4">
            <div
              className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-100 to-yellow-50 ring-1 ring-emerald-200/60 flex items-center justify-center shrink-0"
              style={{ borderRadius: "16px" }}
            >
              <TrendingUp className="w-6 h-6 text-emerald-700" />
            </div>
            <div>
              <h1 className="text-[28px] sm:text-[32px] font-black text-slate-900 tracking-tight leading-none">
                Talep Tahmini
              </h1>
              <p className="text-[12.5px] font-semibold text-slate-500 mt-2 flex flex-wrap items-center gap-2">
                <span>Önümüzdeki 7 gün için satış öngörüsü</span>
                {data?.period_label && (
                  <>
                    <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0" />
                    <span className="tabular-nums">{data.period_label}</span>
                  </>
                )}
                {data?.generated_at && (
                  <>
                    <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0" />
                    <span className="text-slate-400 text-[11.5px]">Üretildi: {data.generated_at}</span>
                  </>
                )}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={refresh}
            disabled={refreshing}
            title="Tahmini yeniden üret"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-[12px] font-bold bg-white border border-slate-200 shadow-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors shrink-0"
          >
            <RefreshCcw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Yenile
          </button>
        </div>
      </div>

      {error && (
        <div className="m-6 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-[13px] font-medium text-red-700">
          {error}
        </div>
      )}

      <div className="px-6 sm:px-8 py-6 flex-1">
        {loading && !data ? (
          <div className="grid gap-4 md:grid-cols-3 mb-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-28 bg-slate-100 animate-pulse rounded-2xl" />
            ))}
          </div>
        ) : (
          <>
            {/* KPI strip */}
            <div className="grid gap-4 md:grid-cols-3 mb-6">
              <KpiCard
                icon={Wallet}
                iconBg="bg-emerald-50"
                iconColor="text-emerald-600"
                label="7 Günlük Tahmini Ciro"
                value={data ? formatTL(data.kpi_revenue_7d) : "—"}
                sub="Son 14 gün ortalamasından"
              />
              <KpiCard
                icon={ShoppingCart}
                iconBg="bg-indigo-50"
                iconColor="text-indigo-600"
                label="Tahmini Sipariş Sayısı"
                value={data ? data.kpi_orders_7d : "—"}
                sub="Önümüzdeki 7 gün"
              />
              <KpiCard
                icon={AlertTriangle}
                iconBg="bg-amber-50"
                iconColor="text-amber-600"
                label="Risk Altındaki Ürün"
                value={data ? data.kpi_at_risk_count : "—"}
                sub="Tahmini talep stoktan fazla"
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Chart + table column */}
              <div className="lg:col-span-2 flex flex-col gap-6">
                {/* Chart card */}
                <div
                  className="bg-white border border-slate-200 shadow-sm p-6"
                  style={{ borderRadius: "16px" }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-[11px] font-extrabold text-slate-500 uppercase tracking-[0.18em]">
                      Günlük Ciro Eğrisi
                    </p>
                    <p className="text-[10.5px] font-semibold text-slate-400 uppercase tracking-wider">
                      Son 30g + Önümüzdeki 7g
                    </p>
                  </div>
                  <ForecastChart points={data?.chart_points ?? []} />
                </div>

                {/* Top products table card */}
                <div
                  className="bg-white border border-slate-200 shadow-sm overflow-hidden"
                  style={{ borderRadius: "16px" }}
                >
                  <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/40">
                    <p className="text-[11px] font-extrabold text-slate-500 uppercase tracking-[0.18em]">
                      Önümüzdeki Hafta Öne Çıkacak 5 Ürün
                    </p>
                    <p className="text-[10.5px] font-semibold text-slate-400 uppercase tracking-wider">
                      Satış adedine göre
                    </p>
                  </div>
                  <TopProductsTable rows={data?.top_products ?? []} />
                </div>
              </div>

              {/* AI summary column */}
              <div className="lg:col-span-1">
                <div
                  className="relative bg-white p-6 sticky top-4 overflow-hidden shadow-lg"
                  style={{
                    borderRadius: "16px",
                    background:
                      "linear-gradient(135deg, #fefce8 0%, #ffffff 45%, #ecfdf5 100%)",
                    boxShadow:
                      "0 1px 0 rgba(245,158,11,0.10), 0 8px 24px -12px rgba(16,185,129,0.20), 0 0 0 1px rgba(245,158,11,0.18)",
                  }}
                >
                  {/* Vibrant orbs */}
                  <div
                    className="absolute -top-16 -right-16 w-52 h-52 rounded-full blur-3xl pointer-events-none"
                    style={{ background: "radial-gradient(circle, rgba(250,204,21,0.40) 0%, transparent 70%)" }}
                  />
                  <div
                    className="absolute -bottom-20 -left-12 w-56 h-56 rounded-full blur-3xl pointer-events-none"
                    style={{ background: "radial-gradient(circle, rgba(16,185,129,0.30) 0%, transparent 70%)" }}
                  />
                  {/* Gradient stripe accent at top */}
                  <div
                    className="absolute top-0 left-0 right-0 h-[3px] pointer-events-none"
                    style={{ background: "linear-gradient(90deg, #facc15 0%, #f59e0b 35%, #10b981 100%)" }}
                  />

                  <div className="relative">
                    <div className="flex items-center gap-3 mb-5">
                      <div
                        className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 shadow-md"
                        style={{
                          background: "linear-gradient(135deg, #facc15 0%, #f59e0b 50%, #10b981 100%)",
                        }}
                      >
                        <Sparkles className="w-5 h-5 text-white drop-shadow" />
                      </div>
                      <div>
                        <p className="text-[10.5px] font-extrabold text-amber-700 uppercase tracking-[0.18em]">
                          AI Yorumu
                        </p>
                        <p className="text-[14px] font-black text-slate-900 tracking-tight leading-tight">
                          Operasyon Analisti
                        </p>
                      </div>
                    </div>
                    <div className="text-[13.5px] leading-relaxed text-slate-700 font-medium whitespace-pre-line">
                      {data?.ai_summary ?? "AI yorumu hazırlanıyor…"}
                    </div>
                    <div className="mt-5 pt-4 border-t border-amber-200/40 text-[10.5px] font-bold flex items-center justify-between">
                      <span className="inline-flex items-center gap-1.5 text-emerald-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        Gemini 2.5 Flash
                      </span>
                      <span className="tabular-nums text-slate-500">{data?.generated_at ?? ""}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
