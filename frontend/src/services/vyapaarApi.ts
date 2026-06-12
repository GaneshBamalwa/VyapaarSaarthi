import api from "./api";
import type {
  OrderListResponse,
  Order,
  IntakeResult,
  DashboardKPIs,
  HITLListResponse,
  AgentTraceListResponse,
  CollectionsResult,
  OCRResult,
  SpeechResult,
} from "@/types";

// ─── Dashboard ───────────────────────────────────────────────────────────────

export const fetchKPIs = (): Promise<DashboardKPIs> =>
  api.get("/dashboard/kpis").then((r) => r.data);

// ─── Orders ──────────────────────────────────────────────────────────────────

export const fetchOrders = (params?: { skip?: number; limit?: number }): Promise<OrderListResponse> =>
  api.get("/orders", { params }).then((r) => r.data);

export const fetchOrder = (id: number): Promise<Order> =>
  api.get(`/orders/${id}`).then((r) => r.data);

// ─── Intake ──────────────────────────────────────────────────────────────────

export const runIntake = (text: string): Promise<IntakeResult> =>
  api.post("/intake", { text }).then((r) => r.data);

// ─── OCR ─────────────────────────────────────────────────────────────────────

export const runOCR = (file: File): Promise<OCRResult> => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/ocr/extract", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

// ─── Speech ──────────────────────────────────────────────────────────────────

export const runSpeech = (file: File, language = "hi-IN"): Promise<SpeechResult> => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post(`/speech/transcribe?language=${language}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

// ─── Collections ─────────────────────────────────────────────────────────────

export const runCollections = (data: {
  invoice_id: string;
  customer: string;
  amount: number;
  due_days: number;
  previous_reminders?: number;
}): Promise<CollectionsResult> =>
  api.post("/collections/analyze", data).then((r) => r.data);

// ─── HITL ────────────────────────────────────────────────────────────────────

export const fetchHITLPending = (): Promise<HITLListResponse> =>
  api.get("/hitl/pending").then((r) => r.data);

export const fetchHITLAll = (limit = 50): Promise<HITLListResponse> =>
  api.get("/hitl/all", { params: { limit } }).then((r) => r.data);

export const resolveHITL = (
  id: number,
  action: "approve" | "reject" | "edit",
  edited_payload?: unknown,
  reviewer_notes?: string
) =>
  api
    .post(`/hitl/${id}/resolve`, { action, edited_payload, reviewer_notes })
    .then((r) => r.data);

// ─── Agent Traces ─────────────────────────────────────────────────────────────

export const fetchTraces = (limit = 100): Promise<AgentTraceListResponse> =>
  api.get("/agents/traces", { params: { limit } }).then((r) => r.data);

// ─── Simulator ───────────────────────────────────────────────────────────────

export const simulateSampleOrder = () =>
  api.post("/simulator/generate-order").then((r) => r.data);

export const simulateAmbiguousOrder = () =>
  api.post("/simulator/generate-ambiguous").then((r) => r.data);

export const simulateOverdueInvoice = () =>
  api.post("/simulator/generate-overdue").then((r) => r.data);
