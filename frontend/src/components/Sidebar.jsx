import React from 'react'
import { NavLink } from 'react-router-dom'
import { PAGES, GROUPS } from '../pages/pageRegistry'
import { useAgents } from '../context/AgentContext'
import { clsx } from 'clsx'

function groupPages(pages) {
  const grouped = {}
  pages.forEach(p => {
    if (!grouped[p.group]) grouped[p.group] = []
    grouped[p.group].push(p)
  })
  return grouped
}

export default function Sidebar() {
  const { connected } = useAgents()
  const grouped = groupPages(PAGES)

  return (
    <aside className="w-56 shrink-0 flex flex-col bg-card border-r border-border h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-2xl">⚡</span>
          <div>
            <p className="text-sm font-bold text-white leading-tight">VyapaarOS</p>
            <p className="text-[10px] text-slate-500">MSME AI Platform</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 mt-3">
          <span className={clsx('w-1.5 h-1.5 rounded-full', connected ? 'bg-green-400 animate-pulse' : 'bg-slate-600')} />
          <span className={clsx('text-[10px]', connected ? 'text-green-400' : 'text-slate-500')}>
            {connected ? 'Backend connected' : 'Demo mode'}
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-4">
        {Object.entries(grouped).map(([group, pages]) => (
          <div key={group}>
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-2 mb-1">
              {GROUPS[group] || group}
            </p>
            <div className="space-y-0.5">
              {pages.map(page => (
                page.status === 'placeholder' ? (
                  <div key={page.id} className="flex items-center gap-2.5 px-2 py-2 rounded-lg text-slate-600 cursor-default">
                    <span className="text-sm grayscale opacity-40">{page.icon}</span>
                    <span className="text-xs truncate flex-1">{page.label}</span>
                    <span className="text-[9px] bg-slate-700 text-slate-500 px-1.5 py-0.5 rounded">WIP</span>
                  </div>
                ) : (
                  <NavLink
                    key={page.id}
                    to={`/${page.id}`}
                    className={({ isActive }) => clsx(
                      'flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm transition',
                      isActive
                        ? 'bg-brand/20 text-white border border-brand/30'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    )}
                  >
                    <span className="text-base">{page.icon}</span>
                    <span className="text-xs truncate">{page.label}</span>
                  </NavLink>
                )
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border">
        <p className="text-[10px] text-slate-600">GCP Vertex AI · USE_MOCK_GCP=true</p>
        <p className="text-[10px] text-slate-700 mt-0.5">Hackindia 2024</p>
      </div>
    </aside>
  )
}
