import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, RefreshCcw, AlertTriangle,
  ShoppingCart, Wallet, Sparkles,
  CheckCircle2, AlertCircle, XCircle, Calendar,
} from "lucide-react";
import { format, parseISO } from "date-fns";
import { tr } from "date-fns/locale";
import { useForecast } from "../hooks/useForecast";

const STATUS_CFG = {
  yeterli: {
    label: "YETERLİ",
    cls: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    bar: "bg-emerald-500",
    Icon: CheckCircle2,
    iconCls: "text-emerald-600",
  },
  uyari: {
    label: "UYARI",
    cls: "bg-amber-50 text-amber-700 border border-amber-200",
    bar: "bg-amber-500",
    Icon: AlertCircle,
    iconCls: "text-amber-600",
  },
  kritik: {
    label: "KRİTİK",
    cls: "bg-red-50 text-red-700 border border-red-200",
    bar: "bg-red-500",
    Icon: XCircle,
    iconCls: "text-red-600",
  },
};

function formatTL(v) {
  return "₺" + Math.round(v).toLocaleString("tr-TR");
}

function compactTL(v) {
  if (v >= 1_000_000) return "₺" + (v / 1_000_000).toFixed(2) + "M";
  if (v >= 1000) return "₺" + Math.round(v / 1000) + "K";
  return formatTL(v);
}

function fmtDate(iso) {
  try { return format(parseISO(iso), "d MMM", { locale: tr }); }
  catch { return iso; }
}

/* ─────────────────── HERO STAT STRIP ─────────────────── */
function HeroStat({ data }) {
  // Compute % delta: forecast 7d vs previous 7d actual
  const { deltaPct, deltaUp } = useMemo(() => {
    if (!data?.chart_points?.length) return { deltaPct: 0, deltaUp: true };
    const real = data.chart_points.filter((p) => !p.is_forecast);
    const last7Real = real.slice(-7).reduce((s, p) => s + p.revenue, 0);
    const fc7 = data.kpi_revenue_7d;
    if (!last7Real) return { deltaPct: 0, deltaUp: true };
    const pct = ((fc7 - last7Real) / last7Real) * 100;
    return { deltaPct: Math.round(pct), deltaUp: pct >= 0 };
  }, [data]);

  return (
    <div
      className="relative bg-white border border-slate-200 shadow-sm overflow-hidden"
      style={{ borderRadius: "16px" }}
    >
      {/* Subtle accent stripe at top */}
      <div
        className="absolute top-0 left-0 right-0 h-[3px] pointer-events-none"
        style={{ background: "linear-gradient(90deg, #facc15 0%, #f59e0b 35%, #10b981 100%)" }}
      />

      <div
        className="grid grid-cols-1 lg:grid-cols-12 gap-5"
        style={{ paddingTop: "36px", paddingBottom: "20px", paddingLeft: "24px", paddingRight: "24px" }}
      >
        {/* Left: Revenue + delta */}
        <div className="lg:col-span-6 flex flex-col justify-center">
          <p className="text-[10px] font-extrabold text-amber-700 uppercase tracking-[0.18em] mb-2">
            7 Günlük Ciro Öngörüsü
          </p>
          <div className="flex items-baseline gap-3 flex-wrap">
            <h2 className="text-[34px] sm:text-[40px] font-black text-slate-900 tracking-tight leading-none tabular-nums">
              {data ? formatTL(data.kpi_revenue_7d) : "—"}
            </h2>
            {data && (
              <span
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-extrabold ${
                  deltaUp
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-red-50 text-red-700 border border-red-200"
                }`}
              >
                {deltaUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {deltaUp ? "+" : ""}%{Math.abs(deltaPct)}
              </span>
            )}
          </div>
          <p className="text-[11.5px] font-medium text-slate-500 mt-2">
            Geçen 7 günün gerçekleşmesine göre · {data?.period_label ?? "—"}
          </p>
        </div>

        {/* Right: 2 mini stats */}
        <div className="lg:col-span-6 grid grid-cols-2 gap-3">
          <MiniStat
            icon={ShoppingCart}
            iconBg="bg-indigo-50"
            iconCls="text-indigo-600"
            label="Tahmini Sipariş"
            value={data ? data.kpi_orders_7d : "—"}
            sub="Önümüzdeki 7 gün"
          />
          <MiniStat
            icon={AlertTriangle}
            iconBg="bg-amber-50"
            iconCls="text-amber-600"
            label="Risk Altında Ürün"
            value={data ? data.kpi_at_risk_count : "—"}
            sub="Tahmin > stok"
          />
        </div>
      </div>
    </div>
  );
}

function MiniStat({ icon: Icon, iconBg, iconCls, label, value, sub }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/40 px-3.5 py-2.5">
      <div className={`w-9 h-9 rounded-xl ${iconBg} flex items-center justify-center shrink-0`}>
        <Icon className={`w-4 h-4 ${iconCls}`} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[9.5px] font-extrabold text-slate-400 uppercase tracking-[0.16em] truncate">
          {label}
        </p>
        <div className="flex items-baseline gap-1.5 mt-0.5">
          <p className="text-[20px] font-black tabular-nums tracking-tight leading-none text-slate-900">
            {value}
          </p>
          <p className="text-[10px] font-medium text-slate-400 truncate">{sub}</p>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────── BIG CHART ─────────────────── */
function ForecastChart({ points }) {
  const [hover, setHover] = useState(null);

  const layout = useMemo(() => {
    if (!points?.length) return null;
    const W = 1200, H = 380, P = 50;
    const max = Math.max(...points.map((p) => p.revenue), 1);
    const min = Math.min(...points.map((p) => p.revenue));
    const padTop = max * 0.15;
    const padBot = Math.max(min * 0.1, 0);
    const yMax = max + padTop;
    const yMin = Math.max(0, min - padBot);
    const norm = (v) => yMax === yMin ? 0.5 : (v - yMin) / (yMax - yMin);
    const x = (i) => (i / Math.max(points.length - 1, 1)) * (W - P * 2) + P;
    const y = (v) => H - (norm(v) * (H - P * 2) + P);

    const pts = points.map((p, i) => ({ ...p, ix: i, x: x(i), y: y(p.revenue) }));
    const splitIdx = pts.findIndex((p) => p.is_forecast);
    const realPts = splitIdx === -1 ? pts : pts.slice(0, splitIdx);
    // include join point so lines connect smoothly
    const fcPts = splitIdx === -1 ? [] : pts.slice(splitIdx - 1);

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

    // Confidence band ±12% around forecast
    function bandPath(arr) {
      if (arr.length < 2) return "";
      const upper = arr.map((p) => ({ x: p.x, y: y(Math.min(yMax, p.revenue * 1.12)) }));
      const lower = arr.map((p) => ({ x: p.x, y: y(Math.max(yMin, p.revenue * 0.88)) })).reverse();
      let d = `M ${upper[0].x} ${upper[0].y}`;
      for (let i = 0; i < upper.length - 1; i++) {
        const c = upper[i], n = upper[i + 1];
        d += ` C ${c.x + (n.x - c.x) / 3} ${c.y}, ${c.x + (n.x - c.x) * (2 / 3)} ${n.y}, ${n.x} ${n.y}`;
      }
      d += ` L ${lower[0].x} ${lower[0].y}`;
      for (let i = 0; i < lower.length - 1; i++) {
        const c = lower[i], n = lower[i + 1];
        d += ` C ${c.x + (n.x - c.x) / 3} ${c.y}, ${c.x + (n.x - c.x) * (2 / 3)} ${n.y}, ${n.x} ${n.y}`;
      }
      d += " Z";
      return d;
    }

    const splitX = splitIdx > 0 ? pts[splitIdx].x : null;

    // Y-axis ticks
    const yTicks = [yMin, (yMin + yMax) / 2, yMax].map((v) => ({ v, y: y(v) }));

    return {
      W, H, P,
      pts, splitIdx,
      realLine: smoothPath(realPts),
      realArea: areaPath(realPts),
      fcLine: smoothPath(fcPts),
      fcArea: areaPath(fcPts),
      fcBand: bandPath(fcPts),
      splitX,
      yTicks,
    };
  }, [points]);

  if (!layout) return <div className="h-72 animate-pulse bg-slate-100" style={{ borderRadius: "16px" }} />;
  const { W, H, P, pts, realLine, realArea, fcLine, fcArea, fcBand, splitX, yTicks } = layout;
  const labelEvery = Math.max(1, Math.floor(pts.length / 9));

  return (
    <div className="relative">
      <svg className="w-full" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height: "320px" }}>
        <defs>
          <linearGradient id="fcRealGradV2" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.55" />
            <stop offset="60%" stopColor="#10b981" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="fcPredGradV2" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.45" />
            <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="realLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#059669" />
            <stop offset="100%" stopColor="#10b981" />
          </linearGradient>
        </defs>

        {/* Y-axis grid lines */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={P} y1={t.y} x2={W - P} y2={t.y} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="2 4" />
            <text x={P - 8} y={t.y + 3} textAnchor="end" fontSize="10" className="fill-slate-400" fontWeight="700">
              {compactTL(t.v)}
            </text>
          </g>
        ))}

        {/* Forecast region soft background */}
        {splitX != null && (
          <rect x={splitX} y={20} width={W - splitX - P} height={H - 40} fill="#fef3c7" opacity="0.20" rx="6" />
        )}

        {/* Confidence band on forecast */}
        {fcBand && <path d={fcBand} fill="#f59e0b" opacity="0.13" />}

        {/* Real area + line */}
        {realArea && <path d={realArea} fill="url(#fcRealGradV2)" />}
        {realLine && (
          <motion.path
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.4, ease: "easeInOut" }}
            d={realLine}
            fill="none"
            stroke="url(#realLineGrad)"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* Forecast area + line */}
        {fcArea && <path d={fcArea} fill="url(#fcPredGradV2)" />}
        {fcLine && (
          <motion.path
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.4, delay: 0.7, ease: "easeInOut" }}
            d={fcLine}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="9 6"
          />
        )}

        {/* Today divider */}
        {splitX != null && (
          <>
            <line x1={splitX} y1={20} x2={splitX} y2={H - 30} stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="4 4" />
            <g transform={`translate(${splitX}, 14)`}>
              <rect x="-22" y="-10" width="44" height="18" rx="4" fill="#0f172a" />
              <text x="0" y="3" textAnchor="middle" fontSize="10" fontWeight="800" className="fill-white" letterSpacing="0.1em">
                BUGÜN
              </text>
            </g>
          </>
        )}

        {/* Hover hit zones */}
        {pts.map((p, i) => {
          const bw = (W - 2 * P) / Math.max(pts.length - 1, 1);
          return (
            <rect
              key={i}
              x={p.x - bw / 2}
              y={20}
              width={bw}
              height={H - 40}
              fill="transparent"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            />
          );
        })}

        {/* Hover marker */}
        {hover != null && (
          <>
            <line x1={pts[hover].x} y1={20} x2={pts[hover].x} y2={H - 30} stroke="#cbd5e1" strokeWidth="1" />
            <circle
              cx={pts[hover].x}
              cy={pts[hover].y}
              r="6"
              fill="white"
              stroke={pts[hover].is_forecast ? "#f59e0b" : "#10b981"}
              strokeWidth="3"
            />
          </>
        )}
      </svg>

      {/* Tooltip */}
      {hover != null && (
        <div
          className="absolute pointer-events-none bg-slate-900 text-white px-3 py-2 rounded-lg text-[11px] font-bold shadow-xl"
          style={{
            left: `${(pts[hover].x / W) * 100}%`,
            top: 0,
            transform: "translate(-50%, -110%)",
            whiteSpace: "nowrap",
          }}
        >
          <div className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
            {pts[hover].is_forecast ? "Tahmin" : "Gerçekleşen"} · {fmtDate(pts[hover].date)}
          </div>
          <div className="text-[14px] font-black tabular-nums mt-0.5">
            {formatTL(pts[hover].revenue)}
          </div>
        </div>
      )}

      {/* Date axis */}
      <div className="flex justify-between px-12 mt-2 -mb-1">
        {pts.map((p, i) =>
          i % labelEvery === 0 || i === pts.length - 1 ? (
            <span
              key={i}
              className={`text-[10px] font-bold tabular-nums ${
                p.is_forecast ? "text-amber-600" : "text-slate-400"
              }`}
            >
              {fmtDate(p.date)}
            </span>
          ) : null,
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mt-5 px-2 text-[11.5px] font-semibold">
        <span className="inline-flex items-center gap-2 text-emerald-700">
          <span className="w-4 h-[3px] bg-emerald-500 rounded-full" />
          Gerçekleşen (son 30 gün)
        </span>
        <span className="inline-flex items-center gap-2 text-amber-700">
          <span className="w-4 h-[3px] rounded-full" style={{ background: "repeating-linear-gradient(90deg, #f59e0b 0 4px, transparent 4px 7px)" }} />
          Tahmin (önümüzdeki 7 gün)
        </span>
        <span className="inline-flex items-center gap-2 text-amber-600/80">
          <span className="w-4 h-3 rounded bg-amber-400/30" />
          ±%12 güven aralığı
        </span>
      </div>
    </div>
  );
}

/* ─────────────────── TOP 5 PRODUCTS WITH MINI BARS ─────────────────── */
function StatusBadge({ status }) {
  const cfg = STATUS_CFG[status] ?? STATUS_CFG.yeterli;
  return (
    <span className={`inline-flex items-center gap-1.5 text-[10.5px] font-extrabold tracking-wide px-2 py-1 rounded-lg ${cfg.cls}`}>
      <cfg.Icon className={`w-3 h-3 ${cfg.iconCls}`} />
      {cfg.label}
    </span>
  );
}

function CoverageBar({ stock, forecast, status }) {
  // Coverage = stock / forecast (cap at 150% for display)
  const ratio = forecast > 0 ? Math.min(stock / forecast, 1.5) : 1;
  const pct = ratio * (100 / 1.5);  // map 0..150% to 0..100% bar
  const cfg = STATUS_CFG[status] ?? STATUS_CFG.yeterli;
  return (
    <div className="w-full">
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: "easeOut" }}
          className={`h-full rounded-full ${cfg.bar}`}
        />
      </div>
      <div className="flex items-center justify-between mt-1.5 text-[9.5px] font-bold tabular-nums">
        <span className="text-slate-400">stok / tahmin</span>
        <span className={status === "kritik" ? "text-red-600" : status === "uyari" ? "text-amber-700" : "text-emerald-700"}>
          %{Math.round((stock / Math.max(forecast, 0.0001)) * 100)}
        </span>
      </div>
    </div>
  );
}

function TopProductsList({ rows }) {
  if (!rows?.length) return (
    <div className="text-center py-12 text-[13px] font-medium text-slate-500">
      Henüz yeterli satış verisi yok.
    </div>
  );
  return (
    <div className="divide-y divide-slate-100">
      {rows.map((p, i) => {
        const cfg = STATUS_CFG[p.stock_status] ?? STATUS_CFG.yeterli;
        return (
          <motion.div
            key={p.product_id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="grid grid-cols-12 gap-4 px-5 py-4 items-center hover:bg-slate-50/60 transition-colors"
          >
            {/* Rank + name */}
            <div className="col-span-4 flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-slate-100 to-slate-50 border border-slate-200 flex items-center justify-center text-[12px] font-black text-slate-600 shrink-0">
                {i + 1}
              </div>
              <div className="min-w-0">
                <p className="text-[13.5px] font-extrabold text-slate-900 truncate">{p.name}</p>
                <p className="text-[10.5px] font-semibold text-slate-400 truncate uppercase tracking-wider">{p.category ?? "—"}</p>
              </div>
            </div>

            {/* Sales & forecast numbers */}
            <div className="col-span-3 flex items-baseline gap-3">
              <div>
                <p className="text-[9.5px] font-bold text-slate-400 uppercase tracking-wider">Son 30g</p>
                <p className="text-[14px] font-extrabold tabular-nums text-slate-700">
                  {p.sales_30d.toLocaleString("tr-TR")}
                  <span className="text-[10px] text-slate-400 ml-0.5">{p.unit ?? ""}</span>
                </p>
              </div>
              <span className="text-slate-300 text-[14px] font-bold">→</span>
              <div>
                <p className="text-[9.5px] font-bold text-amber-600 uppercase tracking-wider">7g Tahmin</p>
                <p className="text-[14px] font-extrabold tabular-nums text-amber-700">
                  {p.forecast_7d.toLocaleString("tr-TR")}
                  <span className="text-[10px] text-amber-500 ml-0.5">{p.unit ?? ""}</span>
                </p>
              </div>
            </div>

            {/* Coverage bar */}
            <div className="col-span-3">
              <CoverageBar stock={p.current_stock} forecast={p.forecast_7d} status={p.stock_status} />
            </div>

            {/* Status badge */}
            <div className="col-span-2 flex justify-end">
              <StatusBadge status={p.stock_status} />
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

/* ─────────────────── PAGE ─────────────────── */
export default function ForecastPage() {
  const { data, loading, refreshing, error, refresh } = useForecast();

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
                {data?.generated_at && (
                  <>
                    <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0" />
                    <span className="text-slate-400 text-[11.5px] inline-flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Üretildi: {data.generated_at}
                    </span>
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

      <div className="px-6 sm:px-8 py-6 flex-1 space-y-6">
        {loading && !data ? (
          <>
            <div className="h-44 bg-slate-100 animate-pulse" style={{ borderRadius: "20px" }} />
            <div className="h-[440px] bg-slate-100 animate-pulse" style={{ borderRadius: "16px" }} />
          </>
        ) : (
          <>
            {/* Hero stat */}
            <HeroStat data={data} />

            {/* Chart */}
            <div
              className="bg-white border border-slate-200 shadow-sm px-5 py-4"
              style={{ borderRadius: "16px" }}
            >
              <div className="flex items-end justify-between mb-3 gap-3">
                <div>
                  <p className="text-[10px] font-extrabold text-slate-500 uppercase tracking-[0.18em]">
                    Günlük Ciro Eğrisi
                  </p>
                  <p className="text-[11.5px] font-semibold text-slate-600 mt-0.5">
                    Son 30 gün + 7 gün öngörü
                  </p>
                </div>
                <p className="text-[9.5px] font-bold text-slate-400 uppercase tracking-wider">
                  Üzerine gel · detay
                </p>
              </div>
              <ForecastChart points={data?.chart_points ?? []} />
            </div>

            {/* Bottom row: Top 5 + AI Yorumu */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
              {/* Top 5 */}
              <div
                className="xl:col-span-7 bg-white border border-slate-200 shadow-sm overflow-hidden"
                style={{ borderRadius: "16px" }}
              >
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/40">
                  <p className="text-[11px] font-extrabold text-slate-500 uppercase tracking-[0.18em]">
                    Önümüzdeki Hafta Öne Çıkacak 5 Ürün
                  </p>
                  <p className="text-[10.5px] font-semibold text-slate-400 uppercase tracking-wider">
                    Stok kapsama oranı
                  </p>
                </div>
                <TopProductsList rows={data?.top_products ?? []} />
              </div>

              {/* AI Yorumu */}
              <div className="xl:col-span-5">
                <div
                  className="relative overflow-hidden p-6 sm:p-7"
                  style={{
                    borderRadius: "16px",
                    background: "linear-gradient(135deg, #fefce8 0%, #ffffff 45%, #ecfdf5 100%)",
                    boxShadow:
                      "0 1px 0 rgba(245,158,11,0.10), 0 8px 24px -12px rgba(16,185,129,0.20), 0 0 0 1px rgba(245,158,11,0.18)",
                  }}
                >
                  <div
                    className="absolute -top-16 -right-16 w-52 h-52 rounded-full blur-3xl pointer-events-none"
                    style={{ background: "radial-gradient(circle, rgba(250,204,21,0.40) 0%, transparent 70%)" }}
                  />
                  <div
                    className="absolute -bottom-20 -left-12 w-56 h-56 rounded-full blur-3xl pointer-events-none"
                    style={{ background: "radial-gradient(circle, rgba(16,185,129,0.30) 0%, transparent 70%)" }}
                  />
                  <div
                    className="absolute top-0 left-0 right-0 h-[3px] pointer-events-none"
                    style={{ background: "linear-gradient(90deg, #facc15 0%, #f59e0b 35%, #10b981 100%)" }}
                  />

                  <div className="relative">
                    <div className="flex items-center gap-3 mb-5">
                      <div
                        className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 shadow-md"
                        style={{ background: "linear-gradient(135deg, #facc15 0%, #f59e0b 50%, #10b981 100%)" }}
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
