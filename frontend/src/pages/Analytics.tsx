import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  Users,
  Brain,
  Clock,
  Award,
  Calendar,
  Download,
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
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
} from 'recharts'
import * as Tabs from '@radix-ui/react-tabs'
import * as Select from '@radix-ui/react-select'
import { useState } from 'react'

// Mock data
const learningProgressData = [
  { date: '2024-01', completionRate: 45, engagementRate: 62 },
  { date: '2024-02', completionRate: 52, engagementRate: 68 },
  { date: '2024-03', completionRate: 58, engagementRate: 71 },
  { date: '2024-04', completionRate: 65, engagementRate: 75 },
  { date: '2024-05', completionRate: 71, engagementRate: 78 },
  { date: '2024-06', completionRate: 78, engagementRate: 82 },
]

const contentEffectiveness = [
  { name: 'Video', effectiveness: 92, count: 234 },
  { name: 'Interactive', effectiveness: 88, count: 189 },
  { name: 'PDF', effectiveness: 75, count: 156 },
  { name: 'VR', effectiveness: 95, count: 67 },
  { name: 'Assessment', effectiveness: 84, count: 123 },
]

const agentUtilization = [
  { name: 'Domain Extractor', value: 78, fill: '#3B82F6' },
  { name: 'Cognitive Manager', value: 85, fill: '#8B5CF6' },
  { name: 'Animation Agent', value: 72, fill: '#EC4899' },
  { name: 'QA Agent', value: 91, fill: '#10B981' },
]

const learnerMetrics = {
  totalLearners: 12847,
  activeLearners: 8923,
  averageScore: 86.4,
  completionRate: 78.2,
}

export default function Analytics() {
  const [dateRange, setDateRange] = useState('last30days')
  const [selectedMetric, setSelectedMetric] = useState('all')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Deep insights into platform performance and learning outcomes
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Select.Root value={dateRange} onValueChange={setDateRange}>
            <Select.Trigger className="px-3 py-2 rounded-lg bg-card border border-input flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <Select.Value />
            </Select.Trigger>
            <Select.Portal>
              <Select.Content className="glass rounded-lg p-1">
                <Select.Item value="last7days" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                  <Select.ItemText>Last 7 days</Select.ItemText>
                </Select.Item>
                <Select.Item value="last30days" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                  <Select.ItemText>Last 30 days</Select.ItemText>
                </Select.Item>
                <Select.Item value="last90days" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                  <Select.ItemText>Last 90 days</Select.ItemText>
                </Select.Item>
              </Select.Content>
            </Select.Portal>
          </Select.Root>
          <button className="p-2 rounded-lg hover:bg-accent transition-colors">
            <Download className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-depth p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <Users className="h-8 w-8 text-primary" />
            <TrendingUp className="h-4 w-4 text-green-500" />
          </div>
          <p className="text-2xl font-bold">{learnerMetrics.totalLearners.toLocaleString()}</p>
          <p className="text-sm text-muted-foreground">Total Learners</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-depth p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <Brain className="h-8 w-8 text-purple-500" />
            <span className="text-sm text-green-500">+12%</span>
          </div>
          <p className="text-2xl font-bold">{learnerMetrics.activeLearners.toLocaleString()}</p>
          <p className="text-sm text-muted-foreground">Active Learners</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-depth p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <Award className="h-8 w-8 text-yellow-500" />
            <span className="text-sm text-green-500">+5.2%</span>
          </div>
          <p className="text-2xl font-bold">{learnerMetrics.averageScore}%</p>
          <p className="text-sm text-muted-foreground">Average Score</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card-depth p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <Clock className="h-8 w-8 text-green-500" />
            <span className="text-sm text-green-500">+8.7%</span>
          </div>
          <p className="text-2xl font-bold">{learnerMetrics.completionRate}%</p>
          <p className="text-sm text-muted-foreground">Completion Rate</p>
        </motion.div>
      </div>

      {/* Analytics Tabs */}
      <Tabs.Root defaultValue="learning" className="space-y-6">
        <Tabs.List className="flex items-center space-x-4 border-b border-border pb-2">
          <Tabs.Trigger
            value="learning"
            className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
          >
            Learning Analytics
          </Tabs.Trigger>
          <Tabs.Trigger
            value="content"
            className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
          >
            Content Performance
          </Tabs.Trigger>
          <Tabs.Trigger
            value="agents"
            className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
          >
            Agent Analytics
          </Tabs.Trigger>
          <Tabs.Trigger
            value="system"
            className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
          >
            System Metrics
          </Tabs.Trigger>
        </Tabs.List>

        {/* Learning Analytics Tab */}
        <Tabs.Content value="learning" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card-depth p-6">
              <h3 className="text-lg font-semibold mb-4">Learning Progress Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={learningProgressData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis dataKey="date" stroke="#9CA3AF" fontSize={12} />
                  <YAxis stroke="#9CA3AF" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(17, 24, 39, 0.8)', 
                      border: '1px solid #374151',
                      backdropFilter: 'blur(10px)'
                    }} 
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="completionRate"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    name="Completion Rate %"
                  />
                  <Line
                    type="monotone"
                    dataKey="engagementRate"
                    stroke="#8B5CF6"
                    strokeWidth={2}
                    name="Engagement Rate %"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card-depth p-6">
              <h3 className="text-lg font-semibold mb-4">Content Effectiveness</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={contentEffectiveness}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis dataKey="name" stroke="#9CA3AF" fontSize={12} />
                  <YAxis stroke="#9CA3AF" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(17, 24, 39, 0.8)', 
                      border: '1px solid #374151',
                      backdropFilter: 'blur(10px)'
                    }} 
                  />
                  <Bar dataKey="effectiveness" fill="#3B82F6" name="Effectiveness %" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Tabs.Content>

        {/* Content Performance Tab */}
        <Tabs.Content value="content" className="space-y-6">
          <div className="card-depth p-6">
            <h3 className="text-lg font-semibold mb-4">Content Generation by Type</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={contentEffectiveness}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                  label
                >
                  {contentEffectiveness.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B'][index]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Tabs.Content>

        {/* Agent Analytics Tab */}
        <Tabs.Content value="agents" className="space-y-6">
          <div className="card-depth p-6">
            <h3 className="text-lg font-semibold mb-4">Agent Utilization</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadialBarChart cx="50%" cy="50%" innerRadius="10%" outerRadius="90%" data={agentUtilization}>
                <RadialBar dataKey="value" cornerRadius={10} fill="#3B82F6" />
                <Legend />
                <Tooltip />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
        </Tabs.Content>

        {/* System Metrics Tab */}
        <Tabs.Content value="system" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card-depth p-6">
              <h4 className="text-sm font-medium mb-2">API Response Time</h4>
              <p className="text-2xl font-bold">124ms</p>
              <p className="text-xs text-muted-foreground">Average</p>
            </div>
            <div className="card-depth p-6">
              <h4 className="text-sm font-medium mb-2">System Uptime</h4>
              <p className="text-2xl font-bold">99.98%</p>
              <p className="text-xs text-muted-foreground">Last 30 days</p>
            </div>
            <div className="card-depth p-6">
              <h4 className="text-sm font-medium mb-2">Error Rate</h4>
              <p className="text-2xl font-bold">0.02%</p>
              <p className="text-xs text-muted-foreground">Last 24 hours</p>
            </div>
          </div>
        </Tabs.Content>
      </Tabs.Root>
    </div>
  )
}