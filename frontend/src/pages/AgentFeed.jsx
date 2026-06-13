import { useState, useEffect, useRef, useCallback } from 'react'
import { RefreshCw, Wifi, WifiOff, Trash2 } from 'lucide-react'
import { api } from '../hooks/useApi'
import { clsx } from 'clsx'

const STATUS_ICON = {
  running:   '⚙️',
  completed: '✅',
  failed:    '❌',
  thinking:  '🤔',
  tool_call: '🔧',
  decision:  '🎯',
  hitl:      '🙋',
}

const STATUS_COLOR = {
  running:   'text-blue-400',
  completed: 'text-green-400',
  failed:    'text-red-400',
  thinking:  'text-yellow-400',
  tool_call: 'text-purple-400',
  decision:  'text-cyan-400',
  hitl:      'text-orange-400',
}

const AGENT_COLOR = {
  'Intake Agent':        'text-blue-400',
  'ClarificationAgent':  'text-orange-400',
  'OCRAgent':            'text-purple-400',
  'SpeechAgent':         'text-teal-400',
  'CollectionsAgent':    'text-red-400',
  'GST Agent':           'text-green-400',
  'Compliance Agent':    'text-indigo-400',
  'Voice Agent':         'text-pink-400',
}

export default function AgentFeed() {
  const [traces, setTraces] = useState([])
  const [wsEvents, setWsEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const [loadingTraces, setLoadingTraces] = useState(true)
  const wsRef = useRef(null)
  const bottomRef = useRef(null)

  const loadTraces = useCallback(async () => {
    setLoadingTraces(true)
    try {
      const data = await api.agentTraces(50)
      setTraces(data)
    } catch (e) {
      console.error('Traces load error:', e)
    } finally {
      setLoadingTraces(false)
    }
  }, [])

  useEffect(() => { loadTraces() }, [loadTraces])

  // WebSocket live feed
  useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const connect = () => {
      const ws = new WebSocket(`${proto}//${window.location.host}/ws`)
      wsRef.current = ws
      ws.onopen  = () => setConnected(true)
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
      ws.onerror = () => setConnected(false)
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'agent_event') {
            setWsEvents(prev => [{ ...msg, live: true, ts: Date.now() }, ...prev].slice(0, 200))
          }
        } catch {}
      }
    }
    connect()
    return () => { wsRef.current?.close() }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [wsEvents])

  const allEvents = [
    ...wsEvents,
    ...traces.map(t => ({
      agent: t.agent_name,
      status: t.status,
      message: t.event,
      data: t.data,
      timestamp: t.timestamp,
      live: false,
    })),
  ]

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Agent Feed</h1>
          <p className="text-sm text-slate-400">Live agentic reasoning trace — all agents broadcast here</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm">
            {connected
              ? <><Wifi size={14} className="text-green-400" /><span className="text-green-400">Live</span></>
              : <><WifiOff size={14} className="text-slate-500" /><span className="text-slate-500">Reconnecting...</span></>}
          </div>
          <button onClick={() => setWsEvents([])}
            className="p-2 rounded-lg bg-card border border-border text-slate-400 hover:text-white transition" title="Clear live events">
            <Trash2 size={14} />
          </button>
          <button onClick={loadTraces} disabled={loadingTraces}
            className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg text-sm text-slate-400 hover:text-white transition disabled:opacity-50">
            <RefreshCw size={14} className={loadingTraces ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Live indicator bar */}
      {wsEvents.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-slate-500 px-1">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          {wsEvents.length} live event{wsEvents.length !== 1 ? 's' : ''} · {traces.length} historical
        </div>
      )}

      <div className="flex-1 bg-slate-950 rounded-xl border border-border overflow-y-auto scrollbar-thin font-mono text-xs">
        {allEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-600 gap-2">
            <span className="text-2xl">🤖</span>
            <p>No agent events yet</p>
            <p className="text-[11px]">Submit an order or send a voice chat to see agents work</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {allEvents.map((ev, i) => (
              <div key={i} className={clsx('px-4 py-2.5 flex gap-3 hover:bg-white/[0.02] transition',
                ev.live && 'border-l-2 border-green-500/50')}>
                <span className="shrink-0 mt-0.5">{STATUS_ICON[ev.status] || '📝'}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                    <span className={clsx('font-semibold', AGENT_COLOR[ev.agent] || 'text-slate-300')}>
                      {ev.agent}
                    </span>
                    <span className={clsx('text-[10px] uppercase tracking-wide', STATUS_COLOR[ev.status] || 'text-slate-500')}>
                      {ev.status}
                    </span>
                    {ev.live && (
                      <span className="text-[10px] text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded-full">LIVE</span>
                    )}
                  </div>
                  <p className="text-slate-300 truncate">{ev.message || ev.event || '—'}</p>
                  {ev.data && typeof ev.data === 'object' && Object.keys(ev.data).length > 0 && (
                    <p className="text-slate-600 mt-0.5 truncate">
                      {JSON.stringify(ev.data)}
                    </p>
                  )}
                </div>
                <span className="text-slate-700 shrink-0 tabular-nums">
                  {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString('en-IN') : ''}
                </span>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  )
}
