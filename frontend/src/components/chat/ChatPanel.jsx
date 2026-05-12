import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Brain, BarChart3, AlertTriangle, ClipboardList, Package } from "lucide-react";
import { useChat } from "../../hooks/useChat";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "../shared/TypingIndicator";

const SUGGESTIONS = [
  { text: "Günlük operasyon raporunu hazırla", Icon: BarChart3, sub: "Kapsamlı operasyon özeti", color: "indigo" },
  { text: "Stok durumunu kontrol et", Icon: Package, sub: "Envanter uyarıları", color: "emerald" },
  { text: "Gecikmiş kargoları listele", Icon: AlertTriangle, sub: "Kritik sevkiyatlar", color: "red" },
  { text: "En çok satılan ürünleri analiz et", Icon: ClipboardList, sub: "7 günlük talep", color: "amber" },
];

const COLORS = {
  indigo: "bg-indigo-50/90 border-indigo-100 text-indigo-800 hover:bg-indigo-100/90",
  emerald: "bg-emerald-50/90 border-emerald-100 text-emerald-800 hover:bg-emerald-100/90",
  red: "bg-red-50/90 border-red-100 text-red-800 hover:bg-red-100/90",
  amber: "bg-amber-50/90 border-amber-100 text-amber-900 hover:bg-amber-100/90",
};

export default function ChatPanel() {
  const { messages, loading, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const showEmpty = messages.length <= 1;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }, [input]);

  function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input.trim());
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <div className="flex flex-col h-full min-h-0 bg-white">

      {/* ── Header ── */}
      <header className="shrink-0 border-b border-slate-100 bg-white">
        <div className="w-full px-6 py-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm shadow-indigo-200 shrink-0">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-[14px] font-extrabold text-slate-900 leading-none">Operasyon asistanı</h1>
            <p className="text-[11px] text-slate-400 font-medium mt-0.5">Sipariş, stok ve sevkiyat özetleri</p>
          </div>
        </div>
      </header>

      {/* ── Scrollable area ── */}
      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col">

        {/* Empty state — takes all available space and centers content */}
        {showEmpty && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex-1 flex flex-col items-center justify-center text-center px-6"
          >
            <div className="w-16 h-16 rounded-[20px] bg-indigo-600 flex items-center justify-center mb-5 shadow-xl shadow-indigo-200/60">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Operasyon ortağınız</h2>
            <p className="text-[13px] font-medium text-slate-400 mt-2.5 max-w-xs leading-relaxed">
              Günlük operasyon, stok uyarıları ve sevkiyat durumunu tek ekrandan sorabilirsiniz.
            </p>
          </motion.div>
        )}

        {/* Messages */}
        {!showEmpty && (
          <div className="flex flex-col gap-4 px-6 py-6 pb-4">
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} />
            ))}
            <AnimatePresence>{loading && <TypingIndicator />}</AnimatePresence>
            <div ref={bottomRef} />
          </div>
        )}
        {showEmpty && <div ref={bottomRef} />}
      </div>

      {/* ── Input bar ── */}
      <div className="shrink-0 border-t border-slate-100 bg-white px-6 py-4">
        <div className="flex flex-col gap-2.5">

          {/* Suggestion chips — full width, 4 equal columns */}
          <div className="grid grid-cols-4 gap-2">
            {SUGGESTIONS.map(({ text, Icon, color, sub }) => (
              <button
                key={text}
                type="button"
                onClick={() => sendMessage(text)}
                disabled={loading}
                className={`flex flex-col items-stretch text-left rounded-xl border px-3 py-2 transition-colors disabled:opacity-50 ${COLORS[color]}`}
              >
                <span className="flex items-center gap-1.5 text-[11px] font-black leading-snug">
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  {text}
                </span>
                <span className="text-[10px] font-medium opacity-70 mt-0.5">{sub}</span>
              </button>
            ))}
          </div>

          {/* Text input row */}
          <form onSubmit={handleSubmit} className="flex gap-2 items-end">
            <div className="relative flex-1 rounded-2xl border border-slate-200 bg-slate-50 focus-within:border-indigo-300 focus-within:bg-white focus-within:ring-2 focus-within:ring-indigo-100/60 transition-all">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                placeholder="Operasyonel soru yazın..."
                rows={1}
                className="w-full bg-transparent text-[14px] font-medium text-slate-900 placeholder-slate-400 resize-none px-4 py-3 outline-none disabled:opacity-50 max-h-32 overflow-y-auto leading-relaxed"
              />
            </div>
            <motion.button
              type="submit"
              disabled={loading || !input.trim()}
              whileTap={{ scale: 0.95 }}
              className="h-10 w-10 shrink-0 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:bg-slate-200 disabled:cursor-not-allowed rounded-xl flex items-center justify-center transition-colors shadow-sm shadow-indigo-200"
              aria-label="Gönder"
            >
              <Send className="w-4 h-4 text-white ml-0.5" />
            </motion.button>
          </form>

          <p className="text-[10px] text-slate-400 text-center font-medium">
            Enter ile gönder · Shift+Enter satır sonu
          </p>
        </div>
      </div>
    </div>
  );
}
