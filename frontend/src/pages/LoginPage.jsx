import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Zap, Truck, AlertTriangle, MessageSquare } from "lucide-react";
import { useAuth } from "../store/authStore";

const FEATURES = [
  { Icon: Truck,          text: "Gerçek zamanlı kargo takibi" },
  { Icon: AlertTriangle,  text: "Gecikme uyarıları ve AI önerileri" },
  { Icon: MessageSquare,  text: "Doğal dilde sorgulama" },
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
      <div className="hidden lg:flex flex-col justify-center px-16 bg-slate-950 relative overflow-hidden">
        {/* Subtle background orb */}
        <div className="absolute top-1/3 right-0 w-64 h-64 bg-indigo-600/8 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10">
          {/* Logo mark */}
          <img src="/harman-logo.png" alt="Harman" className="w-14 h-14 rounded-2xl object-cover shadow-lg mb-8" />

          <h1 className="text-[32px] font-bold text-white tracking-tight leading-tight">
            AI destekli operasyon yönetimi
          </h1>
          <p className="text-[16px] text-slate-500 mt-4 leading-relaxed max-w-sm">
            Siparişlerinizi, kargolarınızı ve müşteri mesajlarınızı tek bir zeki panelden yönetin.
          </p>

          <div className="mt-8 space-y-4">
            {FEATURES.map(({ Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-indigo-400" />
                </div>
                <span className="text-[14px] text-slate-400">{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex items-center justify-center p-8 bg-[#0d0f14] relative overflow-hidden">
        {/* Background orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-600/8 rounded-full blur-3xl pointer-events-none" />

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
                  className="w-full bg-white/[0.05] border border-white/[0.1] text-white placeholder-slate-600 rounded-xl px-4 py-2.5 text-[14px] outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/20 transition-all"
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
                  className="w-full bg-white/[0.05] border border-white/[0.1] text-white placeholder-slate-600 rounded-xl px-4 py-2.5 text-[14px] outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/20 transition-all"
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
                  "Giriş Yap"
                )}
              </motion.button>
            </form>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
