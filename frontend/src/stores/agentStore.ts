import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import type { Agent, AgentStatus } from '@/types'
import { AgentType } from '@/types'
import { agentService } from '@/services/agents'

interface AgentState {
  agents: Agent[]
  activeAgents: Agent[]
  selectedAgent: Agent | null
  isLoading: boolean
  error: string | null
  
  // Actions
  fetchAgents: () => Promise<void>
  selectAgent: (agent: Agent | null) => void
  updateAgentStatus: (agentId: string, status: AgentStatus) => void
  subscribeToUpdates: () => void
  unsubscribeFromUpdates: () => void
}

export const useAgentStore = create<AgentState>()(
  subscribeWithSelector((set, get) => ({
    agents: [],
    activeAgents: [],
    selectedAgent: null,
    isLoading: false,
    error: null,

    fetchAgents: async () => {
      set({ isLoading: true, error: null })
      try {
        const agents = await agentService.getAgents()
        set({ 
          agents,
          activeAgents: agents.filter(a => a.status !== 'idle'),
          isLoading: false 
        })
      } catch (error) {
        set({ 
          error: error instanceof Error ? error.message : 'Failed to fetch agents',
          isLoading: false 
        })
      }
    },

    selectAgent: (agent) => {
      set({ selectedAgent: agent })
    },

    updateAgentStatus: (agentId, status) => {
      set((state) => ({
        agents: state.agents.map(agent =>
          agent.id === agentId ? { ...agent, status } : agent
        ),
        activeAgents: state.agents
          .map(agent => agent.id === agentId ? { ...agent, status } : agent)
          .filter(a => a.status !== 'idle')
      }))
    },

    subscribeToUpdates: () => {
      // WebSocket subscription for real-time updates
      agentService.subscribeToAgentUpdates((update) => {
        if (update.type === 'status_update') {
          get().updateAgentStatus(update.agentId, update.status)
        }
      })
    },

    unsubscribeFromUpdates: () => {
      agentService.unsubscribeFromAgentUpdates()
    },
  }))
)

// Mock data for development
const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'Domain Explorer',
    type: AgentType.DOMAIN_EXTRACTOR,
    status: 'idle' as AgentStatus,
    capabilities: [
      { name: 'PDF Analysis', level: 95 },
      { name: 'Concept Mapping', level: 88 },
    ],
    performance: {
      tasksCompleted: 156,
      averageTime: 45,
      successRate: 0.94,
      qualityScore: 0.89,
    },
    beliefs: [],
    goals: [],
    lastActivity: new Date(),
  },
  {
    id: '2',
    name: 'Cognitive Optimizer',
    type: AgentType.COGNITIVE_LOAD_MANAGER,
    status: 'thinking' as AgentStatus,
    currentTask: 'Analyzing learning sequence for AWS concepts',
    capabilities: [
      { name: 'Load Calculation', level: 92 },
      { name: 'Path Optimization', level: 87 },
    ],
    performance: {
      tasksCompleted: 203,
      averageTime: 38,
      successRate: 0.96,
      qualityScore: 0.91,
    },
    beliefs: [],
    goals: [],
    lastActivity: new Date(),
  },
  {
    id: '3',
    name: 'Visual Maestro',
    type: AgentType.ANIMATION_CHOREOGRAPHER,
    status: 'executing' as AgentStatus,
    currentTask: 'Rendering cloud architecture animation',
    capabilities: [
      { name: 'Animation Design', level: 90 },
      { name: 'Timing Optimization', level: 85 },
    ],
    performance: {
      tasksCompleted: 89,
      averageTime: 120,
      successRate: 0.92,
      qualityScore: 0.94,
    },
    beliefs: [],
    goals: [],
    lastActivity: new Date(),
  },
]

// Initialize with mock data in development
if (import.meta.env.DEV) {
  useAgentStore.setState({ agents: mockAgents, activeAgents: mockAgents.filter(a => a.status !== 'idle') })
}