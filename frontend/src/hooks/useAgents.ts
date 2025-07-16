import { useState, useEffect, useCallback } from 'react';
import { agentService, AgentUpdate } from '@/services/agents';
import type { Agent } from '@/types';

export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial agents
  useEffect(() => {
    let mounted = true;

    const fetchAgents = async () => {
      try {
        setLoading(true);
        const data = await agentService.getAgents();
        if (mounted) {
          setAgents(data);
          setError(null);
        }
      } catch (err) {
        console.error('Failed to fetch agents:', err);
        if (mounted) {
          setError('Failed to fetch agents');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchAgents();

    return () => {
      mounted = false;
    };
  }, []);

  // Subscribe to real-time updates
  useEffect(() => {
    const handleUpdate = (update: AgentUpdate) => {
      setAgents(prevAgents => 
        prevAgents.map(agent => 
          agent.id === update.agent_id
            ? {
                ...agent,
                status: update.state as any,
                currentTask: update.details.current_task || agent.currentTask,
              }
            : agent
        )
      );
    };

    // Subscribe to all agent updates
    agentService.subscribeToAgentUpdates('all', handleUpdate);

    return () => {
      agentService.unsubscribeFromAgentUpdates('all');
    };
  }, []);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await agentService.getAgents();
      setAgents(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch agents');
    } finally {
      setLoading(false);
    }
  }, []);

  return { agents, loading, error, refetch };
}

export function useAgent(agentId: string) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch agent details
  useEffect(() => {
    let mounted = true;

    const fetchAgent = async () => {
      try {
        setLoading(true);
        const [agentData, metricsData] = await Promise.all([
          agentService.getAgent(agentId),
          agentService.getAgentMetrics(agentId),
        ]);
        
        if (mounted) {
          setAgent(agentData);
          setMetrics(metricsData);
          setError(null);
        }
      } catch (err) {
        console.error('Failed to fetch agent:', err);
        if (mounted) {
          setError('Failed to fetch agent details');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    if (agentId) {
      fetchAgent();
    }

    return () => {
      mounted = false;
    };
  }, [agentId]);

  // Subscribe to real-time updates for this specific agent
  useEffect(() => {
    if (!agentId) return;

    const handleUpdate = (update: AgentUpdate) => {
      setAgent(prevAgent => 
        prevAgent
          ? {
              ...prevAgent,
              status: update.state as any,
              currentTask: update.details.current_task || prevAgent.currentTask,
            }
          : null
      );

      // Update metrics if resource usage is provided
      if (update.details.resource_usage) {
        setMetrics(prevMetrics => ({
          ...prevMetrics,
          resourceUsage: update.details.resource_usage,
        }));
      }
    };

    agentService.subscribeToAgentUpdates(agentId, handleUpdate);

    return () => {
      agentService.unsubscribeFromAgentUpdates(agentId);
    };
  }, [agentId]);

  return { agent, metrics, loading, error };
}

export function useAgentCollaboration() {
  const [collaborations, setCollaborations] = useState<any[]>([]);
  const [activeCollaborations, setActiveCollaborations] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Subscribe to collaboration events
    const handleCollaborationEvent = (event: any) => {
      if (event.type === 'collaboration_start') {
        setActiveCollaborations(prev => new Set(prev).add(event.collaboration_id));
        setCollaborations(prev => [event, ...prev].slice(0, 50)); // Keep last 50
      } else if (event.type === 'collaboration_end') {
        setActiveCollaborations(prev => {
          const next = new Set(prev);
          next.delete(event.collaboration_id);
          return next;
        });
      }
    };

    // This would connect to the WebSocket for real-time collaboration events
    // For now, we'll simulate some activity
    const interval = setInterval(() => {
      const mockEvent = {
        type: Math.random() > 0.5 ? 'collaboration_start' : 'collaboration_end',
        collaboration_id: `collab-${Math.floor(Math.random() * 1000)}`,
        agents: ['agent-1', 'agent-2'],
        task: 'Content quality check',
        timestamp: new Date().toISOString(),
      };
      handleCollaborationEvent(mockEvent);
    }, 10000); // Every 10 seconds

    return () => {
      clearInterval(interval);
    };
  }, []);

  return { collaborations, activeCollaborations };
}

export function useAgentPerformance(agentId?: string) {
  const [performance, setPerformance] = useState<any>({
    tasksCompleted: 0,
    successRate: 0,
    averageTime: 0,
    trend: 'stable',
  });

  useEffect(() => {
    // Simulate performance updates
    const interval = setInterval(() => {
      setPerformance(prev => ({
        tasksCompleted: prev.tasksCompleted + Math.floor(Math.random() * 2),
        successRate: 0.95 + Math.random() * 0.05,
        averageTime: 30 + Math.random() * 20,
        trend: Math.random() > 0.5 ? 'improving' : 'stable',
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, [agentId]);

  return performance;
}
