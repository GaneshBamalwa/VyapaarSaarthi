import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ReactNode;
  trend?: { value: number; label: string };
  color?: "primary" | "success" | "warning" | "error" | "info";
  className?: string;
}

const colorMap = {
  primary: "from-saffron-500/20 to-saffron-600/10 border-saffron-500/20",
  success: "from-green-500/20 to-green-600/10 border-green-500/20",
  warning: "from-yellow-500/20 to-yellow-600/10 border-yellow-500/20",
  error: "from-red-500/20 to-red-600/10 border-red-500/20",
  info: "from-blue-500/20 to-blue-600/10 border-blue-500/20",
};

const iconColorMap = {
  primary: "bg-saffron-500/20 text-saffron-400",
  success: "bg-green-500/20 text-green-400",
  warning: "bg-yellow-500/20 text-yellow-400",
  error: "bg-red-500/20 text-red-400",
  info: "bg-blue-500/20 text-blue-400",
};

export function KPICard({ title, value, subtitle, icon, trend, color = "primary", className }: Props) {
  return (
    <div className={cn(
      "kpi-card bg-gradient-to-br",
      colorMap[color],
      className
    )}>
      <div className="flex items-start justify-between mb-4">
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", iconColorMap[color])}>
          {icon}
        </div>
        {trend && (
          <div className={cn(
            "text-xs font-medium px-2 py-1 rounded-full",
            trend.value >= 0 ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10"
          )}>
            {trend.value >= 0 ? "+" : ""}{trend.value}% {trend.label}
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-foreground mb-1">{value}</div>
      <div className="text-sm font-medium text-foreground/80">{title}</div>
      {subtitle && <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>}
    </div>
  );
}
