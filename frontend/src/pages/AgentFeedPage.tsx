import { useRef, useEffect } from "react";
import { Activity, Trash2 } from "lucide-react";
import { FeedItem } from "@/components/FeedItem";
import { useAgentStore } from "@/stores/agentStore";

export function AgentFeedPage() {
  const { events, clearEvents, connected } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="space-y-6 animate-fade-in h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Agent Feed</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-muted-foreground"}`} />
            <p className="text-muted-foreground text-sm">
              {connected ? "Live — streaming agent events" : "Disconnected"} · {events.length} events
            </p>
          </div>
        </div>
        <button
          onClick={clearEvents}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/60 hover:bg-muted
                     text-sm text-muted-foreground hover:text-foreground transition-all"
        >
          <Trash2 size={14} /> Clear
        </button>
      </div>

      <div className="glass-card p-4 space-y-2 min-h-96 max-h-[calc(100vh-200px)] overflow-y-auto">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Activity size={40} className="mb-3 opacity-30" />
            <div className="text-sm font-medium">Waiting for agent events...</div>
            <div className="text-xs mt-1">Use the ⚡ Simulator to trigger agents</div>
          </div>
        ) : (
          <>
            {[...events].reverse().map((event, i) => (
              <FeedItem key={`${event.timestamp}-${i}`} event={event} />
            ))}
            <div ref={bottomRef} />
          </>
        )}
      </div>
    </div>
  );
}
