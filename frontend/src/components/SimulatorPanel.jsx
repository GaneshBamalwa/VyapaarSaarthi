import React, { useState } from 'react'
import { ChevronRight, ChevronLeft, Play, Loader2 } from 'lucide-react'
import { api } from '../hooks/useApi'

const SCENARIOS = [
  {
    label: '📦 Incoming Order',
    desc: 'Fire a WhatsApp-style Hinglish order',
    action: () => api.chat('Ramesh bhai ko bol do 100 kilo steel rod chahiye kal tak, rate 85 rupaye kilo', 'simulator'),
  },
  {
    label: '⚠️ GST Notice',
    desc: 'Simulate a DRC-01 penalty notice',
    action: () => api.translateNotice('DRC-01 Notice: Tax demand of Rs. 45,000 along with interest of Rs. 8,100 and penalty of Rs. 4,500 raised for FY 2023-24 Q3. Payment due within 30 days.'),
  },
  {
    label: '💸 Collection Run',
    desc: 'Trigger 9 AM overdue invoice check',
    action: () => api.chat('Collections check karo — kaun kaun ka payment overdue hai?', 'simulator'),
  },
  {
    label: '🏛️ Scheme Match',
    desc: 'Match business to MSME schemes',
    action: () => api.matchSchemes({ annual_turnover: 2850000, employee_count: 12 }),
  },
  {
    label: '🧾 Generate Invoice',
    desc: 'Draft GST invoice for Kaveri Steel',
    action: () => api.generateInvoice({
      order_id: 99,
      buyer_name: 'Kaveri Steel Works',
      buyer_state: 'Tamil Nadu',
      buyer_gstin: '33AABCS1429B1Z0',
      line_items: [{ name: 'Steel Rods', qty: 200, unit: 'kg', rate: 82 }],
    }),
  },
  {
    label: '📻 Weekly Briefing',
    desc: 'Generate Hindi audio briefing',
    action: () => api.weeklyBriefing(),
  },
]

export default function SimulatorPanel() {
  const [open, setOpen] = useState(false)
  const [running, setRunning] = useState(null)
  const [results, setResults] = useState({})

  const run = async (scenario, idx) => {
    setRunning(idx)
    try {
      const result = await scenario.action()
      setResults(prev => ({ ...prev, [idx]: { ok: true, data: JSON.stringify(result).slice(0, 120) + '...' } }))
    } catch (e) {
      setResults(prev => ({ ...prev, [idx]: { ok: false, data: e.message || 'Backend offline — start the FastAPI server' } }))
    } finally {
      setRunning(null)
    }
  }

  return (
    <div className={`fixed right-0 top-1/4 z-50 flex transition-transform duration-300 ${open ? 'translate-x-0' : 'translate-x-[calc(100%-2.5rem)]'}`}>
      {/* Toggle tab */}
      <button
        onClick={() => setOpen(v => !v)}
        className="w-10 bg-brand rounded-l-xl flex items-center justify-center shadow-lg self-center h-28 hover:bg-brand-dark transition"
        title="Demo Simulator Panel"
      >
        {open ? <ChevronRight size={16} className="text-white" /> : <ChevronLeft size={16} className="text-white" />}
      </button>

      {/* Panel */}
      <div className="w-72 bg-card border border-border rounded-l-xl shadow-2xl overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-brand/10">
          <p className="text-xs font-bold text-brand uppercase tracking-wide">🎭 Hackathon Simulator</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Fire demo scenarios with one click</p>
        </div>
        <div className="p-3 space-y-2 max-h-[60vh] overflow-y-auto scrollbar-thin">
          {SCENARIOS.map((s, i) => (
            <div key={i} className="bg-surface rounded-lg border border-border p-2.5">
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-white truncate">{s.label}</p>
                  <p className="text-[10px] text-slate-500 truncate">{s.desc}</p>
                </div>
                <button
                  onClick={() => run(s, i)}
                  disabled={running === i}
                  className="shrink-0 w-7 h-7 rounded-lg bg-brand/20 hover:bg-brand/40 text-brand flex items-center justify-center transition disabled:opacity-50"
                >
                  {running === i ? <Loader2 size={12} className="animate-spin" /> : <Play size={11} />}
                </button>
              </div>
              {results[i] && (
                <p className={`text-[10px] mt-1.5 leading-tight ${results[i].ok ? 'text-green-400' : 'text-red-400'}`}>
                  {results[i].ok ? '✓ ' : '✗ '}{results[i].data}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
