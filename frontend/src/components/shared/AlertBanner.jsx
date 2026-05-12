import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import { motion } from "framer-motion";
import { useShipmentAlerts } from "../../hooks/useShipments";

export default function AlertBanner() {
  const delayedCount = useShipmentAlerts();
  const navigate = useNavigate();
  const [dismissed, setDismissed] = useState(false);

  if (delayedCount === 0 || dismissed) return null;

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: "auto", opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="overflow-hidden shrink-0"
    >
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 flex items-center gap-3">
        <div className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse shrink-0" />
        <span className="text-[13px] text-amber-300/90 font-medium">
          {delayedCount} gecikmiş kargo
        </span>
        <span className="text-[13px] text-amber-500">
          — müşteriler bilgilendirilmeli
        </span>
        <div className="flex-1" />
        <button
          onClick={() => navigate("/shipments")}
          className="text-[12px] font-medium text-amber-400 border border-amber-500/30 hover:bg-amber-500/10 px-3 py-1 rounded-lg transition-colors whitespace-nowrap"
        >
          Görüntüle
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="text-amber-600 hover:text-amber-400 transition-colors ml-1"
          aria-label="Kapat"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </motion.div>
  );
}
