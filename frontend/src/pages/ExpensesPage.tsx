import { useState, useMemo, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Wallet, Plus, Download, CheckCircle, Clock, Trash2, IndianRupee, Lock, X
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, Cell
} from "recharts";
import {
  fetchExpenses, createExpense, markExpensePaid, deleteExpense, fetchMonthlyReport, fetchOrders
} from "@/services/vyapaarApi";
import { useAgentStore } from "@/stores/agentStore";

const CATEGORIES = [
  "RENT", "ELECTRICITY", "GST_TAX", "RAW_MATERIAL", "DELIVERY", "SALARY", "MISCELLANEOUS"
];

const COLORS = ['#1E3A5F', '#4A90E2', '#50E3C2', '#F5A623', '#D0021B', '#BD10E0', '#B8E986'];

export default function ExpensesPage() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });
  const [filter, setFilter] = useState<"All" | "Paid" | "Pending">("All");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: string } | null>(null);

  const showToast = (message: string, type: string = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const last6Months = Array.from({ length: 6 }).map((_, i) => {
    const d = new Date();
    d.setMonth(d.getMonth() - i);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });

  const { data: expenses = [] } = useQuery({
    queryKey: ["expenses", month],
    queryFn: () => fetchExpenses(month),
    refetchInterval: 10000,
  });

  const { data: report } = useQuery({
    queryKey: ["monthlyReport", month],
    queryFn: () => fetchMonthlyReport(month),
    refetchInterval: 10000,
  });

  const events = useAgentStore((state) => state.events);
  
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[0];
      if (latestEvent.type === "order_event") {
        queryClient.invalidateQueries({ queryKey: ["monthlyReport", month] });
      }
    }
  }, [events, month, queryClient]);

  const filteredExpenses = useMemo(() => {
    if (filter === "Paid") return expenses.filter((e: any) => e.is_paid);
    if (filter === "Pending") return expenses.filter((e: any) => !e.is_paid);
    return expenses;
  }, [expenses, filter]);

  const downloadReport = () => {
    window.open(`http://localhost:8000/api/reports/download?month=${month}&report_type=expenses`, "_blank");
  };

  const markPaidMutation = useMutation({
    mutationFn: (id: number) => markExpensePaid(id),
    onSuccess: () => {
      showToast("Expense marked as paid", "success");
      queryClient.invalidateQueries({ queryKey: ["expenses", month] });
      queryClient.invalidateQueries({ queryKey: ["monthlyReport", month] });
    },
    onError: () => showToast("Failed to mark expense paid", "error"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteExpense(id),
    onSuccess: () => {
      showToast("Expense deleted", "success");
      queryClient.invalidateQueries({ queryKey: ["expenses", month] });
      queryClient.invalidateQueries({ queryKey: ["monthlyReport", month] });
    },
    onError: () => showToast("Failed to delete expense", "error"),
  });

  const isClosed = report?.is_closed;

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Wallet size={24} className="text-indigo-500" />
            Expense Tracker
          </h1>
          <div className="flex items-center gap-2 bg-muted/30 px-3 py-1.5 rounded-lg border border-border">
            <select
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="bg-transparent border-none text-sm font-medium focus:ring-0 cursor-pointer"
            >
              {last6Months.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            {isClosed && <span title="Month is closed"><Lock size={14} className="text-red-500" /></span>}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={downloadReport}
            className="btn-secondary flex items-center gap-2 text-sm px-4 py-2"
          >
            <Download size={16} />
            Download Report (XLSX)
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            disabled={isClosed}
            title={isClosed ? "This month is closed. Contact admin to reopen." : ""}
            className="btn-primary flex items-center gap-2 text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus size={16} />
            Add Expense
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-green-500">
          <div className="text-muted-foreground text-sm font-medium mb-1">Total Orders Revenue</div>
          <div className="text-3xl font-bold text-foreground">
            ₹{report?.orders_total?.toLocaleString() ?? "0"}
          </div>
        </div>
        <div className="glass-card p-6 border-l-4 border-l-red-500">
          <div className="text-muted-foreground text-sm font-medium mb-1">Total Expenses</div>
          <div className="text-3xl font-bold text-foreground">
            ₹{report?.expenses_total?.toLocaleString() ?? "0"}
          </div>
        </div>
        <div className={`glass-card p-6 border-l-4 ${report?.net_position >= 0 ? 'border-l-green-500' : 'border-l-red-500'}`}>
          <div className="text-muted-foreground text-sm font-medium mb-1">Net Position</div>
          <div className={`text-3xl font-bold ${report?.net_position >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            ₹{report?.net_position?.toLocaleString() ?? "0"}
          </div>
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold mb-6 text-foreground">Category Breakdown</h2>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={report?.category_breakdown || []} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <XAxis type="number" tickFormatter={(v) => `₹${v}`} stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis dataKey="category" type="category" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} width={120} />
              <RechartsTooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '8px', border: 'none', backgroundColor: '#1E293B', color: '#fff' }} />
              <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                {(report?.category_breakdown || []).map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <h2 className="text-lg font-semibold text-foreground">Expenses</h2>
          <div className="flex bg-muted/50 p-1 rounded-lg">
            {["All", "Paid", "Pending"].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f as any)}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  filter === f ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border/50 bg-muted/20">
                <th className="p-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Category</th>
                <th className="p-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Description</th>
                <th className="p-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Vendor</th>
                <th className="p-4 text-xs font-medium text-muted-foreground uppercase tracking-wider text-right">Amount</th>
                <th className="p-4 text-xs font-medium text-muted-foreground uppercase tracking-wider text-center">Due Date</th>
                <th className="p-4 text-xs font-medium text-muted-foreground uppercase tracking-wider text-center">Status</th>
                <th className="p-4 text-xs font-medium text-muted-foreground uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredExpenses.map((exp: any) => (
                <tr key={exp.id} className="border-b border-border/50 hover:bg-muted/10 transition-colors">
                  <td className="p-4">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-500">
                      {exp.category}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-foreground">{exp.description}</td>
                  <td className="p-4 text-sm text-muted-foreground">{exp.vendor_name || "-"}</td>
                  <td className="p-4 text-sm font-medium text-foreground text-right">₹{exp.amount.toLocaleString()}</td>
                  <td className="p-4 text-sm text-muted-foreground text-center">{exp.due_date || "-"}</td>
                  <td className="p-4 text-center">
                    {exp.is_paid ? (
                      <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-500">
                        <CheckCircle size={14} /> Paid
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-500">
                        <Clock size={14} /> Pending
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {!exp.is_paid && (
                        <button
                          onClick={() => markPaidMutation.mutate(exp.id)}
                          disabled={isClosed || markPaidMutation.isPending}
                          title={isClosed ? "This month is closed" : "Mark Paid"}
                          className="p-2 text-green-500 hover:bg-green-500/10 rounded-lg transition-colors disabled:opacity-50"
                        >
                          <CheckCircle size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => deleteMutation.mutate(exp.id)}
                        disabled={isClosed || deleteMutation.isPending}
                        title={isClosed ? "This month is closed" : "Delete Expense"}
                        className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredExpenses.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-muted-foreground">
                    No expenses found for this month.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <AddExpenseModal
          month={month}
          onClose={() => setIsModalOpen(false)}
          showToast={showToast}
          onSuccess={() => {
            setIsModalOpen(false);
            queryClient.invalidateQueries({ queryKey: ["expenses", month] });
            queryClient.invalidateQueries({ queryKey: ["monthlyReport", month] });
          }}
        />
      )}
      {toast && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: toast.type === "success" ? "#0A1F14" : "#1A0A0A",
            border: `1px solid ${toast.type === "success" ? "#065F46" : "#7F1D1D"}`,
            color: toast.type === "success" ? "#10B981" : "#EF4444",
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

function AddExpenseModal({ month, onClose, onSuccess, showToast }: any) {
  const [formData, setFormData] = useState({
    category: CATEGORIES[0],
    description: "",
    vendor_name: "",
    amount: "",
    due_date: "",
    linked_order_id: "",
    receipt_ref: ""
  });

  const { data: ordersData } = useQuery({
    queryKey: ["orders", month],
    queryFn: () => fetchOrders({ month, limit: 100 })
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => createExpense(data),
    onSuccess: () => {
      showToast("Expense added successfully", "success");
      onSuccess();
    },
    onError: () => showToast("Failed to add expense", "error")
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      ...formData,
      amount: parseFloat(formData.amount),
      linked_order_id: formData.linked_order_id ? parseInt(formData.linked_order_id) : undefined
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-background border border-border rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Plus size={18} className="text-indigo-500" />
            Add New Expense
          </h2>
          <button onClick={onClose} className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">Category *</label>
              <select
                required
                value={formData.category}
                onChange={e => setFormData({ ...formData, category: e.target.value })}
                className="input-base w-full"
              >
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">Amount (₹) *</label>
              <input
                required
                type="number"
                min="0"
                step="0.01"
                value={formData.amount}
                onChange={e => setFormData({ ...formData, amount: e.target.value })}
                className="input-base w-full"
                placeholder="0.00"
              />
            </div>
          </div>
          
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-muted-foreground">Description *</label>
            <input
              required
              type="text"
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              className="input-base w-full"
              placeholder="e.g. Office supplies for June"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">Vendor Name</label>
              <input
                type="text"
                value={formData.vendor_name}
                onChange={e => setFormData({ ...formData, vendor_name: e.target.value })}
                className="input-base w-full"
                placeholder="Vendor Name"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">Due Date</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={e => setFormData({ ...formData, due_date: e.target.value })}
                className="input-base w-full"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">Link Order (Optional)</label>
              <select
                value={formData.linked_order_id}
                onChange={e => setFormData({ ...formData, linked_order_id: e.target.value })}
                className="input-base w-full"
              >
                <option value="">-- None --</option>
                {ordersData?.orders?.map((o: any) => (
                  <option key={o.id} value={o.id}>
                    #{o.id} - {o.customer}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">Receipt Ref</label>
              <input
                type="text"
                value={formData.receipt_ref}
                onChange={e => setFormData({ ...formData, receipt_ref: e.target.value })}
                className="input-base w-full"
                placeholder="e.g. INV-1234"
              />
            </div>
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary px-4 py-2 text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn-primary px-6 py-2 text-sm flex items-center gap-2"
            >
              {createMutation.isPending ? "Adding..." : "Add Expense"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
