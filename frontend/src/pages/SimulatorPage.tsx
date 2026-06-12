import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Zap, Package, AlertTriangle, DollarSign, RefreshCw } from "lucide-react";
import {
  simulateSampleOrder,
  simulateAmbiguousOrder,
  simulateOverdueInvoice,
} from "@/services/vyapaarApi";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function SimulatorPage() {
  const [activeResult, setActiveResult] = useState<{ type: string; data: unknown } | null>(null);
  const qc = useQueryClient();

  const sampleMutation = useMutation({
    mutationFn: simulateSampleOrder,
    onSuccess: (data) => {
      setActiveResult({ type: "Sample Order", data });
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["kpis"] });
    },
  });

  const ambiguousMutation = useMutation({
    mutationFn: simulateAmbiguousOrder,
    onSuccess: (data) => {
      setActiveResult({ type: "Ambiguous Order", data });
      qc.invalidateQueries({ queryKey: ["hitl"] });
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  const overdueM = useMutation({
    mutationFn: simulateOverdueInvoice,
    onSuccess: (data) => setActiveResult({ type: "Overdue Invoice", data }),
  });

  const isAnyLoading = sampleMutation.isPending || ambiguousMutation.isPending || overdueM.isPending;

  const scenarios = [
    {
      icon: "📦",
      label: "Generate Sample Order",
      description: "Simulate a realistic Hindi/English order through the full pipeline",
      color: "from-saffron-500/10 to-saffron-600/5 border-saffron-500/20 hover:border-saffron-500/40",
      iconBg: "bg-saffron-500/20 text-saffron-400",
      mutation: sampleMutation,
    },
    {
      icon: "🔍",
      label: "Generate Ambiguous Order",
      description: "Trigger clarification detection and HITL approval queue",
      color: "from-purple-500/10 to-purple-600/5 border-purple-500/20 hover:border-purple-500/40",
      iconBg: "bg-purple-500/20 text-purple-400",
      mutation: ambiguousMutation,
    },
    {
      icon: "💰",
      label: "Generate Overdue Invoice",
      description: "Analyze a collection case and generate Hindi payment reminder",
      color: "from-red-500/10 to-red-600/5 border-red-500/20 hover:border-red-500/40",
      iconBg: "bg-red-500/20 text-red-400",
      mutation: overdueM,
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-saffron-500 to-indigo-500 flex items-center justify-center">
          <Zap size={20} className="text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Demo Simulator</h1>
          <p className="text-muted-foreground text-sm">
            Instantly trigger demo scenarios to showcase agent workflows
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarios.map((s) => (
          <button
            key={s.label}
            onClick={() => s.mutation.mutate()}
            disabled={isAnyLoading}
            className={cn(
              "glass-card p-5 text-left bg-gradient-to-br border transition-all duration-300",
              "hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50",
              s.color
            )}
          >
            <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4", s.iconBg)}>
              {s.mutation.isPending ? <RefreshCw size={22} className="animate-spin" /> : s.icon}
            </div>
            <div className="text-sm font-semibold text-foreground mb-2">{s.label}</div>
            <div className="text-xs text-muted-foreground leading-relaxed">{s.description}</div>
          </button>
        ))}
      </div>

      {/* Result Panel */}
      {activeResult && (
        <div className="glass-card p-5 animate-slide-up">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={16} className="text-primary" />
            <span className="text-sm font-semibold">{activeResult.type} — Result</span>
          </div>
          <pre className="text-xs bg-muted/40 p-4 rounded-xl overflow-x-auto text-muted-foreground font-mono max-h-80">
            {JSON.stringify(activeResult.data, null, 2)}
          </pre>
        </div>
      )}

      {/* Instructions */}
      <div className="glass-card p-5 border-border/30">
        <h3 className="text-sm font-semibold mb-3">Demo Flow Instructions</h3>
        <div className="space-y-2 text-xs text-muted-foreground">
          <div className="flex gap-2">
            <span className="text-saffron-400 shrink-0">1.</span>
            Click "Generate Sample Order" → check Orders page to see parsed output
          </div>
          <div className="flex gap-2">
            <span className="text-purple-400 shrink-0">2.</span>
            Click "Generate Ambiguous Order" → check Approvals page for HITL queue
          </div>
          <div className="flex gap-2">
            <span className="text-red-400 shrink-0">3.</span>
            Click "Generate Overdue Invoice" → see risk assessment and Hindi reminder
          </div>
          <div className="flex gap-2">
            <span className="text-blue-400 shrink-0">4.</span>
            Watch the Agent Feed page for real-time event streaming via WebSocket
          </div>
        </div>
      </div>
    </div>
  );
}
