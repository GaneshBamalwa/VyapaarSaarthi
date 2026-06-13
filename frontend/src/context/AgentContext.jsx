import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'

const AgentContext = createContext(null)

const AGENT_STATUS = {
  'GST Agent': { icon: '🧾', color: 'text-yellow-400' },
  'Compliance Agent': { icon: '⚖️', color: 'text-purple-400' },
  'Voice Agent': { icon: '🎙️', color: 'text-blue-400' },
  'Collections Agent': { icon: '💰', color: 'text-green-400' },
  'Intake Agent': { icon: '📥', color: 'text-orange-400' },
  'HITL': { icon: '👤', color: 'text-pink-400' },
}

export function AgentProvider({ children }) {
  const [feed, setFeed] = useState([])
  const [agentStates, setAgentStates] = useState({})
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws')
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        clearTimeout(reconnectTimer.current)
      }

      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data)
          const meta = AGENT_STATUS[event.agent] || { icon: '🤖', color: 'text-gray-400' }
          setFeed(prev => [{ ...event, ...meta, id: Date.now() + Math.random() }, ...prev].slice(0, 80))
          setAgentStates(prev => ({
            ...prev,
            [event.agent]: { status: event.event, message: event.message, lastUpdate: event.timestamp },
          }))
        } catch { /* ignore malformed */ }
      }

      ws.onclose = () => {
        setConnected(false)
        reconnectTimer.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    } catch { /* ws unavailable in preview */ }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  // Inject mock feed entries for demo when backend is offline
  useEffect(() => {
    if (connected) return
    const MOCK_EVENTS = [
      { agent: 'GST Agent', event: 'idle', message: 'Monitoring invoice queue...', icon: '🧾', color: 'text-yellow-400' },
      { agent: 'Compliance Agent', event: 'idle', message: 'Watching GST portal for notices...', icon: '⚖️', color: 'text-purple-400' },
      { agent: 'Voice Agent', event: 'idle', message: 'Ready for voice input...', icon: '🎙️', color: 'text-blue-400' },
      { agent: 'Collections Agent', event: 'thinking', message: 'Evaluating overdue invoices — 3 at risk...', icon: '💰', color: 'text-green-400' },
    ]
    MOCK_EVENTS.forEach((e, i) => {
      setTimeout(() => {
        setFeed(prev => [{ ...e, id: Date.now() + i, timestamp: new Date().toISOString() }, ...prev])
        setAgentStates(prev => ({ ...prev, [e.agent]: { status: e.event, message: e.message } }))
      }, i * 600)
    })
  }, [connected])

  return (
    <AgentContext.Provider value={{ feed, agentStates, connected, AGENT_STATUS }}>
      {children}
    </AgentContext.Provider>
  )
}

export const useAgents = () => useContext(AgentContext)
