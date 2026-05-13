import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mail, Send, X, Loader2, RefreshCw, Sparkles, CheckCircle,
  ChevronDown, ChevronUp, Building2, Package, AlertCircle,
} from "lucide-react";
import {
  fetchSupplierDrafts, sendSupplierDraft, cancelSupplierDraft,
} from "../../api/client";

const TRIGGERED_BY_LABEL = {
  agent: "Otomatik (envanter ajanı)",
  chat: "AI sohbet aracı",
  manual: "Manuel oluşturuldu",
};

function DraftCard({ draft, onSent, onCancelled }) {
  const [expanded, setExpanded] = useState(false);
  const [busy, setBusy] = useState(null);

  const isPending = draft.status === "draft";
  const isSent = draft.status === "sent";
  const isCancelled = draft.status === "cancelled";

  async function handleSend() {
    setBusy("send");
    try {
      const res = await sendSupplierDraft(draft.id);
      onSent?.(res);
    } catch (e) {
      alert(e?.response?.data?.detail || "Gönderim başarısız.");
    } finally {
      setBusy(null);
    }
  }

  async function handleCancel() {
    if (!confirm("Bu taslak iptal edilsin mi?")) return;
    setBusy("cancel");
    try {
      await cancelSupplierDraft(draft.id);
      onCancelled?.(draft.id);
    } catch (e) {
      alert(e?.response?.data?.detail || "İptal başarısız.");
    } finally {
      setBusy(null);
    }
  }

  const statusBadge = isSent
    ? { cls: "bg-emerald-100 text-emerald-700 border-emerald-200", label: "✓ Gönderildi" }
    : isCancelled
    ? { cls: "bg-slate-100 text-slate-500 border-slate-200", label: "İptal edildi" }
    : { cls: "bg-amber-50 text-amber-700 border-amber-200", label: "Onay bekliyor" };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`bg-white border rounded-3xl overflow-hidden transition-shadow ${
        isPending ? "border-amber-200 shadow-sm" : "border-slate-200"
      }`}
    >
      {/* Email-style header */}
      <div className={`px-5 py-4 border-b ${isPending ? "bg-amber-50/40 border-amber-100" : "bg-slate-50/60 border-slate-100"}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
              isPending ? "bg-amber-100 text-amber-700" : "bg-slate-200 text-slate-500"
            }`}>
              <Mail className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-semibold mb-0.5">
                <Sparkles className="w-3 h-3 text-indigo-500" />
                <span>AI tarafından üretildi · {TRIGGERED_BY_LABEL[draft.triggered_by] || draft.triggered_by}</span>
              </div>
              <p className="text-[14px] font-extrabold text-slate-900 leading-snug truncate">
                {draft.subject}
              </p>
              <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1 text-[11px] text-slate-500 font-medium">
                <span className="flex items-center gap-1">
                  <Building2 className="w-3 h-3" />
                  <strong className="text-slate-700">{draft.supplier_name}</strong>
                </span>
                <span className="text-slate-400">{draft.supplier_email}</span>
              </div>
            </div>
          </div>
          <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full border whitespace-nowrap shrink-0 ${statusBadge.cls}`}>
            {statusBadge.label}
          </span>
        </div>
      </div>

      {/* Product line */}
      <div className="px-5 py-2.5 bg-white flex items-center gap-2 text-[12px] border-b border-slate-50">
        <Package className="w-3.5 h-3.5 text-indigo-500" />
        <span className="font-bold text-slate-700">{draft.product_name}</span>
        <span className="text-slate-400">·</span>
        <span className="text-slate-500 font-medium">{draft.quantity.toFixed(0)} {draft.unit}</span>
        <span className="text-slate-300 ml-auto text-[11px]">{draft.created_at}</span>
      </div>

      {/* Body preview / expanded */}
      <div className="px-5 py-3 bg-white">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="w-full flex items-center gap-1.5 text-[11px] font-bold text-indigo-600 hover:text-indigo-700 mb-2"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? "E-postayı gizle" : "E-postayı önizle"}
        </button>
        <AnimatePresence initial={false}>
          {expanded && (
            <motion.pre
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="text-[12px] text-slate-700 leading-relaxed font-sans whitespace-pre-wrap bg-slate-50 border border-slate-100 rounded-2xl p-4 overflow-hidden"
            >
              {draft.body}
            </motion.pre>
          )}
        </AnimatePresence>
        {!expanded && (
          <p className="text-[12px] text-slate-500 leading-relaxed line-clamp-2">
            {draft.body}
          </p>
        )}
      </div>

      {/* Actions */}
      {isPending && (
        <div className="px-5 pb-4 flex gap-2 bg-white">
          <button
            type="button"
            onClick={handleSend}
            disabled={!!busy}
            className="flex-[2] flex items-center justify-center gap-2 h-10 bg-emerald-600 hover:bg-emerald-700 text-white text-[12px] font-extrabold rounded-2xl transition-colors disabled:opacity-60"
          >
            {busy === "send" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {busy === "send" ? "Gönderiliyor…" : "Tedarikçiye Gönder"}
          </button>
          <button
            type="button"
            onClick={handleCancel}
            disabled={!!busy}
            className="flex items-center justify-center gap-1.5 h-10 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[12px] font-bold rounded-2xl transition-colors disabled:opacity-60"
          >
            <X className="w-3.5 h-3.5" />
            İptal
          </button>
        </div>
      )}

      {isSent && (
        <div className="px-5 pb-4 bg-white">
          <div className="flex items-center gap-2 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2 font-semibold">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{draft.sent_at} tarihinde {draft.supplier_email} adresine iletildi</span>
          </div>
        </div>
      )}
    </motion.div>
  );
}

export default function SupplierDraftsPanel() {
  const [drafts, setDrafts] = useState([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSupplierDrafts();
      setDrafts(data.drafts || []);
      setPendingCount(data.pending_count || 0);
    } catch {
      // sessizce yut — backend boşsa boş listede kalsın
      setDrafts([]);
      setPendingCount(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const int = setInterval(refresh, 30000);
    return () => clearInterval(int);
  }, [refresh]);

  function handleSent(res) {
    setToast({ ok: true, msg: res?.detail || "Gönderildi." });
    setTimeout(() => setToast(null), 3500);
    refresh();
  }

  function handleCancelled() {
    setToast({ ok: true, msg: "Taslak iptal edildi." });
    setTimeout(() => setToast(null), 3000);
    refresh();
  }

  // Hiç draft yoksa minik bir "her şey yolunda" chip'i göster (kayıp olmayalım)
  if (!loading && drafts.length === 0) {
    return (
      <div className="flex items-center gap-2 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-xl px-3 py-2 w-fit">
        <Sparkles className="w-3 h-3" />
        AI tedarikçi taslakları: şu an onay bekleyen yok
        <CheckCircle className="w-3 h-3 ml-1" />
      </div>
    );
  }

  return (
    <section className="relative">
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className={`fixed top-6 right-6 z-50 px-4 py-2.5 rounded-2xl shadow-lg text-[12px] font-extrabold ${
            toast.ok ? "bg-emerald-600 text-white" : "bg-red-600 text-white"
          }`}
        >
          {toast.msg}
        </motion.div>
      )}

      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-black text-slate-900 tracking-tight">
              Tedarikçi E-posta Taslakları
            </h2>
            <p className="text-[11px] font-medium text-slate-400">
              AI tarafından üretildi · operatör onayıyla iletilir
              {pendingCount > 0 && (
                <span className="ml-2 inline-flex items-center gap-1 text-amber-600 font-bold">
                  <AlertCircle className="w-3 h-3" />
                  {pendingCount} taslak onay bekliyor
                </span>
              )}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={refresh}
          className="p-2 rounded-xl hover:bg-slate-100 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {loading && drafts.length === 0 ? (
          <div className="h-32 bg-white border border-slate-100 rounded-3xl animate-pulse" />
        ) : (
          drafts.map((d) => (
            <DraftCard
              key={d.id}
              draft={d}
              onSent={handleSent}
              onCancelled={handleCancelled}
            />
          ))
        )}
      </div>
    </section>
  );
}
