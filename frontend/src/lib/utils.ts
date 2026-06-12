import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function getRiskColor(risk: string): string {
  switch (risk) {
    case "LOW": return "risk-low";
    case "MEDIUM": return "risk-medium";
    case "HIGH": return "risk-high";
    default: return "risk-low";
  }
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    PENDING: "text-yellow-400 bg-yellow-400/10",
    AWAITING_APPROVAL: "text-orange-400 bg-orange-400/10",
    APPROVED: "text-green-400 bg-green-400/10",
    REJECTED: "text-red-400 bg-red-400/10",
    COMPLETED: "text-blue-400 bg-blue-400/10",
    PROCESSING: "text-indigo-400 bg-indigo-400/10",
    CLARIFICATION_NEEDED: "text-purple-400 bg-purple-400/10",
  };
  return map[status] || "text-muted-foreground bg-muted";
}

export function getAgentColor(agent: string): string {
  const map: Record<string, string> = {
    IntakeAgent: "text-saffron-400 bg-saffron-400/10 border-saffron-400/30",
    ClarificationAgent: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    OCRAgent: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    SpeechAgent: "text-green-400 bg-green-400/10 border-green-400/30",
    CollectionsAgent: "text-red-400 bg-red-400/10 border-red-400/30",
  };
  return map[agent] || "text-muted-foreground bg-muted border-border";
}

export function getAgentIcon(agent: string): string {
  const map: Record<string, string> = {
    IntakeAgent: "📦",
    ClarificationAgent: "🔍",
    OCRAgent: "👁️",
    SpeechAgent: "🎤",
    CollectionsAgent: "💰",
  };
  return map[agent] || "🤖";
}

export function confidenceToPercent(confidence: number | null): string {
  if (confidence === null) return "—";
  return `${Math.round(confidence * 100)}%`;
}
