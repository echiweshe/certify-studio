import { motion } from 'framer-motion'
import { GitBranch, Search, Filter, Maximize2, Download } from 'lucide-react'
import { useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'react-flow-renderer'

export default function KnowledgeGraph() {
  const [searchQuery, setSearchQuery] = useState('')
  
  // Mock nodes and edges
  const initialNodes = [
    {
      id: '1',
      position: { x: 250, y: 100 },
      data: { label: 'AWS Cloud' },
      style: { 
        background: '#3B82F6', 
        color: 'white',
        border: '2px solid #1E40AF',
        borderRadius: '8px',
        padding: '10px',
      },
    },
    {
      id: '2',
      position: { x: 100, y: 200 },
      data: { label: 'EC2' },
      style: { 
        background: '#8B5CF6', 
        color: 'white',
        borderRadius: '8px',
        padding: '10px',
      },
    },
    {
      id: '3',
      position: { x: 400, y: 200 },
      data: { label: 'S3' },
      style: { 
        background: '#8B5CF6', 
        color: 'white',
        borderRadius: '8px',
        padding: '10px',
      },
    },
    {
      id: '4',
      position: { x: 250, y: 300 },
      data: { label: 'VPC' },
      style: { 
        background: '#10B981', 
        color: 'white',
        borderRadius: '8px',
        padding: '10px',
      },
    },
  ]

  const initialEdges = [
    { id: 'e1-2', source: '1', target: '2', type: 'smoothstep', animated: true },
    { id: 'e1-3', source: '1', target: '3', type: 'smoothstep', animated: true },
    { id: 'e1-4', source: '1', target: '4', type: 'smoothstep', animated: true },
    { id: 'e2-4', source: '2', target: '4', type: 'smoothstep', style: { stroke: '#6B7280' } },
  ]

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Graph</h1>
          <p className="text-muted-foreground mt-1">
            Explore concept relationships and learning pathways
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button className="p-2 rounded-lg hover:bg-accent transition-colors">
            <Download className="h-4 w-4" />
          </button>
          <button className="p-2 rounded-lg hover:bg-accent transition-colors">
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Search and filters */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search concepts..."
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-card border border-input focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <button className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors">
          <Filter className="h-4 w-4" />
          <span>Filters</span>
        </button>
      </div>

      {/* Graph visualization */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="card-depth p-0 overflow-hidden h-[600px]"
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
        >
          <Background variant="dots" gap={12} size={1} />
          <Controls />
          <MiniMap 
            nodeColor={(node) => node.style?.background || '#6B7280'}
            nodeStrokeWidth={3}
            pannable
            zoomable
          />
        </ReactFlow>
      </motion.div>

      {/* Graph statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card-depth p-4">
          <GitBranch className="h-5 w-5 text-primary mb-2" />
          <p className="text-2xl font-bold">156</p>
          <p className="text-sm text-muted-foreground">Total Concepts</p>
        </div>
        <div className="card-depth p-4">
          <GitBranch className="h-5 w-5 text-purple-500 mb-2" />
          <p className="text-2xl font-bold">423</p>
          <p className="text-sm text-muted-foreground">Relationships</p>
        </div>
        <div className="card-depth p-4">
          <GitBranch className="h-5 w-5 text-green-500 mb-2" />
          <p className="text-2xl font-bold">12</p>
          <p className="text-sm text-muted-foreground">Learning Paths</p>
        </div>
        <div className="card-depth p-4">
          <GitBranch className="h-5 w-5 text-yellow-500 mb-2" />
          <p className="text-2xl font-bold">8</p>
          <p className="text-sm text-muted-foreground">Domains</p>
        </div>
      </div>
    </div>
  )
}