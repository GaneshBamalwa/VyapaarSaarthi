import { useQuery } from "@tanstack/react-query";
import {
  ShoppingCart, CheckSquare, Activity, Package,
  Eye, Mic, DollarSign, TrendingUp,
} from "lucide-react";
import { KPICard } from "@/components/KPICard";
import { AgentStatusCard } from "@/components/AgentStatusCard";
import { FeedItem } from "@/components/FeedItem";
import { fetchKPIs } from "@/services/vyapaarApi";
import { useAgentStore } from "@/stores/agentStore";
import type { AgentName } from "@/types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from "recharts";

const AGENTS: AgentName[] = [
  "IntakeAgent", "OCRAgent", "SpeechAgent", "CollectionsAgent"
];

const STATUS_COLORS: Record<string, string> = {
  PENDING: "#eab308",
  APPROVED: "#22c55e",
  REJECTED: "#ef4444",
  AWAITING_APPROVAL: "#f97316",
  COMPLETED: "#6366f1",
};

export function DashboardPage() {
  const { data: kpis, isLoading } = useQuery({
    queryKey: ["kpis"],
    queryFn: fetchKPIs,
    refetchInterval: 5000,
  });

  const { events, agentStates } = useAgentStore();
  const recentEvents = events.slice(0, 8);

  const chartData = kpis
    ? Object.entries(kpis.status_breakdown).map(([status, count]) => ({
        name: status.replace("_", " "),
        count,
        fill: STATUS_COLORS[status] || "#6366f1",
      }))
    : [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold gradient-text">Command Center</h1>
        <p className="text-muted-foreground text-sm mt-1">
          AI-native operations dashboard for your MSME
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Orders Processed"
          value={isLoading ? "—" : kpis?.orders_processed ?? 0}
          icon={<ShoppingCart size={18} />}
          color="primary"
          subtitle="Total across all agents"
        />
        <KPICard
          title="Pending Approvals"
          value={isLoading ? "—" : kpis?.pending_approvals ?? 0}
          icon={<CheckSquare size={18} />}
          color="warning"
          subtitle="Needs human review"
        />
        <KPICard
          title="Agent Runs"
          value={isLoading ? "—" : kpis?.agent_runs ?? 0}
          icon={<Activity size={18} />}
          color="info"
          subtitle="Total agent invocations"
        />
        <KPICard
          title="Approved Orders"
          value={isLoading ? "—" : kpis?.approved_orders ?? 0}
          icon={<TrendingUp size={18} />}
          color="success"
          subtitle="Successfully processed"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status Grid */}
        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-foreground mb-3">Agent Status</h2>
          <div className="grid grid-cols-2 gap-3">
            {AGENTS.map((agent) => (
              <AgentStatusCard
                key={agent}
                agent={agent}
                status={agentStates[agent].status}
                lastEvent={agentStates[agent].lastEvent}
                lastUpdated={agentStates[agent].lastUpdated}
              />
            ))}
          </div>

          {/* Status Chart */}
          {chartData.length > 0 && (
            <div className="glass-card p-4 mt-4">
              <h3 className="text-sm font-semibold mb-3">Order Status Breakdown</h3>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={chartData} barSize={32}>
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10, fill: "#64748b" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(222 47% 8%)",
                      border: "1px solid hsl(223 47% 14%)",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} fillOpacity={0.8} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Live Feed Preview */}
        <div>
          <h2 className="text-sm font-semibold text-foreground mb-3">Live Agent Feed</h2>
          <div className="glass-card p-3 space-y-2 max-h-96 overflow-y-auto">
            {recentEvents.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-xs">
                <Activity size={24} className="mx-auto mb-2 opacity-40" />
                No events yet. Use the simulator ⚡
              </div>
            ) : (
              recentEvents.map((event, i) => (
                <FeedItem key={i} event={event} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
