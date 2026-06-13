import React, { useState, useEffect, useCallback } from 'react'
import { TrendingUp, AlertTriangle, CheckCircle2, Clock, IndianRupee, Users, RefreshCw, Zap } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import AgentMatrix from '../components/AgentMatrix'
import { api } from '../hooks/useApi'
import { clsx } from 'clsx'

function MetricCard({ label, value, sub, icon: Icon, color, loading }) {
  return (
    <div className="bg-card rounded-xl border border-border p-4 flex items-start gap-3">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${color}`}>
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-400 truncate">{label}</p>
        {loading ? (
          <div className="h-7 w-24 bg-slate-700 rounded animate-pulse mt-0.5" />
        ) : (
          <p className="text-xl font-bold text-white mt-0.5">{value}</p>
        )}
        {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-card border border-border rounded-lg p-3 text-xs">
      <p className="font-semibold text-white mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name === 'in' ? '↑ Income' : '↓ Expense'}: ₹{p.value?.toLocaleString('en-IN')}
        </p>
      ))}
    </div>
  )
}

const fmt = (n) => n >= 100000 ? `₹${(n / 100000).toFixed(2)}L` : `₹${n?.toLocaleString('en-IN')}`

export default function CommandCentre() {
  const [metrics, setMetrics] = useState(null)
  const [cashflow, setCashflow] = useState([])
  const [alerts, setAlerts] = useState([])
  const [hitlQueue, setHitlQueue] = useState([])
  const [intakeQueue, setIntakeQueue] = useState([])
  const [metricsLoading, setMetricsLoading] = useState(true)
  const [cashflowLoading, setCashflowLoading] = useState(true)
  const [deciding, setDeciding] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const load = useCallback(async () => {
    setMetricsLoading(true)
    setCashflowLoading(true)
    try {
      const [m, cf, al, hitl, intake] = await Promise.all([
        api.dashboardMetrics(),
        api.dashboardCashflow(),
        api.dashboardAlerts(),
        api.hitlQueue(),
        api.intakeHitlQueue(),
      ])
      setMetrics(m)
      setCashflow(cf)
      setAlerts(al)
      setHitlQueue(hitl)
      setIntakeQueue(intake.filter(i => i.status === 'PENDING'))
      setLastRefresh(new Date())
    } catch (e) {
      console.error('Dashboard load error:', e)
    } finally {
      setMetricsLoading(false)
      setCashflowLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const decideGst = async (id, action) => {
    setDeciding(id)
    try {
      await api.hitlDecide(id, action, null)
      setHitlQueue(prev => prev.filter(i => i.id !== id))
    } finally { setDeciding(null) }
  }

  const decideIntake = async (id, approved) => {
    setDeciding(`intake_${id}`)
    try {
      await api.reviewIntakeHitl(id, approved, {}, '')
      setIntakeQueue(prev => prev.filter(i => i.id !== id))
    } finally { setDeciding(null) }
  }

  const totalPending = hitlQueue.length + intakeQueue.length

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Command Centre</h1>
          <p className="text-sm text-slate-400">
            Real-time business overview
            {lastRefresh && <span className="ml-2 text-slate-600">· refreshed {lastRefresh.toLocaleTimeString('en-IN')}</span>}
          </p>
        </div>
        <button onClick={load} disabled={metricsLoading}
          className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg text-sm text-slate-400 hover:text-white transition disabled:opacity-50">
          <RefreshCw size={14} className={metricsLoading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Live alerts from DB */}
      {alerts.map((alert, i) => (
        <div key={i} className={clsx('rounded-xl p-3 flex items-center gap-3 border',
          alert.severity === 'high' ? 'bg-red-500/10 border-red-500/30' :
          alert.severity === 'medium' ? 'bg-orange-500/10 border-orange-500/30' :
          'bg-yellow-500/10 border-yellow-500/30')}>
          <AlertTriangle size={16} className={
            alert.severity === 'high' ? 'text-red-400' :
            alert.severity === 'medium' ? 'text-orange-400' : 'text-yellow-400'} />
          <p className={`text-sm ${
            alert.severity === 'high' ? 'text-red-300' :
            alert.severity === 'medium' ? 'text-orange-300' : 'text-yellow-300'}`}>
            {alert.message}
          </p>
        </div>
      ))}

      {/* KPI grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard loading={metricsLoading} label="Weekly Revenue" icon={TrendingUp} color="bg-green-500/20 text-green-400"
          value={metrics ? fmt(metrics.weekly_revenue) : '—'}
          sub={metrics ? `${metrics.total_invoices} total invoices` : ''} />
        <MetricCard loading={metricsLoading} label="Outstanding" icon={IndianRupee} color="bg-orange-500/20 text-orange-400"
          value={metrics ? fmt(metrics.outstanding) : '—'}
          sub={metrics ? `${metrics.overdue_count} overdue` : ''} />
        <MetricCard loading={metricsLoading} label="Recovered (Week)" icon={CheckCircle2} color="bg-blue-500/20 text-blue-400"
          value={metrics ? fmt(metrics.recovered_this_week) : '—'}
          sub="paid this week" />
        <MetricCard loading={metricsLoading} label="Pending Approvals" icon={Clock} color="bg-purple-500/20 text-purple-400"
          value={metrics ? String(metrics.pending_approvals) : '—'}
          sub={`${hitlQueue.length} GST · ${intakeQueue.length} orders`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Cash flow chart */}
        <div className="bg-card rounded-xl border border-border p-4">
          <p className="text-sm font-semibold text-white mb-4">Cash Flow — Last 6 Months</p>
          {cashflowLoading ? (
            <div className="h-48 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-brand border-t-transparent rounded-full animate-spin" />
            </div>
          ) : cashflow.every(m => m.in === 0) ? (
            <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
              No invoice data for this period
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={cashflow} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false}
                  tickFormatter={v => v >= 100000 ? `₹${(v/100000).toFixed(0)}L` : `₹${(v/1000).toFixed(0)}K`} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.05)' }} />
                <Bar dataKey="in" fill="#6366f1" radius={[4,4,0,0]} name="in" />
                <Bar dataKey="out" fill="#f43f5e" radius={[4,4,0,0]} name="out" />
              </BarChart>
            </ResponsiveContainer>
          )}
          <div className="flex gap-4 mt-2 text-xs text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-brand" /> Income</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-rose-500" /> Est. Expenses</span>
          </div>
        </div>

        {/* Agent matrix */}
        <div className="bg-card rounded-xl border border-border p-4">
          <p className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Zap size={14} className="text-brand" /> Agent Matrix
          </p>
          <AgentMatrix />
        </div>
      </div>

      {/* GST HITL queue */}
      {hitlQueue.length > 0 && (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <span className="text-sm font-semibold text-white">GST Approval Queue ({hitlQueue.length})</span>
          </div>
          <div className="divide-y divide-border">
            {hitlQueue.map(item => (
              <div key={item.id} className="p-4 flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white capitalize">{item.action_type?.replace('_', ' ')}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {item.payload?.invoice_number && `Invoice ${item.payload.invoice_number} · `}
                    {item.payload?.buyer?.name || item.payload?.buyer_name || ''}
                    {(item.payload?.grand_total || item.payload?.total) &&
                      ` · ₹${(item.payload?.grand_total || item.payload?.total)?.toLocaleString('en-IN')}`}
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => decideGst(item.id, 'reject')} disabled={deciding === item.id}
                    className="px-3 py-1.5 bg-red-500/20 border border-red-500/40 text-red-400 rounded-lg text-xs hover:bg-red-500/30 transition disabled:opacity-50">
                    Reject
                  </button>
                  <button onClick={() => decideGst(item.id, 'approve')} disabled={deciding === item.id}
                    className="flex items-center gap-1 px-3 py-1.5 bg-green-500/20 border border-green-500/40 text-green-400 rounded-lg text-xs hover:bg-green-500/30 transition disabled:opacity-50">
                    <CheckCircle2 size={12} /> Approve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Order / Intake HITL queue */}
      {intakeQueue.length > 0 && (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <span className="text-sm font-semibold text-white">Order Approval Queue ({intakeQueue.length})</span>
          </div>
          <div className="divide-y divide-border">
            {intakeQueue.map(item => (
              <div key={item.id} className="p-4 flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white">Order #{item.order_id}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{item.reason}</p>
                  {item.payload?.clarification?.data?.clarification_question && (
                    <p className="text-xs text-yellow-400 mt-1">
                      ⚠ {item.payload.clarification.data.clarification_question}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => decideIntake(item.id, false)} disabled={deciding === `intake_${item.id}`}
                    className="px-3 py-1.5 bg-red-500/20 border border-red-500/40 text-red-400 rounded-lg text-xs hover:bg-red-500/30 transition disabled:opacity-50">
                    Reject
                  </button>
                  <button onClick={() => decideIntake(item.id, true)} disabled={deciding === `intake_${item.id}`}
                    className="flex items-center gap-1 px-3 py-1.5 bg-green-500/20 border border-green-500/40 text-green-400 rounded-lg text-xs hover:bg-green-500/30 transition disabled:opacity-50">
                    <CheckCircle2 size={12} /> Approve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {totalPending === 0 && !metricsLoading && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 flex items-center gap-2">
          <CheckCircle2 size={14} className="text-green-400" />
          <p className="text-sm text-green-400">No pending approvals — all caught up!</p>
        </div>
      )}
    </div>
  )
}
