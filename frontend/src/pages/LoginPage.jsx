import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Truck, AlertTriangle, MessageSquare, Sparkles, ArrowRight } from "lucide-react";
import { useAuth } from "../store/authStore";

const FEATURES = [
  { Icon: Truck,          title: "Kargo Takibi",         text: "Gerçek zamanlı 5 günlük lojistik akışı" },
  { Icon: AlertTriangle,  title: "AI Uyarıları",         text: "Gecikme öngörüsü ve operasyonel öneriler" },
  { Icon: MessageSquare,  title: "Doğal Dil",            text: "Müşteri mesajlarını sınıflandır + otomatik taslak" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Giriş başarısız. Lütfen tekrar deneyin.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left panel — value proposition (lg+ only) */}
      <div className="hidden lg:flex flex-col justify-between px-16 py-14 bg-slate-950 relative overflow-hidden">
        {/* Atmospheric orbs — Harman yellow-green palette */}
        <div className="absolute -top-32 -left-20 w-[28rem] h-[28rem] bg-yellow-500/[0.10] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-1/3 -right-20 w-96 h-96 bg-emerald-600/[0.10] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-[22rem] h-[22rem] bg-amber-700/[0.08] rounded-full blur-[100px] pointer-events-none" />
        {/* Faint grid */}
        <div
          className="absolute inset-0 opacity-[0.04] pointer-events-none"
          style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "32px 32px" }}
        />

        {/* Top — Brand */}
        <div className="relative z-10 flex items-center gap-3">
          <img src="/harman-logo.png" alt="Harman" className="w-11 h-11 rounded-xl object-cover shadow-lg ring-1 ring-white/10" />
          <div>
            <p className="text-[18px] font-black text-white tracking-tight leading-none">Harman</p>
            <p className="text-[10px] font-bold text-yellow-500/90 tracking-[0.22em] uppercase mt-1">Tarım Ops · AI</p>
          </div>
        </div>

        {/* Middle — Headline + features */}
        <div className="relative z-10 max-w-md">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-[10.5px] font-bold tracking-[0.18em] text-yellow-300 uppercase mb-6">
              <Sparkles className="w-3 h-3" />
              Gemini · Groq destekli
            </span>
            <h1 className="text-[44px] font-black text-white tracking-tight leading-[1.05]">
              Kooperatifin için
              <br />
              <span className="bg-gradient-to-r from-yellow-300 via-amber-300 to-emerald-300 bg-clip-text text-transparent">
                otonom operasyon.
              </span>
            </h1>
            <p className="text-[15px] text-slate-400 mt-5 leading-relaxed">
              Siparişlerden kargoya, stoktan müşteri mesajına — tüm operasyonu tek panelde yönet, AI ajanları arka planda çalıştır.
            </p>
          </motion.div>

          <div className="mt-10 space-y-3">
            {FEATURES.map(({ Icon, title, text }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.25 + i * 0.1, ease: [0.16, 1, 0.3, 1] }}
                className="flex items-start gap-3 p-3 rounded-2xl bg-white/[0.025] border border-white/[0.06] hover:bg-white/[0.04] transition-colors"
              >
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-yellow-500/20 to-emerald-600/20 border border-yellow-500/15 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-yellow-300" />
                </div>
                <div className="min-w-0">
                  <p className="text-[13px] font-bold text-white leading-tight">{title}</p>
                  <p className="text-[12px] text-slate-400 leading-snug mt-0.5">{text}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Bottom — Footer line */}
        <div className="relative z-10 flex items-center justify-between text-[11px] font-medium text-slate-500">
          <span className="inline-flex items-center gap-2">
            <span className="relative flex w-1.5 h-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400" />
            </span>
            4/4 ajan canlı
          </span>
          <span className="font-mono">v4.2 · Anadolu Tarım Koop.</span>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex items-center justify-center p-8 bg-[#0d0f14] relative overflow-hidden">
        {/* Background orbs — Harman palette */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-yellow-600/[0.10] rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-emerald-700/[0.10] rounded-full blur-3xl pointer-events-none" />

        <div className="w-full max-w-sm relative z-10">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <img src="/harman-logo.png" alt="Harman" className="w-9 h-9 rounded-xl object-cover shadow-lg" />
            <span className="text-[16px] font-bold text-white">Harman</span>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="bg-white/[0.03] backdrop-blur-2xl border border-white/[0.08] rounded-3xl p-8 shadow-2xl"
          >
            <h2 className="text-[22px] font-bold text-white tracking-tight mb-1">
              Hesabınıza giriş yapın
            </h2>
            <p className="text-[13px] text-slate-500 mb-6">
              Demo: admin@demo.com · demo123
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-[13px] font-medium text-slate-400 mb-1.5">
                  E-posta adresi
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="admin@demo.com"
                  className="w-full bg-white/[0.05] border border-white/[0.1] text-white placeholder-slate-600 rounded-xl px-4 py-2.5 text-[14px] outline-none focus:border-yellow-500/60 focus:ring-1 focus:ring-yellow-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-[13px] font-medium text-slate-400 mb-1.5">
                  Şifre
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-white/[0.05] border border-white/[0.1] text-white placeholder-slate-600 rounded-xl px-4 py-2.5 text-[14px] outline-none focus:border-yellow-500/60 focus:ring-1 focus:ring-yellow-500/20 transition-all"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl px-4 py-2.5 text-[13px]">
                  {error}
                </div>
              )}

              <motion.button
                type="submit"
                disabled={loading}
                whileTap={{ scale: 0.98 }}
                className="w-full bg-gradient-to-r from-yellow-600 to-green-700 hover:from-yellow-500 hover:to-green-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all shadow-xl shadow-green-900/30 text-[14px] mt-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Giriş yapılıyor...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    Giriş Yap
                    <ArrowRight className="w-4 h-4" />
                  </span>
                )}
              </motion.button>
            </form>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
