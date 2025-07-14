import { motion } from 'framer-motion'
import { Download, Eye, Share2, CheckCircle } from 'lucide-react'
import type { OutputFormat } from '@/types'

interface OutputPreviewProps {
  formats: OutputFormat[]
}

const formatDetails: Record<OutputFormat, { size: string; ready: boolean }> = {
  video: { size: '245 MB', ready: true },
  interactive: { size: '12 MB', ready: true },
  pdf: { size: '3.2 MB', ready: true },
  slides: { size: '8.5 MB', ready: false },
  vr: { size: '156 MB', ready: false },
  assessment: { size: '1.1 MB', ready: true },
}

export default function OutputPreview({ formats }: OutputPreviewProps) {
  return (
    <div className="card-depth p-6">
      <h3 className="text-lg font-semibold mb-4">Generated Content</h3>
      
      <div className="space-y-3">
        {formats.map((format, index) => {
          const details = formatDetails[format]
          
          return (
            <motion.div
              key={format}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <CheckCircle className={details.ready ? "h-4 w-4 text-green-500" : "h-4 w-4 text-gray-500"} />
                  <span className="font-medium capitalize">{format}</span>
                </div>
                <span className="text-sm text-muted-foreground">{details.size}</span>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  disabled={!details.ready}
                  className="flex items-center space-x-1 text-sm px-3 py-1 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Eye className="h-3 w-3" />
                  <span>Preview</span>
                </button>
                <button
                  disabled={!details.ready}
                  className="flex items-center space-x-1 text-sm px-3 py-1 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="h-3 w-3" />
                  <span>Download</span>
                </button>
                <button
                  disabled={!details.ready}
                  className="flex items-center space-x-1 text-sm px-3 py-1 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Share2 className="h-3 w-3" />
                  <span>Share</span>
                </button>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Quality report */}
      <div className="mt-6 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
        <div className="flex items-start space-x-3">
          <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
          <div>
            <p className="font-medium text-sm">Quality Check Passed</p>
            <p className="text-xs text-muted-foreground mt-1">
              Pedagogical score: 94% • Accessibility: 100% • Accuracy: 98%
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}