import { motion } from 'framer-motion'
import { Brain, Zap, Clock, Trophy } from 'lucide-react'
import { cn } from '@/utils'
import type { Agent, AgentStatus } from '@/types'

interface AgentCardProps {
  agent: Agent
}

const statusColors: Record<AgentStatus, string> = {
  idle: 'border-gray-500',
  thinking: 'border-yellow-500',
  planning: 'border-blue-500',
  executing: 'border-green-500',
  collaborating: 'border-purple-500',
  learning: 'border-pink-500',
  error: 'border-red-500',
}

const statusBgColors: Record<AgentStatus, string> = {
  idle: 'bg-gray-500/10',
  thinking: 'bg-yellow-500/10',
  planning: 'bg-blue-500/10',
  executing: 'bg-green-500/10',
  collaborating: 'bg-purple-500/10',
  learning: 'bg-pink-500/10',
  error: 'bg-red-500/10',
}

export default function AgentCard({ agent }: AgentCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        'card-depth p-6 border-2 transition-all duration-300',
        statusColors[agent.status],
        agent.status !== 'idle' && 'shadow-lg'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={cn('h-10 w-10 rounded-lg flex items-center justify-center', statusBgColors[agent.status])}>
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold">{agent.name}</h3>
            <p className="text-sm text-muted-foreground capitalize">{agent.status}</p>
          </div>
        </div>
        {agent.status !== 'idle' && (
          <div className="relative">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
            <div className="absolute inset-0 h-2 w-2 bg-green-500 rounded-full animate-ping" />
          </div>
        )}
      </div>

      {/* Current Task */}
      {agent.currentTask && (
        <div className="mb-4 p-3 rounded-lg bg-muted/50">
          <div className="flex items-center space-x-2 mb-1">
            <Zap className="h-3 w-3 text-yellow-500" />
            <span className="text-xs font-medium">Current Task</span>
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2">{agent.currentTask}</p>
        </div>
      )}

      {/* Capabilities */}
      <div className="space-y-2 mb-4">
        {agent.capabilities.slice(0, 2).map((capability, index) => (
          <div key={index}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">{capability.name}</span>
              <span className="text-xs font-medium">{capability.level}%</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${capability.level}%` }}
                transition={{ duration: 1, delay: index * 0.1 }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Performance Stats */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="flex items-center space-x-2">
          <Clock className="h-3 w-3 text-muted-foreground" />
          <span>{agent.performance.averageTime}s avg</span>
        </div>
        <div className="flex items-center space-x-2">
          <Trophy className="h-3 w-3 text-muted-foreground" />
          <span>{(agent.performance.successRate * 100).toFixed(0)}% success</span>
        </div>
      </div>
    </motion.div>
  )
}