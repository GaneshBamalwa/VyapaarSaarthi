import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AgentProvider } from './context/AgentContext'
import Sidebar from './components/Sidebar'
import AgentFeed from './components/AgentFeed'
import SimulatorPanel from './components/SimulatorPanel'
import { PAGES } from './pages/pageRegistry'

function PlaceholderPage({ page }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center gap-4 p-12">
      <span className="text-5xl">{page.icon}</span>
      <div>
        <h2 className="text-2xl font-bold text-white">{page.label}</h2>
        <p className="text-slate-400 mt-1">Owned by <span className="text-brand">{page.owner}</span></p>
      </div>
      <div className="bg-card border border-border rounded-xl p-5 max-w-md text-left">
        <p className="text-xs font-semibold text-slate-300 mb-2">👋 For the team building this page:</p>
        <ol className="text-xs text-slate-400 space-y-1 list-decimal list-inside">
          <li>Create <code className="text-brand bg-surface px-1 rounded">src/pages/{page.label.replace(/\s+/g,'')}.jsx</code></li>
          <li>Import it in <code className="text-brand bg-surface px-1 rounded">src/pages/pageRegistry.js</code></li>
          <li>Replace <code className="text-brand bg-surface px-1 rounded">component: null</code> with your component</li>
          <li>Change <code className="text-brand bg-surface px-1 rounded">status: 'placeholder'</code> to <code className="text-brand bg-surface px-1 rounded">'ready'</code></li>
        </ol>
      </div>
      <p className="text-xs text-slate-600">API base: <code>http://localhost:8000</code> · Docs: <code>/docs</code></p>
    </div>
  )
}

export default function App() {
  return (
    <AgentProvider>
      <div className="flex h-screen overflow-hidden bg-surface">
        <Sidebar />

        <main className="flex-1 flex overflow-hidden">
          {/* Page area */}
          <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
            <Routes>
              <Route path="/" element={<Navigate to="/command" replace />} />
              {PAGES.map(page => (
                <Route
                  key={page.id}
                  path={`/${page.id}`}
                  element={
                    page.component
                      ? <page.component />
                      : <PlaceholderPage page={page} />
                  }
                />
              ))}
              <Route path="*" element={<Navigate to="/command" replace />} />
            </Routes>
          </div>

          {/* Live Agent Feed — right panel */}
          <aside className="w-64 shrink-0 border-l border-border bg-card hidden xl:flex flex-col">
            <AgentFeed />
          </aside>
        </main>

        {/* Simulator drawer */}
        <SimulatorPanel />
      </div>
    </AgentProvider>
  )
}
