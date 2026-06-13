import { useState, useEffect } from 'react'
import { api } from '../hooks/useApi'

export default function Approvals() {
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(false)
  const [notes, setNotes] = useState({})

  const load = () => api.intakeHitlQueue().then(setQueue).catch(() => {})
  useEffect(() => { load() }, [])

  async function decide(id, approved) {
    setLoading(true)
    try {
      await api.reviewIntakeHitl(id, approved, {}, notes[id] || '')
      load()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">HITL Approvals</h1>
        <button onClick={load} className="text-sm text-blue-600 hover:underline">Refresh</button>
      </div>

      {queue.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400">
          <div className="text-4xl mb-3">✅</div>
          <p className="font-medium">No pending approvals</p>
          <p className="text-sm mt-1">Ambiguous orders will appear here for human review</p>
        </div>
      ) : (
        <div className="space-y-4">
          {queue.map(item => (
            <div key={item.id} className="bg-white rounded-xl border border-orange-200 p-5 shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <span className="text-xs font-medium text-orange-700 bg-orange-100 px-2 py-0.5 rounded-full">
                    Awaiting Approval
                  </span>
                  <p className="mt-2 text-sm font-semibold text-gray-800">Order #{item.order_id}</p>
                </div>
                <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleString('en-IN')}</span>
              </div>

              <div className="bg-orange-50 rounded-lg p-3 mb-3 text-sm text-orange-900">
                <p className="font-medium mb-1">Clarification needed:</p>
                <p>{item.reason || 'Order text is ambiguous or incomplete'}</p>
              </div>

              {item.payload?.clarification && (
                <div className="text-xs text-gray-500 mb-3">
                  <span className="font-medium">Agent question: </span>
                  {item.payload.clarification?.data?.clarification_question || '—'}
                </div>
              )}

              <textarea
                className="w-full border border-gray-200 rounded-lg p-2 text-sm resize-none mb-3"
                rows={2}
                placeholder="Reviewer notes (optional)"
                value={notes[item.id] || ''}
                onChange={e => setNotes(n => ({ ...n, [item.id]: e.target.value }))}
              />

              <div className="flex gap-3">
                <button
                  onClick={() => decide(item.id, true)}
                  disabled={loading}
                  className="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-40">
                  Approve & Continue
                </button>
                <button
                  onClick={() => decide(item.id, false)}
                  disabled={loading}
                  className="flex-1 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 disabled:opacity-40">
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
