import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, ChevronRight } from "lucide-react";

const CATEGORY_TR = {
  teslimat_gecikmesi: "Teslimat",
  yanlis_urun: "Yanlış ürün",
  siparis_talebi: "Sipariş",
  fatura_duzeltme: "Fatura",
  stok_bilgisi: "Stok",
  genel_destek: "Genel",
};

export default function TodayMessagesCard({ data, loading }) {
  const navigate = useNavigate();
  const count = data?.inbound_messages_today_count ?? 0;
  const items = data?.inbound_messages_today ?? [];

  if (loading) {
    return (
      <div className="bg-white border border-slate-100 rounded-2xl p-5 h-36 animate-pulse" />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm"
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-violet-50 flex items-center justify-center">
            <Mail className="w-4 h-4 text-violet-600" />
          </div>
          <div>
            <h3 className="text-[14px] font-bold text-slate-900">Bugün gelen müşteri mesajları</h3>
            <p className="text-[11px] text-slate-500">
              Bugün kayda geçen <span className="font-bold text-slate-800 tabular-nums">{count}</span> gelen ileti
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate("/messages")}
          className="text-[11px] font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-0.5 shrink-0"
        >
          Tümü
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {items.length === 0 ? (
        <p className="text-[12px] text-slate-400 font-medium py-2">Bugün için yeni gelen mesaj yok.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((m) => (
            <li
              key={m.id}
              className="flex flex-col gap-0.5 border border-slate-50 rounded-xl px-3 py-2 bg-slate-50/50"
            >
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="font-semibold text-slate-800 truncate max-w-[180px] text-[12px]">{m.customer_name}</span>
                {m.category && (
                  <span className="text-[10px] font-bold text-violet-700 bg-violet-50 px-2 py-0.5 rounded-md">
                    {CATEGORY_TR[m.category] ?? m.category.replace(/_/g, " ")}
                  </span>
                )}
                <span className="text-slate-400 text-[10px] ml-auto">{m.created_at}</span>
              </div>
              {m.ai_summary && (
                <p className="text-[11.5px] text-slate-600 leading-snug truncate">{m.ai_summary}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </motion.div>
  );
}
