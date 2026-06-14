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
    PENDING: "text-[#F59E0B] bg-[#1C1407] border border-[#78350F]",
    AWAITING_APPROVAL: "text-[#818CF8] bg-[#1A1033] border border-[#3730A3]",
    APPROVED: "text-[#10B981] bg-[#0A1F14] border border-[#065F46]",
    REJECTED: "text-red-400 bg-red-400/10 border border-red-400/20",
    COMPLETED: "text-[#10B981] bg-[#0A1F14] border border-[#065F46]",
    PROCESSING: "text-indigo-400 bg-indigo-400/10 border border-indigo-400/20",
    CLARIFICATION_NEEDED: "text-purple-400 bg-purple-400/10 border border-purple-400/20",
  };
  return map[status] || "text-muted-foreground bg-muted border border-border";
}

export function getAgentColor(agent: string): string {
  return "text-[#6366F1] bg-transparent border-[#6366F1]";
}

export function getAgentIcon(agent: string): string {
  const map: Record<string, string> = {
    IntakeAgent: "IA",
    ClarificationAgent: "CA",
    OCRAgent: "OA",
    SpeechAgent: "SA",
    CollectionsAgent: "CO",
  };
  return map[agent] || "AI";
}

export function confidenceToPercent(confidence: number | null): string {
  if (confidence === null) return "—";
  return `${Math.round(confidence * 100)}%`;
}
