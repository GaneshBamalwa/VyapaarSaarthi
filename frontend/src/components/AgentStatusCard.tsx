import { cn, getAgentColor, getAgentIcon } from "@/lib/utils";
import type { AgentName, AgentStatus } from "@/types";

interface Props {
  agent: AgentName;
  status: AgentStatus;
  lastEvent: string;
  lastUpdated: string | null;
}

const STATUS_LABELS: Record<AgentStatus, string> = {
  idle: "Idle",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  waiting: "Waiting for Input",
};

export function AgentStatusCard({ agent, status, lastEvent, lastUpdated }: Props) {
  return (
    <div className={cn(
      "glass-card p-4 transition-all duration-300",
      status === "running" && "border-[#6366F1]",
      status === "failed" && "border-[#EF4444]",
      status === "waiting" && "border-[#F59E0B]",
    )}>
      <div className="flex items-start gap-3 mb-3">
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center text-xl border", getAgentColor(agent))}>
          {getAgentIcon(agent)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-foreground truncate">{agent}</div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className={cn("status-dot",
              status === "idle" && "status-idle",
              status === "running" && "status-running",
              status === "completed" && "status-completed",
              status === "failed" && "status-failed",
              status === "waiting" && "status-waiting",
            )} />
            <span className="text-xs text-muted-foreground">{STATUS_LABELS[status]}</span>
          </div>
        </div>
      </div>
      {lastEvent && (
        <div className="text-xs text-muted-foreground truncate">
          Last: {lastEvent}
        </div>
      )}
      {lastUpdated && (
        <div className="text-xs text-muted-foreground/60 mt-0.5">
          {new Date(lastUpdated).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
