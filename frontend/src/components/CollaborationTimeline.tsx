import { useState } from 'react'
import { motion } from 'framer-motion'
import { Clock, Users, CheckCircle, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { cn } from '@/utils'

interface CollaborationEvent {
  id: string
  type: 'started' | 'completed' | 'failed' | 'milestone'
  agents: string[]
  task: string
  timestamp: Date
  duration?: number
}

const mockEvents: CollaborationEvent[] = [
  {
    id: '1',
    type: 'completed',
    agents: ['Domain Explorer', 'Cognitive Optimizer'],
    task: 'Knowledge extraction and optimization',
    timestamp: new Date(Date.now() - 1000 * 60 * 45),
    duration: 300,
  },
  {
    id: '2',
    type: 'started',
    agents: ['Visual Maestro', 'Component Builder'],
    task: 'Animation sequence generation',
    timestamp: new Date(Date.now() - 1000 * 60 * 20),
  },
  {
    id: '3',
    type: 'milestone',
    agents: ['All Agents'],
    task: 'Phase 1 complete: Content analysis',
    timestamp: new Date(Date.now() - 1000 * 60 * 10),
  },
]

const eventIcons = {
  started: Clock,
  completed: CheckCircle,
  failed: AlertCircle,
  milestone: Users,
}

const eventColors = {
  started: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  milestone: 'text-purple-500',
}

export default function CollaborationTimeline() {
  const [events] = useState(mockEvents)

  return (
    <div className="card-depth p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
        <Clock className="h-5 w-5" />
        <span>Collaboration Timeline</span>
      </h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

        {/* Events */}
        <div className="space-y-4">
          {events.map((event, index) => {
            const Icon = eventIcons[event.type]
            
            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative flex items-start"
              >
                {/* Event dot */}
                <div className="absolute left-0 h-8 w-8 rounded-full bg-background border-2 border-border flex items-center justify-center">
                  <Icon className={cn('h-4 w-4', eventColors[event.type])} />
                </div>

                {/* Event content */}
                <div className="ml-12 flex-1">
                  <div className="card-depth p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-sm">{event.task}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {event.agents.join(' + ')}
                        </p>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(event.timestamp, { addSuffix: true })}
                      </span>
                    </div>
                    {event.duration && (
                      <p className="text-xs text-muted-foreground mt-2">
                        Duration: {Math.floor(event.duration / 60)}m {event.duration % 60}s
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}