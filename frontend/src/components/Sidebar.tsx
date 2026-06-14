import { useState } from "react";
import { NavLink } from "react-router-dom";
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
  Shield,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Sun,
  Moon,
  Wallet,
  Settings,
} from "lucide-react";
import { useAgentStore } from "@/stores/agentStore";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/lib/utils";

type NavItem = { label: string; icon: typeof LayoutDashboard; path: string };
type NavSection = { title: string | null; items: NavItem[] };

const NAV_SECTIONS: NavSection[] = [
  {
    title: null,
    items: [
      { label: "Dashboard", icon: LayoutDashboard, path: "/" },
      { label: "Orders", icon: ShoppingCart, path: "/orders" },
      { label: "Expense Tracker", icon: Wallet, path: "/expenses" },
      { label: "Approvals", icon: CheckSquare, path: "/approvals" },
      { label: "Agent Feed", icon: Activity, path: "/feed" },
      { label: "Voice Chat", icon: MessageSquare, path: "/voice-chat" },
    ],
  },
  {
    title: "Agents",
    items: [
      { label: "Intake Agent", icon: Package, path: "/agents/intake" },
      { label: "OCR Agent", icon: Eye, path: "/agents/ocr" },
      { label: "Speech Agent", icon: Mic, path: "/agents/speech" },
      { label: "Collections Agent", icon: DollarSign, path: "/collections" },
      { label: "GST & Compliance", icon: Shield, path: "/agents/gst" },
    ],
  },
  {
    title: "Tools",
    items: [
      { label: "Simulator", icon: Zap, path: "/simulator" },
      { label: "Settings", icon: Settings, path: "/settings" }
    ],
  },
];

const EXPANDED_W = 256;
const RAIL_W = 76;
const PIN_KEY = "vs-sidebar-pinned";

export function Sidebar() {
  const { connected, pendingApprovals } = useAgentStore();
  const { theme, toggleTheme } = useTheme();

  const [pinned, setPinned] = useState<boolean>(() => {
    try {
      return localStorage.getItem(PIN_KEY) === "true";
    } catch {
      return false;
    }
  });
  const [hovered, setHovered] = useState(false);
  const expanded = pinned || hovered;

  const togglePin = () => {
    setPinned((p) => {
      const next = !p;
      try {
        localStorage.setItem(PIN_KEY, String(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  };

  // Labels fade/slide in only when the panel is expanded.
  const labelCls = cn(
    "truncate transition-all duration-200",
    expanded ? "opacity-100" : "opacity-0 -translate-x-1"
  );

  return (
    // Outer element reserves layout width; the panel below floats over content
    // when it expands on hover so the page never reflows.
    <div
      className="relative shrink-0 h-screen transition-[width] duration-300 ease-out"
      style={{ width: pinned ? EXPANDED_W : RAIL_W }}
    >
      <aside
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        className="glass-panel absolute inset-y-0 left-0 z-30 flex flex-col overflow-hidden
                   border-r border-border/60 shadow-xl shadow-black/20
                   transition-[width] duration-300 ease-out"
        style={{ width: expanded ? EXPANDED_W : RAIL_W }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-[20px] h-[56px] border-b border-[#27272A] shrink-0"
          style={{ width: EXPANDED_W }}
        >
          <img
            src={theme === "dark" ? "/logo-dark.png" : "/logo-light.png"}
            alt="Vyapaar Saarthi"
            className="h-[28px] w-auto object-contain object-left"
          />
          <button
            type="button"
            onClick={togglePin}
            title={pinned ? "Unpin sidebar (hover to expand)" : "Pin sidebar open"}
            className={cn(
              "shrink-0 p-1.5 rounded-md text-muted-foreground transition-colors",
              "hover:text-foreground hover:bg-muted/70",
              labelCls
            )}
          >
            {pinned ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
          </button>
        </div>

        {/* Nav */}
        <nav
          className="flex-1 overflow-y-auto overflow-x-hidden py-3 px-3 space-y-3"
          style={{ width: EXPANDED_W }}
        >
          {NAV_SECTIONS.map((section, si) => (
            <div key={si} className="space-y-0.5">
              {section.title && (
                <div
                  className={cn(
                    "px-2 pt-2 pb-1 text-[11px] font-normal uppercase tracking-[0.08em] text-[#3F3F46]",
                    labelCls
                  )}
                >
                  {section.title}
                </div>
              )}
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === "/"}
                    title={item.label}
                    className={({ isActive }) => cn("nav-item", isActive && "active")}
                  >
                    <Icon size={18} className="shrink-0" />
                    <span className={labelCls}>{item.label}</span>
                    {item.label === "Approvals" && pendingApprovals > 0 && (
                      <span
                        className={cn(
                          "ml-auto text-[10px] bg-[#6366F1] text-white px-1.5 py-0.5 rounded-full",
                          labelCls
                        )}
                      >
                        {pendingApprovals}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Footer: theme toggle + live status */}
        <div className="border-t border-border/60 p-3 space-y-1 shrink-0" style={{ width: EXPANDED_W }}>
          <button type="button" onClick={toggleTheme} className="nav-item w-full" title="Toggle light / dark theme">
            {theme === "dark" ? <Sun size={18} className="shrink-0" /> : <Moon size={18} className="shrink-0" />}
            <span className={labelCls}>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
          </button>

          <div
            className={cn(
              "nav-item cursor-default",
              connected ? "text-green-500 hover:text-green-500" : "text-muted-foreground"
            )}
          >
            {connected ? <Wifi size={18} className="shrink-0" /> : <WifiOff size={18} className="shrink-0" />}
            <span className={labelCls}>{connected ? "Live connected" : "Connecting…"}</span>
            {connected && (
              <span className={cn("ml-auto w-1.5 h-1.5 rounded-full bg-success", labelCls)} />
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
