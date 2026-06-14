import { cn, getStatusColor, formatDate, confidenceToPercent } from "@/lib/utils";
import type { Order } from "@/types";
import { CheckCircle2 } from "lucide-react";
import { fulfillOrder } from "@/services/vyapaarApi";
import { useState } from "react";

interface Props {
  order: Order;
  onClick?: (order: Order) => void;
}

export function OrderCard({ order, onClick }: Props) {
  const [isFulfilling, setIsFulfilling] = useState(false);

  const handleFulfill = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFulfilling(true);
    try {
      await fulfillOrder(order.id);
      // The websocket will broadcast the status update and react-query will refetch
    } catch (err) {
      console.error("Failed to fulfill order:", err);
      setIsFulfilling(false);
    }
  };
  return (
    <div
      className="glass-card p-4 hover:border-[#6366F1] transition-all duration-200 cursor-pointer animate-fade-in"
      onClick={() => onClick?.(order)}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono text-[#71717A]">Order #{order.id}</span>
            {order.input_type === "voice" && <span className="text-[10px] text-[#A1A1AA] border border-[#27272A] px-1 rounded">Voice</span>}
            {order.input_type === "image" && <span className="text-[10px] text-[#A1A1AA] border border-[#27272A] px-1 rounded">Image</span>}
          </div>
          {order.customer ? (
            <h3 className="text-base font-semibold text-foreground truncate">
              {order.customer}
            </h3>
          ) : (
            <h3 className="text-base font-semibold text-foreground italic opacity-70">
              Unknown Customer
            </h3>
          )}
        </div>
        <div className={cn("px-[8px] py-[3px] shrink-0 rounded-[4px] text-[11px] font-medium tracking-[0.05em] capitalize", getStatusColor(order.status))}>
          {order.status === "AWAITING_APPROVAL" ? "Awaiting approval" : order.status.toLowerCase()}
        </div>
      </div>

      <div className="mb-3 text-sm text-muted-foreground/80 italic line-clamp-2 bg-muted/30 px-2 py-1.5 rounded-md">
        "{order.raw_input}"
      </div>

      {order.items.length > 0 ? (
        <div className="flex flex-col gap-2 mb-3 bg-muted/20 rounded-lg p-2 border border-border/50">
          {order.items.map((item, i) => {
            const hasPrice = typeof item.price === "number" && item.price > 0;
            const hasQuantity = typeof item.quantity === "number" && item.quantity > 0;
            const total = hasPrice && hasQuantity ? item.price! * item.quantity! : null;
            return (
              <div key={i} className="grid grid-cols-[1fr_auto_auto] gap-x-[24px] items-center text-sm">
                <span className="font-medium text-foreground">
                  {item.name}
                  {hasQuantity && (
                    <span className="text-[#A1A1AA] text-xs font-normal ml-1.5">
                      x {item.quantity}
                    </span>
                  )}
                </span>
                {hasPrice ? (
                  <span className="text-[13px] text-[#71717A]">₹{item.price?.toLocaleString("en-IN")} / {item.unit || "unit"}</span>
                ) : (
                  <span className="text-[13px] text-[#3F3F46]">₹ — / {item.unit || "unit"}</span>
                )}
                {total !== null ? (
                  <span className="text-[13px] text-[#E4E4E7] font-medium">₹{total.toLocaleString("en-IN")}</span>
                ) : (
                  <span className="text-[13px] text-[#3F3F46]">—</span>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-xs text-muted-foreground mb-3">No parsed items</div>
      )}

      {order.delivery_date && (
        <div className="text-xs text-[#A1A1AA] mb-3 flex items-center gap-1.5">
          Due: <span className="font-medium">{order.delivery_date}</span>
        </div>
      )}

      {order.items.length > 0 && (
        <>
          <div className="h-[1px] bg-[#27272A] my-3 w-full" />
          <div className="flex justify-between items-center mb-3">
            <span className="text-[13px] text-[#52525B]">Total Order Value</span>
            <span className="text-[13px] text-[#E4E4E7] font-semibold">
              {(() => {
                const total = order.items.reduce((acc, item) => acc + ((item.price || 0) * (item.quantity || 1)), 0);
                return total > 0 ? `₹${total.toLocaleString("en-IN")}` : "—";
              })()}
            </span>
          </div>
        </>
      )}

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-border/40">
        <div className="flex flex-col text-xs text-muted-foreground">
          <span>{formatDate(order.created_at)}</span>
          {order.confidence !== null && (
            <span className={cn(
              "mt-1 w-fit px-1.5 py-0.5 rounded",
              order.confidence >= 0.8 ? "text-green-400 bg-green-400/10" : "text-yellow-400 bg-yellow-400/10"
            )}>
              {confidenceToPercent(order.confidence)} confidence
            </span>
          )}
        </div>
        {order.status !== "COMPLETED" && order.status !== "REJECTED" && (
          <button
            onClick={handleFulfill}
            disabled={isFulfilling}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-400 text-xs font-medium transition-colors"
          >
            {isFulfilling ? (
              <span className="animate-pulse">Fulfilling...</span>
            ) : (
              <>
                <CheckCircle2 size={14} />
                Fulfill
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
