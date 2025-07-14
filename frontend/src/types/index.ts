// Agent Types
export interface Agent {
  id: string
  name: string
  type: AgentType
  status: AgentStatus
  capabilities: AgentCapability[]
  currentTask?: string
  performance: AgentPerformance
  beliefs: AgentBelief[]
  goals: AgentGoal[]
  lastActivity: Date
}

export enum AgentType {
  DOMAIN_EXTRACTOR = 'domain_extractor',
  COGNITIVE_LOAD_MANAGER = 'cognitive_load_manager',
  ANIMATION_CHOREOGRAPHER = 'animation_choreographer',
  COMPONENT_ASSEMBLER = 'component_assembler',
  QUALITY_ASSURANCE = 'quality_assurance',
  PEDAGOGICAL_STRATEGIST = 'pedagogical_strategist',
  MULTIMODAL_SYNTHESIZER = 'multimodal_synthesizer'
}

export enum AgentStatus {
  IDLE = 'idle',
  THINKING = 'thinking',
  PLANNING = 'planning',
  EXECUTING = 'executing',
  COLLABORATING = 'collaborating',
  LEARNING = 'learning',
  ERROR = 'error'
}

export interface AgentCapability {
  name: string
  level: number // 0-100
}

export interface AgentPerformance {
  tasksCompleted: number
  averageTime: number
  successRate: number
  qualityScore: number
}

export interface AgentBelief {
  id: string
  content: any
  confidence: number
  source: string
  timestamp: Date
}

export interface AgentGoal {
  id: string
  description: string
  priority: number
  deadline?: Date
  progress: number
  status: 'pending' | 'active' | 'completed' | 'failed'
}

// Learning Models
export interface Concept {
  id: string
  name: string
  type: ConceptType
  description: string
  prerequisites: string[]
  difficulty: number
  cognitiveLoad: CognitiveLoadProfile
  teachingPatterns: TeachingPattern[]
}

export enum ConceptType {
  FUNDAMENTAL = 'fundamental',
  PROCEDURAL = 'procedural',
  CONCEPTUAL = 'conceptual',
  METACOGNITIVE = 'metacognitive'
}

export interface CognitiveLoadProfile {
  intrinsic: number
  extraneous: number
  germane: number
  total: number
  optimizationStrategies: string[]
}

export interface TeachingPattern {
  id: string
  name: string
  effectiveness: number
  applicableTo: ConceptType[]
  description: string
}

// Generation Models
export interface GenerationRequest {
  id: string
  sourceFile?: File
  sourceText?: string
  targetAudience: AudienceProfile
  outputFormats: OutputFormat[]
  constraints: GenerationConstraints
  status: GenerationStatus
  progress: number
  startedAt?: Date
  completedAt?: Date
}

export interface AudienceProfile {
  level: 'beginner' | 'intermediate' | 'advanced'
  priorKnowledge: string[]
  learningStyle?: 'visual' | 'auditory' | 'kinesthetic' | 'reading'
  timeAvailable?: number // in minutes
}

export enum OutputFormat {
  VIDEO = 'video',
  INTERACTIVE = 'interactive',
  PDF = 'pdf',
  SLIDES = 'slides',
  VR = 'vr',
  ASSESSMENT = 'assessment'
}

export interface GenerationConstraints {
  maxDuration?: number
  accessibility: AccessibilityRequirement[]
  style?: 'formal' | 'casual' | 'playful'
  includeAssessments: boolean
}

export enum AccessibilityRequirement {
  CAPTIONS = 'captions',
  AUDIO_DESCRIPTION = 'audio_description',
  HIGH_CONTRAST = 'high_contrast',
  KEYBOARD_NAVIGATION = 'keyboard_navigation',
  SCREEN_READER = 'screen_reader'
}

export enum GenerationStatus {
  PENDING = 'pending',
  ANALYZING = 'analyzing',
  PLANNING = 'planning',
  GENERATING = 'generating',
  QUALITY_CHECK = 'quality_check',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// Knowledge Graph Types
export interface KnowledgeNode {
  id: string
  label: string
  type: 'concept' | 'skill' | 'topic' | 'prerequisite'
  properties: Record<string, any>
  x?: number
  y?: number
}

export interface KnowledgeEdge {
  id: string
  source: string
  target: string
  type: 'requires' | 'relates_to' | 'builds_on' | 'contrasts_with'
  weight: number
  properties?: Record<string, any>
}

export interface KnowledgeGraphData {
  nodes: KnowledgeNode[]
  edges: KnowledgeEdge[]
}

// Analytics Types
export interface PlatformMetrics {
  totalGenerations: number
  activeUsers: number
  averageQualityScore: number
  systemHealth: number
  agentUtilization: number
  revenueToday: number
}

export interface LearningAnalytics {
  engagementRate: number
  completionRate: number
  averageTimeToMastery: number
  conceptRetention: number
  learnerSatisfaction: number
}

export interface AgentAnalytics {
  agentType: AgentType
  tasksCompleted: number
  averageProcessingTime: number
  errorRate: number
  collaborationScore: number
  resourceUsage: number
}

// User Types
export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  organization?: string
  preferences: UserPreferences
  createdAt: Date
  lastLogin: Date
}

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  CONTENT_CREATOR = 'content_creator',
  REVIEWER = 'reviewer',
  VIEWER = 'viewer',
  API_USER = 'api_user'
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  notifications: NotificationPreferences
}

export interface NotificationPreferences {
  email: boolean
  push: boolean
  generationComplete: boolean
  qualityAlerts: boolean
  systemUpdates: boolean
}

// API Types
export interface ApiResponse<T> {
  data: T
  status: 'success' | 'error'
  message?: string
  timestamp: Date
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// WebSocket Types
export interface WebSocketMessage {
  type: WebSocketMessageType
  payload: any
  timestamp: Date
}

export enum WebSocketMessageType {
  AGENT_STATUS_UPDATE = 'agent_status_update',
  GENERATION_PROGRESS = 'generation_progress',
  SYSTEM_NOTIFICATION = 'system_notification',
  COLLABORATION_EVENT = 'collaboration_event',
  METRIC_UPDATE = 'metric_update'
}

// Component Types
export interface AnimationComponent {
  id: string
  name: string
  type: ComponentType
  preview: string
  duration: number
  cognitiveLoad: number
  tags: string[]
  usage: number
}

export enum ComponentType {
  SERVICE = 'service',
  FLOW = 'flow',
  CONCEPTUAL = 'conceptual',
  INTERACTIVE = 'interactive',
  ASSESSMENT = 'assessment'
}
