import { api } from './auth'
import type { Agent, AgentStatus, WebSocketMessage } from '@/types'

interface AgentUpdate {
  type: 'status_update' | 'task_update' | 'performance_update'
  agentId: string
  status?: AgentStatus
  task?: string
  performance?: any
}

class AgentService {
  private ws: WebSocket | null = null
  private updateCallback: ((update: AgentUpdate) => void) | null = null

  async getAgents(): Promise<Agent[]> {
    const response = await api.get<Agent[]>('/agents')
    return response.data
  }

  async getAgent(id: string): Promise<Agent> {
    const response = await api.get<Agent>(`/agents/${id}`)
    return response.data
  }

  async getAgentMetrics(id: string): Promise<any> {
    const response = await api.get(`/agents/${id}/metrics`)
    return response.data
  }

  async assignTask(agentId: string, task: any): Promise<void> {
    await api.post(`/agents/${agentId}/tasks`, task)
  }

  async getAgentHistory(id: string): Promise<any> {
    const response = await api.get(`/agents/${id}/history`)
    return response.data
  }

  subscribeToAgentUpdates(callback: (update: AgentUpdate) => void) {
    this.updateCallback = callback
    
    // In production, this would be a real WebSocket connection
    if (import.meta.env.PROD) {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/agents`
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data)
        if (message.type === 'agent_status_update' && this.updateCallback) {
          this.updateCallback(message.payload)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } else {
      // Mock updates in development
      this.mockAgentUpdates()
    }
  }

  unsubscribeFromAgentUpdates() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.updateCallback = null
  }

  private mockAgentUpdates() {
    // Simulate random agent updates
    const agents = ['1', '2', '3']
    const statuses: AgentStatus[] = ['idle', 'thinking', 'planning', 'executing', 'collaborating']
    
    setInterval(() => {
      if (this.updateCallback) {
        const agentId = agents[Math.floor(Math.random() * agents.length)]
        const status = statuses[Math.floor(Math.random() * statuses.length)]
        
        this.updateCallback({
          type: 'status_update',
          agentId,
          status,
        })
      }
    }, 5000)
  }
}

export const agentService = new AgentService()