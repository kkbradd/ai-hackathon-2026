import { useState, useRef, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send, Brain, BarChart3, AlertTriangle, ClipboardList, Package,
  Sparkles, Truck, MessageSquare, Zap, ArrowRight, Mic,
} from "lucide-react";
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

const CAPABILITY_CARDS = [
  {
    Icon: BarChart3,
    title: "Operasyonel Özet",
    body: "Günün özetini, kritik durumları ve önerilen aksiyonları al.",
    sample: "Bugün dikkat etmem gereken 3 şey ne?",
    iconColor: "text-emerald-700",
    iconBg: "bg-emerald-50",
    border: "border-emerald-100/80",
  },
  {
    Icon: Truck,
    title: "Lojistik Takibi",
    body: "Gecikmiş kargolar, taşıyıcı performansı, dağıtım durumu.",
    sample: "Hangi kargolar bugün gecikti?",
    iconColor: "text-amber-700",
    iconBg: "bg-amber-50",
    border: "border-amber-100/80",
  },
  {
    Icon: Package,
    title: "Stok Zekası",
    body: "Eşik altı ürünler, talep trendi, sipariş önerisi.",
    sample: "Önümüzdeki hafta hangi ürünleri sipariş etmeliyim?",
    iconColor: "text-yellow-700",
    iconBg: "bg-yellow-50",
    border: "border-yellow-100/80",
  },
  {
    Icon: MessageSquare,
    title: "Müşteri Sinyalleri",
    body: "Şikayet sınıflandırma, urgency analizi, hızlı yanıt taslağı.",
    sample: "Yüksek öncelikli müşteri mesajlarını özetle",
    iconColor: "text-violet-700",
    iconBg: "bg-violet-50",
    border: "border-violet-100/80",
  },
];

const STATS = [
  { val: "Gemini 2.5", label: "Flash" },
  { val: "Groq", label: "Fallback" },
  { val: "4/4", label: "Ajan canlı" },
  { val: "15 dk", label: "Tarama döngüsü" },
];

export default function ChatPanel() {
  const { messages, loading, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);
  const showEmpty = messages.length <= 1;

  const SpeechRecognition = useMemo(
    () =>
      typeof window !== "undefined"
        ? window.SpeechRecognition || window.webkitSpeechRecognition
        : null,
    [],
  );
  const voiceSupported = !!SpeechRecognition;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }, [input]);

  useEffect(() => {
    if (!voiceSupported) return;
    const rec = new SpeechRecognition();
    rec.lang = "tr-TR";
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (e) => {
      const transcript = Array.from(e.results)
        .map((r) => r[0].transcript)
        .join("");
      setInput(transcript);
    };
    rec.onerror = (e) => {
      setListening(false);
      const msg =
        e.error === "not-allowed" || e.error === "service-not-allowed"
          ? "Mikrofon izni reddedildi."
          : e.error === "no-speech"
          ? "Ses algılanamadı."
          : "Ses tanıma hatası.";
      setVoiceError(msg);
      setTimeout(() => setVoiceError(""), 3500);
    };
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    return () => {
      try { rec.abort(); } catch { /* noop */ }
    };
  }, [voiceSupported, SpeechRecognition]);

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

  function toggleVoice() {
    const rec = recognitionRef.current;
    if (!rec) return;
    if (listening) {
      try { rec.stop(); } catch { /* noop */ }
      return;
    }
    setVoiceError("");
    try {
      rec.start();
      setListening(true);
    } catch {
      /* already started */
    }
  }

  return (
    <div className="flex flex-col h-full min-h-0 bg-slate-50/30">

      {/* ── Header ── */}
      <header className="shrink-0 border-b border-slate-100 bg-white">
        <div className="w-full px-6 py-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-yellow-500 to-emerald-700 flex items-center justify-center shadow-sm shadow-yellow-200/50 shrink-0">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-[14px] font-extrabold text-slate-900 leading-none">AI Asistan</h1>
            <p className="text-[11px] text-slate-400 font-medium mt-0.5">Operasyonel sorularını doğal dilde sor</p>
          </div>
        </div>
      </header>

      {/* ── Scrollable area ── */}
      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col">

        {/* Empty state — editorial moment */}
        {showEmpty && (
          <div className="flex-1 flex items-center justify-center px-6 py-10">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="relative w-full max-w-4xl"
            >
              {/* Hero block */}
              <div
                className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950 mb-6"
                style={{ borderRadius: "20px", padding: "44px 48px" }}
              >
                {/* Atmospheric orbs */}
                <div className="absolute -top-24 -right-16 w-80 h-80 bg-yellow-500/[0.13] rounded-full blur-[100px] pointer-events-none" />
                <div className="absolute -bottom-24 -left-16 w-96 h-96 bg-emerald-600/[0.10] rounded-full blur-[120px] pointer-events-none" />
                <div
                  className="absolute inset-0 opacity-[0.05] pointer-events-none"
                  style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "26px 26px" }}
                />

                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="min-w-0">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 mb-4">
                      <Sparkles className="w-3 h-3 text-yellow-300" />
                      <span className="text-[10px] font-bold text-yellow-300 tracking-[0.22em] uppercase">
                        AI ortağı · canlı veri
                      </span>
                    </div>
                    <h2 className="text-[34px] sm:text-[42px] font-black text-white tracking-tight leading-[1.05]">
                      Operasyonu{" "}
                      <span className="bg-gradient-to-r from-yellow-300 via-amber-200 to-emerald-300 bg-clip-text text-transparent">
                        doğal dilde
                      </span>{" "}
                      sor.
                    </h2>
                    <p className="text-[14.5px] text-slate-400 mt-3 leading-relaxed max-w-xl">
                      Sipariş, stok, kargo ve müşteri verisinin tamamına erişebilen{" "}
                      <span className="text-slate-200 font-semibold">çoklu-ajan</span> AI sistemi.
                      Tek bir soru — tam operasyonel cevap.
                    </p>
                  </div>

                  <div className="hidden md:flex w-20 h-20 rounded-2xl bg-gradient-to-br from-yellow-400 via-amber-500 to-emerald-600 items-center justify-center shadow-2xl shadow-emerald-900/40 shrink-0">
                    <Brain className="w-10 h-10 text-white" />
                  </div>
                </div>

                {/* Stats row */}
                <div className="relative z-10 grid grid-cols-2 sm:grid-cols-4 gap-3 mt-7 pt-5 border-t border-white/[0.08]">
                  {STATS.map((s, i) => (
                    <div key={i} className="flex flex-col">
                      <span className="text-[18px] font-black text-white tracking-tight tabular-nums">{s.val}</span>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.18em] mt-0.5">{s.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Capability cards */}
              <p className="text-[10.5px] font-bold text-slate-500 uppercase tracking-[0.22em] mb-3 px-1">
                Şunları sorabilirsin
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {CAPABILITY_CARDS.map((c, i) => (
                  <motion.button
                    type="button"
                    key={c.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, delay: 0.12 + i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                    onClick={() => sendMessage(c.sample)}
                    disabled={loading}
                    className={`group flex items-start gap-3 text-left rounded-xl border bg-white ${c.border} hover:shadow-md hover:border-slate-300 transition-all p-4 disabled:opacity-50`}
                    style={{ borderRadius: "14px" }}
                  >
                    <div className={`w-10 h-10 rounded-xl ${c.iconBg} flex items-center justify-center shrink-0`}>
                      <c.Icon className={`w-5 h-5 ${c.iconColor}`} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-extrabold text-slate-900 leading-tight">{c.title}</p>
                      <p className="text-[11.5px] text-slate-500 leading-snug mt-1">{c.body}</p>
                      <p className="text-[11px] font-semibold text-slate-700 leading-snug mt-2 flex items-center gap-1 group-hover:text-slate-900">
                        <span className="italic opacity-80">"{c.sample}"</span>
                        <ArrowRight className="w-3 h-3 shrink-0 opacity-60 group-hover:translate-x-0.5 transition-transform" />
                      </p>
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          </div>
        )}

        {/* Messages */}
        {!showEmpty && (
          <div className="flex flex-col gap-4 px-6 py-6 pb-4 max-w-4xl mx-auto w-full">
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
      <div className="shrink-0 border-t border-slate-100 bg-white py-4 px-6 flex justify-center">
        <div
          className="flex flex-col gap-2.5 w-full"
          style={{ maxWidth: "640px" }}
        >

          {/* Suggestion chips — only when chat is active */}
          {!showEmpty && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
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
          )}

          {/* Text input row */}
          <form onSubmit={handleSubmit} className="flex gap-2 items-end">
            <div className="relative flex-1 rounded-2xl border border-slate-200 bg-slate-50 focus-within:border-yellow-400 focus-within:bg-white focus-within:ring-2 focus-within:ring-yellow-200/50 transition-all">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                placeholder={listening ? "Dinliyorum…" : "Operasyonel soru yazın…"}
                rows={1}
                className="w-full bg-transparent text-[14px] font-medium text-slate-900 placeholder-slate-400 resize-none px-4 py-3 outline-none disabled:opacity-50 max-h-32 overflow-y-auto leading-relaxed"
              />
            </div>
            {voiceSupported && (
              <motion.button
                type="button"
                onClick={toggleVoice}
                whileTap={{ scale: 0.94 }}
                className={`relative h-10 w-10 shrink-0 rounded-xl flex items-center justify-center transition-colors border ${
                  listening
                    ? "bg-red-500 border-red-600 text-white shadow-sm shadow-red-200"
                    : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
                aria-label={listening ? "Dinlemeyi durdur" : "Sesle yaz"}
                title={listening ? "Dinlemeyi durdur" : "Sesle yaz (Türkçe)"}
              >
                <Mic className="w-4 h-4" />
                {listening && (
                  <span className="absolute inset-0 rounded-xl bg-red-500/40 animate-ping pointer-events-none" />
                )}
              </motion.button>
            )}
            <motion.button
              type="submit"
              disabled={loading || !input.trim()}
              whileTap={{ scale: 0.95 }}
              className="h-10 w-10 shrink-0 bg-gradient-to-br from-yellow-500 to-emerald-700 hover:from-yellow-400 hover:to-emerald-600 disabled:opacity-40 disabled:bg-slate-200 disabled:cursor-not-allowed rounded-xl flex items-center justify-center transition-all shadow-sm shadow-yellow-200/50"
              aria-label="Gönder"
            >
              <Send className="w-4 h-4 text-white ml-0.5" />
            </motion.button>
          </form>

          {voiceError ? (
            <p className="text-[11px] font-bold text-red-600 text-center">{voiceError}</p>
          ) : (
            <p className="text-[10px] text-slate-400 text-center font-medium">
              {voiceSupported
                ? "Enter ile gönder · Shift+Enter satır sonu · Mikrofon ile sesle yaz"
                : "Enter ile gönder · Shift+Enter satır sonu"}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
