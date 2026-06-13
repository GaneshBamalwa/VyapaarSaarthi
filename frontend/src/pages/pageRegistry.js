/**
 * PAGE REGISTRY — Add your page here to wire it into the sidebar + router.
 *
 * HOW TO ADD A NEW PAGE:
 * 1. Create your component file in src/pages/YourPage.jsx
 * 2. Import it below
 * 3. Add an entry to the PAGES array
 *
 * Entry shape:
 * {
 *   id: 'unique-id',        // used as URL path: /your-id
 *   label: 'Display Name',  // shown in sidebar
 *   icon: '🔥',             // emoji icon for sidebar
 *   component: YourPage,    // the React component
 *   owner: 'Your Name',     // so teammates know who built it
 *   status: 'ready',        // 'ready' | 'wip' | 'placeholder'
 * }
 *
 * Pages with status 'placeholder' show a "Coming Soon" banner but are still routable.
 */

import CommandCentre from './CommandCentre'
import VoiceChat from './VoiceChat'
import GSTCompliance from './GSTCompliance'

// ─── VyapaarSaarthi Agent Pages ───────────────────────────────────────────────
import Orders from './Orders'
import Approvals from './Approvals'
import AgentFeed from './AgentFeed'
import OCRAgent from './OCRAgent'
import SpeechAgentPage from './SpeechAgentPage'
import CollectionsAgent from './CollectionsAgent'
// ─────────────────────────────────────────────────────────────────────────────

// ─── TEAMMATE PAGES — import and add below ───────────────────────────────────
// import CashFlow from './CashFlow'           // Track C team
// import GovSchemes from './GovSchemes'       // Track C team
// ─────────────────────────────────────────────────────────────────────────────

export const PAGES = [
  {
    id: 'command',
    label: 'Command Centre',
    icon: '🏠',
    component: CommandCentre,
    owner: 'Core Team',
    status: 'ready',
    group: 'core',
  },
  {
    id: 'voice-chat',
    label: 'Voice & Chat',
    icon: '🎙️',
    component: VoiceChat,
    owner: 'Core Team',
    status: 'ready',
    group: 'core',
  },
  {
    id: 'gst-compliance',
    label: 'GST & Compliance',
    icon: '🧾',
    component: GSTCompliance,
    owner: 'Core Team',
    status: 'ready',
    group: 'core',
  },

  // ─── VyapaarSaarthi Agent Pages ──────────────────────────────────────────
  {
    id: 'orders',
    label: 'Orders',
    icon: '📦',
    component: Orders,
    owner: 'VyapaarSaarthi',
    status: 'ready',
    group: 'agents',
  },
  {
    id: 'approvals',
    label: 'HITL Approvals',
    icon: '✅',
    component: Approvals,
    owner: 'VyapaarSaarthi',
    status: 'ready',
    group: 'agents',
  },
  {
    id: 'agent-feed',
    label: 'Agent Feed',
    icon: '⚡',
    component: AgentFeed,
    owner: 'VyapaarSaarthi',
    status: 'ready',
    group: 'agents',
  },
  {
    id: 'ocr-agent',
    label: 'OCR Agent',
    icon: '📄',
    component: OCRAgent,
    owner: 'VyapaarSaarthi',
    status: 'ready',
    group: 'agents',
  },
  {
    id: 'speech-agent',
    label: 'Speech Agent',
    icon: '🎤',
    component: SpeechAgentPage,
    owner: 'VyapaarSaarthi',
    status: 'ready',
    group: 'agents',
  },
  {
    id: 'collections',
    label: 'Collections',
    icon: '💰',
    component: CollectionsAgent,
    owner: 'VyapaarSaarthi',
    status: 'ready',
    group: 'agents',
  },

  // ─── TEAMMATE PAGES — uncomment when ready ──────────────────────────────
  {
    id: 'cash-flow',
    label: 'Cash Flow',
    icon: '📊',
    component: null,   // replace with: CashFlow
    owner: 'Track C',
    status: 'placeholder',
    group: 'analytics',
  },
  {
    id: 'gov-schemes',
    label: 'Gov Schemes',
    icon: '🏛️',
    component: null,   // replace with: GovSchemes
    owner: 'Track C',
    status: 'placeholder',
    group: 'analytics',
  },
  // ─────────────────────────────────────────────────────────────────────────
]

export const GROUPS = {
  core: 'Core',
  agents: 'Agents',
  analytics: 'Analytics',
}
