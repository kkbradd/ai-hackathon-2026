import { motion } from "framer-motion";
import { MapPin, Clock } from "lucide-react";

export default function ShipmentTimeline({ updates = [], isDelayed }) {
  if (!updates.length) {
    return (
      <p className="text-[13px] font-medium text-slate-500 py-2">
        Henüz kargo hareketi kaydedilmemiş.
      </p>
    );
  }

  return (
    <div className="relative pl-6">
      {/* Gradient vertical line */}
      <div className="absolute left-0 top-3 bottom-3 w-0.5 bg-gradient-to-b from-emerald-400 via-indigo-400 to-slate-200 rounded-full" />

      {updates.map((update, i) => {
        const isLast = i === updates.length - 1;

        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06, duration: 0.3 }}
            className="relative flex gap-4 pb-6 last:pb-0"
          >
            {/* Node dot */}
            <div className="absolute -left-[25px] top-0.5 flex items-center justify-center">
              {isLast ? (
                <div className="relative">
                  <div className="w-3 h-3 rounded-full bg-indigo-600 border-2 border-indigo-200 shadow-sm" />
                  {/* Pulsing ring */}
                  <motion.div
                    animate={{ scale: [1, 1.8, 1], opacity: [0.3, 0, 0.3] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    className="absolute inset-0 rounded-full bg-indigo-400"
                  />
                </div>
              ) : (
                <div className="w-3 h-3 rounded-full bg-emerald-500 border-2 border-emerald-200" />
              )}
            </div>

            {/* Content */}
            <div className="pl-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className={`${
                    isLast
                      ? "text-[14px] font-extrabold text-slate-900"
                      : "text-[13px] font-bold text-slate-500"
                  }`}
                >
                  {update.status}
                </span>
                {isLast && isDelayed && (
                  <span className="bg-red-100 text-red-700 border border-red-200 text-[10px] px-2 py-0.5 rounded-md font-bold uppercase">
                    Gecikmiş
                  </span>
                )}
              </div>

              {update.location && (
                <div className="flex items-center gap-1 mt-1">
                  <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="text-[12px] font-medium text-slate-600">{update.location}</span>
                </div>
              )}

              {update.description && (
                <p className="text-[12px] font-medium text-slate-600 mt-1">{update.description}</p>
              )}

              {update.timestamp && (
                <div className="flex items-center gap-1 mt-1.5">
                  <Clock className="w-3 h-3 text-slate-400 shrink-0" />
                  <span className="text-[11px] font-semibold text-slate-500">{update.timestamp}</span>
                </div>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
