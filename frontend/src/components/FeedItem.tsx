import { cn, getAgentColor, getAgentIcon, formatTime } from "@/lib/utils";
import type { WSEvent } from "@/types";

interface Props {
  event: WSEvent;
}

export function FeedItem({ event }: Props) {
  if (event.type === "agent_event") {
    const agentClass = getAgentColor(event.agent);
    return (
      <div className="feed-item">
        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center text-base shrink-0 border", agentClass)}>
          {getAgentIcon(event.agent)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-xs font-semibold text-foreground">{event.agent}</span>
            <span className={cn(
              "text-xs px-1.5 py-0.5 rounded-full font-medium",
              event.status === "running" && "bg-blue-500/20 text-blue-400",
              event.status === "completed" && "bg-green-500/20 text-green-400",
              event.status === "failed" && "bg-red-500/20 text-red-400",
              event.status === "waiting" && "bg-yellow-500/20 text-yellow-400",
            )}>
              {event.status}
            </span>
            {event.order_id && (
              <span className="text-xs text-muted-foreground/60">#{event.order_id}</span>
            )}
          </div>
          <div className="text-xs text-muted-foreground font-mono">{event.event}</div>
          {event.error && (
            <div className="text-xs text-red-400 mt-0.5">Error: {event.error}</div>
          )}
        </div>
        <div className="text-xs text-muted-foreground/50 shrink-0 font-mono">
          {formatTime(event.timestamp)}
        </div>
      </div>
    );
  }

  if (event.type === "hitl_event") {
    return (
      <div className="feed-item border border-yellow-500/20">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shrink-0 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
          HI
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold text-yellow-400">HITL #{event.hitl_id}</div>
          <div className="text-xs text-muted-foreground">{event.status}</div>
        </div>
        <div className="text-xs text-muted-foreground/50 shrink-0 font-mono">
          {formatTime(event.timestamp)}
        </div>
      </div>
    );
  }

  if (event.type === "order_event") {
    return (
      <div className="feed-item border border-indigo-500/20">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shrink-0 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          OR
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold text-indigo-400">Order #{event.order_id}</div>
          <div className="text-xs text-muted-foreground">{event.status}</div>
        </div>
        <div className="text-xs text-muted-foreground/50 shrink-0 font-mono">
          {formatTime(event.timestamp)}
        </div>
      </div>
    );
  }

  return null;
}
