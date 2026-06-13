import React from 'react'
import { useAgents } from '../context/AgentContext'

const AGENTS = [
  { name: 'GST Agent', icon: '🧾', desc: 'Invoice & Tax Calculator' },
  { name: 'Compliance Agent', icon: '⚖️', desc: 'Notices & GSTR Filing' },
  { name: 'Voice Agent', icon: '🎙️', desc: 'STT / TTS Pipeline' },
  { name: 'Collections Agent', icon: '💰', desc: 'Payment Reminders' },
  { name: 'Intake Agent', icon: '📥', desc: 'Order Parsing' },
  { name: 'HITL', icon: '👤', desc: 'Human Approvals' },
]

const STATUS_STYLE = {
  thinking: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40 animate-pulse',
  completed: 'bg-green-500/20 text-green-400 border-green-500/40',
  tool_call: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
  decision: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
  approved: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  idle: 'bg-slate-700/40 text-slate-400 border-slate-600/40',
}

export default function AgentMatrix() {
  const { agentStates } = useAgents()

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
      {AGENTS.map(agent => {
        const state = agentStates[agent.name]
        const statusKey = state?.status || 'idle'
        const style = STATUS_STYLE[statusKey] || STATUS_STYLE.idle
        return (
          <div key={agent.name} className={`rounded-lg border p-3 transition-all duration-300 ${style}`}>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{agent.icon}</span>
              <div className="min-w-0">
                <p className="text-xs font-semibold truncate">{agent.name}</p>
                <p className="text-[10px] opacity-70 truncate">{agent.desc}</p>
              </div>
            </div>
            <p className="text-[10px] leading-tight opacity-80 truncate">
              {state?.message || 'Idle — monitoring...'}
            </p>
            <div className="mt-1.5 flex items-center gap-1">
              {statusKey === 'thinking' && <span className="w-1.5 h-1.5 rounded-full bg-current animate-ping" />}
              {statusKey === 'completed' && <span className="w-1.5 h-1.5 rounded-full bg-green-400" />}
              {!['thinking', 'completed'].includes(statusKey) && <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50" />}
              <span className="text-[9px] uppercase tracking-wide opacity-60">{statusKey}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
