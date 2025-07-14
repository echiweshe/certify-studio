import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, ArrowRight, Zap } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { cn } from '@/utils'

interface Message {
  id: string
  from: string
  to: string
  type: 'request' | 'response' | 'broadcast' | 'collaboration'
  content: string
  timestamp: Date
}

// Mock messages
const mockMessages: Message[] = [
  {
    id: '1',
    from: 'Domain Explorer',
    to: 'Cognitive Optimizer',
    type: 'request',
    content: 'Extracted 15 concepts from AWS guide. Need cognitive load analysis.',
    timestamp: new Date(Date.now() - 1000 * 60 * 2),
  },
  {
    id: '2',
    from: 'Cognitive Optimizer',
    to: 'Domain Explorer',
    type: 'response',
    content: 'Analysis complete. Recommended learning path: EC2 → VPC → S3 → IAM.',
    timestamp: new Date(Date.now() - 1000 * 60 * 1.5),
  },
  {
    id: '3',
    from: 'Visual Maestro',
    to: 'All Agents',
    type: 'broadcast',
    content: 'Animation rendering at 67%. Need component suggestions for cloud architecture.',
    timestamp: new Date(Date.now() - 1000 * 30),
  },
]

const messageTypeColors = {
  request: 'border-blue-500 bg-blue-500/10',
  response: 'border-green-500 bg-green-500/10',
  broadcast: 'border-purple-500 bg-purple-500/10',
  collaboration: 'border-yellow-500 bg-yellow-500/10',
}

export default function MessageFlow() {
  const [messages, setMessages] = useState(mockMessages)
  const [autoScroll, setAutoScroll] = useState(true)

  // Simulate new messages
  useEffect(() => {
    const interval = setInterval(() => {
      const agents = ['Domain Explorer', 'Cognitive Optimizer', 'Visual Maestro', 'Quality Guardian']
      const types: Message['type'][] = ['request', 'response', 'broadcast', 'collaboration']
      const contents = [
        'Processing new concept relationships',
        'Optimizing learning sequence',
        'Rendering animation frame',
        'Quality check passed',
        'Collaboration request accepted',
      ]

      const newMessage: Message = {
        id: Date.now().toString(),
        from: agents[Math.floor(Math.random() * agents.length)],
        to: Math.random() > 0.7 ? 'All Agents' : agents[Math.floor(Math.random() * agents.length)],
        type: types[Math.floor(Math.random() * types.length)],
        content: contents[Math.floor(Math.random() * contents.length)],
        timestamp: new Date(),
      }

      setMessages(prev => [...prev.slice(-9), newMessage])
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="card-depth p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center space-x-2">
          <MessageSquare className="h-5 w-5" />
          <span>Message Flow</span>
        </h3>
        <button
          onClick={() => setAutoScroll(!autoScroll)}
          className={cn(
            "text-xs px-2 py-1 rounded-md transition-colors",
            autoScroll ? "bg-primary text-primary-foreground" : "bg-muted"
          )}
        >
          Auto-scroll
        </button>
      </div>

      <div className="space-y-2 max-h-[300px] overflow-y-auto smooth-scrollbar">
        <AnimatePresence initial={false}>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className={cn(
                "p-3 rounded-lg border",
                messageTypeColors[message.type]
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2 text-xs">
                  <span className="font-medium">{message.from}</span>
                  <ArrowRight className="h-3 w-3" />
                  <span className="font-medium">{message.to}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatDistanceToNow(message.timestamp, { addSuffix: true })}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">{message.content}</p>
              {message.type === 'broadcast' && (
                <Zap className="h-3 w-3 text-yellow-500 mt-1" />
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Message flow indicator */}
      <div className="mt-4 relative h-2 bg-muted rounded-full overflow-hidden">
        <div className="absolute inset-0 message-flow" />
      </div>
    </div>
  )
}