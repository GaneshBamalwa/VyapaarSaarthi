import { useState, useCallback } from 'react'
import axios from 'axios'

const BASE = '/api'

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const call = useCallback(async (method, path, data = null, options = {}) => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios({ method, url: BASE + path, data, ...options })
      return res.data
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Request failed'
      setError(msg)
      throw e
    } finally {
      setLoading(false)
    }
  }, [])

  return { call, loading, error }
}

// Typed helpers used by pages
export const api = {
  chat: (message, session_id, generate_audio = false) =>
    axios.post('/api/voice/chat', { message, session_id, generate_audio }).then(r => r.data),

  transcribe: (formData) =>
    axios.post('/api/voice/transcribe', formData).then(r => r.data),

  synthesize: (formData) =>
    axios.post('/api/voice/synthesize', formData).then(r => r.data),

  weeklyBriefing: () =>
    axios.post('/api/voice/weekly-briefing').then(r => r.data),

  generateInvoice: (payload) =>
    axios.post('/api/gst/invoice/generate', payload).then(r => r.data),

  listInvoices: () =>
    axios.get('/api/gst/invoices').then(r => r.data),

  verifyGstin: (gstin) =>
    axios.get(`/api/gst/gstin/verify/${gstin}`).then(r => r.data),

  validateReturn: () =>
    axios.post('/api/gst/validate-return').then(r => r.data),

  lookupHsn: (product) =>
    axios.get(`/api/gst/hsn/lookup?product=${encodeURIComponent(product)}`).then(r => r.data),

  translateNotice: (raw_text) =>
    axios.post('/api/compliance/notice/translate', { raw_text }).then(r => r.data),

  listNotices: () =>
    axios.get('/api/compliance/notices').then(r => r.data),

  complianceCalendar: (gstin) =>
    axios.get(`/api/compliance/calendar/${gstin}`).then(r => r.data),

  matchSchemes: (payload) =>
    axios.post('/api/compliance/schemes/match', payload).then(r => r.data),

  gstrSummary: (period) =>
    axios.get(`/api/compliance/gstr-summary/${period}`).then(r => r.data),

  hitlQueue: () =>
    axios.get('/api/hitl/queue').then(r => r.data),

  hitlDecide: (id, action, edited_payload) =>
    axios.post(`/api/hitl/queue/${id}/decide`, { action, edited_payload }).then(r => r.data),

  // ── VyapaarSaarthi / Order Intake ──────────────────────────────────────────
  submitOrder: (text, input_type = 'text') =>
    axios.post('/api/intake/order', { text, input_type }).then(r => r.data),

  listOrders: () =>
    axios.get('/api/intake/orders').then(r => r.data),

  getOrder: (id) =>
    axios.get(`/api/intake/orders/${id}`).then(r => r.data),

  intakeHitlQueue: () =>
    axios.get('/api/intake/hitl-queue').then(r => r.data),

  reviewIntakeHitl: (id, approved, edited_payload = {}, reviewer_notes = '') =>
    axios.post(`/api/intake/hitl-queue/${id}/review`, { approved, edited_payload, reviewer_notes }).then(r => r.data),

  // ── OCR ─────────────────────────────────────────────────────────────────────
  ocrExtract: (formData) =>
    axios.post('/api/ocr/extract', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data),

  // ── Speech ──────────────────────────────────────────────────────────────────
  speechTranscribe: (formData) =>
    axios.post('/api/speech/transcribe', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data),

  // ── Collections ─────────────────────────────────────────────────────────────
  analyzeCollection: (payload) =>
    axios.post('/api/collections/analyze', payload).then(r => r.data),

  overdueInvoices: () =>
    axios.get('/api/collections/overdue').then(r => r.data),

  // ── Agent Traces ─────────────────────────────────────────────────────────────
  agentTraces: (limit = 50) =>
    axios.get(`/api/agents/traces?limit=${limit}`).then(r => r.data),

  // ── Dashboard ────────────────────────────────────────────────────────────────
  dashboardMetrics: () =>
    axios.get('/api/dashboard/metrics').then(r => r.data),

  dashboardCashflow: () =>
    axios.get('/api/dashboard/cashflow').then(r => r.data),

  dashboardAlerts: () =>
    axios.get('/api/dashboard/alerts').then(r => r.data),

  // ── Simulator ───────────────────────────────────────────────────────────────
  simulateOrder: () =>
    axios.post('/api/simulator/generate-order').then(r => r.data),

  simulateAmbiguous: () =>
    axios.post('/api/simulator/generate-ambiguous').then(r => r.data),

  simulateOverdue: () =>
    axios.post('/api/simulator/generate-overdue').then(r => r.data),
}
