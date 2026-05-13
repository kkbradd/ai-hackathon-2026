import { useState, useEffect } from "react";
import { Brain, Truck, Package, MessageSquare, Activity } from "lucide-react";
import { fetchAgentStatus } from "../../api/client";

const AGENT_META = {
  operational:    { label: "Operasyon Zekâsı",  Icon: Activity },
  shipment:       { label: "Kargo İzleme",       Icon: Truck },
  inventory:      { label: "Envanter Analizi",   Icon: Package },
  customer_issue: { label: "Müşteri İletişim",   Icon: MessageSquare },
};

export default function AgentActivityLog() {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchAgentStatus();
        if (!cancelled) setAgents(data.agents || []);
      } catch {
        // silent — non-critical UI element
      }
    }
    load();
    const id = setInterval(load, 60_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  if (agents.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-slate-100">
      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2.5">
        Ajan Aktivitesi
      </p>
      <div className="space-y-1.5">
        {agents.map((agent) => {
          const meta = AGENT_META[agent.agent_name] || { label: agent.agent_name, Icon: Brain };
          const { Icon } = meta;
          return (
            <div key={agent.agent_name} className="flex items-center gap-2.5">
              <div className="w-5 h-5 rounded-md bg-yellow-50 flex items-center justify-center shrink-0">
                <Icon className="w-2.5 h-2.5 text-yellow-700" />
              </div>
              <span className="text-[11px] text-slate-600 flex-1 font-medium">{meta.label}</span>
              {agent.last_run_at ? (
                <span className="text-[10px] text-slate-400">{agent.last_run_at}</span>
              ) : (
                <span className="text-[10px] text-slate-300 italic">Henüz çalışmadı</span>
              )}
              {agent.insight_count > 0 && (
                <span className="text-[9px] font-bold bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">
                  {agent.insight_count}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
