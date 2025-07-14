import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
  ConnectionMode,
  MarkerType,
} from 'react-flow-renderer'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Sphere, Box, Line } from '@react-three/drei'
import * as THREE from 'three'
import {
  Brain,
  Sparkles,
  GitBranch,
  Layers,
  Shield,
  BookOpen,
  Palette,
  Play,
  Pause,
  RotateCcw,
  Settings,
  Maximize2,
} from 'lucide-react'
import { cn } from '@/utils'
import { useAgentStore } from '@/stores/agentStore'
import type { Agent, AgentType, AgentStatus } from '@/types'
import AgentDetails from '@/components/AgentDetails'
import MessageFlow from '@/components/MessageFlow'
import CollaborationTimeline from '@/components/CollaborationTimeline'

// Agent type to icon mapping
const agentIcons: Record<AgentType, any> = {
  domain_extractor: GitBranch,
  cognitive_load_manager: Brain,
  animation_choreographer: Palette,
  component_assembler: Layers,
  quality_assurance: Shield,
  pedagogical_strategist: BookOpen,
  multimodal_synthesizer: Sparkles,
}

// Agent positions in the flow
const agentPositions: Record<string, { x: number; y: number }> = {
  '1': { x: 100, y: 200 },
  '2': { x: 300, y: 100 },
  '3': { x: 300, y: 300 },
  '4': { x: 500, y: 100 },
  '5': { x: 500, y: 300 },
  '6': { x: 700, y: 200 },
  '7': { x: 400, y: 200 },
}

const statusColors: Record<AgentStatus, string> = {
  idle: '#6B7280',
  thinking: '#F59E0B',
  planning: '#3B82F6',
  executing: '#10B981',
  collaborating: '#8B5CF6',
  learning: '#EC4899',
  error: '#EF4444',
}

export default function AgentOrchestrator() {
  const { agents, selectedAgent, selectAgent } = useAgentStore()
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d')
  const [isPlaying, setIsPlaying] = useState(true)
  const [showDetails, setShowDetails] = useState(false)

  // Convert agents to flow nodes
  const initialNodes: Node[] = agents.map((agent, index) => ({
    id: agent.id,
    type: 'custom',
    position: agentPositions[agent.id] || { x: 100 + index * 200, y: 200 },
    data: { agent },
    draggable: true,
  }))

  // Create edges based on agent collaboration
  const initialEdges: Edge[] = [
    {
      id: 'e1-2',
      source: '1',
      target: '2',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#8B5CF6', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed },
    },
    {
      id: 'e2-3',
      source: '2',
      target: '3',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#8B5CF6', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed },
    },
  ]

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Custom node component
  const CustomNode = ({ data }: { data: { agent: Agent } }) => {
    const { agent } = data
    const Icon = agentIcons[agent.type]
    const isActive = agent.status !== 'idle'
    const isSelected = selectedAgent?.id === agent.id

    return (
      <motion.div
        className={cn(
          'relative p-4 rounded-lg border-2 bg-card cursor-pointer',
          'transition-all duration-300 hover:shadow-lg',
          isSelected && 'ring-2 ring-primary ring-offset-2',
          isActive && 'shadow-lg'
        )}
        style={{ borderColor: statusColors[agent.status] }}
        onClick={() => {
          selectAgent(agent)
          setShowDetails(true)
        }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {/* Status indicator */}
        {isActive && (
          <div className="absolute -top-2 -right-2">
            <div className="relative">
              <div
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: statusColors[agent.status] }}
              />
              <div
                className="absolute inset-0 h-3 w-3 rounded-full animate-ping"
                style={{ backgroundColor: statusColors[agent.status] }}
              />
            </div>
          </div>
        )}

        <div className="flex items-center space-x-3">
          <div
            className="h-10 w-10 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${statusColors[agent.status]}20` }}
          >
            <Icon className="h-5 w-5" style={{ color: statusColors[agent.status] }} />
          </div>
          <div>
            <p className="font-medium text-sm">{agent.name}</p>
            <p className="text-xs text-muted-foreground capitalize">{agent.status}</p>
          </div>
        </div>

        {agent.currentTask && (
          <div className="mt-2 text-xs text-muted-foreground line-clamp-1">
            {agent.currentTask}
          </div>
        )}
      </motion.div>
    )
  }

  const nodeTypes = {
    custom: CustomNode,
  }

  // 3D Visualization Component
  const AgentNetwork3D = () => {
    return (
      <Canvas camera={{ position: [0, 0, 15], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
        
        {agents.map((agent, index) => {
          const angle = (index / agents.length) * Math.PI * 2
          const radius = 5
          const x = Math.cos(angle) * radius
          const z = Math.sin(angle) * radius
          const y = agent.status === 'idle' ? 0 : Math.random() * 2 - 1

          return (
            <group key={agent.id} position={[x, y, z]}>
              <Sphere args={[0.5, 32, 32]} onClick={() => selectAgent(agent)}>
                <meshStandardMaterial color={statusColors[agent.status]} />
              </Sphere>
              {agent.status !== 'idle' && (
                <Box args={[0.2, 0.2, 0.2]} position={[0, 1, 0]}>
                  <meshStandardMaterial
                    color={statusColors[agent.status]}
                    emissive={statusColors[agent.status]}
                    emissiveIntensity={0.5}
                  />
                </Box>
              )}
            </group>
          )
        })}

        {/* Connection lines */}
        {agents.map((agent, i) => {
          if (agent.status === 'collaborating' && i < agents.length - 1) {
            const angle1 = (i / agents.length) * Math.PI * 2
            const angle2 = ((i + 1) / agents.length) * Math.PI * 2
            const points = [
              new THREE.Vector3(Math.cos(angle1) * 5, 0, Math.sin(angle1) * 5),
              new THREE.Vector3(Math.cos(angle2) * 5, 0, Math.sin(angle2) * 5),
            ]
            return (
              <Line
                key={`line-${i}`}
                points={points}
                color="#8B5CF6"
                lineWidth={2}
                dashed
                dashScale={5}
              />
            )
          }
          return null
        })}
      </Canvas>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agent Orchestrator</h1>
          <p className="text-muted-foreground mt-1">
            Real-time visualization of agent collaboration and workflow
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 rounded-lg hover:bg-accent transition-colors"
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </button>
            <button className="p-2 rounded-lg hover:bg-accent transition-colors">
              <RotateCcw className="h-4 w-4" />
            </button>
            <button className="p-2 rounded-lg hover:bg-accent transition-colors">
              <Settings className="h-4 w-4" />
            </button>
          </div>

          {/* View mode toggle */}
          <div className="flex items-center bg-muted rounded-lg p-1">
            <button
              onClick={() => setViewMode('2d')}
              className={cn(
                'px-3 py-1 rounded-md text-sm font-medium transition-colors',
                viewMode === '2d' ? 'bg-background shadow-sm' : 'text-muted-foreground'
              )}
            >
              2D Flow
            </button>
            <button
              onClick={() => setViewMode('3d')}
              className={cn(
                'px-3 py-1 rounded-md text-sm font-medium transition-colors',
                viewMode === '3d' ? 'bg-background shadow-sm' : 'text-muted-foreground'
              )}
            >
              3D Network
            </button>
          </div>
        </div>
      </div>

      {/* Main visualization */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <div className="card-depth p-0 overflow-hidden h-[600px]">
            {viewMode === '2d' ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                connectionMode={ConnectionMode.Loose}
                fitView
              >
                <Background variant="dots" gap={12} size={1} />
                <Controls />
                <MiniMap
                  nodeColor={(node) => statusColors[node.data.agent.status]}
                  nodeStrokeWidth={3}
                  pannable
                  zoomable
                />
              </ReactFlow>
            ) : (
              <div className="h-full bg-black/50">
                <AgentNetwork3D />
              </div>
            )}
          </div>
        </div>

        {/* Side panels */}
        <div className="space-y-6">
          {/* Message Flow */}
          <MessageFlow />

          {/* Collaboration Timeline */}
          <CollaborationTimeline />
        </div>
      </div>

      {/* Agent Details Modal */}
      <AnimatePresence>
        {showDetails && selectedAgent && (
          <AgentDetails
            agent={selectedAgent}
            onClose={() => {
              setShowDetails(false)
              selectAgent(null)
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
