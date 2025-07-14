import { useState } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Upload,
  FileText,
  Sparkles,
  Settings2,
  Play,
  Download,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  Book,
  Video,
  FileCode,
  Presentation,
  Gamepad2,
  TestTube,
} from 'lucide-react'
import { cn, formatBytes } from '@/utils'
import type { GenerationRequest, OutputFormat } from '@/types'
import * as Slider from '@radix-ui/react-slider'
import * as Switch from '@radix-ui/react-switch'
import * as Select from '@radix-ui/react-select'
import GenerationProgress from '@/components/GenerationProgress'
import OutputPreview from '@/components/OutputPreview'

const outputFormatIcons = {
  video: Video,
  interactive: FileCode,
  pdf: FileText,
  slides: Presentation,
  vr: Gamepad2,
  assessment: TestTube,
}

export default function ContentGeneration() {
  const [file, setFile] = useState<File | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [selectedFormats, setSelectedFormats] = useState<OutputFormat[]>(['video'])
  const [audienceLevel, setAudienceLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('intermediate')
  const [includeAssessments, setIncludeAssessments] = useState(true)
  const [maxDuration, setMaxDuration] = useState(30)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0])
      }
    },
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  })

  const handleGenerate = () => {
    setIsGenerating(true)
    setGenerationProgress(0)

    // Simulate generation progress
    const interval = setInterval(() => {
      setGenerationProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsGenerating(false)
          return 100
        }
        return prev + 2
      })
    }, 500)
  }

  const toggleFormat = (format: OutputFormat) => {
    setSelectedFormats(prev =>
      prev.includes(format)
        ? prev.filter(f => f !== format)
        : [...prev, format]
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Content Generation</h1>
        <p className="text-muted-foreground mt-1">
          Transform your content into engaging, multi-format learning experiences
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - Input and settings */}
        <div className="lg:col-span-2 space-y-6">
          {/* File upload */}
          <div className="card-depth p-6">
            <h2 className="text-lg font-semibold mb-4">Source Content</h2>
            
            {!file ? (
              <div
                {...getRootProps()}
                className={cn(
                  "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                  isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                )}
              >
                <input {...getInputProps()} />
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">
                  {isDragActive ? "Drop your file here" : "Drag & drop or click to upload"}
                </p>
                <p className="text-sm text-muted-foreground">
                  Supports PDF, TXT, and DOCX files up to 50MB
                </p>
              </div>
            ) : (
              <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                <div className="flex items-center space-x-3">
                  <FileText className="h-8 w-8 text-primary" />
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">{formatBytes(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="text-sm text-destructive hover:underline"
                >
                  Remove
                </button>
              </div>
            )}
          </div>

          {/* Output formats */}
          <div className="card-depth p-6">
            <h2 className="text-lg font-semibold mb-4">Output Formats</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {(Object.keys(outputFormatIcons) as OutputFormat[]).map(format => {
                const Icon = outputFormatIcons[format]
                const isSelected = selectedFormats.includes(format)
                
                return (
                  <button
                    key={format}
                    onClick={() => toggleFormat(format)}
                    className={cn(
                      "p-4 rounded-lg border-2 transition-all",
                      isSelected
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <Icon className={cn(
                      "h-6 w-6 mb-2 mx-auto",
                      isSelected ? "text-primary" : "text-muted-foreground"
                    )} />
                    <p className="text-sm font-medium capitalize">{format}</p>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Generation settings */}
          <div className="card-depth p-6">
            <h2 className="text-lg font-semibold mb-4">Generation Settings</h2>
            <div className="space-y-6">
              {/* Audience level */}
              <div>
                <label className="text-sm font-medium mb-2 block">Audience Level</label>
                <Select.Root value={audienceLevel} onValueChange={(value: any) => setAudienceLevel(value)}>
                  <Select.Trigger className="w-full px-3 py-2 rounded-lg bg-card border border-input flex items-center justify-between">
                    <Select.Value />
                    <Select.Icon>
                      <Settings2 className="h-4 w-4" />
                    </Select.Icon>
                  </Select.Trigger>
                  <Select.Portal>
                    <Select.Content className="glass rounded-lg p-1">
                      <Select.Item value="beginner" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                        <Select.ItemText>Beginner</Select.ItemText>
                      </Select.Item>
                      <Select.Item value="intermediate" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                        <Select.ItemText>Intermediate</Select.ItemText>
                      </Select.Item>
                      <Select.Item value="advanced" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                        <Select.ItemText>Advanced</Select.ItemText>
                      </Select.Item>
                    </Select.Content>
                  </Select.Portal>
                </Select.Root>
              </div>

              {/* Max duration */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Maximum Duration: {maxDuration} minutes
                </label>
                <Slider.Root
                  value={[maxDuration]}
                  onValueChange={([value]) => setMaxDuration(value)}
                  max={120}
                  min={5}
                  step={5}
                  className="relative flex items-center select-none touch-none w-full h-5"
                >
                  <Slider.Track className="bg-muted relative grow rounded-full h-2">
                    <Slider.Range className="absolute bg-primary rounded-full h-full" />
                  </Slider.Track>
                  <Slider.Thumb className="block w-5 h-5 bg-primary rounded-full hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary" />
                </Slider.Root>
              </div>

              {/* Include assessments */}
              <div className="flex items-center justify-between">
                <label htmlFor="assessments" className="text-sm font-medium">
                  Include Assessments
                </label>
                <Switch.Root
                  id="assessments"
                  checked={includeAssessments}
                  onCheckedChange={setIncludeAssessments}
                  className="w-11 h-6 bg-muted rounded-full relative data-[state=checked]:bg-primary transition-colors"
                >
                  <Switch.Thumb className="block w-5 h-5 bg-white rounded-full transition-transform translate-x-0.5 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>
            </div>
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={!file || selectedFormats.length === 0 || isGenerating}
            className={cn(
              "w-full py-3 rounded-lg font-medium transition-all",
              "bg-primary text-primary-foreground hover:bg-primary/90",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "flex items-center justify-center space-x-2"
            )}
          >
            {isGenerating ? (
              <>
                <div className="h-5 w-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                <span>Generate Content</span>
              </>
            )}
          </button>
        </div>

        {/* Right column - Progress and preview */}
        <div className="space-y-6">
          {/* Generation progress */}
          {isGenerating && (
            <GenerationProgress progress={generationProgress} />
          )}

          {/* Output preview */}
          {generationProgress === 100 && (
            <OutputPreview formats={selectedFormats} />
          )}

          {/* Tips */}
          <div className="card-depth p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              <span>Pro Tips</span>
            </h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start space-x-2">
                <span className="text-primary">•</span>
                <span>Well-structured content with clear headings generates better results</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-primary">•</span>
                <span>Include examples and use cases for more engaging content</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-primary">•</span>
                <span>Shorter content (under 50 pages) processes faster</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}