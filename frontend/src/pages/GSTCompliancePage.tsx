import React, { useState, useEffect } from "react";
import {
  FileText,
  ShieldCheck,
  Gift,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
} from "lucide-react";
import * as api from "@/services/vyapaarApi";
import { clsx } from "clsx";

interface TabBtnProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function TabBtn({ active, onClick, children }: TabBtnProps) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "px-4 py-2 text-sm font-medium rounded-lg transition",
        active ? "bg-brand text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
      )}
    >
      {children}
    </button>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    paid: "bg-green-500/20 text-green-400 border-green-500/30",
    approved: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    overdue: "bg-red-500/20 text-red-400 border-red-500/30",
    draft: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    Filed: "bg-green-500/20 text-green-400 border-green-500/30",
    Pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    unreviewed: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  };
  return (
    <span
      className={clsx(
        "text-xs px-2 py-0.5 rounded-full border",
        styles[status] || "bg-slate-600/50 text-slate-300 border-slate-500/30"
      )}
    >
      {status}
    </span>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 flex items-center gap-2 text-sm text-red-400">
      <AlertCircle size={14} /> {message}
    </div>
  );
}

// ── Invoices Tab ──────────────────────────────────────────────────────────────
function InvoicesTab() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [form, setForm] = useState({
    buyer_name: "",
    buyer_state: "Maharashtra",
    buyer_gstin: "",
    product: "Steel Rods",
    qty: 100,
    rate: 85,
  });

  const loadInvoices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listInvoices();
      setInvoices(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to load invoices");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, []);

  const generateInvoice = async () => {
    if (!form.buyer_name.trim()) return;
    setGenerating(true);
    try {
      await api.generateInvoice({
        order_id: Math.floor(Math.random() * 1000),
        buyer_name: form.buyer_name,
        buyer_state: form.buyer_state,
        buyer_gstin: form.buyer_gstin || null,
        line_items: [
          { name: form.product, qty: Number(form.qty), unit: "kg", rate: Number(form.rate) },
        ],
      });
      await loadInvoices();
      setForm((prev) => ({ ...prev, buyer_name: "", buyer_gstin: "" }));
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Invoice generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const validateReturn = async () => {
    setValidating(true);
    setValidationResult(null);
    try {
      const data = await api.validateReturn();
      setValidationResult(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Validation failed");
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="space-y-5">
      {error && <ErrorBanner message={error} />}

      <div className="bg-card rounded-xl border border-border p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <FileText size={14} /> Generate GST Invoice
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { label: "Buyer Name *", key: "buyer_name", placeholder: "Ramesh Traders" },
            { label: "Buyer State", key: "buyer_state", placeholder: "Maharashtra" },
            { label: "Buyer GSTIN (optional)", key: "buyer_gstin", placeholder: "29AABCT1332L1ZK" },
            { label: "Product", key: "product", placeholder: "Steel Rods" },
            { label: "Qty (kg)", key: "qty", placeholder: "100", type: "number" },
            { label: "Rate (₹/kg)", key: "rate", placeholder: "85", type: "number" },
          ].map((f) => (
            <div key={f.key}>
              <label className="text-xs text-slate-400 mb-1 block">{f.label}</label>
              <input
                type={f.type || "text"}
                value={form[f.key as keyof typeof form]}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    [f.key]: f.type === "number" ? Number(e.target.value) : e.target.value,
                  }))
                }
                placeholder={f.placeholder}
                className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-brand/60"
              />
            </div>
          ))}
        </div>
        <div className="flex gap-3 mt-4">
          <button
            onClick={generateInvoice}
            disabled={generating || !form.buyer_name.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-brand hover:bg-brand-dark text-white rounded-lg text-sm transition disabled:opacity-50"
          >
            {generating ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
            {generating ? "Generating..." : "Generate Invoice"}
          </button>
          <button
            onClick={validateReturn}
            disabled={validating}
            className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/40 text-green-400 rounded-lg text-sm hover:bg-green-500/30 transition disabled:opacity-50"
          >
            {validating ? <Loader2 size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
            Validate GSTR
          </button>
        </div>

        {validationResult && (
          <div
            className={clsx(
              "mt-3 p-3 rounded-lg border text-sm",
              validationResult.filing_ready
                ? "bg-green-500/10 border-green-500/30"
                : "bg-yellow-500/10 border-yellow-500/30"
            )}
          >
            <div className="flex items-center gap-2 font-medium mb-2">
              {validationResult.filing_ready ? (
                <CheckCircle2 size={14} className="text-green-400" />
              ) : (
                <AlertCircle size={14} className="text-yellow-400" />
              )}
              <span className={validationResult.filing_ready ? "text-green-400" : "text-yellow-400"}>
                {validationResult.overall_status === "valid"
                  ? "Return valid — ready to file"
                  : "Issues found — review before filing"}
              </span>
            </div>
            {validationResult.suggestions?.map((s: string, i: number) => (
              <p key={i} className="text-xs text-slate-300 ml-5">
                {s}
              </p>
            ))}
            {validationResult.issues?.map((s: string, i: number) => (
              <p key={i} className="text-xs text-red-300 ml-5">
                {s}
              </p>
            ))}
          </div>
        )}
      </div>

      <div className="bg-card rounded-xl border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <span className="text-sm font-semibold text-white">
            All Invoices {!loading && `(${invoices.length})`}
          </span>
          <button onClick={loadInvoices} className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
        {loading ? (
          <div className="p-8 flex justify-center">
            <div className="w-6 h-6 border-2 border-brand border-t-transparent rounded-full animate-spin" />
          </div>
        ) : invoices.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No invoices found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-slate-400">
                  {["Invoice #", "Buyer", "State", "Subtotal", "Tax", "Total", "Type", "Status"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id} className="border-b border-border/50 hover:bg-white/5 transition">
                    <td className="px-4 py-2.5 text-brand font-mono text-[11px]">{inv.invoice_number}</td>
                    <td className="px-4 py-2.5 text-white">{inv.buyer_name}</td>
                    <td className="px-4 py-2.5 text-slate-400">{inv.buyer_state}</td>
                    <td className="px-4 py-2.5 text-slate-300">₹{inv.subtotal?.toLocaleString("en-IN")}</td>
                    <td className="px-4 py-2.5 text-slate-300">
                      ₹{((inv.cgst || 0) + (inv.sgst || 0) + (inv.igst || 0)).toLocaleString("en-IN")}
                    </td>
                    <td className="px-4 py-2.5 text-white font-medium">₹{inv.total?.toLocaleString("en-IN")}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={clsx(
                          "px-2 py-0.5 rounded text-[10px] font-medium",
                          inv.tax_type === "IGST" ? "bg-blue-500/20 text-blue-300" : "bg-purple-500/20 text-purple-300"
                        )}
                      >
                        {inv.tax_type}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={inv.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Notices Tab ──────────────────────────────────────────────────────────────
function NoticesTab() {
  const [notices, setNotices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [translating, setTranslating] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    api.listNotices()
      .then(setNotices)
      .catch((e: any) => setError(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  const translateNotice = async () => {
    if (!input.trim()) return;
    setTranslating(true);
    setError(null);
    try {
      const result = await api.translateNotice(input);
      setNotices((prev) => [
        {
          id: result.notice_id || Date.now(),
          raw_text: input,
          translated_hindi: result.hindi_translation,
          action_items: result.action_items,
          status: "unreviewed",
          created_at: new Date().toISOString(),
        },
        ...prev,
      ]);
      setInput("");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Translation failed");
    } finally {
      setTranslating(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}

      <div className="bg-card rounded-xl border border-border p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Paste GST Notice → Hindi Translation + Action Plan</h3>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste the full text of your GST notice here (ASMT-10, DRC-01, etc.)..."
          rows={4}
          className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-brand/60 resize-none"
        />
        <button
          onClick={translateNotice}
          disabled={translating || !input.trim()}
          className="mt-2 flex items-center gap-2 px-4 py-2 bg-brand hover:bg-brand-dark text-white rounded-lg text-sm transition disabled:opacity-50"
        >
          {translating ? <Loader2 size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
          {translating ? "Analyzing with Gemini..." : "Translate & Explain in Hindi"}
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="w-6 h-6 border-2 border-brand border-t-transparent rounded-full animate-spin" />
        </div>
      ) : notices.length === 0 ? (
        <div className="bg-card rounded-xl border border-border p-8 text-center text-slate-500 text-sm">
          No GST notices yet
        </div>
      ) : (
        <div className="space-y-3">
          {notices.map((notice) => (
            <div key={notice.id} className="bg-card rounded-xl border border-border overflow-hidden">
              <div
                className="p-4 flex items-start justify-between cursor-pointer"
                onClick={() => setExpanded(expanded === notice.id ? null : notice.id)}
              >
                <div className="flex-1 min-w-0 mr-3">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertCircle size={14} className="text-orange-400 shrink-0" />
                    <span className="text-sm font-medium text-white truncate">
                      {notice.raw_text?.substring(0, 70)}...
                    </span>
                    <StatusBadge status={notice.status} />
                  </div>
                  <p className="text-xs text-slate-500">{new Date(notice.created_at).toLocaleDateString("en-IN")}</p>
                </div>
                {expanded === notice.id ? (
                  <ChevronUp size={16} className="text-slate-400 shrink-0" />
                ) : (
                  <ChevronDown size={16} className="text-slate-400 shrink-0" />
                )}
              </div>
              {expanded === notice.id && (
                <div className="px-4 pb-4 space-y-3 border-t border-border pt-3">
                  {notice.translated_hindi ? (
                    <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
                      <p className="text-xs text-yellow-300 font-medium mb-1">हिंदी में सारांश</p>
                      <p className="text-sm text-slate-200 leading-relaxed">{notice.translated_hindi}</p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">Not yet translated — paste text above to analyze</p>
                  )}
                  {notice.action_items?.length > 0 && (
                    <div>
                      <p className="text-xs text-slate-400 font-medium mb-2">Action Items:</p>
                      {notice.action_items.map((item: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-sm text-slate-300 mb-1.5">
                          <span className="w-5 h-5 rounded-full bg-brand/20 text-brand text-xs flex items-center justify-center shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          {item}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Calendar Tab ─────────────────────────────────────────────────────────────
function CalendarTab() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.complianceCalendar("27AAPFU0939F1ZV")
      .then(setData)
      .catch((e: any) => setError(e?.response?.data?.detail || e.message || "Failed to load calendar"))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <div className="w-6 h-6 border-2 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    );
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      {data.alerts?.map((alert: string, i: number) => (
        <div key={i} className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-3 flex items-start gap-2">
          <AlertCircle size={16} className="text-orange-400 shrink-0 mt-0.5" />
          <p className="text-sm text-orange-300">{alert}</p>
        </div>
      ))}

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "ITC Available", value: `₹${data.itc_available?.toLocaleString("en-IN")}`, color: "text-green-400" },
          { label: "ITC Utilized", value: `₹${data.itc_utilized?.toLocaleString("en-IN")}`, color: "text-blue-400" },
          { label: "ITC Balance", value: `₹${data.itc_balance?.toLocaleString("en-IN")}`, color: "text-brand" },
        ].map((s) => (
          <div key={s.label} className="bg-card rounded-xl border border-border p-4">
            <p className="text-xs text-slate-400 mb-1">{s.label}</p>
            <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-slate-500 mt-1">From real invoices</p>
          </div>
        ))}
      </div>

      <div className="bg-card rounded-xl border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <span className="text-sm font-semibold text-white">Filing Calendar — {data.current_period}</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-slate-400 text-xs">
              {["Period", "GSTR-1 Due", "GSTR-1", "GSTR-3B Due", "GSTR-3B", "Invoices"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.deadlines?.map((d: any, i: number) => (
              <tr key={i} className="border-b border-border/50 hover:bg-white/5">
                <td className="px-4 py-2.5 text-white font-medium">{d.month}</td>
                <td className="px-4 py-2.5 text-slate-300 font-mono text-xs">{d.gstr1_due}</td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={d.gstr1_status} />
                </td>
                <td className="px-4 py-2.5 text-slate-300 font-mono text-xs">{d.gstr3b_due}</td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={d.gstr3b_status} />
                </td>
                <td className="px-4 py-2.5 text-slate-400">{d.invoice_count ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Schemes Tab ──────────────────────────────────────────────────────────────
function SchemesTab() {
  const [schemes, setSchemes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [turnover, setTurnover] = useState("2850000");
  const [employees, setEmployees] = useState("12");

  const match = async () => {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await api.matchSchemes({ annual_turnover: Number(turnover), employee_count: Number(employees) });
      setSchemes(result.matched_schemes);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Scheme matching failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}
      <div className="bg-card rounded-xl border border-border p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Check MSME Scheme Eligibility</h3>
        <div className="flex gap-3 flex-wrap">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Annual Turnover (₹)</label>
            <input
              type="number"
              value={turnover}
              onChange={(e) => setTurnover(e.target.value)}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand/60 w-48"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Employees</label>
            <input
              type="number"
              value={employees}
              onChange={(e) => setEmployees(e.target.value)}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand/60 w-32"
            />
          </div>
          <div className="self-end">
            <button
              onClick={match}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-brand hover:bg-brand-dark text-white rounded-lg text-sm transition disabled:opacity-50"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Gift size={14} />}
              {loading ? "Searching..." : "Find Schemes"}
            </button>
          </div>
        </div>
      </div>

      {!searched && (
        <div className="bg-card rounded-xl border border-dashed border-border p-8 text-center text-slate-500 text-sm">
          Enter your turnover and employees above, then click Find Schemes
        </div>
      )}

      {searched && schemes.length === 0 && !loading && (
        <div className="bg-card rounded-xl border border-border p-8 text-center text-slate-500 text-sm">
          No matching schemes found for the given profile
        </div>
      )}

      {schemes.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {schemes.map((s, i) => (
            <div key={i} className="bg-card rounded-xl border border-brand/30 p-4 hover:border-brand/60 transition">
              <div className="flex items-start justify-between mb-2">
                <span className="text-sm font-semibold text-white">{s.name}</span>
                <span className="text-xs font-bold text-green-400 bg-green-500/20 px-2 py-0.5 rounded-full shrink-0 ml-2">
                  {s.match_score}%
                </span>
              </div>
              <p className="text-xs text-brand mb-2">{s.benefit}</p>
              <p className="text-xs text-slate-400 mb-3">{s.match_reason}</p>
              <a
                href={`https://${s.apply_url}`}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-brand hover:underline"
              >
                Apply → {s.apply_url}
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function GSTCompliancePage() {
  const [tab, setTab] = useState("invoices");

  const TABS = [
    { id: "invoices", label: "Invoices & GST", component: InvoicesTab },
    { id: "notices", label: "Notices", component: NoticesTab },
    { id: "calendar", label: "Filing Calendar", component: CalendarTab },
    { id: "schemes", label: "MSME Schemes", component: SchemesTab },
  ];

  const ActiveTab = TABS.find((t) => t.id === tab)?.component || InvoicesTab;

  return (
    <div className="flex flex-col h-full gap-4">
      <div>
        <h1 className="text-xl font-bold text-white">GST & Compliance</h1>
        <p className="text-sm text-slate-400">
          Invoice generation · Notice translation · Filing calendar · MSME schemes
        </p>
      </div>

      <div className="flex gap-1 bg-card rounded-xl border border-border p-1 flex-wrap">
        {TABS.map((t) => (
          <TabBtn key={t.id} active={tab === t.id} onClick={() => setTab(t.id)}>
            {t.label}
          </TabBtn>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <ActiveTab />
      </div>
    </div>
  );
}
