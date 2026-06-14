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

export const fetchOrders = (params?: { skip?: number; limit?: number; month?: string }): Promise<OrderListResponse> =>
  api.get("/orders", { params }).then((r) => r.data);

export const fetchOrder = async (id: number) => {
  const res = await api.get(`/orders/${id}`);
  return res.data;
};

export const fulfillOrder = async (id: number) => {
  const res = await api.post(`/orders/${id}/fulfill`);
  return res.data;
};

// ─── Intake ──────────────────────────────────────────────────────────────────

export const runIntake = (text: string): Promise<IntakeResult> =>
  api.post("/intake", { text }).then((r) => r.data);

// ─── Expenses ──────────────────────────────────────────────────────────────────

export const fetchExpenses = (month?: string) =>
  api.get("/expenses", { params: { month } }).then((r) => r.data);

export const createExpense = (payload: any) =>
  api.post("/expenses", payload).then((r) => r.data);

export const markExpensePaid = (id: number) =>
  api.patch(`/expenses/${id}/mark-paid`).then((r) => r.data);

export const deleteExpense = (id: number) =>
  api.delete(`/expenses/${id}`).then((r) => r.data);

export const fetchMonthlyReport = (month?: string) =>
  api.get("/reports/monthly", { params: { month } }).then((r) => r.data);

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

// ─── Voice & Chat ────────────────────────────────────────────────────────────

export const chat = (message: string, sessionId?: string, generateAudio = false) =>
  api.post("/voice/chat", { message, session_id: sessionId, generate_audio: generateAudio }).then((r) => r.data);

export const transcribe = (formData: FormData) =>
  api.post("/voice/transcribe", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);

export const synthesize = (formData: FormData) =>
  api.post("/voice/synthesize", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);

export const weeklyBriefing = () =>
  api.post("/voice/weekly-briefing", null, { timeout: 90000 }).then((r) => r.data);

export const getSessionHistory = (sessionId: string) =>
  api.get(`/voice/sessions/${sessionId}/history`).then((r) => r.data);

// ─── GST & Invoices ──────────────────────────────────────────────────────────

export const generateInvoice = (payload: any) =>
  api.post("/gst/invoice/generate", payload).then((r) => r.data);

export const listInvoices = () =>
  api.get("/gst/invoices").then((r) => r.data);

export const verifyGstin = (gstin: string) =>
  api.get(`/gst/gstin/verify/${gstin}`).then((r) => r.data);

export const validateReturn = () =>
  api.post("/gst/validate-return").then((r) => r.data);

export const lookupHsn = (product: string) =>
  api.get(`/gst/hsn/lookup?product=${encodeURIComponent(product)}`).then((r) => r.data);

// ─── Compliance ──────────────────────────────────────────────────────────────

export const translateNotice = (raw_text: string) =>
  api.post("/compliance/notice/translate", { raw_text }).then((r) => r.data);

export const listNotices = () =>
  api.get("/compliance/notices").then((r) => r.data);

export const complianceCalendar = (gstin: string) =>
  api.get(`/compliance/calendar/${gstin}`).then((r) => r.data);

export const matchSchemes = (payload: any) =>
  api.post("/compliance/schemes/match", payload).then((r) => r.data);

export const gstrSummary = (period: string) =>
  api.get(`/compliance/gstr-summary/${period}`).then((r) => r.data);

export const fetchOverdueInvoices = () =>
  api.get("/collections/overdue").then((r) => r.data);

// ─── Collections (Autonomous Agent) ──────────────────────────────────────────

export const fetchCollectionsStats = () =>
  api.get("/collections/stats").then((r) => r.data);

export const fetchCollectionsOverdue = (params?: { min_days?: number; max_days?: number }) =>
  api.get("/collections/overdue", { params }).then((r) => r.data);

export const fetchCollectionsRiskScores = (tier?: string) =>
  api.get("/collections/risk-scores", { params: tier ? { tier } : {} }).then((r) => r.data);

export const fetchCollectionsHistory = (params?: { status?: string; buyer_name?: string; limit?: number; offset?: number }) =>
  api.get("/collections/reminder-history", { params }).then((r) => r.data);

export const sendCollectionsReminder = (body: { invoice_id: number; override_level?: number }) =>
  api.post("/collections/send-reminder", body).then((r) => r.data);

export const triggerCollectionsJob = () =>
  api.post("/collections/run-job").then((r) => r.data);

export const approveCollectionsReminder = (body: { reminder_id: number; approved: boolean; approved_by: string }) =>
  api.post("/collections/hitl/approve", body).then((r) => r.data);

export const saveBuyerPhone = (body: { buyer_name: string; phone: string }) =>
  api.post("/collections/buyers/phone", body).then((r) => r.data);

export const markPaymentPaid = (invoice_id: number) =>
  api.post(`/collections/mark-paid/${invoice_id}`).then((r) => r.data);

// ─── Company Profile ────────────────────────────────────────────────────────

export const fetchCompanyProfile = () =>
  api.get("/company/profile").then((r) => r.data);

export const updateCompanyProfile = (payload: any) =>
  api.post("/company/profile", payload).then((r) => r.data);
