import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Mail, CheckCircle, Clock, User, Inbox, RefreshCw, ChevronRight,
  Filter, Package, Truck, Plus, X, Sparkles, AlertTriangle, Loader2,
  Send, ChevronDown,
} from "lucide-react";
import { useMessages } from "../hooks/useMessages";
import { createMessage, fetchMessageCategories, fetchCustomers } from "../api/client";

const CATEGORY_OPTIONS = [
  { value: "", label: "Tüm kategoriler" },
  { value: "teslimat_gecikmesi", label: "Teslimat gecikmesi" },
  { value: "urun_hasari", label: "Ürün / hasar" },
  { value: "yanlis_urun", label: "Yanlış ürün" },
  { value: "paket_hasari", label: "Paket hasarı" },
  { value: "siparis_talebi", label: "Sipariş talebi" },
  { value: "fatura_duzeltme", label: "Fatura" },
  { value: "stok_bilgisi", label: "Stok sorusu" },
  { value: "genel_destek", label: "Genel" },
];

const URGENCY_LABEL = {
  yüksek: "Yüksek öncelik",
  orta: "Normal",
  düşük: "Düşük",
};

const URGENCY_COLOR = {
  yüksek: "bg-red-100/90 text-red-800 border-red-200/80",
  orta: "bg-amber-50 text-amber-900 border-amber-200/80",
  düşük: "bg-slate-100 text-slate-600 border-slate-200",
};

// ── New Message Modal ─────────────────────────────────────────────────────────

function NewMessageModal({ onClose, onCreated }) {
  const [customers, setCustomers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({
    customer_id: "",
    category: "",
    subject: "",
    body: "",
    related_order_id: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [customerSearch, setCustomerSearch] = useState("");
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false);

  useEffect(() => {
    fetchMessageCategories().then((d) => setCategories(d.categories || [])).catch(() => {});
    fetchCustomers().then((d) => setCustomers(d.customers || [])).catch(() => {});
  }, []);

  const filteredCustomers = useMemo(() => {
    if (!customerSearch) return customers.slice(0, 10);
    const q = customerSearch.toLowerCase();
    return customers.filter((c) => c.name.toLowerCase().includes(q)).slice(0, 10);
  }, [customers, customerSearch]);

  const selectedCustomer = customers.find((c) => c.id === Number(form.customer_id));

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.customer_id || !form.category || !form.subject.trim() || !form.body.trim()) {
      setError("Müşteri, kategori, konu ve mesaj zorunludur.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const res = await createMessage({
        customer_id: Number(form.customer_id),
        category: form.category,
        subject: form.subject.trim(),
        body: form.body.trim(),
        related_order_id: form.related_order_id ? Number(form.related_order_id) : undefined,
      });
      setResult(res);
      onCreated?.();
    } catch (err) {
      setError(err?.response?.data?.detail || "Mesaj gönderilemedi.");
    } finally {
      setSubmitting(false);
    }
  }

  const selectedCategory = categories.find((c) => c.value === form.category);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && !result && onClose()}
    >
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 24, scale: 0.97 }}
        transition={{ duration: 0.22 }}
        className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm shadow-indigo-200">
              <Plus className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-[15px] font-extrabold text-slate-900">Yeni Mesaj Gir</p>
              <p className="text-[11px] text-slate-400 font-medium">AI kategori analizi ile</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-slate-100 transition-colors"
          >
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {result ? (
          /* ── AI Result View ── */
          <div className="p-6 space-y-4">
            <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-2xl px-4 py-3">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <div>
                <p className="text-[13px] font-extrabold">Mesaj kaydedildi</p>
                <p className="text-[11px] font-medium opacity-80">{result.customer_name} · #{result.id}</p>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-500 shrink-0" />
                <p className="text-[12px] font-extrabold text-slate-800 uppercase tracking-wide">AI Analizi</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200">
                  {categories.find((c) => c.value === result.category)?.label ?? result.category}
                </span>
                <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${URGENCY_COLOR[result.urgency] ?? "bg-slate-100 text-slate-600"}`}>
                  {URGENCY_LABEL[result.urgency] ?? result.urgency}
                </span>
              </div>
              <p className="text-[12px] font-semibold text-slate-600 leading-relaxed">
                <span className="text-[10px] font-black uppercase tracking-wide text-slate-400 mr-1">Özet</span>
                {result.ai_summary}
              </p>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[11px] font-extrabold text-amber-800 uppercase tracking-wide mb-1">Önerilen Aksiyon</p>
                  <p className="text-[13px] font-semibold text-amber-900 leading-relaxed">{result.ai_action}</p>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="w-full h-11 bg-slate-900 text-white text-[13px] font-extrabold rounded-2xl hover:bg-slate-800 transition-colors"
            >
              Kapat
            </button>
          </div>
        ) : (
          /* ── Form View ── */
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Customer picker */}
            <div className="relative">
              <label className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wide block mb-1.5">
                Müşteri
              </label>
              {selectedCustomer ? (
                <div className="flex items-center justify-between bg-indigo-50 border border-indigo-200 rounded-2xl px-4 py-2.5">
                  <div>
                    <p className="text-[13px] font-bold text-slate-900">{selectedCustomer.name}</p>
                    <p className="text-[10px] text-slate-500">{selectedCustomer.email}</p>
                  </div>
                  <button type="button" onClick={() => { set("customer_id", ""); setCustomerSearch(""); }}
                    className="p-1 rounded-lg hover:bg-indigo-100 transition-colors">
                    <X className="w-3.5 h-3.5 text-indigo-500" />
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="text"
                    value={customerSearch}
                    onChange={(e) => { setCustomerSearch(e.target.value); setShowCustomerDropdown(true); }}
                    onFocus={() => setShowCustomerDropdown(true)}
                    placeholder="Müşteri adı ara..."
                    className="w-full h-10 border border-slate-200 rounded-2xl px-4 text-[13px] font-medium text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 bg-slate-50/80"
                  />
                  <ChevronDown className="absolute right-3 top-2.5 w-4 h-4 text-slate-400 pointer-events-none" />
                  {showCustomerDropdown && filteredCustomers.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-2xl shadow-lg z-10 overflow-hidden max-h-44 overflow-y-auto">
                      {filteredCustomers.map((c) => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => { set("customer_id", c.id); setCustomerSearch(""); setShowCustomerDropdown(false); }}
                          className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors text-left"
                        >
                          <div className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 text-[10px] font-bold flex items-center justify-center shrink-0">
                            {c.name[0]}
                          </div>
                          <div className="min-w-0">
                            <p className="text-[13px] font-semibold text-slate-900 truncate">{c.name}</p>
                            <p className="text-[10px] text-slate-400 capitalize">{c.customer_type}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Category */}
            <div>
              <label className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wide block mb-1.5">
                Konu Kategorisi
              </label>
              <div className="flex flex-wrap gap-2">
                {categories.map((c) => (
                  <button
                    key={c.value}
                    type="button"
                    onClick={() => set("category", c.value)}
                    className={`text-[11px] font-bold px-3 py-1.5 rounded-xl border transition-colors ${
                      form.category === c.value
                        ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                        : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"
                    }`}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
              {selectedCategory && (
                <p className="text-[11px] text-slate-400 mt-1.5 font-medium">
                  Otomatik öncelik:
                  <span className={`ml-1 font-bold ${
                    selectedCategory.urgency === "yüksek" ? "text-red-600" :
                    selectedCategory.urgency === "orta" ? "text-amber-600" : "text-slate-500"
                  }`}>
                    {URGENCY_LABEL[selectedCategory.urgency]}
                  </span>
                </p>
              )}
            </div>

            {/* Subject */}
            <div>
              <label className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wide block mb-1.5">
                Konu Başlığı
              </label>
              <input
                type="text"
                value={form.subject}
                onChange={(e) => set("subject", e.target.value)}
                placeholder="Konu başlığını girin..."
                className="w-full h-10 border border-slate-200 rounded-2xl px-4 text-[13px] font-medium text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 bg-slate-50/80"
              />
            </div>

            {/* Body */}
            <div>
              <label className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wide block mb-1.5">
                Mesaj
              </label>
              <textarea
                value={form.body}
                onChange={(e) => set("body", e.target.value)}
                placeholder="Mesaj içeriğini yazın..."
                rows={3}
                className="w-full border border-slate-200 rounded-2xl px-4 py-3 text-[13px] font-medium text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 bg-slate-50/80 resize-none"
              />
            </div>

            {/* Optional order ID */}
            <div>
              <label className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wide block mb-1.5">
                İlgili Sipariş No <span className="font-medium normal-case text-slate-400">(isteğe bağlı)</span>
              </label>
              <input
                type="number"
                value={form.related_order_id}
                onChange={(e) => set("related_order_id", e.target.value)}
                placeholder="Sipariş numarası..."
                className="w-full h-10 border border-slate-200 rounded-2xl px-4 text-[13px] font-medium text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 bg-slate-50/80"
              />
            </div>

            {error && (
              <p className="text-[12px] font-bold text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
                {error}
              </p>
            )}

            <div className="flex gap-2 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 h-11 bg-slate-100 text-slate-700 text-[13px] font-extrabold rounded-2xl hover:bg-slate-200 transition-colors"
              >
                İptal
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-[2] h-11 bg-indigo-600 text-white text-[13px] font-extrabold rounded-2xl hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    AI analiz yapıyor…
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Kaydet ve Analiz Et
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </motion.div>
    </motion.div>
  );
}

// ── Message Card ──────────────────────────────────────────────────────────────

function MessageCard({ msg, onMarkRead, index }) {
  const navigate = useNavigate();

  const urgencyCls =
    msg.urgency === "yüksek"
      ? "bg-red-100/90 text-red-800 border-red-200/80"
      : msg.urgency === "düşük"
      ? "bg-slate-100 text-slate-600 border-slate-200"
      : "bg-amber-50 text-amber-900 border-amber-200/80";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
      className={`relative group rounded-3xl transition-all hover:shadow-md border p-6 ${
        msg.is_read ? "border-slate-200 bg-white" : "border-indigo-200 bg-indigo-50/30 shadow-sm"
      }`}
    >
      <div className="flex flex-col lg:flex-row gap-5 lg:gap-8">
        <div className="flex items-start gap-4 flex-1 min-w-0">
          <div
            className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${msg.is_read ? "bg-slate-100 text-slate-400" : "bg-indigo-100 text-indigo-600"}`}
          >
            {msg.is_read ? <CheckCircle className="w-6 h-6" /> : <Mail className="w-6 h-6" />}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-start justify-between gap-3 mb-2">
              <h3 className="text-[16px] font-extrabold text-slate-900 leading-snug">{msg.subject || "Konusuz mesaj"}</h3>
              <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1 shrink-0 whitespace-nowrap">
                <Clock className="w-3 h-3" />
                {msg.created_at}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="text-[11px] font-bold text-indigo-600 bg-white/80 px-2 py-0.5 rounded-md flex items-center gap-1 border border-indigo-100">
                <User className="w-3 h-3" />
                {msg.customer_name}
              </span>
              <span className="text-[11px] font-medium text-slate-400 truncate">{msg.customer_email}</span>
              <span className="text-[10px] font-bold uppercase tracking-wide text-slate-500 px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200">
                {msg.direction === "outbound" ? "Giden" : "Gelen"}
              </span>
              {msg.direction === "inbound" && msg.category && (
                <span className="text-[10px] font-bold text-violet-700 bg-violet-50 border border-violet-100 px-2 py-0.5 rounded-full">
                  {msg.category.replace(/_/g, " ")}
                </span>
              )}
              {msg.direction === "inbound" && msg.urgency && (
                <span className={`text-[10px] font-black px-2 py-0.5 rounded-full border ${urgencyCls}`}>
                  {URGENCY_LABEL[msg.urgency] ?? msg.urgency}
                </span>
              )}
            </div>

            {msg.ai_summary && (
              <p className="text-[12px] font-semibold text-slate-600 bg-white/70 border border-slate-100 rounded-xl px-3 py-2 mb-4 leading-relaxed">
                <span className="text-[10px] font-black uppercase tracking-wide text-indigo-500 mr-2">Özet</span>
                {msg.ai_summary}
              </p>
            )}

            <p className="text-[14px] text-slate-600 leading-relaxed line-clamp-4">{msg.body}</p>

            {(msg.related_order_id || msg.related_shipment_id) && (
              <div className="flex flex-wrap gap-2 mt-4">
                {msg.related_order_id && (
                  <button
                    type="button"
                    onClick={() => navigate("/orders")}
                    className="inline-flex items-center gap-1.5 text-[11px] font-bold text-indigo-700 bg-white border border-indigo-100 px-3 py-1.5 rounded-xl shadow-sm hover:bg-indigo-50 transition-colors"
                  >
                    <Package className="w-3 h-3" />
                    Sipariş #{msg.related_order_id}
                  </button>
                )}
                {msg.related_shipment_id && (
                  <button
                    type="button"
                    onClick={() => navigate("/shipments")}
                    className="inline-flex items-center gap-1.5 text-[11px] font-bold text-slate-700 bg-white border border-slate-200 px-3 py-1.5 rounded-xl shadow-sm hover:bg-slate-50 transition-colors"
                  >
                    <Truck className="w-3 h-3" />
                    Sevkiyat #{msg.related_shipment_id}
                  </button>
                )}
              </div>
            )}

            {!msg.is_read && msg.direction === "inbound" && (
              <button
                type="button"
                onClick={() => onMarkRead(msg.id)}
                className="mt-5 inline-flex items-center gap-2 text-[12px] font-black text-indigo-600 hover:text-indigo-700 bg-white border border-indigo-100 px-4 py-2 rounded-xl shadow-sm hover:shadow"
              >
                Okundu işaretle
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {!msg.is_read && msg.direction === "inbound" && (
        <div className="absolute top-6 right-6">
          <span className="flex h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
        </div>
      )}
    </motion.div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function MessagesPage() {
  const { data, loading, error, refresh, markAsRead } = useMessages();
  const [categoryFilter, setCategoryFilter] = useState("");
  const [showNewModal, setShowNewModal] = useState(false);

  const filtered = useMemo(() => {
    const list = data?.messages ?? [];
    if (!categoryFilter) return list;
    return list.filter(
      (m) => m.direction === "outbound" || m.category === categoryFilter,
    );
  }, [data?.messages, categoryFilter]);

  function handleCreated() {
    refresh();
  }

  return (
    <div className="h-full overflow-auto bg-slate-50/30">
      <div className="max-w-6xl mx-auto px-8 py-12 w-full">
        <div className="flex flex-col gap-10 mb-14">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <h1 className="text-4xl font-black text-slate-900 tracking-tight">Müşteri iletişimleri</h1>
              <p className="text-sm font-semibold text-slate-500 mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 leading-relaxed">
                {!loading && data?.stats ? (
                  <>
                    <span>
                      Okunmamış gelen:{" "}
                      <strong className="text-slate-900 tabular-nums">{data.stats.unread_inbound}</strong>
                    </span>
                    <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0" />
                    <span>
                      Kayıtlı ileti: <strong className="tabular-nums">{data.stats.conversation_total}</strong>
                    </span>
                    <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0" />
                    <span className="text-slate-400 text-xs font-medium">
                      Gelen {data.stats.inbound_total} · Giden {data.stats.outbound_total}
                    </span>
                  </>
                ) : (
                  "Yükleniyor…"
                )}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowNewModal(true)}
                className="flex items-center gap-2 h-10 px-4 bg-indigo-600 text-white text-[12px] font-extrabold rounded-2xl hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-200"
              >
                <Plus className="w-4 h-4" />
                Yeni Mesaj
              </button>
              <button
                type="button"
                onClick={refresh}
                className="p-3 bg-white border border-slate-200 shadow-sm hover:bg-slate-50 rounded-2xl transition-all shrink-0"
              >
                <RefreshCw className={`w-5 h-5 text-slate-600 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-2 text-slate-500">
              <Filter className="w-4 h-4" />
              <span className="text-[12px] font-bold uppercase tracking-wider">Kategori</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {CATEGORY_OPTIONS.map((o) => (
                <button
                  key={o.value || "all"}
                  type="button"
                  onClick={() => setCategoryFilter(o.value)}
                  className={`text-[11px] font-bold px-3 py-1.5 rounded-xl border transition-colors ${
                    categoryFilter === o.value
                      ? "bg-slate-900 text-white border-slate-900 shadow-md"
                      : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-3xl p-5 text-sm font-bold mb-10">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-44 bg-white border border-slate-100 rounded-[32px] animate-pulse" />
            ))
          ) : filtered.length > 0 ? (
            filtered.map((msg, i) => (
              <MessageCard key={msg.id} msg={msg} onMarkRead={markAsRead} index={i} />
            ))
          ) : (
            <div className="text-center py-32 bg-white border border-slate-200 rounded-[40px] shadow-sm">
              <Inbox className="w-16 h-16 text-slate-200 mx-auto mb-4" />
              <p className="text-slate-400 font-black text-xl tracking-tight">Kayıt yok</p>
              <p className="text-slate-400 text-sm font-medium mt-1">Seçilen filtre için sonuç bulunmadı.</p>
            </div>
          )}
        </div>

        {!loading && !error && filtered.length > 0 && (
          <p className="text-center text-[12px] font-semibold text-slate-400 mt-14">
            {filtered.length} kayıt listeleniyor
          </p>
        )}
      </div>

      <AnimatePresence>
        {showNewModal && (
          <NewMessageModal
            onClose={() => setShowNewModal(false)}
            onCreated={handleCreated}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
