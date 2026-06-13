import { useState, useEffect } from 'react'
import { api } from '../hooks/useApi'

const STATUS_COLOR = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  CLARIFICATION_NEEDED: 'bg-orange-100 text-orange-800',
  AWAITING_APPROVAL: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  PROCESSING: 'bg-purple-100 text-purple-800',
  COMPLETED: 'bg-emerald-100 text-emerald-800',
}

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = () => api.listOrders().then(setOrders).catch(() => {})

  useEffect(() => { load() }, [])

  async function handleSimulate(type) {
    const sim = type === 'clear' ? api.simulateOrder() : api.simulateAmbiguous()
    const data = await sim
    setText(data.text)
  }

  async function handleSubmit() {
    if (!text.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await api.submitOrder(text)
      setResult(res)
      setText('')
      load()
    } finally {
      setLoading(false)
    }
  }

  async function handleSelect(id) {
    const order = await api.getOrder(id)
    setSelected(order)
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Order Intake</h1>
        <span className="text-sm text-gray-500">IntakeAgent + ClarificationAgent</span>
      </div>

      {/* Input */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
        <label className="block text-sm font-medium text-gray-700">New Order (Hinglish / Hindi / English)</label>
        <textarea
          className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="e.g. Ramesh bhai 50 kg atta aur 20 kg chini chahiye kal tak"
        />
        <div className="flex gap-2 flex-wrap">
          <button onClick={handleSubmit} disabled={loading || !text.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40">
            {loading ? 'Processing...' : 'Submit Order'}
          </button>
          <button onClick={() => handleSimulate('clear')}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200">
            Sample Order
          </button>
          <button onClick={() => handleSimulate('ambiguous')}
            className="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg text-sm hover:bg-orange-200">
            Ambiguous Order
          </button>
        </div>

        {result && (
          <div className={`mt-3 p-3 rounded-lg text-sm ${result.interrupted ? 'bg-orange-50 border border-orange-200' : 'bg-green-50 border border-green-200'}`}>
            {result.interrupted
              ? `Order #${result.order_id} needs clarification — sent to HITL queue`
              : `Order #${result.order_id} processed successfully`}
          </div>
        )}
      </div>

      {/* Orders list */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center">
          <h2 className="font-semibold text-gray-800">Recent Orders</h2>
          <button onClick={load} className="text-xs text-blue-600 hover:underline">Refresh</button>
        </div>
        {orders.length === 0 ? (
          <p className="p-5 text-sm text-gray-400">No orders yet. Submit one above.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">ID</th>
                <th className="px-4 py-3 text-left">Customer</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Confidence</th>
                <th className="px-4 py-3 text-left">Type</th>
                <th className="px-4 py-3 text-left">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orders.map(o => (
                <tr key={o.id} onClick={() => handleSelect(o.id)}
                  className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-4 py-3 font-mono text-gray-600">#{o.id}</td>
                  <td className="px-4 py-3 font-medium">{o.customer}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOR[o.status] || 'bg-gray-100 text-gray-600'}`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{o.confidence ? `${Math.round(o.confidence * 100)}%` : '—'}</td>
                  <td className="px-4 py-3 capitalize">{o.input_type}</td>
                  <td className="px-4 py-3 text-gray-500">{new Date(o.created_at).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Order detail modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">Order #{selected.id}</h3>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <div className="space-y-2 text-sm">
              <div><span className="text-gray-500">Customer:</span> <span className="font-medium">{selected.customer}</span></div>
              <div><span className="text-gray-500">Status:</span> <span className={`ml-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOR[selected.status] || 'bg-gray-100'}`}>{selected.status}</span></div>
              <div><span className="text-gray-500">Raw input:</span> <span className="italic text-gray-700">{selected.raw_input}</span></div>
              {selected.delivery_date && <div><span className="text-gray-500">Delivery:</span> {selected.delivery_date}</div>}
              {selected.items?.length > 0 && (
                <div>
                  <p className="text-gray-500 mt-2 mb-1">Items:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {selected.items.map((it, i) => (
                      <li key={i}>{it.quantity} {it.unit} of {it.name} {it.price ? `@ ₹${it.price}` : ''}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
