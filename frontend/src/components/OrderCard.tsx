import { cn, getStatusColor, formatDate, confidenceToPercent } from "@/lib/utils";
import type { Order } from "@/types";

interface Props {
  order: Order;
  onClick?: (order: Order) => void;
}

export function OrderCard({ order, onClick }: Props) {
  return (
    <div
      className="glass-card p-4 hover:border-primary/30 transition-all duration-200 cursor-pointer hover:shadow-lg hover:shadow-primary/5 animate-fade-in"
      onClick={() => onClick?.(order)}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-muted-foreground">#{order.id}</span>
            {order.input_type === "voice" && <span className="text-xs">🎤</span>}
            {order.input_type === "image" && <span className="text-xs">📷</span>}
          </div>
          <p className="text-sm font-medium text-foreground line-clamp-2">{order.raw_input}</p>
        </div>
        <div className={cn("tag px-2 py-1 shrink-0 rounded-md text-xs font-medium", getStatusColor(order.status))}>
          {order.status}
        </div>
      </div>

      {order.customer && (
        <div className="text-xs text-muted-foreground mb-2">
          👤 {order.customer}
        </div>
      )}

      {order.items.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {order.items.map((item, i) => (
            <span key={i} className="text-xs bg-muted px-2 py-0.5 rounded-full text-muted-foreground">
              {item.quantity && `${item.quantity} `}{item.unit && `${item.unit} `}{item.name}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{formatDate(order.created_at)}</span>
        {order.confidence !== null && (
          <span className={cn(
            "px-1.5 py-0.5 rounded",
            order.confidence >= 0.8 ? "text-green-400 bg-green-400/10" : "text-yellow-400 bg-yellow-400/10"
          )}>
            {confidenceToPercent(order.confidence)} confidence
          </span>
        )}
      </div>
    </div>
  );
}
