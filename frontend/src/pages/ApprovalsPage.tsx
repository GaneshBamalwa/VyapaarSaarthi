import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckSquare, RefreshCw } from "lucide-react";
import { HITLCard } from "@/components/HITLCard";
import { fetchHITLAll } from "@/services/vyapaarApi";
import { useAgentStore } from "@/stores/agentStore";
import { useEffect } from "react";

export function ApprovalsPage() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["hitl"],
    queryFn: () => fetchHITLAll(100),
    refetchInterval: 5000,
  });

  const { setPendingApprovals } = useAgentStore();

  useEffect(() => {
    const pending = data?.items.filter((i) => i.status === "PENDING").length ?? 0;
    setPendingApprovals(pending);
  }, [data, setPendingApprovals]);

  const pending = data?.items.filter((i) => i.status === "PENDING") ?? [];
  const resolved = data?.items.filter((i) => i.status !== "PENDING") ?? [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Approvals</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Human-in-the-loop review queue
          </p>
        </div>
        <div className="flex items-center gap-3">
          {pending.length > 0 && (
            <span className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-3 py-1 rounded-full text-xs font-medium">
              {pending.length} Pending
            </span>
          )}
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/60 hover:bg-muted
                       text-sm text-muted-foreground hover:text-foreground transition-all"
          >
            <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-48 rounded-xl" />)}
        </div>
      ) : pending.length === 0 && resolved.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <CheckSquare size={48} className="mx-auto mb-4 text-muted-foreground/30" />
          <div className="text-foreground font-medium mb-2">No approvals needed</div>
          <div className="text-muted-foreground text-sm">
            Use the Simulator → Ambiguous Order to trigger HITL
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {pending.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-yellow-400 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                Pending Review ({pending.length})
              </h2>
              <div className="space-y-3">
                {pending.map((item) => (
                  <HITLCard key={item.id} item={item} onResolved={() => refetch()} />
                ))}
              </div>
            </div>
          )}

          {resolved.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground mb-3">
                Resolved ({resolved.length})
              </h2>
              <div className="space-y-3">
                {resolved.map((item) => (
                  <HITLCard key={item.id} item={item} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
