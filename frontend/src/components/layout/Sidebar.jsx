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
  ChevronRight,
  Bot,
  TrendingUp,
} from "lucide-react";
import { useAuth } from "../../store/authStore";

const NAV_ITEMS = [
  { to: "/",          icon: LayoutDashboard, label: "Genel Bakış",  color: "text-yellow-700" },
  { to: "/chat",      icon: Bot,             label: "AI Asistan",   color: "text-green-700"  },
  { to: "/orders",    icon: ClipboardList,   label: "Siparişler",   color: "text-amber-700"  },
  { to: "/shipments", icon: Truck,           label: "Kargo Takip",  color: "text-yellow-600" },
  { to: "/inventory", icon: Package,         label: "Envanter",     color: "text-green-600"  },
  { to: "/forecast",  icon: TrendingUp,      label: "Talep Tahmini",color: "text-emerald-700"},
  { to: "/messages",  icon: MessageSquare,   label: "Mesajlar",     color: "text-amber-600"  },
];

function NavItem({ to, icon: Icon, label, color, collapsed }) {
  const { pathname } = useLocation();
  const isActive = to === "/" ? pathname === "/" : pathname.startsWith(to);

  return (
    <NavLink
      to={to}
      title={label}
      className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 group ${
        isActive
          ? "bg-gradient-to-r from-yellow-600 to-green-700 text-white shadow-sm shadow-yellow-200"
          : "text-slate-500 hover:bg-yellow-50 hover:text-slate-800"
      }`}
    >
      <Icon className={`w-[18px] h-[18px] shrink-0 ${isActive ? "text-white" : color}`} />
      <AnimatePresence>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.2 }}
            className="leading-none overflow-hidden whitespace-nowrap"
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>
      {!collapsed && isActive && (
        <ChevronRight className="w-3.5 h-3.5 ml-auto text-white/60" />
      )}
      {/* Tooltip for collapsed */}
      {collapsed && (
        <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-slate-900 text-white text-xs font-medium rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
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
      animate={{ width: collapsed ? 72 : 236 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="relative h-screen flex flex-col bg-white border-r border-slate-100 shrink-0 z-30"
      style={{ boxShadow: "1px 0 0 0 #f1f5f9" }}
    >
      {/* Logo zone */}
      <div className={`flex items-center gap-3 py-5 shrink-0 ${collapsed ? "px-4 justify-center" : "px-5"}`}>
        <img
          src="/harman-logo.png"
          alt="Harman"
          onClick={() => setCollapsed((c) => !c)}
          className="w-9 h-9 rounded-xl object-cover shadow-sm shrink-0 cursor-pointer hover:scale-105 transition-transform"
          title={collapsed ? "Genişlet" : "Daralt"}
        />
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.18 }}
              className="overflow-hidden"
            >
              <p className="text-[16px] font-black text-slate-900 tracking-tight whitespace-nowrap">
                Harman
              </p>
              <p className="text-[10px] font-semibold text-yellow-600 tracking-widest uppercase whitespace-nowrap">
                AI Ops
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Divider */}
      <div className="mx-4 h-px bg-slate-100 mb-3" />

      {/* Nav zone */}
      <nav className={`flex-1 overflow-y-auto space-y-1 ${collapsed ? "px-2" : "px-3"}`}>
        {!collapsed && (
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-2 mb-2">
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
      <div className={`py-4 ${collapsed ? "px-2" : "px-3"}`}>
        {!collapsed ? (
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 transition-colors mb-1">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-yellow-100 to-green-100 flex items-center justify-center text-green-800 text-[11px] font-bold shrink-0 border border-green-100">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-semibold text-slate-800 truncate leading-tight">
                {user?.full_name ?? "Kullanıcı"}
              </p>
              <p className="text-[10px] font-medium text-slate-400 truncate capitalize leading-tight mt-0.5">
                {user?.role ?? "operator"}
              </p>
            </div>
          </div>
        ) : (
          <div className="w-8 h-8 mx-auto rounded-lg bg-gradient-to-br from-yellow-100 to-green-100 flex items-center justify-center text-green-800 text-[11px] font-bold border border-green-100 mb-1">
            {initials}
          </div>
        )}
        <button
          onClick={handleLogout}
          title="Çıkış Yap"
          className={`flex items-center justify-center gap-2 rounded-xl text-[12px] font-semibold transition-colors text-slate-500 hover:text-red-600 hover:bg-red-50 ${
            collapsed ? "w-full h-9" : "w-full h-9 px-3"
          }`}
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && <span>Çıkış Yap</span>}
        </button>
      </div>
    </motion.aside>
  );
}
