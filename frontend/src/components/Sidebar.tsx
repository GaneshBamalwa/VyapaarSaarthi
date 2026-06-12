import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  ShoppingCart,
  CheckSquare,
  Activity,
  Package,
  Eye,
  Mic,
  DollarSign,
  Zap,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useAgentStore } from "@/stores/agentStore";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Orders", icon: ShoppingCart, path: "/orders" },
  { label: "Approvals", icon: CheckSquare, path: "/approvals" },
  { label: "Agent Feed", icon: Activity, path: "/feed" },
  { divider: true },
  { label: "Intake Agent", icon: Package, path: "/agents/intake" },
  { label: "OCR Agent", icon: Eye, path: "/agents/ocr" },
  { label: "Speech Agent", icon: Mic, path: "/agents/speech" },
  { label: "Collections Agent", icon: DollarSign, path: "/agents/collections" },
  { divider: true },
  { label: "Simulator", icon: Zap, path: "/simulator" },
];

export function Sidebar() {
  const { connected, agentStates, pendingApprovals } = useAgentStore();

  return (
    <aside className="w-64 h-screen flex flex-col bg-card/40 border-r border-border/50 backdrop-blur-xl sticky top-0">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-saffron-500 to-indigo-500 flex items-center justify-center text-white font-bold text-sm shadow-lg">
            VS
          </div>
          <div>
            <h1 className="text-sm font-bold text-foreground">Vyapaar Saarthi</h1>
            <p className="text-xs text-muted-foreground">AI OS for MSMEs</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item, i) => {
          if ("divider" in item) {
            return <div key={i} className="my-2 border-t border-border/50" />;
          }
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                cn("nav-item", isActive && "active")
              }
            >
              <Icon size={16} />
              <span>{item.label}</span>
              {item.label === "Approvals" && pendingApprovals > 0 && (
                <span className="ml-auto text-xs bg-destructive text-white px-1.5 py-0.5 rounded-full">
                  {pendingApprovals}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* WS Status */}
      <div className="px-4 py-3 border-t border-border/50">
        <div className={cn("flex items-center gap-2 text-xs", connected ? "text-green-400" : "text-muted-foreground")}>
          {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
          <span>{connected ? "Live Connected" : "Connecting..."}</span>
          {connected && (
            <span className="ml-auto w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          )}
        </div>
      </div>
    </aside>
  );
}
