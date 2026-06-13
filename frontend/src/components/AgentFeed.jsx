import React from 'react'
import { useAgents } from '../context/AgentContext'
import { Wifi, WifiOff } from 'lucide-react'

const EVENT_COLORS = {
  thinking: 'text-yellow-300',
  completed: 'text-green-400',
  tool_call: 'text-blue-300',
  decision: 'text-purple-300',
  approved: 'text-emerald-400',
  idle: 'text-slate-400',
  error: 'text-red-400',
}

export default function AgentFeed() {
  const { feed, connected } = useAgents()

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Live Agent Feed</span>
        <div className="flex items-center gap-1.5">
          {connected
            ? <><Wifi size={12} className="text-green-400" /><span className="text-xs text-green-400">Live</span></>
            : <><WifiOff size={12} className="text-slate-500" /><span className="text-xs text-slate-500">Demo</span></>
          }
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-3 py-2 space-y-1.5">
        {feed.length === 0 && (
          <p className="text-xs text-slate-500 text-center mt-4">Agents initializing...</p>
        )}
        {feed.map(event => (
          <div key={event.id} className="flex gap-2 text-xs group">
            <span className="shrink-0 mt-0.5">{event.icon}</span>
            <div className="min-w-0">
              <span className={`font-medium ${event.color}`}>{event.agent}</span>
              <span className={` ml-1 ${EVENT_COLORS[event.event] || 'text-slate-400'}`}>
                [{event.event}]
              </span>
              <p className="text-slate-300 leading-tight mt-0.5 truncate">{event.message}</p>
              <p className="text-slate-600 text-[10px]">
                {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
