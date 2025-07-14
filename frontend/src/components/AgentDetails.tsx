import { motion } from 'framer-motion'
import { X, Brain, Activity, Target, Clock, Trophy, Sparkles } from 'lucide-react'
import { cn } from '@/utils'
import type { Agent } from '@/types'
import * as Dialog from '@radix-ui/react-dialog'
import * as Tabs from '@radix-ui/react-tabs'

interface AgentDetailsProps {
  agent: Agent
  onClose: () => void
}

export default function AgentDetails({ agent, onClose }: AgentDetailsProps) {
  return (
    <Dialog.Root open onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 animate-in fade-in-0" />
        <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-2xl translate-x-[-50%] translate-y-[-50%] glass rounded-lg p-6 animate-in fade-in-0 zoom-in-95">
          <Dialog.Title className="text-xl font-semibold mb-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Brain className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h2>{agent.name}</h2>
                <p className="text-sm text-muted-foreground capitalize">{agent.type.replace('_', ' ')}</p>
              </div>
            </div>
            <Dialog.Close className="p-2 hover:bg-accent rounded-lg transition-colors">
              <X className="h-4 w-4" />
            </Dialog.Close>
          </Dialog.Title>

          <Tabs.Root defaultValue="overview" className="mt-6">
            <Tabs.List className="flex items-center space-x-4 border-b border-border pb-2">
              <Tabs.Trigger
                value="overview"
                className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
              >
                Overview
              </Tabs.Trigger>
              <Tabs.Trigger
                value="beliefs"
                className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
              >
                Beliefs & Goals
              </Tabs.Trigger>
              <Tabs.Trigger
                value="performance"
                className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
              >
                Performance
              </Tabs.Trigger>
              <Tabs.Trigger
                value="history"
                className="text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors"
              >
                History
              </Tabs.Trigger>
            </Tabs.List>

            {/* Overview Tab */}
            <Tabs.Content value="overview" className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="card-depth p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Current Status</span>
                  </div>
                  <p className="text-lg font-semibold capitalize">{agent.status}</p>
                  {agent.currentTask && (
                    <p className="text-sm text-muted-foreground mt-1">{agent.currentTask}</p>
                  )}
                </div>

                <div className="card-depth p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Trophy className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Success Rate</span>
                  </div>
                  <p className="text-lg font-semibold">
                    {(agent.performance.successRate * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {agent.performance.tasksCompleted} tasks completed
                  </p>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium mb-3">Capabilities</h3>
                <div className="space-y-3">
                  {agent.capabilities.map((capability, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">{capability.name}</span>
                        <span className="text-sm font-medium">{capability.level}%</span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
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
              </div>
            </Tabs.Content>

            {/* Beliefs & Goals Tab */}
            <Tabs.Content value="beliefs" className="mt-4 space-y-4">
              <div>
                <h3 className="text-sm font-medium mb-3">Current Goals</h3>
                <div className="space-y-2">
                  {agent.goals.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No active goals</p>
                  ) : (
                    agent.goals.map((goal) => (
                      <div key={goal.id} className="card-depth p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <Target className="h-4 w-4 text-primary" />
                            <span className="text-sm font-medium">{goal.description}</span>
                          </div>
                          <span className={cn(
                            "text-xs px-2 py-1 rounded-full",
                            goal.status === 'completed' ? 'bg-green-500/20 text-green-500' :
                            goal.status === 'active' ? 'bg-blue-500/20 text-blue-500' :
                            goal.status === 'failed' ? 'bg-red-500/20 text-red-500' :
                            'bg-gray-500/20 text-gray-500'
                          )}>
                            {goal.status}
                          </span>
                        </div>
                        <div className="mt-2">
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${goal.progress}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium mb-3">Recent Beliefs</h3>
                <div className="space-y-2">
                  {agent.beliefs.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No recorded beliefs</p>
                  ) : (
                    agent.beliefs.slice(0, 3).map((belief) => (
                      <div key={belief.id} className="card-depth p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-muted-foreground">{belief.source}</span>
                          <span className="text-xs text-muted-foreground">
                            Confidence: {(belief.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-sm">{JSON.stringify(belief.content)}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </Tabs.Content>

            {/* Performance Tab */}
            <Tabs.Content value="performance" className="mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="card-depth p-4">
                  <h4 className="text-sm font-medium mb-2">Average Processing Time</h4>
                  <p className="text-2xl font-bold">{agent.performance.averageTime}s</p>
                </div>
                <div className="card-depth p-4">
                  <h4 className="text-sm font-medium mb-2">Quality Score</h4>
                  <p className="text-2xl font-bold">
                    {(agent.performance.qualityScore * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="card-depth p-4">
                  <h4 className="text-sm font-medium mb-2">Total Tasks</h4>
                  <p className="text-2xl font-bold">{agent.performance.tasksCompleted}</p>
                </div>
                <div className="card-depth p-4">
                  <h4 className="text-sm font-medium mb-2">Success Rate</h4>
                  <p className="text-2xl font-bold">
                    {(agent.performance.successRate * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </Tabs.Content>

            {/* History Tab */}
            <Tabs.Content value="history" className="mt-4">
              <p className="text-sm text-muted-foreground">Task history coming soon...</p>
            </Tabs.Content>
          </Tabs.Root>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}