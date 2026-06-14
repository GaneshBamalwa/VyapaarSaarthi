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
  primary: "border-[#27272A]",
  success: "border-[#27272A]",
  warning: "border-[#27272A]",
  error: "border-[#27272A]",
  info: "border-[#27272A]",
};

const iconColorMap = {
  primary: "bg-[#18181B] text-[#6366F1]",
  success: "bg-[#18181B] text-[#10B981]",
  warning: "bg-[#18181B] text-[#F59E0B]",
  error: "bg-[#18181B] text-[#EF4444]",
  info: "bg-[#18181B] text-[#6366F1]",
};

export function KPICard({ title, value, subtitle, icon, trend, color = "primary", className }: Props) {
  return (
    <div className={cn(
      "kpi-card",
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
