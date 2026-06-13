import { useState, useEffect } from 'react'
import { api } from '../hooks/useApi'

const RISK_STYLE = {
  LOW: { bar: 'bg-green-500', badge: 'bg-green-100 text-green-800', label: 'Low Risk' },
  MEDIUM: { bar: 'bg-yellow-500', badge: 'bg-yellow-100 text-yellow-800', label: 'Medium Risk' },
  HIGH: { bar: 'bg-red-500', badge: 'bg-red-100 text-red-800', label: 'High Risk' },
}

export default function CollectionsAgent() {
  const [overdue, setOverdue] = useState([])
  const [form, setForm] = useState({ invoice_id: '', customer: '', amount: '', due_days: '', previous_reminders: 0 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.overdueInvoices().then(setOverdue).catch(() => {})
  }, [])

  async function handleSimulate() {
    const data = await api.simulateOverdue()
    setForm({ invoice_id: data.invoice_id, customer: data.customer, amount: String(data.amount), due_days: String(data.due_days), previous_reminders: 0 })
  }

  async function handleAnalyze() {
    setLoading(true)
    setResult(null)
    try {
      const res = await api.analyzeCollection({
        invoice_id: form.invoice_id || null,
        customer: form.customer || null,
        amount: form.amount ? parseFloat(form.amount) : null,
        due_days: form.due_days !== '' ? parseInt(form.due_days) : null,
        previous_reminders: parseInt(form.previous_reminders) || 0,
      })
      setResult(res)
    } finally {
      setLoading(false)
    }
  }

  const risk = result?.data?.risk
  const style = RISK_STYLE[risk] || RISK_STYLE.LOW

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Collections Agent</h1>
        <span className="text-sm text-gray-500">Hindi reminders + risk assessment</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input form */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-gray-800">Analyze Invoice</h2>
            <button onClick={handleSimulate} className="text-xs text-blue-600 hover:underline">Load sample</button>
          </div>

          {[
            { label: 'Invoice ID', key: 'invoice_id', placeholder: 'VYP/2024/0001' },
            { label: 'Customer Name', key: 'customer', placeholder: 'Ramesh Traders' },
            { label: 'Amount (₹)', key: 'amount', placeholder: '48300' },
            { label: 'Days Overdue', key: 'due_days', placeholder: '45' },
            { label: 'Previous Reminders', key: 'previous_reminders', placeholder: '2' },
          ].map(({ label, key, placeholder }) => (
            <div key={key}>
              <label className="block text-xs text-gray-500 mb-1">{label}</label>
              <input
                className="w-full border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400"
                placeholder={placeholder}
                value={form[key]}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
              />
            </div>
          ))}

          <button onClick={handleAnalyze} disabled={loading}
            className="w-full py-2.5 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-40">
            {loading ? 'Analyzing...' : 'Generate Reminder'}
          </button>
        </div>

        {/* Result */}
        {result ? (
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <div className="flex justify-between items-center">
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${style.badge}`}>
                {style.label}
              </span>
              <span className="text-sm text-gray-500">
                Score: {result.data?.risk_score ? `${Math.round(result.data.risk_score * 100)}%` : '—'}
              </span>
            </div>

            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className={`h-2 rounded-full ${style.bar}`}
                style={{ width: `${Math.round((result.data?.risk_score || 0) * 100)}%` }} />
            </div>

            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Hindi Reminder</p>
              <p className="text-base text-gray-800 leading-relaxed">{result.data?.message || '—'}</p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Recommended Action</p>
                <p className="font-semibold text-gray-800 mt-0.5 capitalize">{result.data?.recommended_action?.replace('_', ' ') || '—'}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Follow-up in</p>
                <p className="font-semibold text-gray-800 mt-0.5">{result.data?.follow_up_days || '—'} days</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-xl border border-dashed border-gray-200 p-10 flex flex-col items-center justify-center text-center">
            <div className="text-4xl mb-3">💰</div>
            <p className="text-sm text-gray-400">Fill in invoice details and click Generate Reminder</p>
          </div>
        )}
      </div>

      {/* Overdue list */}
      {overdue.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-800">Overdue Invoices ({overdue.length})</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Invoice</th>
                <th className="px-4 py-3 text-left">Customer</th>
                <th className="px-4 py-3 text-right">Amount</th>
                <th className="px-4 py-3 text-right">Days Overdue</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {overdue.map(inv => (
                <tr key={inv.invoice_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-600">{inv.invoice_id}</td>
                  <td className="px-4 py-3 font-medium">{inv.customer}</td>
                  <td className="px-4 py-3 text-right">₹{inv.amount?.toLocaleString('en-IN')}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      inv.due_days > 20 ? 'bg-red-100 text-red-800' :
                      inv.due_days > 7 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>{inv.due_days}d</span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setForm({ invoice_id: inv.invoice_id, customer: inv.customer, amount: String(inv.amount), due_days: String(inv.due_days), previous_reminders: 0 })}
                      className="text-xs text-blue-600 hover:underline">Analyze</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
