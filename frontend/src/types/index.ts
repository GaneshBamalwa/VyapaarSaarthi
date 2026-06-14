// ─── Order Types ─────────────────────────────────────────────────────────────

export type OrderStatus =
  | "PENDING"
  | "CLARIFICATION_NEEDED"
  | "AWAITING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "PROCESSING"
  | "COMPLETED";

export interface OrderItem {
  id: number;
  order_id: number;
  name: string;
  quantity: number | null;
  unit: string | null;
  price: number | null;
}

export interface Order {
  id: number;
  customer: string | null;
  raw_input: string;
  input_type: "text" | "voice" | "image";
  status: OrderStatus;
  confidence: number | null;
  delivery_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface OrderListResponse {
  total: number;
  orders: Order[];
}

// ─── Agent Types ──────────────────────────────────────────────────────────────

export type AgentName =
  | "IntakeAgent"
  | "ClarificationAgent"
  | "OCRAgent"
  | "SpeechAgent"
  | "CollectionsAgent";

export type AgentStatus = "idle" | "running" | "completed" | "failed" | "waiting";

export interface AgentTrace {
  id: number;
  agent: AgentName;
  event: string;
  status: string;
  payload: unknown;
  error: string | null;
  duration_ms: number | null;
  order_id: number | null;
  timestamp: string;
}

export interface AgentTraceListResponse {
  total: number;
  traces: AgentTrace[];
}

// ─── HITL Types ───────────────────────────────────────────────────────────────

export type HITLStatus = "PENDING" | "APPROVED" | "REJECTED" | "EDITED";

export interface HITLItem {
  id: number;
  order_id: number | null;
  graph_thread_id: string | null;
  status: HITLStatus;
  reason: string | null;
  payload: Record<string, unknown>;
  edited_payload: Record<string, unknown> | null;
  reviewer_notes: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface HITLListResponse {
  total: number;
  items: HITLItem[];
}

// ─── Intake Types ─────────────────────────────────────────────────────────────

export interface IntakeResult {
  status: string;
  order_id: number;
  parsed: {
    customer: string;
    items: Array<{ name: string; quantity: number; unit: string }>;
    delivery_date: string;
    confidence: number;
    notes: string;
  };
  requires_hitl: boolean;
  hitl_id: number | null;
  clarification: {
    status: "CLEAR" | "AMBIGUOUS";
    clarification_question: string;
    ambiguity_type: string;
    confidence: number;
  } | null;
}

// ─── Collections Types ────────────────────────────────────────────────────────

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface CollectionsResult {
  status: string;
  data: {
    risk: RiskLevel;
    risk_score: number;
    message: string;
    recommended_action: string;
    follow_up_days: number;
  };
}

// ─── OCR Types ────────────────────────────────────────────────────────────────

export interface OCRResult {
  status: string;
  data: {
    raw_text: string;
    document_type: string;
    language: string;
    confidence: number;
    key_fields: Record<string, string>;
  };
}

// ─── Speech Types ─────────────────────────────────────────────────────────────

export interface SpeechResult {
  status: string;
  data: {
    transcript: string;
    language_code: string;
  };
}

// ─── Dashboard Types ──────────────────────────────────────────────────────────

export interface DashboardKPIs {
  orders_processed: number;
  pending_approvals: number;
  agent_runs: number;
  approved_orders: number;
  rejected_orders: number;
  status_breakdown: Record<string, number>;
}

// ─── WebSocket Event Types ────────────────────────────────────────────────────

export interface WSAgentEvent {
  type: "agent_event";
  agent: AgentName;
  status: AgentStatus;
  event: string;
  data: unknown;
  order_id: number | null;
  error: string | null;
  timestamp: string;
}

export interface WSHITLEvent {
  type: "hitl_event";
  hitl_id: number;
  status: string;
  payload: unknown;
  timestamp: string;
}

export interface WSOrderEvent {
  type: "order_event";
  order_id: number;
  status: string;
  data: unknown;
  timestamp: string;
}

export type WSEvent = WSAgentEvent | WSHITLEvent | WSOrderEvent;
