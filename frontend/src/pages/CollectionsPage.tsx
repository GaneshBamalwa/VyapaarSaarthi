import { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import * as api from "@/services/vyapaarApi";
import { cn } from "@/lib/utils";

// ─── INR formatter ────────────────────────────────────────────────────────────

function formatINR(amount: number): string {
  const num = Math.round(amount);
  const s = String(num);
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  const rest = s.slice(0, -3);
  const formatted = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return formatted + "," + last3;
}

// ─── Relative time helper ─────────────────────────────────────────────────────

function relativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 60) return minutes <= 1 ? "just now" : `${minutes} minutes ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
  });
}

// ─── Status badge ─────────────────────────────────────────────────────────────

const RISK_BADGE: Record<string, string> = {
  low: "bg-[#0A1F14] text-[#10B981] border border-[#065F46]",
  medium: "bg-[#1C1407] text-[#F59E0B] border border-[#78350F]",
  high: "bg-[#1A0A0A] text-[#EF4444] border border-[#7F1D1D]",
};

const REMINDER_STATUS_BADGE: Record<string, string> = {
  sent: "bg-[#0A1F14] text-[#10B981] border border-[#065F46]",
  approved: "bg-[#0A1F14] text-[#10B981] border border-[#065F46]",
  failed: "bg-[#1A0A0A] text-[#EF4444] border border-[#7F1D1D]",
  rejected: "bg-[#1A0A0A] text-[#EF4444] border border-[#7F1D1D]",
  pending_hitl: "bg-[#1C1407] text-[#F59E0B] border border-[#78350F]",
};

const REMINDER_STATUS_LABEL: Record<string, string> = {
  sent: "Sent",
  approved: "Approved",
  failed: "Failed",
  rejected: "Rejected",
  pending_hitl: "Awaiting approval",
};

// ─── Badge component ──────────────────────────────────────────────────────────

function Badge({ label, className }: { label: string; className: string }) {
  return (
    <span
      className={cn(
        "px-[8px] py-[3px] rounded-[4px] text-[11px] font-medium tracking-[0.05em]",
        className
      )}
    >
      {label}
    </span>
  );
}

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  accentColor,
}: {
  label: string;
  value: string | number;
  accentColor?: string;
}) {
  return (
    <div
      className="kpi-card p-4"
      style={accentColor ? { borderLeft: `2px solid ${accentColor}` } : undefined}
    >
      <p className="text-[12px] text-[#A1A1AA] mb-1">{label}</p>
      <p className="text-[22px] font-semibold text-[#E4E4E7]">{value}</p>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

const TABS = ["Overdue", "Buyer Risk", "History"] as const;
type Tab = (typeof TABS)[number];

export function CollectionsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Overdue");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [historyOffset, setHistoryOffset] = useState(0);
  const [historyRows, setHistoryRows] = useState<any[]>([]);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  // Row states for inline phone input
  const [rowStates, setRowStates] = useState<
    Record<number, { phoneInput: string; showPhoneInput: boolean; loading: boolean }>
  >({});

  const getRowState = (invoiceId: number) =>
    rowStates[invoiceId] || { phoneInput: "", showPhoneInput: false, loading: false };

  const setRowState = (invoiceId: number, updates: Partial<ReturnType<typeof getRowState>>) => {
    setRowStates((prev) => ({
      ...prev,
      [invoiceId]: { ...getRowState(invoiceId), ...updates },
    }));
  };

  // Toast
  const [toast, setToast] = useState<{ message: string; type: string } | null>(null);
  const showToast = (message: string, type: string = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  // Stats
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ["collections-stats"],
    queryFn: () => api.fetchCollectionsStats(),
    refetchInterval: 30_000,
  });

  // Overdue
  const { data: overdueData, isLoading: overdueLoading, refetch: refetchOverdue } = useQuery({
    queryKey: ["collections-overdue"],
    queryFn: () => api.fetchCollectionsOverdue(),
    enabled: activeTab === "Overdue",
  });

  // Risk scores
  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ["collections-risk"],
    queryFn: () => api.fetchCollectionsRiskScores(),
    enabled: activeTab === "Buyer Risk",
  });

  // History (lazy load)
  const loadHistory = useCallback(
    async (offset: number, replace = false) => {
      const rows = await api.fetchCollectionsHistory({ limit: 50, offset });
      setHistoryRows((prev) => (replace ? rows : [...prev, ...rows]));
      setHistoryOffset(offset + 50);
    },
    []
  );

  useEffect(() => {
    if (activeTab === "History" && historyRows.length === 0) {
      loadHistory(0, true);
    }
  }, [activeTab]);

  // Send manual reminder
  const handleSendReminder = async (row: any) => {
    setRowState(row.invoice_id, { loading: true });
    try {
      const result = await api.sendCollectionsReminder({ invoice_id: row.invoice_id });
      if (result.status === "sent") {
        showToast(`Reminder sent to ${row.buyer_name}`, "success");
      } else if (result.status === "pending_hitl") {
        showToast(`Queued for approval — high risk buyer`, "warning");
      } else {
        showToast(`Failed: ${result.whatsapp_sid || "unknown error"}`, "error");
      }
    } catch {
      showToast("Failed to send reminder. Check server logs.", "error");
    } finally {
      setRowState(row.invoice_id, { loading: false });
    }
  };

  const handleMarkPaid = async (invoice_id: number) => {
    try {
      setRowState(invoice_id, { loading: true });
      await api.markPaymentPaid(invoice_id);
      showToast("Order marked as paid", "success");
      refetchOverdue();
      refetchStats();
    } catch (err) {
      showToast("Failed to mark as paid", "error");
      setRowState(invoice_id, { loading: false });
    }
  };

  const handleSaveAndSend = async (row: any) => {
    const phone = getRowState(row.invoice_id).phoneInput.trim();
    if (!phone) return;

    setRowState(row.invoice_id, { loading: true });
    try {
      // Step 1: Save phone number
      await api.saveBuyerPhone({ buyer_name: row.buyer_name, phone: phone });

      // Step 2: Send reminder
      const sendData = await api.sendCollectionsReminder({ invoice_id: row.invoice_id });

      if (sendData.status === "sent") {
        showToast(`Reminder sent to ${row.buyer_name}`, "success");
        setRowState(row.invoice_id, { showPhoneInput: false, phoneInput: "", loading: false });
        refetchOverdue();
      } else if (sendData.status === "pending_hitl") {
        showToast("Queued for approval — high risk buyer", "warning");
        setRowState(row.invoice_id, { showPhoneInput: false, phoneInput: "", loading: false });
        refetchOverdue();
      } else {
        showToast("Number saved but reminder failed to send", "error");
        setRowState(row.invoice_id, { loading: false });
        refetchOverdue();
      }
    } catch (err) {
      showToast("Something went wrong", "error");
      setRowState(row.invoice_id, { loading: false });
    }
  };

  const filteredRisk =
    riskFilter === "all"
      ? (riskData ?? [])
      : (riskData ?? []).filter((r: any) => r.risk_tier === riskFilter);

  return (
    <div className="flex flex-col h-full gap-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-[#E4E4E7]">Collections</h1>
        <p className="text-sm text-[#A1A1AA]">
          Autonomous payment follow-ups and buyer risk monitoring
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Overdue invoices"
          value={statsLoading ? "—" : stats?.total_overdue_invoices ?? 0}
        />
        <StatCard
          label="Amount outstanding"
          value={
            statsLoading
              ? "—"
              : `₹${formatINR(stats?.total_overdue_amount ?? 0)}`
          }
        />
        <StatCard
          label="High risk buyers"
          value={statsLoading ? "—" : stats?.high_risk_buyers ?? 0}
          accentColor="#EF4444"
        />
        <StatCard
          label="Awaiting approval"
          value={statsLoading ? "—" : stats?.reminders_pending_hitl ?? 0}
          accentColor="#F59E0B"
        />
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-[#27272A] pb-0">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-[1px] transition-colors",
              activeTab === tab
                ? "border-[#6366F1] text-[#E4E4E7]"
                : "border-transparent text-[#71717A] hover:text-[#A1A1AA]"
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab: Overdue */}
      {activeTab === "Overdue" && (
        <div className="flex-1 overflow-auto">
          {overdueLoading ? (
            <p className="text-[#A1A1AA] text-sm">Loading...</p>
          ) : !overdueData || overdueData.length === 0 ? (
            <p className="text-[#52525B] text-sm text-center py-16">
              No overdue invoices. All caught up.
            </p>
          ) : (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-left text-[11px] text-[#52525B] uppercase tracking-[0.08em]">
                  <th className="pb-3 pr-6">Order #</th>
                  <th className="pb-3 pr-6">Buyer</th>
                  <th className="pb-3 pr-6">Amount Due</th>
                  <th className="pb-3 pr-6">Days Overdue</th>
                  <th className="pb-3 pr-6">Risk</th>
                  <th className="pb-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272A]">
                {overdueData.map((inv: any) => (
                  <tr key={inv.invoice_id} className="hover:bg-[#18181B] transition-colors">
                    <td className="py-3 pr-6 font-mono text-[11px] text-[#71717A]">
                      Order #{inv.invoice_id}
                    </td>
                    <td className="py-3 pr-6 text-[#E4E4E7]">{inv.buyer_name}</td>
                    <td className="py-3 pr-6 font-medium text-[#E4E4E7]">
                      ₹{formatINR(inv.amount_due)}
                    </td>
                    <td className="py-3 pr-6">
                      <span
                        className={cn(
                          "font-medium",
                          inv.days_overdue > 7
                            ? "text-[#EF4444]"
                            : "text-[#F59E0B]"
                        )}
                      >
                        {inv.days_overdue} days
                      </span>
                    </td>
                    <td className="py-3 pr-6">
                      {inv.risk_tier ? (
                        <Badge
                          label={inv.risk_tier}
                          className={RISK_BADGE[inv.risk_tier] ?? RISK_BADGE.low}
                        />
                      ) : (
                        <span className="text-[#3F3F46] text-[11px]">—</span>
                      )}
                    </td>
                    <td className="py-3">
                      {inv.has_phone ? (
                        <div className="flex items-center gap-2">
                          <button
                            disabled={getRowState(inv.invoice_id).loading}
                            onClick={() => handleSendReminder(inv)}
                            className="px-3 py-1 text-xs border border-[#27272A] text-[#A1A1AA] rounded-[4px] hover:bg-[#18181B] hover:text-[#E4E4E7] transition disabled:opacity-40"
                          >
                            {getRowState(inv.invoice_id).loading ? "Sending..." : "Send reminder"}
                          </button>
                          <button
                            disabled={getRowState(inv.invoice_id).loading}
                            onClick={() => handleMarkPaid(inv.invoice_id)}
                            className="px-3 py-1 text-xs border border-[#064E3B] text-[#10B981] rounded-[4px] hover:bg-[#064E3B] transition disabled:opacity-40"
                            title="Mark as paid"
                          >
                            Paid
                          </button>
                        </div>
                      ) : getRowState(inv.invoice_id).showPhoneInput ? (
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <input
                            type="tel"
                            placeholder="+91 98765 43210"
                            value={getRowState(inv.invoice_id).phoneInput}
                            onChange={(e) =>
                              setRowState(inv.invoice_id, { phoneInput: e.target.value })
                            }
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleSaveAndSend(inv);
                              if (e.key === "Escape")
                                setRowState(inv.invoice_id, { showPhoneInput: false, phoneInput: "" });
                            }}
                            autoFocus
                            style={{
                              background: "#0D0D0F",
                              border: "1px solid #4338CA",
                              borderRadius: "5px",
                              padding: "5px 10px",
                              color: "#E4E4E7",
                              fontSize: "13px",
                              width: "160px",
                              outline: "none",
                            }}
                          />
                          <button
                            style={{
                              background: "#6366F1",
                              color: "#fff",
                              border: "none",
                              borderRadius: "5px",
                              padding: "5px 12px",
                              fontSize: "12px",
                              fontWeight: 500,
                              cursor: "pointer",
                            }}
                            disabled={
                              getRowState(inv.invoice_id).loading ||
                              !getRowState(inv.invoice_id).phoneInput.trim()
                            }
                            onClick={() => handleSaveAndSend(inv)}
                          >
                            {getRowState(inv.invoice_id).loading ? "..." : "Send"}
                          </button>
                          <button
                            onClick={() =>
                              setRowState(inv.invoice_id, { showPhoneInput: false, phoneInput: "" })
                            }
                            style={{
                              background: "transparent",
                              border: "none",
                              color: "#52525B",
                              cursor: "pointer",
                              fontSize: "16px",
                              padding: "0 4px",
                            }}
                          >
                            ×
                          </button>
                        </div>
                      ) : (
                        <button
                          style={{
                            background: "transparent",
                            border: "1px solid #27272A",
                            borderRadius: "5px",
                            padding: "5px 12px",
                            color: "#71717A",
                            fontSize: "12px",
                            cursor: "pointer",
                          }}
                          onClick={() => setRowState(inv.invoice_id, { showPhoneInput: true })}
                        >
                          Add number to send
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab: Buyer Risk */}
      {activeTab === "Buyer Risk" && (
        <div className="flex-1 flex flex-col gap-4 overflow-auto">
          {/* Filter row */}
          <div className="flex gap-2">
            {["all", "low", "medium", "high"].map((f) => (
              <button
                key={f}
                onClick={() => setRiskFilter(f)}
                className={cn(
                  "px-3 py-1 text-xs rounded-[4px] border transition-colors capitalize",
                  riskFilter === f
                    ? "bg-[#1E1B4B] border-[#4338CA] text-[#818CF8]"
                    : "bg-transparent border-[#27272A] text-[#71717A] hover:text-[#A1A1AA] hover:bg-[#18181B]"
                )}
              >
                {f === "all" ? "All" : f}
              </button>
            ))}
          </div>

          {riskLoading ? (
            <p className="text-[#A1A1AA] text-sm">Loading...</p>
          ) : !filteredRisk || filteredRisk.length === 0 ? (
            <p className="text-[#52525B] text-sm text-center py-16">
              No risk profiles yet. Run the daily job to populate.
            </p>
          ) : (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-left text-[11px] text-[#52525B] uppercase tracking-[0.08em]">
                  <th className="pb-3 pr-6">Buyer</th>
                  <th className="pb-3 pr-6">Risk Tier</th>
                  <th className="pb-3 pr-6">Avg Delay</th>
                  <th className="pb-3 pr-6">Overdue Ratio</th>
                  <th className="pb-3 pr-6">Payments Tracked</th>
                  <th className="pb-3">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272A]">
                {filteredRisk.map((r: any) => (
                  <tr key={r.buyer_name} className="hover:bg-[#18181B] transition-colors">
                    <td className="py-3 pr-6 text-[#E4E4E7]">{r.buyer_name}</td>
                    <td className="py-3 pr-6">
                      <Badge
                        label={r.risk_tier}
                        className={RISK_BADGE[r.risk_tier] ?? RISK_BADGE.low}
                      />
                    </td>
                    <td className="py-3 pr-6 text-[#A1A1AA]">
                      {r.avg_delay_days.toFixed(1)} days
                    </td>
                    <td className="py-3 pr-6 text-[#A1A1AA]">
                      {Math.round(r.overdue_ratio * 100)}%
                    </td>
                    <td className="py-3 pr-6 text-[#A1A1AA]">{r.payment_count}</td>
                    <td className="py-3 text-[#52525B] text-xs">
                      {relativeTime(r.last_updated)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab: History */}
      {activeTab === "History" && (
        <div className="flex-1 flex flex-col gap-4 overflow-auto">
          {historyRows.length === 0 ? (
            <p className="text-[#A1A1AA] text-sm">Loading...</p>
          ) : (
            <>
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="text-left text-[11px] text-[#52525B] uppercase tracking-[0.08em]">
                    <th className="pb-3 pr-4">Date / Time</th>
                    <th className="pb-3 pr-4">Buyer</th>
                    <th className="pb-3 pr-4">Amount</th>
                    <th className="pb-3 pr-4">Level</th>
                    <th className="pb-3 pr-4">Status</th>
                    <th className="pb-3">Message</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#27272A]">
                  {historyRows.map((r: any) => (
                    <>
                      <tr
                        key={r.id}
                        onClick={() =>
                          setExpandedRow((prev) => (prev === r.id ? null : r.id))
                        }
                        className="cursor-pointer hover:bg-[#18181B] transition-colors"
                      >
                        <td className="py-3 pr-4 text-[#71717A] text-xs font-mono whitespace-nowrap">
                          {new Date(r.sent_at).toLocaleString("en-IN", {
                            day: "2-digit",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </td>
                        <td className="py-3 pr-4 text-[#E4E4E7]">{r.buyer_name}</td>
                        <td className="py-3 pr-4 font-medium text-[#E4E4E7]">
                          ₹{formatINR(r.amount_due)}
                        </td>
                        <td className="py-3 pr-4">
                          <span
                            className={
                              r.level === 2
                                ? "text-[11px] text-[#F59E0B]"
                                : "text-[11px] text-[#52525B]"
                            }
                          >
                            Level {r.level}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <Badge
                            label={REMINDER_STATUS_LABEL[r.status] ?? r.status}
                            className={
                              REMINDER_STATUS_BADGE[r.status] ??
                              "bg-muted text-[#A1A1AA] border border-[#27272A]"
                            }
                          />
                        </td>
                        <td className="py-3 text-[#71717A] max-w-[240px] truncate">
                          {(r.message_text ?? "").slice(0, 60)}
                          {(r.message_text ?? "").length > 60 ? "..." : ""}
                        </td>
                      </tr>
                      {expandedRow === r.id && (
                        <tr>
                          <td colSpan={6} className="py-0">
                            <pre className="font-mono text-xs text-[#A1A1AA] p-[12px] bg-[#111113] border border-[#27272A] rounded-[4px] whitespace-pre-wrap mb-2">
                              {r.message_text}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
              <button
                onClick={() => loadHistory(historyOffset)}
                className="self-start px-4 py-2 text-xs border border-[#27272A] text-[#71717A] rounded-[5px] hover:bg-[#18181B] hover:text-[#A1A1AA] transition"
              >
                Load more
              </button>
            </>
          )}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background:
              toast.type === "success"
                ? "#0A1F14"
                : toast.type === "warning"
                ? "#1C1407"
                : "#1A0A0A",
            border: `1px solid ${
              toast.type === "success"
                ? "#065F46"
                : toast.type === "warning"
                ? "#78350F"
                : "#7F1D1D"
            }`,
            color:
              toast.type === "success"
                ? "#10B981"
                : toast.type === "warning"
                ? "#F59E0B"
                : "#EF4444",
            padding: "12px 20px",
            borderRadius: "6px",
            fontSize: "13px",
            fontWeight: 500,
            zIndex: 1000,
            maxWidth: "320px",
          }}
        >
          {toast.message}
        </div>
      )}
    </div>
  );
}
