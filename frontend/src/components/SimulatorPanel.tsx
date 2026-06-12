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
  color: string;
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
      icon: "📦",
      action: simulateSampleOrder,
      color: "border-saffron-500/30 hover:border-saffron-500/50 text-saffron-400",
    },
    {
      id: "ambiguous-order",
      label: "Ambiguous Order",
      description: "Trigger clarification + HITL flow",
      icon: "🔍",
      action: simulateAmbiguousOrder,
      color: "border-purple-500/30 hover:border-purple-500/50 text-purple-400",
    },
    {
      id: "overdue-invoice",
      label: "Overdue Invoice",
      description: "Generate collections reminder",
      icon: "💰",
      action: simulateOverdueInvoice,
      color: "border-red-500/30 hover:border-red-500/50 text-red-400",
    },
  ];

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full
                   bg-gradient-to-br from-saffron-500 to-indigo-500
                   flex items-center justify-center shadow-2xl shadow-primary/40
                   hover:scale-110 transition-all duration-300 active:scale-95"
        title="Open Simulator"
      >
        <Zap size={20} className="text-white" />
      </button>

      {/* Drawer */}
      {open && (
        <div className="fixed bottom-20 right-6 z-50 w-80 animate-slide-up">
          <div className="glass-card border border-border/80 shadow-2xl shadow-black/40">
            <div className="flex items-center justify-between p-4 border-b border-border/50">
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
                    "w-full flex items-center gap-3 p-3 rounded-lg border bg-muted/30",
                    "hover:bg-muted/50 transition-all duration-200 text-left disabled:opacity-50",
                    btn.color
                  )}
                >
                  <span className="text-xl">{btn.icon}</span>
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
