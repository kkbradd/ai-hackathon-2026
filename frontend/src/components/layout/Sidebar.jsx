import { useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  MessageSquare,
  ClipboardList,
  Truck,
  Package,
  LogOut,
  Bot,
  TrendingUp,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../../store/authStore";

const NAV_ITEMS = [
  { to: "/",          icon: LayoutDashboard, label: "Genel Bakış",   tint: "bg-yellow-50 text-yellow-700 ring-yellow-200/60" },
  { to: "/chat",      icon: Bot,             label: "AI Asistan",    tint: "bg-emerald-50 text-emerald-700 ring-emerald-200/60", featured: true },
  { to: "/orders",    icon: ClipboardList,   label: "Siparişler",    tint: "bg-amber-50 text-amber-700 ring-amber-200/60" },
  { to: "/shipments", icon: Truck,           label: "Kargo Takip",   tint: "bg-blue-50 text-blue-700 ring-blue-200/60" },
  { to: "/inventory", icon: Package,         label: "Envanter",      tint: "bg-green-50 text-green-700 ring-green-200/60" },
  { to: "/forecast",  icon: TrendingUp,      label: "Talep Tahmini", tint: "bg-emerald-50 text-emerald-700 ring-emerald-200/60" },
  { to: "/messages",  icon: MessageSquare,   label: "Mesajlar",      tint: "bg-violet-50 text-violet-700 ring-violet-200/60" },
];

function NavItem({ to, icon: Icon, label, tint, featured, collapsed }) {
  const { pathname } = useLocation();
  const isActive = to === "/" ? pathname === "/" : pathname.startsWith(to);

  return (
    <NavLink
      to={to}
      title={label}
      className={`relative group flex items-center ${collapsed ? "justify-center px-0" : "px-2.5"} py-2 rounded-xl transition-all duration-200 ${
        isActive
          ? "bg-yellow-50/70"
          : "hover:bg-slate-50"
      }`}
    >
      {/* Left accent bar — only when active */}
      {isActive && !collapsed && (
        <motion.span
          layoutId="navAccent"
          className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-7 rounded-r-full bg-gradient-to-b from-yellow-500 to-emerald-600"
          transition={{ type: "spring", stiffness: 380, damping: 30 }}
        />
      )}

      {/* Icon container */}
      <div
        className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ring-1 transition-colors ${
          isActive ? tint : "bg-slate-50 text-slate-500 ring-slate-200/60 group-hover:bg-white group-hover:ring-slate-300/70"
        }`}
      >
        <Icon className="w-[17px] h-[17px]" />
      </div>

      {/* Label */}
      <AnimatePresence>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.18 }}
            className={`ml-3 overflow-hidden whitespace-nowrap text-[13px] tracking-tight ${
              isActive ? "font-extrabold text-slate-900" : "font-semibold text-slate-600 group-hover:text-slate-900"
            }`}
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>

      {/* Featured marker for AI Asistan */}
      {featured && !collapsed && (
        <span className="ml-auto inline-flex items-center justify-center w-5 h-5 shrink-0">
          <Sparkles className="w-3 h-3 text-yellow-500" />
        </span>
      )}

      {/* Tooltip when collapsed */}
      {collapsed && (
        <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
          {label}
        </div>
      )}
    </NavLink>
  );
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const initials = user?.full_name
    ? user.full_name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()
    : "U";

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <motion.aside
      animate={{ width: collapsed ? 76 : 252 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="relative h-screen flex flex-col bg-white border-r border-slate-100 shrink-0 z-30"
      style={{ boxShadow: "1px 0 0 0 #f1f5f9" }}
    >
      {/* Brand zone */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        title={collapsed ? "Genişlet" : "Daralt"}
        className={`flex items-center gap-3 py-5 shrink-0 hover:bg-slate-50/60 transition-colors ${
          collapsed ? "px-4 justify-center" : "px-5"
        }`}
      >
        <div className="relative shrink-0">
          <img
            src="/harman-logo.png"
            alt="Harman"
            className="w-10 h-10 rounded-xl object-cover shadow-sm ring-1 ring-yellow-200/40"
          />
          <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.18 }}
              className="overflow-hidden text-left"
            >
              <p className="text-[16px] font-black text-slate-900 tracking-tight whitespace-nowrap leading-none">
                Harman
              </p>
              <p className="text-[9.5px] font-extrabold text-yellow-600 tracking-[0.22em] uppercase whitespace-nowrap mt-1.5">
                AI Ops
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </button>

      {/* Divider */}
      <div className="mx-4 h-px bg-slate-100 mb-2" />

      {/* Nav zone */}
      <nav className={`flex-1 overflow-y-auto space-y-0.5 ${collapsed ? "px-2.5" : "px-3"}`}>
        {!collapsed && (
          <p className="text-[9.5px] font-extrabold text-slate-400 uppercase tracking-[0.2em] px-3 mt-1 mb-2">
            Navigasyon
          </p>
        )}
        {NAV_ITEMS.map((item) => (
          <NavItem key={item.to} {...item} collapsed={collapsed} />
        ))}
      </nav>

      {/* Divider */}
      <div className="mx-4 h-px bg-slate-100 mt-3" />

      {/* User zone */}
      <div className={`py-4 ${collapsed ? "px-2.5" : "px-3"}`}>
        {!collapsed ? (
          <div
            className="relative overflow-hidden flex items-center gap-3 px-3 py-3 rounded-2xl mb-2"
            style={{
              background: "linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #ecfdf5 100%)",
              boxShadow: "0 0 0 1px rgba(245,158,11,0.12)",
            }}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-yellow-500 to-emerald-700 flex items-center justify-center text-white text-[12px] font-extrabold shrink-0 shadow-sm">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[12.5px] font-extrabold text-slate-900 truncate leading-tight">
                {user?.full_name ?? "Kullanıcı"}
              </p>
              <p className="text-[10px] font-bold text-amber-700 uppercase tracking-[0.14em] truncate leading-tight mt-1">
                {user?.role ?? "operator"}
              </p>
            </div>
          </div>
        ) : (
          <div
            className="relative overflow-hidden mx-auto mb-2 flex items-center justify-center"
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "14px",
              background: "linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #ecfdf5 100%)",
              boxShadow: "0 0 0 1px rgba(245,158,11,0.18)",
            }}
            title={user?.full_name ?? "Kullanıcı"}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-yellow-500 to-emerald-700 flex items-center justify-center text-white text-[10.5px] font-extrabold shadow-sm">
              {initials}
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          title="Çıkış Yap"
          className={`flex items-center justify-center gap-2 rounded-xl text-[12px] font-bold transition-colors text-slate-500 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-100 ${
            collapsed ? "w-full h-9" : "w-full h-9 px-3"
          }`}
        >
          <LogOut className="w-3.5 h-3.5 shrink-0" />
          {!collapsed && <span>Çıkış Yap</span>}
        </button>
      </div>
    </motion.aside>
  );
}
