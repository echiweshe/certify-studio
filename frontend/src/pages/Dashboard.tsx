import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Brain,
  Sparkles,
  TrendingUp,
  Users,
  FileText,
  Clock,
  Zap,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'
import { cn, formatDuration } from '@/utils'
import type { PlatformMetrics, AgentAnalytics } from '@/types'
import { useAgentStore } from '@/stores/agentStore'
import AgentCard from '@/components/AgentCard'
import MetricCard from '@/components/MetricCard'
import RecentGenerations from '@/components/RecentGenerations'

// Mock data for charts
const generationTrend = [
  { time: '00:00', value: 45 },
  { time: '04:00', value: 32 },
  { time: '08:00', value: 67 },
  { time: '12:00', value: 85 },
  { time: '16:00', value: 91 },
  { time: '20:00', value: 73 },
  { time: '24:00', value: 58 },
]

const qualityMetrics = [
  { metric: 'Pedagogy', value: 92 },
  { metric: 'Accuracy', value: 96 },
  { metric: 'Accessibility', value: 89 },
  { metric: 'Engagement', value: 87 },
  { metric: 'Cognitive', value: 91 },
]

const contentTypes = [
  { name: 'Video', value: 35, color: '#3B82F6' },
  { name: 'Interactive', value: 28, color: '#8B5CF6' },
  { name: 'PDF', value: 20, color: '#EC4899' },
  { name: 'VR', value: 12, color: '#10B981' },
  { name: 'Assessment', value: 5, color: '#F59E0B' },
]

const agentPerformance = [
  { agent: 'Domain', performance: 95, utilization: 78 },
  { agent: 'Cognitive', performance: 92, utilization: 85 },
  { agent: 'Animation', performance: 88, utilization: 72 },
  { agent: 'Assembly', performance: 90, utilization: 68 },
  { agent: 'QA', performance: 96, utilization: 81 },
]

export default function Dashboard() {
  const { agents, fetchAgents, subscribeToUpdates, unsubscribeFromUpdates } = useAgentStore()
  const [metrics, setMetrics] = useState<PlatformMetrics>({
    totalGenerations: 1247,
    activeUsers: 89,
    averageQualityScore: 0.91,
    systemHealth: 0.98,
    agentUtilization: 0.76,
    revenueToday: 4832,
  })

  useEffect(() => {
    fetchAgents()
    subscribeToUpdates()
    
    return () => {
      unsubscribeFromUpdates()
    }
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Real-time overview of your AI orchestration platform
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Generations"
          value={metrics.totalGenerations.toLocaleString()}
          change={12.5}
          icon={FileText}
          trend="up"
        />
        <MetricCard
          title="Active Users"
          value={metrics.activeUsers}
          change={8.2}
          icon={Users}
          trend="up"
        />
        <MetricCard
          title="Quality Score"
          value={`${(metrics.averageQualityScore * 100).toFixed(0)}%`}
          change={2.1}
          icon={Sparkles}
          trend="up"
        />
        <MetricCard
          title="System Health"
          value={`${(metrics.systemHealth * 100).toFixed(0)}%`}
          change={0}
          icon={Activity}
          trend="neutral"
        />
        <MetricCard
          title="Agent Utilization"
          value={`${(metrics.agentUtilization * 100).toFixed(0)}%`}
          change={-3.4}
          icon={Brain}
          trend="down"
        />
        <MetricCard
          title="Revenue Today"
          value={`$${metrics.revenueToday.toLocaleString()}`}
          change={15.7}
          icon={TrendingUp}
          trend="up"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Generation Trend */}
        <div className="card-depth p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
            Generation Trend
            <span className="text-sm text-muted-foreground">Last 24h</span>
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={generationTrend}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(17, 24, 39, 0.8)', 
                  border: '1px solid #374151',
                  backdropFilter: 'blur(10px)'
                }} 
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3B82F6"
                fillOpacity={1}
                fill="url(#colorValue)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Content Distribution */}
        <div className="card-depth p-6">
          <h3 className="text-lg font-semibold mb-4">Content Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={contentTypes}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name} ${entry.value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {contentTypes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Quality Metrics Radar */}
        <div className="card-depth p-6">
          <h3 className="text-lg font-semibold mb-4">Quality Metrics</h3>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={qualityMetrics}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="metric" stroke="#9CA3AF" fontSize={12} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9CA3AF" />
              <Radar
                name="Score"
                dataKey="value"
                stroke="#8B5CF6"
                fill="#8B5CF6"
                fillOpacity={0.6}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Active Agents */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Active Agents</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.filter(a => a.status !== 'idle').map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      </div>

      {/* Agent Performance & Recent Generations */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Agent Performance */}
        <div className="card-depth p-6">
          <h3 className="text-lg font-semibold mb-4">Agent Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agentPerformance} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
              <YAxis dataKey="agent" type="category" stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(17, 24, 39, 0.8)', 
                  border: '1px solid #374151',
                  backdropFilter: 'blur(10px)'
                }} 
              />
              <Bar dataKey="performance" fill="#3B82F6" name="Performance %" />
              <Bar dataKey="utilization" fill="#8B5CF6" name="Utilization %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Generations */}
        <RecentGenerations />
      </div>
    </div>
  )
}