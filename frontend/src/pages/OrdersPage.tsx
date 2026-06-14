import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, ShoppingCart, Download } from "lucide-react";
import { OrderCard } from "@/components/OrderCard";
import { fetchOrders } from "@/services/vyapaarApi";
import { useAgentStore } from "@/stores/agentStore";

export function OrdersPage() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });

  const events = useAgentStore((state) => state.events);

  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[0];
      if (latestEvent.type === "order_event") {
        queryClient.invalidateQueries({ queryKey: ["orders", month] });
      }
    }
  }, [events, month, queryClient]);

  const last6Months = Array.from({ length: 6 }).map((_, i) => {
    const d = new Date();
    d.setMonth(d.getMonth() - i);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["orders", month],
    queryFn: () => fetchOrders({ limit: 100, month }),
    refetchInterval: 10000,
  });

  const currentRevenue = data?.orders.reduce((acc, order) => {
    if (order.status === "COMPLETED") {
      const orderTotal = order.items.reduce((sum, item) => sum + ((item.price || 0) * (item.quantity || 0)), 0);
      return acc + orderTotal;
    }
    return acc;
  }, 0) || 0;

  const unrealisedRevenue = data?.orders.reduce((acc, order) => {
    if (order.status !== "COMPLETED" && order.status !== "REJECTED") {
      const orderTotal = order.items.reduce((sum, item) => sum + ((item.price || 0) * (item.quantity || 0)), 0);
      return acc + orderTotal;
    }
    return acc;
  }, 0) || 0;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Orders</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {data?.total ?? 0} orders processed by agents
          </p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="input-base"
          >
            {last6Months.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <button
            onClick={() => window.open(`http://localhost:8000/api/reports/download?month=${month}&report_type=orders`, "_blank")}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500/10 text-indigo-500 hover:bg-indigo-500/20 text-sm font-medium transition-all duration-200"
          >
            <Download size={16} />
            Download Report (XLSX)
          </button>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/60 hover:bg-muted
                     text-sm text-muted-foreground hover:text-foreground transition-all duration-200"
        >
           <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-green-500">
          <div className="text-muted-foreground text-sm font-medium mb-1">Current Revenue (Realised)</div>
          <div className="text-3xl font-bold text-foreground">
            ₹{currentRevenue.toLocaleString()}
          </div>
        </div>
        <div className="glass-card p-6 border-l-4 border-l-yellow-500">
          <div className="text-muted-foreground text-sm font-medium mb-1">Unrealised Revenue (Pending)</div>
          <div className="text-3xl font-bold text-foreground">
            ₹{unrealisedRevenue.toLocaleString()}
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton h-36 rounded-xl" />
          ))}
        </div>
      ) : data?.orders.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <ShoppingCart size={48} className="mx-auto mb-4 text-muted-foreground/30" />
          <div className="text-foreground font-medium mb-2">No orders yet</div>
          <div className="text-muted-foreground text-sm">
            Use the Simulator to generate sample orders
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data?.orders.map((order) => (
            <OrderCard key={order.id} order={order} />
          ))}
        </div>
      )}
    </div>
  );
}
