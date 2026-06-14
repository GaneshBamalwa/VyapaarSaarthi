import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Zap, RefreshCw } from "lucide-react";
import {
  simulateSampleOrder,
  simulateAmbiguousOrder,
  simulateOverdueInvoice,
} from "@/services/vyapaarApi";
import { cn } from "@/lib/utils";

interface SimButton {
  id: string;
  label: string;
  description: string;
  icon: string;
  action: () => Promise<unknown>;
}

export function SimulatorPanel() {
  const [open, setOpen] = useState(false);
  const [lastResult, setLastResult] = useState<unknown>(null);

  const mutation = useMutation({
    mutationFn: async (action: () => Promise<unknown>) => {
      const result = await action();
      setLastResult(result);
      return result;
    },
  });

  const buttons: SimButton[] = [
    {
      id: "sample-order",
      label: "Sample Order",
      description: "Generate realistic order in Hindi",
      icon: "SO",
      action: simulateSampleOrder,
    },
    {
      id: "ambiguous-order",
      label: "Ambiguous Order",
      description: "Trigger clarification + HITL flow",
      icon: "AO",
      action: simulateAmbiguousOrder,
    },
    {
      id: "overdue-invoice",
      label: "Overdue Invoice",
      description: "Generate collections reminder",
      icon: "OI",
      action: simulateOverdueInvoice,
    },
  ];

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 z-50 w-[40px] h-[40px] rounded-[10px]
                   bg-[#6366F1]
                   flex items-center justify-center
                   hover:scale-110 transition-all duration-300 active:scale-95 shadow-none"
        title="Open Simulator"
      >
        <Zap size={18} className="text-white" />
      </button>

      {/* Drawer */}
      {open && (
        <div className="fixed bottom-20 right-6 z-50 w-80 animate-slide-up">
          <div className="glass-card border border-[#27272A]">
            <div className="flex items-center justify-between p-4 border-b border-[#27272A]">
              <div className="flex items-center gap-2">
                <Zap size={16} className="text-primary" />
                <span className="text-sm font-semibold">Demo Simulator</span>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-muted-foreground hover:text-foreground text-lg leading-none"
              >
                ×
              </button>
            </div>

            <div className="p-4 space-y-2">
              {buttons.map((btn) => (
                <button
                  key={btn.id}
                  onClick={() => mutation.mutate(btn.action)}
                  disabled={mutation.isPending}
                  className={cn(
                    "w-full flex items-center gap-3 p-3 rounded-[6px] border border-[#27272A] bg-transparent text-[#A1A1AA]",
                    "hover:bg-[#18181B] hover:text-[#E4E4E7] transition-all duration-200 text-left disabled:opacity-50"
                  )}
                >
                  <span className="text-sm font-bold w-6 text-center">{btn.icon}</span>
                  <div className="flex-1">
                    <div className="text-xs font-semibold">{btn.label}</div>
                    <div className="text-xs text-muted-foreground">{btn.description}</div>
                  </div>
                  {mutation.isPending && (
                    <RefreshCw size={14} className="animate-spin text-muted-foreground" />
                  )}
                </button>
              ))}
            </div>

            {/* Last Result */}
            {lastResult !== null && (
              <div className="px-4 pb-4">
                <div className="text-xs text-muted-foreground mb-2">Last Result</div>
                <pre className="text-xs bg-muted/40 p-2 rounded overflow-x-auto max-h-40 text-muted-foreground font-mono">
                  {JSON.stringify(lastResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
