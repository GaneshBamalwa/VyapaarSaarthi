import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, XCircle, Edit3, ChevronDown, ChevronUp } from "lucide-react";
import { resolveHITL } from "@/services/vyapaarApi";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { HITLItem } from "@/types";

interface Props {
  item: HITLItem;
  onResolved?: () => void;
}

export function HITLCard({ item, onResolved }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState("");
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: (action: "approve" | "reject" | "edit") =>
      resolveHITL(item.id, action, undefined, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hitl"] });
      onResolved?.();
    },
  });

  const parsedOrder = item.payload?.parsed_order as Record<string, unknown> | undefined;
  const confidence = item.payload?.confidence as number | undefined;

  return (
    <div className={cn(
      "glass-card border transition-all duration-300",
      item.status === "PENDING" ? "border-yellow-500/30" : "border-border/50",
    )}>
      <div className="p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
            <span className="text-xs font-mono text-muted-foreground">HITL #{item.id}</span>
            {item.order_id && (
              <span className="text-xs text-muted-foreground">→ Order #{item.order_id}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              "tag",
              item.reason === "low_confidence" && "bg-yellow-400/10 text-yellow-400",
              item.reason === "ambiguous" && "bg-purple-400/10 text-purple-400",
            )}>
              {item.reason || "review"}
            </span>
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
        </div>

        {/* Raw input */}
        {typeof item.payload?.raw_input === "string" && (
          <div className="bg-muted/40 rounded-lg p-3 mb-3">
            <div className="text-xs text-muted-foreground mb-1">Original Input</div>
            <div className="text-sm text-foreground">{item.payload.raw_input as string}</div>
          </div>
        )}

        {/* Parsed order preview */}
        {parsedOrder && (
          <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
            <div className="bg-muted/30 p-2 rounded">
              <div className="text-muted-foreground mb-0.5">Customer</div>
              <div className="text-foreground font-medium">
                {(parsedOrder.customer as string) || "Unknown"}
              </div>
            </div>
            <div className="bg-muted/30 p-2 rounded">
              <div className="text-muted-foreground mb-0.5">Items</div>
              <div className="text-foreground font-medium">
                {String((parsedOrder.items as unknown[] | undefined)?.length ?? 0)} items
              </div>
            </div>
            <div className="bg-muted/30 p-2 rounded">
              <div className="text-muted-foreground mb-0.5">Confidence</div>
              <div className={cn("font-medium",
                confidence && confidence >= 0.8 ? "text-green-400" : "text-yellow-400"
              )}>
                {confidence !== undefined ? `${Math.round((confidence as number) * 100)}%` : "—"}
              </div>
            </div>
          </div>
        )}

        {/* Expanded payload */}
        {expanded && (
          <div className="mb-3 animate-fade-in">
            <pre className="text-xs bg-muted/40 p-3 rounded-lg overflow-x-auto text-muted-foreground font-mono">
              {JSON.stringify(item.payload, null, 2)}
            </pre>
          </div>
        )}

        {/* Notes */}
        {item.status === "PENDING" && (
          <input
            className="vs-input mb-3 text-xs"
            placeholder="Reviewer notes (optional)..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        )}

        {/* Actions */}
        {item.status === "PENDING" ? (
          <div className="flex gap-2">
            <button
              onClick={() => mutation.mutate("approve")}
              disabled={mutation.isPending}
              className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg
                         bg-green-500/20 hover:bg-green-500/30 text-green-400 text-xs font-medium
                         border border-green-500/20 transition-all duration-200 disabled:opacity-50"
            >
              <CheckCircle size={14} /> Approve
            </button>
            <button
              onClick={() => mutation.mutate("reject")}
              disabled={mutation.isPending}
              className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg
                         bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs font-medium
                         border border-red-500/20 transition-all duration-200 disabled:opacity-50"
            >
              <XCircle size={14} /> Reject
            </button>
          </div>
        ) : (
          <div className="text-xs text-muted-foreground">
            Resolved: <span className={cn(
              "font-medium",
              item.status === "APPROVED" && "text-green-400",
              item.status === "REJECTED" && "text-red-400",
              item.status === "EDITED" && "text-blue-400",
            )}>{item.status}</span>
            {item.resolved_at && ` on ${formatDate(item.resolved_at)}`}
          </div>
        )}
      </div>
    </div>
  );
}
