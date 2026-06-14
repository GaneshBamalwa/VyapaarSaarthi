import { create } from "zustand";
import type { WSEvent, AgentName, AgentStatus } from "@/types";

interface AgentState {
  status: AgentStatus;
  lastEvent: string;
  lastUpdated: string | null;
}

interface AgentStore {
  connected: boolean;
  events: WSEvent[];
  agentStates: Record<AgentName, AgentState>;
  pendingApprovals: number;

  setConnected: (v: boolean) => void;
  addEvent: (event: WSEvent) => void;
  clearEvents: () => void;
  setPendingApprovals: (count: number) => void;
}

const DEFAULT_AGENT: AgentState = {
  status: "idle",
  lastEvent: "",
  lastUpdated: null,
};

const DEFAULT_AGENTS: Record<AgentName, AgentState> = {
  IntakeAgent: { ...DEFAULT_AGENT },
  ClarificationAgent: { ...DEFAULT_AGENT },
  OCRAgent: { ...DEFAULT_AGENT },
  SpeechAgent: { ...DEFAULT_AGENT },
  CollectionsAgent: { ...DEFAULT_AGENT },
};

export const useAgentStore = create<AgentStore>((set) => ({
  connected: false,
  events: [],
  agentStates: DEFAULT_AGENTS,
  pendingApprovals: 0,

  setConnected: (connected) => set({ connected }),

  addEvent: (event) =>
    set((state) => {
      const newEvents = [event, ...state.events].slice(0, 200); // Keep last 200

      // Update agent state if it's an agent event
      if (event.type === "agent_event") {
        const agentName = event.agent as AgentName;
        const newAgentStates = {
          ...state.agentStates,
          [agentName]: {
            status: event.status,
            lastEvent: event.event,
            lastUpdated: event.timestamp,
          },
        };
        return { events: newEvents, agentStates: newAgentStates };
      }

      return { events: newEvents };
    }),

  clearEvents: () => set({ events: [] }),
  setPendingApprovals: (pendingApprovals) => set({ pendingApprovals }),
}));
