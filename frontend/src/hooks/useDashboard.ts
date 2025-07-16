import { useState, useEffect } from 'react';
import { api, wsManager } from '@/services/api';

export interface DashboardStats {
  totalAgents: number;
  activeAgents: number;
  totalGenerationsToday: number;
  averageGenerationTime: number;
  qualityScoreAverage: number;
  activeUsers: number;
  systemHealth: 'healthy' | 'busy' | 'unhealthy';
}

export function useDashboardStats() {
  const [stats, setStats] = useState<DashboardStats>({
    totalAgents: 0,
    activeAgents: 0,
    totalGenerationsToday: 0,
    averageGenerationTime: 0,
    qualityScoreAverage: 0,
    activeUsers: 0,
    systemHealth: 'healthy',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await api.getDashboardStats();
        
        if (mounted) {
          setStats({
            totalAgents: data.total_agents,
            activeAgents: data.active_agents,
            totalGenerationsToday: data.total_generations_today,
            averageGenerationTime: data.average_generation_time,
            qualityScoreAverage: data.quality_score_average,
            activeUsers: data.active_users,
            systemHealth: data.system_health,
          });
          setError(null);
        }
      } catch (err) {
        console.error('Failed to fetch dashboard stats:', err);
        if (mounted) {
          setError('Failed to fetch dashboard statistics');
          // Use mock data as fallback
          setStats({
            totalAgents: 6,
            activeAgents: 3,
            totalGenerationsToday: 47,
            averageGenerationTime: 245.6,
            qualityScoreAverage: 0.92,
            activeUsers: 12,
            systemHealth: 'healthy',
          });
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchStats();

    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);

    // Subscribe to real-time updates
    const handleUpdate = (data: any) => {
      if (data.type === 'stats_update' && mounted) {
        setStats(prev => ({
          ...prev,
          ...data.stats,
        }));
      }
    };

    wsManager.subscribe('dashboard', handleUpdate);

    return () => {
      mounted = false;
      clearInterval(interval);
      wsManager.unsubscribe('dashboard', handleUpdate);
    };
  }, []);

  return { stats, loading, error };
}

export interface CollaborationMetrics {
  totalCollaborations: number;
  activeCollaborations: number;
  collaborationPatterns: Record<string, number>;
  averageAgentsPerTask: number;
  collaborationSuccessRate: number;
}

export function useCollaborationMetrics() {
  const [metrics, setMetrics] = useState<CollaborationMetrics>({
    totalCollaborations: 0,
    activeCollaborations: 0,
    collaborationPatterns: {},
    averageAgentsPerTask: 0,
    collaborationSuccessRate: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const data = await api.getCollaborationMetrics();
        
        if (mounted) {
          setMetrics({
            totalCollaborations: data.total_collaborations,
            activeCollaborations: data.active_collaborations,
            collaborationPatterns: data.collaboration_patterns,
            averageAgentsPerTask: data.average_agents_per_task,
            collaborationSuccessRate: data.collaboration_success_rate,
          });
          setError(null);
        }
      } catch (err) {
        console.error('Failed to fetch collaboration metrics:', err);
        if (mounted) {
          setError('Failed to fetch collaboration metrics');
          // Use mock data as fallback
          setMetrics({
            totalCollaborations: 342,
            activeCollaborations: 7,
            collaborationPatterns: {
              'content_qa': 156,
              'domain_content': 98,
              'qa_export': 88,
            },
            averageAgentsPerTask: 2.3,
            collaborationSuccessRate: 0.94,
          });
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchMetrics();

    // Refresh every minute
    const interval = setInterval(fetchMetrics, 60000);

    // Subscribe to collaboration events
    const handleCollaboration = (data: any) => {
      if (mounted) {
        setMetrics(prev => ({
          ...prev,
          activeCollaborations: prev.activeCollaborations + (data.event_type === 'start' ? 1 : -1),
          totalCollaborations: prev.totalCollaborations + (data.event_type === 'start' ? 1 : 0),
        }));
      }
    };

    wsManager.subscribe('collaboration', handleCollaboration);

    return () => {
      mounted = false;
      clearInterval(interval);
      wsManager.unsubscribe('collaboration', handleCollaboration);
    };
  }, []);

  return { metrics, loading, error };
}

export interface KnowledgeGraphStats {
  totalNodes: number;
  totalRelationships: number;
  domainsCovered: number;
  conceptsExtracted: number;
  recentUpdates: Array<{
    type: string;
    name: string;
    timestamp: string;
  }>;
}

export function useKnowledgeGraphStats() {
  const [stats, setStats] = useState<KnowledgeGraphStats>({
    totalNodes: 0,
    totalRelationships: 0,
    domainsCovered: 0,
    conceptsExtracted: 0,
    recentUpdates: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await api.getKnowledgeGraphStats();
        
        if (mounted) {
          setStats({
            totalNodes: data.total_nodes,
            totalRelationships: data.total_relationships,
            domainsCovered: data.domains_covered,
            conceptsExtracted: data.concepts_extracted,
            recentUpdates: data.recent_updates,
          });
          setError(null);
        }
      } catch (err) {
        console.error('Failed to fetch knowledge graph stats:', err);
        if (mounted) {
          setError('Failed to fetch knowledge graph statistics');
          // Use mock data as fallback
          setStats({
            totalNodes: 2847,
            totalRelationships: 5632,
            domainsCovered: 15,
            conceptsExtracted: 847,
            recentUpdates: [
              { type: 'concept', name: 'Machine Learning Fundamentals', timestamp: new Date().toISOString() },
              { type: 'domain', name: 'AWS AI Services', timestamp: new Date().toISOString() },
              { type: 'relationship', name: 'prerequisite_of', timestamp: new Date().toISOString() },
            ],
          });
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchStats();

    // Refresh every 2 minutes
    const interval = setInterval(fetchStats, 120000);

    // Subscribe to knowledge graph updates
    const handleUpdate = (data: any) => {
      if (data.type === 'knowledge_update' && mounted) {
        setStats(prev => ({
          ...prev,
          totalNodes: prev.totalNodes + (data.nodes_added || 0),
          totalRelationships: prev.totalRelationships + (data.relationships_added || 0),
          recentUpdates: [
            {
              type: data.update_type,
              name: data.name,
              timestamp: new Date().toISOString(),
            },
            ...prev.recentUpdates.slice(0, 9), // Keep last 10
          ],
        }));
      }
    };

    wsManager.subscribe('knowledge_graph', handleUpdate);

    return () => {
      mounted = false;
      clearInterval(interval);
      wsManager.unsubscribe('knowledge_graph', handleUpdate);
    };
  }, []);

  return { stats, loading, error };
}

// Export all hooks
export default {
  useDashboardStats,
  useCollaborationMetrics,
  useKnowledgeGraphStats,
};
