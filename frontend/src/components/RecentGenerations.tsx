import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, Clock, Sparkles, CheckCircle, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { cn } from '@/utils'
import type { GenerationRequest, GenerationStatus } from '@/types'

// Mock data for recent generations
const mockGenerations: GenerationRequest[] = [
  {
    id: '1',
    sourceFile: new File([''], 'AWS-SAA-Guide.pdf'),
    targetAudience: {
      level: 'intermediate',
      priorKnowledge: ['Basic AWS', 'Networking'],
      learningStyle: 'visual',
      timeAvailable: 120,
    },
    outputFormats: ['video', 'interactive'],
    constraints: {
      maxDuration: 30,
      accessibility: ['captions', 'high_contrast'],
      style: 'formal',
      includeAssessments: true,
    },
    status: 'completed',
    progress: 100,
    startedAt: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
    completedAt: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
  },
  {
    id: '2',
    sourceText: 'Introduction to Machine Learning concepts...',
    targetAudience: {
      level: 'beginner',
      priorKnowledge: ['Python basics'],
      learningStyle: 'kinesthetic',
    },
    outputFormats: ['interactive', 'assessment'],
    constraints: {
      accessibility: ['screen_reader'],
      style: 'casual',
      includeAssessments: true,
    },
    status: 'generating',
    progress: 67,
    startedAt: new Date(Date.now() - 1000 * 60 * 8),
  },
  {
    id: '3',
    sourceFile: new File([''], 'Kubernetes-Deep-Dive.pdf'),
    targetAudience: {
      level: 'advanced',
      priorKnowledge: ['Docker', 'Container orchestration'],
      learningStyle: 'reading',
    },
    outputFormats: ['pdf', 'slides'],
    constraints: {
      accessibility: ['captions'],
      style: 'formal',
      includeAssessments: false,
    },
    status: 'quality_check',
    progress: 85,
    startedAt: new Date(Date.now() - 1000 * 60 * 25),
  },
]

const statusIcons: Record<GenerationStatus, any> = {
  pending: AlertCircle,
  analyzing: FileText,
  planning: Sparkles,
  generating: Sparkles,
  quality_check: CheckCircle,
  completed: CheckCircle,
  failed: AlertCircle,
}

const statusColors: Record<GenerationStatus, string> = {
  pending: 'text-gray-500',
  analyzing: 'text-blue-500',
  planning: 'text-purple-500',
  generating: 'text-yellow-500',
  quality_check: 'text-orange-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
}

export default function RecentGenerations() {
  const [generations, setGenerations] = useState(mockGenerations)

  // Simulate progress updates
  useEffect(() => {
    const interval = setInterval(() => {
      setGenerations(prev => prev.map(gen => {
        if (gen.status === 'generating' && gen.progress < 100) {
          return { ...gen, progress: Math.min(gen.progress + 5, 100) }
        }
        if (gen.status === 'quality_check' && gen.progress < 100) {
          return { ...gen, progress: Math.min(gen.progress + 2, 100) }
        }
        return gen
      }))
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="card-depth p-6">
      <h3 className="text-lg font-semibold mb-4">Recent Generations</h3>
      <div className="space-y-4">
        {generations.map((generation, index) => {
          const StatusIcon = statusIcons[generation.status]
          const fileName = generation.sourceFile?.name || 'Text Input'
          
          return (
            <motion.div
              key={generation.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-start space-x-3">
                  <div className={cn('mt-0.5', statusColors[generation.status])}>
                    <StatusIcon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{fileName}</p>
                    <p className="text-xs text-muted-foreground">
                      {generation.targetAudience.level} • {generation.outputFormats.join(', ')}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">
                    {formatDistanceToNow(generation.startedAt, { addSuffix: true })}
                  </p>
                  {generation.completedAt && (
                    <p className="text-xs text-green-500">
                      Completed
                    </p>
                  )}
                </div>
              </div>
              
              {/* Progress bar */}
              {generation.status !== 'completed' && generation.status !== 'failed' && (
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground capitalize">
                      {generation.status.replace('_', ' ')}
                    </span>
                    <span className="text-xs font-medium">{generation.progress}%</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-primary rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${generation.progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}