import { motion } from 'framer-motion'
import { Clock, Brain, Sparkles, CheckCircle, Zap } from 'lucide-react'
import { cn } from '@/utils'

interface GenerationProgressProps {
  progress: number
}

const stages = [
  { name: 'Analyzing', icon: Brain, threshold: 20 },
  { name: 'Planning', icon: Clock, threshold: 40 },
  { name: 'Generating', icon: Sparkles, threshold: 80 },
  { name: 'Quality Check', icon: CheckCircle, threshold: 100 },
]

export default function GenerationProgress({ progress }: GenerationProgressProps) {
  const currentStage = stages.findIndex(stage => progress <= stage.threshold)

  return (
    <div className="card-depth p-6">
      <h3 className="text-lg font-semibold mb-4">Generation Progress</h3>
      
      {/* Overall progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Overall Progress</span>
          <span className="text-sm font-medium">{progress}%</span>
        </div>
        <div className="h-3 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          >
            <div className="h-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          </motion.div>
        </div>
      </div>

      {/* Stage indicators */}
      <div className="space-y-3">
        {stages.map((stage, index) => {
          const Icon = stage.icon
          const isActive = index === currentStage
          const isComplete = progress > stage.threshold
          
          return (
            <div
              key={stage.name}
              className={cn(
                "flex items-center space-x-3 p-3 rounded-lg transition-all",
                isActive && "bg-primary/10 border border-primary",
                isComplete && "opacity-50"
              )}
            >
              <div className={cn(
                "h-8 w-8 rounded-lg flex items-center justify-center",
                isActive ? "bg-primary text-primary-foreground" : "bg-muted"
              )}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">{stage.name}</p>
                {isActive && (
                  <p className="text-xs text-muted-foreground">Processing...</p>
                )}
              </div>
              {isComplete && (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              {isActive && (
                <div className="relative">
                  <Zap className="h-4 w-4 text-yellow-500 animate-pulse" />
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Agent activity */}
      <div className="mt-6 p-3 rounded-lg bg-muted/50">
        <p className="text-xs text-muted-foreground">
          {currentStage === 0 && "Domain Extractor is analyzing your content..."}
          {currentStage === 1 && "Cognitive Load Manager is optimizing the learning path..."}
          {currentStage === 2 && "Multiple agents are collaborating to generate content..."}
          {currentStage === 3 && "Quality Assurance Agent is reviewing the output..."}
        </p>
      </div>
    </div>
  )
}