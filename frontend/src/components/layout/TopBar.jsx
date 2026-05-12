import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, ChevronDown, LogOut, Activity } from "lucide-react";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import { useShipmentAlerts } from "../../hooks/useShipments";
import { useAuth } from "../../store/authStore";

const PAGE_LABELS = {
  "/":          { label: "Genel Bakış",  sub: "Operasyon Merkezi" },
  "/chat":      { label: "AI Asistan",   sub: "Operasyonel Zeka" },
  "/orders":    { label: "Siparişler",   sub: "Sipariş Yönetimi" },
  "/shipments": { label: "Kargo Takip",  sub: "Lojistik İzleme" },
  "/inventory": { label: "Envanter",     sub: "Stok Yönetimi" },
  "/messages":  { label: "Mesajlar",     sub: "Müşteri İletişimi" },
};

export default function TopBar() {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const alertCount = useShipmentAlerts();
  const [now, setNow] = useState(new Date());
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const pageInfo = PAGE_LABELS[pathname] ?? { label: "Kooperatif Hub", sub: "" };

  const initials = user?.full_name
    ? user.full_name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()
    : "U";

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    function handleClick(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleLogout() {
    setDropdownOpen(false);
    logout();
    navigate("/login");
  }

  return (
    <header className="h-[60px] bg-white border-b border-slate-100 flex items-center px-6 gap-4 shrink-0 z-20">
      {/* Left — Page identity */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            className="flex flex-col"
          >
            <span className="text-[14px] font-bold text-slate-900 leading-tight">{pageInfo.label}</span>
            <span className="text-[11px] font-medium text-slate-400 leading-tight">{pageInfo.sub}</span>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Center — Live status + clock */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2.5 pointer-events-none">
        <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-100 px-2.5 py-1 rounded-full">
          <Activity className="w-3 h-3 text-slate-500" />
          <span className="text-[11px] font-semibold text-slate-600">Oturum</span>
        </div>
        <span className="text-[11px] text-slate-400 tabular-nums font-medium">
          {format(now, "d MMM · HH:mm:ss", { locale: tr })}
        </span>
      </div>

      {/* Right zone */}
      <div className="flex items-center gap-2">
        {/* Notification bell */}
        <button className="relative w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center transition-colors">
          <Bell className="w-4 h-4 text-slate-500" />
          <AnimatePresence>
            {alertCount > 0 && (
              <motion.span
                key="badge"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 20 }}
                className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-[9px] text-white font-bold"
              >
                {alertCount > 9 ? "9+" : alertCount}
              </motion.span>
            )}
          </AnimatePresence>
        </button>

        {/* Divider */}
        <div className="w-px h-4 bg-slate-200" />

        {/* User chip */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen((o) => !o)}
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white text-[10px] font-bold shrink-0">
              {initials}
            </div>
            <span className="text-[12px] font-semibold text-slate-700 hidden sm:block">
              {user?.full_name?.split(" ")[0] ?? "Kullanıcı"}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          <AnimatePresence>
            {dropdownOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.96, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96, y: -4 }}
                transition={{ duration: 0.12 }}
                className="absolute top-full right-0 mt-1.5 w-44 bg-white border border-slate-100 rounded-xl p-1 z-50"
                style={{ boxShadow: "0 8px 32px rgba(0,0,0,0.12)" }}
              >
                <div className="px-3 py-2 mb-1">
                  <p className="text-[12px] font-bold text-slate-800 truncate">{user?.full_name}</p>
                  <p className="text-[11px] text-slate-400 capitalize">{user?.role ?? "operator"}</p>
                </div>
                <div className="h-px bg-slate-100 mb-1" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[12px] font-semibold text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5 shrink-0" />
                  Çıkış Yap
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
