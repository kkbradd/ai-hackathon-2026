import { useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, ChevronLeft, ChevronRight } from "lucide-react";

function WeekNav({ weeksAgo, setWeeksAgo }) {
  const getRange = () => {
    const now = new Date();
    const monday = new Date(now);
    monday.setDate(now.getDate() - (now.getDay() === 0 ? 6 : now.getDay() - 1));
    const target = new Date(monday);
    target.setDate(monday.getDate() - weeksAgo * 7);
    const end = new Date(target);
    end.setDate(target.getDate() + 6);
    const fmt = (d) => d.toLocaleDateString("tr-TR", { day: "numeric", month: "short" });
    return `${fmt(target)} – ${fmt(end)}`;
  };
  return (
    <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-2 py-1">
      <button type="button" onClick={() => setWeeksAgo((p) => p + 1)} className="p-1 hover:bg-white rounded-lg transition-colors text-slate-400 hover:text-indigo-600">
        <ChevronLeft className="w-4 h-4" />
      </button>
      <span className="text-[12px] font-bold text-slate-700 min-w-[130px] text-center">{getRange()}</span>
      <button type="button" onClick={() => setWeeksAgo((p) => Math.max(0, p - 1))} disabled={weeksAgo === 0} className="p-1 hover:bg-white rounded-lg transition-colors text-slate-400 hover:text-indigo-600 disabled:opacity-30">
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

function BarChart({ chartData, weeksAgo }) {
  const [hoverIdx, setHoverIdx] = useState(null);
  if (!chartData?.length) return <div className="h-40 animate-shimmer rounded-xl" />;
  const todayIdx = (new Date().getDay() + 6) % 7;
  const max = Math.max(...chartData.map((d) => d.orders), 1);
  const sumOrders = chartData.reduce((s, d) => s + d.orders, 0) || 1;

  return (
    <div className="relative flex flex-col gap-3">
      {hoverIdx != null && !Number.isNaN(hoverIdx) && (
        <div
          className="absolute left-1/2 -translate-x-1/2 bottom-[52px] z-20 max-w-[200px] rounded-xl border border-slate-200 bg-white px-3 py-2 text-[11px] font-medium text-slate-800 shadow-lg pointer-events-none text-center"
          role="tooltip"
        >
          <div className="font-bold text-slate-900">{chartData[hoverIdx]?.date ?? ""}</div>
          <div className="mt-0.5 tabular-nums">
            {(chartData[hoverIdx]?.orders ?? 0).toLocaleString("tr-TR")} sipariş
          </div>
          <div className="text-slate-500 text-[10px] mt-1 leading-snug">
            Haftalık sipariş toplamının yaklaşık %{Math.round(((chartData[hoverIdx]?.orders ?? 0) / sumOrders) * 100)}’si bu gün
          </div>
        </div>
      )}
      <div className="flex items-end gap-1.5 h-36">
        {chartData.map((d, i) => {
          const isFuture = weeksAgo === 0 && i > todayIdx;
          const pct = (d.orders / max) * 100;
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <button
                type="button"
                aria-label={`${d.date}: ${d.orders} sipariş`}
                className={`relative w-full rounded-lg overflow-hidden h-28 flex items-end outline-none ring-offset-2 focus-visible:ring-2 focus-visible:ring-indigo-400 ${isFuture ? "opacity-20 cursor-default" : "cursor-crosshair hover:opacity-95"}`}
                onMouseEnter={() => !isFuture && setHoverIdx(i)}
                onMouseLeave={() => setHoverIdx(null)}
                onFocus={() => !isFuture && setHoverIdx(i)}
                onBlur={() => setHoverIdx(null)}
                disabled={isFuture}
              >
                <div className="absolute inset-0 bg-slate-50 rounded-lg pointer-events-none" />
                {!isFuture && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${pct}%` }}
                    transition={{ duration: 0.8, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
                    className="relative w-full bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-lg pointer-events-none"
                  />
                )}
              </button>
              <span className={`text-[9px] font-bold uppercase tracking-wider ${hoverIdx === i ? "text-indigo-600" : "text-slate-400"}`}>
                {d.date}
              </span>
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-between text-[11px] text-slate-500">
        <span>Toplam: <strong className="text-slate-800">{chartData.reduce((s, x) => s + x.orders, 0)} sipariş</strong></span>
        <span className="text-indigo-600 font-semibold">Haftalık sipariş dağılımı</span>
      </div>
    </div>
  );
}

function LineChart({ chartData, weeksAgo }) {
  const [hoverIdx, setHoverIdx] = useState(null);
  if (!chartData?.length) return <div className="h-40 animate-shimmer rounded-xl" />;
  const todayIdx = (new Date().getDay() + 6) % 7;
  const maxRev = Math.max(...chartData.map((d) => d.revenue), 1);
  const minRev = Math.min(...chartData.map((d) => d.revenue));
  const prevRevForDelta = (i) => (i > 0 ? chartData[i - 1].revenue : null);
  const norm = (v) => maxRev === minRev ? 0.5 : (v - minRev) / (maxRev - minRev);
  const W = 1000, H = 300, P = 30;
  const pts = chartData.map((d, i) => ({
    ix: i,
    x: (i / Math.max(chartData.length - 1, 1)) * (W - P * 2) + P,
    y: H - (norm(d.revenue) * (H - P * 2) + P),
  }));

  let path = "";
  const linePts = pts.filter((p) => (weeksAgo === 0 ? p.ix <= todayIdx : true));
  if (linePts.length >= 2) {
    path = `M ${linePts[0].x} ${linePts[0].y}`;
    for (let i = 0; i < linePts.length - 1; i++) {
      const c = linePts[i],
        n = linePts[i + 1];
      path += ` C ${c.x + (n.x - c.x) / 3} ${c.y}, ${c.x + (n.x - c.x) * (2 / 3)} ${n.y}, ${n.x} ${n.y}`;
    }
  }

  const totalRev = chartData.reduce((s, d) => s + d.revenue, 0);

  const tooltipPct = hoverIdx != null && prevRevForDelta(hoverIdx) != null && prevRevForDelta(hoverIdx) > 0
    ? Math.round(
        ((chartData[hoverIdx].revenue - prevRevForDelta(hoverIdx)) / prevRevForDelta(hoverIdx)) * 100,
      )
    : null;

  return (
    <div className="relative flex flex-col gap-3">
      {hoverIdx != null && (
        <div
          className="absolute left-1/2 -translate-x-1/2 bottom-[48px] z-20 max-w-[220px] rounded-xl border border-slate-200 bg-white px-3 py-2 text-[11px] font-medium text-slate-800 shadow-lg pointer-events-none text-center"
          role="tooltip"
        >
          <div className="font-bold text-slate-900">{chartData[hoverIdx]?.date}</div>
          <div className="mt-0.5 tabular-nums">
            ₺{Math.round(chartData[hoverIdx]?.revenue ?? 0).toLocaleString("tr-TR")} ciro
          </div>
          {tooltipPct != null && hoverIdx > 0 && (
            <div className="text-slate-600 text-[10px] mt-1">
              Önceki güne göre %{Math.abs(tooltipPct)} {tooltipPct >= 0 ? "üzerinde" : "altında"}
            </div>
          )}
        </div>
      )}
      <div className="h-36 relative">
        <svg className="w-full h-full" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="revGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#34d399" />
            </linearGradient>
          </defs>
          {chartData.map((d, i) => {
            const isFuture = weeksAgo === 0 && i > todayIdx;
            const bw = W / chartData.length;
            return (
              <rect
                key={i}
                x={i * bw}
                y={0}
                width={bw}
                height={H}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => !isFuture && setHoverIdx(i)}
                onMouseLeave={() => setHoverIdx(null)}
              />
            );
          })}
          {path && (
            <motion.path
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 1.4, ease: "easeInOut" }}
              d={path}
              fill="none"
              stroke="url(#revGrad)"
              strokeWidth="5"
              strokeLinecap="round"
              pointerEvents="none"
            />
          )}
          {linePts.map((p) => (
            <circle
              key={p.ix}
              cx={p.x}
              cy={p.y}
              r={hoverIdx === p.ix ? 11 : 8}
              fill="#fff"
              stroke="#10b981"
              strokeWidth={hoverIdx === p.ix ? 5 : 4}
              pointerEvents="none"
            />
          ))}
        </svg>
        <div className="absolute inset-x-0 bottom-0 flex justify-between pointer-events-none">
          {chartData.map((d, i) => (
            <span
              key={i}
              className={`text-[9px] font-bold uppercase tracking-wider flex-1 text-center ${hoverIdx === i ? "text-emerald-600" : "text-slate-400"}`}
            >
              {d.date}
            </span>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between text-[11px] text-slate-500">
        <span>
          Haftalık toplam:{" "}
          <strong className="text-slate-800">₺{Math.round(totalRev).toLocaleString("tr-TR")}</strong>
        </span>
        <span className="text-emerald-600 font-semibold">Günlük ciro eğrisi</span>
      </div>
    </div>
  );
}

export default function AnalyticsSection({ data, loading, weeksAgo, setWeeksAgo }) {
  const chartData = data?.weekly_chart_data;

  return (
    <div className="flex flex-col gap-5 mt-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-[15px] font-bold text-slate-900">Operasyonel Analitik</h2>
          <p className="text-[11px] text-slate-400 mt-0.5">Seçilen haftanın sipariş ve ciro görünümü</p>
        </div>
        <WeekNav weeksAgo={weeksAgo} setWeeksAgo={setWeeksAgo} />
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white border border-slate-100 rounded-2xl p-6" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
          <div className="flex items-center gap-2 mb-5">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-indigo-600" />
            </div>
            <div>
              <p className="text-[13px] font-bold text-slate-900">Sipariş Akışı</p>
              <p className="text-[10px] text-slate-400">Seçilen haftanın gün bazlı sipariş sayıları</p>
            </div>
          </div>
          {loading ? <div className="h-40 animate-shimmer rounded-xl" /> : <BarChart chartData={chartData} weeksAgo={weeksAgo} />}
        </div>

        <div className="bg-white border border-slate-100 rounded-2xl p-6" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
          <div className="flex items-center gap-2 mb-5">
            <div className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            </div>
            <div>
              <p className="text-[13px] font-bold text-slate-900">Gelir Analizi</p>
              <p className="text-[10px] text-slate-400">Günlük ciro · üzerinde gezin</p>
            </div>
          </div>
          {loading ? <div className="h-40 animate-shimmer rounded-xl" /> : <LineChart chartData={chartData} weeksAgo={weeksAgo} />}
        </div>
      </div>
    </div>
  );
}
