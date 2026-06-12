import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { DollarSign, Send, Loader2 } from "lucide-react";
import { runCollections } from "@/services/vyapaarApi";
import { cn, getRiskColor } from "@/lib/utils";
import type { RiskLevel } from "@/types";

export function CollectionsAgentPage() {
  const [form, setForm] = useState({
    invoice_id: "INV-2024-001",
    customer: "Sharma Constructions",
    amount: 45000,
    due_days: 15,
    previous_reminders: 0,
  });
  const [result, setResult] = useState<unknown>(null);

  const mutation = useMutation({
    mutationFn: runCollections,
    onSuccess: (data) => setResult(data),
  });

  const handleChange = (field: string, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const r = result as Record<string, unknown> | null;
  const data = r?.data as Record<string, unknown> | undefined;

  const RISK_ICON: Record<RiskLevel, string> = {
    LOW: "🟢",
    MEDIUM: "🟡",
    HIGH: "🔴",
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center">
          <DollarSign size={20} className="text-red-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Collections Agent</h1>
          <p className="text-muted-foreground text-sm">
            Analyze overdue invoices and generate Hindi payment reminders
          </p>
        </div>
      </div>

      <div className="glass-card p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block">Invoice ID</label>
            <input
              className="vs-input"
              value={form.invoice_id}
              onChange={(e) => handleChange("invoice_id", e.target.value)}
              placeholder="INV-2024-001"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block">Customer Name</label>
            <input
              className="vs-input"
              value={form.customer}
              onChange={(e) => handleChange("customer", e.target.value)}
              placeholder="Customer name"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block">Amount (₹)</label>
            <input
              className="vs-input"
              type="number"
              value={form.amount}
              onChange={(e) => handleChange("amount", Number(e.target.value))}
              placeholder="45000"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block">Days Overdue</label>
            <input
              className="vs-input"
              type="number"
              value={form.due_days}
              onChange={(e) => handleChange("due_days", Number(e.target.value))}
              placeholder="15"
            />
          </div>
        </div>

        {/* Quick risk presets */}
        <div>
          <div className="text-xs text-muted-foreground mb-2">Quick presets:</div>
          <div className="flex gap-2">
            {[
              { label: "Low Risk (5 days)", days: 5, amount: 15000 },
              { label: "Medium Risk (15 days)", days: 15, amount: 50000 },
              { label: "High Risk (30 days)", days: 30, amount: 150000 },
            ].map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => setForm((p) => ({ ...p, due_days: preset.days, amount: preset.amount }))}
                className="text-xs px-3 py-1.5 rounded-lg bg-muted/60 border border-border/50
                           text-muted-foreground hover:text-foreground transition-all"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={() => mutation.mutate(form)}
          disabled={mutation.isPending}
          className="btn-primary flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm disabled:opacity-50"
        >
          {mutation.isPending ? (
            <><Loader2 size={16} className="animate-spin" /> Analyzing...</>
          ) : (
            <><Send size={16} /> Generate Reminder</>
          )}
        </button>
      </div>

      {/* Result */}
      {data && (
        <div className="glass-card p-5 space-y-4 animate-slide-up">
          {/* Risk badge */}
          <div className="flex items-center gap-3">
            <span className="text-2xl">{RISK_ICON[data.risk as RiskLevel]}</span>
            <div>
              <div className={cn("text-lg font-bold", getRiskColor(data.risk as string).includes("green") ? "text-green-400" : getRiskColor(data.risk as string).includes("yellow") ? "text-yellow-400" : "text-red-400")}>
                {data.risk as string} RISK
              </div>
              <div className="text-xs text-muted-foreground">
                Risk Score: {Math.round((data.risk_score as number) * 100)}% · 
                Follow up in {data.follow_up_days as number} days · 
                Action: {data.recommended_action as string}
              </div>
            </div>
          </div>

          {/* Hindi Message */}
          <div>
            <div className="text-xs text-muted-foreground mb-2">Generated Hindi Reminder</div>
            <div className="bg-muted/40 p-4 rounded-xl border border-border/50 text-sm text-foreground leading-relaxed">
              {data.message as string}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
