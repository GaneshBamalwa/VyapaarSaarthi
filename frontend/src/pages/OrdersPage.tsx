import { useQuery } from "@tanstack/react-query";
import { RefreshCw, ShoppingCart } from "lucide-react";
import { OrderCard } from "@/components/OrderCard";
import { fetchOrders } from "@/services/vyapaarApi";

export function OrdersPage() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["orders"],
    queryFn: () => fetchOrders({ limit: 100 }),
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Orders</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {data?.total ?? 0} orders processed by agents
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/60 hover:bg-muted
                     text-sm text-muted-foreground hover:text-foreground transition-all duration-200"
        >
          <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
          Refresh
        </button>
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
            Use the ⚡ Simulator to generate sample orders
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
