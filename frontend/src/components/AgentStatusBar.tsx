import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Brain, Zap } from 'lucide-react'
import { cn } from '@/utils'
import type { Agent, AgentStatus } from '@/types'
import { useAgentStore } from '@/stores/agentStore'

const statusColors: Record<AgentStatus, string> = {
  idle: 'bg-gray-500',
  thinking: 'bg-yellow-500',
  planning: 'bg-blue-500',
  executing: 'bg-green-500',
  collaborating: 'bg-purple-500',
  learning: 'bg-pink-500',
  error: 'bg-red-500',
}

const statusAnimations: Record<AgentStatus, string> = {
  idle: '',
  thinking: 'animate-pulse',
  planning: 'animate-pulse',
  executing: 'animate-spin-slow',
  collaborating: 'animate-bounce-slow',
  learning: 'animate-pulse-slow',
  error: 'animate-pulse',
}

export default function AgentStatusBar() {
  const { agents, activeAgents } = useAgentStore()
  const [expanded, setExpanded] = useState(false)

  const totalAgents = agents.length
  const idleAgents = agents.filter(a => a.status === 'idle').length
  const workingAgents = totalAgents - idleAgents

  return (
    <div className="space-y-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left space-y-2"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Agent Pool</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-muted-foreground">
              {workingAgents}/{totalAgents} active
            </span>
            <Activity className={cn(
              "h-3 w-3",
              workingAgents > 0 ? "text-green-500" : "text-gray-500"
            )} />
          </div>
        </div>
        
        {/* Agent activity bar */}
        <div className="relative h-2 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-green-500 to-blue-500"
            initial={{ width: 0 }}
            animate={{ width: `${(workingAgents / totalAgents) * 100}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
          {workingAgents > 0 && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          )}
        </div>
      </button>

      {/* Expanded agent list */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-1 overflow-hidden"
          >
            {activeAgents.map((agent) => (
              <div
                key={agent.id}
                className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
              >
                <div className="flex items-center space-x-2">
                  <div className={cn(
                    "h-2 w-2 rounded-full",
                    statusColors[agent.status],
                    statusAnimations[agent.status]
                  )} />
                  <span className="text-xs font-medium truncate max-w-[120px]">
                    {agent.name}
                  </span>
                </div>
                {agent.currentTask && (
                  <Zap className="h-3 w-3 text-yellow-500" />
                )}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}