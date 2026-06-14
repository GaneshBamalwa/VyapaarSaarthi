import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Package, Send, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { runIntake } from "@/services/vyapaarApi";
import { cn, confidenceToPercent } from "@/lib/utils";

const SAMPLE_ORDERS = [
  "Bhai kal 20 cement bags bhej dena",
  "50 steel rods Friday tak chahiye, Sharma ji ke liye",
  "100 floor tiles aur 10 bags adhesive Monday tak",
  "Wahi maal bhej dena",
  "Same as last time, urgent hai",
];

export function IntakeAgentPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<unknown>(null);

  const mutation = useMutation({
    mutationFn: runIntake,
    onSuccess: (data) => setResult(data),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) mutation.mutate(text.trim());
  };

  const r = result as Record<string, unknown> | null;
  const parsed = r?.parsed as Record<string, unknown> | undefined;

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-saffron-500/20 border border-saffron-500/30 flex items-center justify-center">
          <Package size={20} className="text-saffron-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Intake Agent</h1>
          <p className="text-muted-foreground text-sm">
            Convert unstructured Hindi/English orders into structured JSON
          </p>
        </div>
      </div>

      {/* Input */}
      <div className="glass-card p-5">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block">
              Order Input (Hindi or English)
            </label>
            <textarea
              className="vs-input min-h-28 resize-none font-medium"
              placeholder="e.g. Bhai kal 20 cement bags bhej dena..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          {/* Sample buttons */}
          <div>
            <div className="text-xs text-muted-foreground mb-2">Quick samples:</div>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_ORDERS.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setText(s)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-muted/60 hover:bg-muted
                             text-muted-foreground hover:text-foreground transition-all border border-border/50"
                >
                  {s.length > 35 ? s.slice(0, 35) + "…" : s}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={mutation.isPending || !text.trim()}
            className="btn-primary flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm disabled:opacity-50"
          >
            {mutation.isPending ? (
              <><Loader2 size={16} className="animate-spin" /> Extracting...</>
            ) : (
              <><Send size={16} /> Extract Order</>
            )}
          </button>
        </form>
      </div>

      {/* Result */}
      {r && (
        <div className="glass-card p-5 space-y-4 animate-slide-up">
          <div className="flex items-center gap-2">
            {r.status === "success" ? (
              <CheckCircle size={16} className="text-green-400" />
            ) : (
              <AlertCircle size={16} className="text-red-400" />
            )}
            <span className="text-sm font-semibold">Extraction Result</span>
            {r.requires_hitl === true && (
              <span className="tag bg-yellow-400/10 text-yellow-400 border border-yellow-400/20">
                HITL Required
              </span>
            )}
          </div>

          {parsed && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Customer</div>
                  <div className="text-sm font-medium">{(parsed.customer as string) || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Delivery Date</div>
                  <div className="text-sm font-medium">{(parsed.delivery_date as string) || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Confidence</div>
                  <div className={cn(
                    "text-sm font-bold",
                    (parsed.confidence as number) >= 0.8 ? "text-green-400" : "text-yellow-400"
                  )}>
                    {confidenceToPercent(parsed.confidence as number)}
                  </div>
                </div>
              </div>

              <div>
                <div className="text-xs text-muted-foreground mb-2">Items Extracted</div>
                <div className="space-y-1.5">
                  {((parsed.items as unknown[]) || []).map((item: unknown, i: number) => {
                    const it = item as Record<string, unknown>;
                    return (
                      <div key={i} className="flex items-center gap-2 text-xs bg-muted/40 px-3 py-2 rounded-lg">
                        <span className="text-primary font-mono">{String(it.quantity ?? "")}</span>
                        <span className="text-muted-foreground">{String(it.unit ?? "")}</span>
                        <span className="text-foreground font-medium">{String(it.name ?? "")}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Clarification */}
          {r.clarification !== null && r.clarification !== undefined &&
           (r.clarification as Record<string, unknown>).status === "AMBIGUOUS" && (
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
              <div className="text-xs text-purple-400 font-medium mb-1">Clarification Needed</div>
              <div className="text-sm text-foreground">
                {String((r.clarification as Record<string, unknown>).clarification_question ?? "")}
              </div>
            </div>
          )}

          <div>
            <div className="text-xs text-muted-foreground mb-2">Raw JSON Response</div>
            <pre className="text-xs bg-muted/40 p-3 rounded-lg overflow-x-auto text-muted-foreground font-mono">
              {JSON.stringify(r, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
