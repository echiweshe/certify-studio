import { api, wsManager } from './api';
import type { Agent, AgentStatus } from '@/types';

export interface AgentUpdate {
  agent_id: string;
  state: string;
  details: {
    current_task?: string;
    progress?: number;
    resource_usage?: any;
  };
}

export interface AgentStatusData {
  agent_id: string;
  agent_type: string;
  state: string;
  current_task?: string;
  tasks_completed: number;
  success_rate: number;
  average_processing_time: number;
  last_active: string;
}

class AgentService {
  private updateCallbacks: Map<string, (update: AgentUpdate) => void> = new Map();
  private connected: boolean = false;

  async initialize() {
    try {
      await wsManager.connect();
      this.connected = true;
      
      // Subscribe to agent updates
      wsManager.subscribe('agents', (data: AgentUpdate) => {
        this.notifyUpdateCallbacks(data);
      });

      // Subscribe to initial state
      wsManager.subscribe('initial_state', (data: any) => {
        if (data.agents) {
          // Process initial agent states
          Object.entries(data.agents).forEach(([agentId, state]: [string, any]) => {
            this.notifyUpdateCallbacks(state);
          });
        }
      });
    } catch (error) {
      console.error('Failed to initialize agent service:', error);
      // Fall back to polling if WebSocket fails
      this.startPolling();
    }
  }

  async getAgents(): Promise<Agent[]> {
    try {
      const statuses = await api.getAgentStatuses();
      
      // Transform API response to Agent type
      return statuses.map((status: AgentStatusData) => ({
        id: status.agent_id,
        name: this.getAgentName(status.agent_type),
        type: status.agent_type,
        icon: this.getAgentIcon(status.agent_type),
        status: this.mapApiStatusToAgentStatus(status.state),
        currentTask: status.current_task || 'Idle',
        tasksCompleted: status.tasks_completed,
        successRate: status.success_rate,
        averageProcessingTime: status.average_processing_time,
        lastActive: new Date(status.last_active),
      }));
    } catch (error) {
      console.error('Failed to get agents:', error);
      // Return mock data as fallback
      return this.getMockAgents();
    }
  }

  async getAgent(id: string): Promise<Agent> {
    const agents = await this.getAgents();
    const agent = agents.find(a => a.id === id);
    if (!agent) {
      throw new Error(`Agent ${id} not found`);
    }
    return agent;
  }

  async getAgentMetrics(id: string): Promise<any> {
    try {
      // For now, return mock metrics
      // TODO: Implement when backend endpoint is available
      return {
        tasksCompleted: Math.floor(Math.random() * 100),
        successRate: 0.95 + Math.random() * 0.05,
        averageProcessingTime: 30 + Math.random() * 20,
        resourceUsage: {
          cpu: Math.random() * 100,
          memory: Math.random() * 100,
          gpu: Math.random() * 100,
        },
      };
    } catch (error) {
      console.error('Failed to get agent metrics:', error);
      throw error;
    }
  }

  subscribeToAgentUpdates(agentId: string, callback: (update: AgentUpdate) => void) {
    this.updateCallbacks.set(agentId, callback);
    
    if (!this.connected) {
      // Try to connect if not already connected
      this.initialize();
    }
  }

  unsubscribeFromAgentUpdates(agentId: string) {
    this.updateCallbacks.delete(agentId);
  }

  private notifyUpdateCallbacks(update: AgentUpdate) {
    const callback = this.updateCallbacks.get(update.agent_id);
    if (callback) {
      callback(update);
    }
    
    // Also notify 'all' subscribers
    const allCallback = this.updateCallbacks.get('all');
    if (allCallback) {
      allCallback(update);
    }
  }

  private startPolling() {
    // Fallback polling mechanism if WebSocket fails
    setInterval(async () => {
      try {
        const agents = await this.getAgents();
        agents.forEach(agent => {
          this.notifyUpdateCallbacks({
            agent_id: agent.id,
            state: agent.status,
            details: {
              current_task: agent.currentTask,
              progress: Math.random() * 100,
            },
          });
        });
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 5000);
  }

  private getAgentName(agentType: string): string {
    const nameMap: Record<string, string> = {
      'ContentGenerationAgent': 'Content Generator',
      'DomainExtractionAgent': 'Domain Extractor',
      'QualityAssuranceAgent': 'Quality Assurance',
      'ExportAgent': 'Export Specialist',
      'CognitiveLoadAgent': 'Cognitive Load Manager',
      'AnimationAgent': 'Animation Choreographer',
    };
    return nameMap[agentType] || agentType;
  }

  private getAgentIcon(agentType: string): string {
    const iconMap: Record<string, string> = {
      'ContentGenerationAgent': 'FileText',
      'DomainExtractionAgent': 'Brain',
      'QualityAssuranceAgent': 'Shield',
      'ExportAgent': 'Download',
      'CognitiveLoadAgent': 'Activity',
      'AnimationAgent': 'Sparkles',
    };
    return iconMap[agentType] || 'Bot';
  }

  private mapApiStatusToAgentStatus(state: string): AgentStatus {
    const statusMap: Record<string, AgentStatus> = {
      'idle': 'idle',
      'busy': 'executing',
      'thinking': 'thinking',
      'planning': 'planning',
      'collaborating': 'collaborating',
      'error': 'idle',
    };
    return statusMap[state] || 'idle';
  }

  private getMockAgents(): Agent[] {
    return [
      {
        id: '1',
        name: 'Content Generator',
        type: 'ContentGenerationAgent',
        icon: 'FileText',
        status: 'idle',
        currentTask: 'Waiting for instructions',
        tasksCompleted: 42,
        successRate: 0.98,
        averageProcessingTime: 45.2,
        lastActive: new Date(),
      },
      {
        id: '2',
        name: 'Domain Extractor',
        type: 'DomainExtractionAgent',
        icon: 'Brain',
        status: 'thinking',
        currentTask: 'Analyzing content structure',
        tasksCompleted: 38,
        successRate: 0.96,
        averageProcessingTime: 32.5,
        lastActive: new Date(),
      },
      {
        id: '3',
        name: 'Quality Assurance',
        type: 'QualityAssuranceAgent',
        icon: 'Shield',
        status: 'executing',
        currentTask: 'Checking pedagogical quality',
        tasksCompleted: 35,
        successRate: 0.97,
        averageProcessingTime: 28.3,
        lastActive: new Date(),
      },
    ];
  }
}

export const agentService = new AgentService();

// Initialize on import
if (typeof window !== 'undefined') {
  agentService.initialize().catch(console.error);
}
