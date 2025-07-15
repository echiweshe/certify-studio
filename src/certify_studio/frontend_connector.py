"""
Frontend Connector for Real-Time Agent Data

This module provides WebSocket and REST endpoints for the frontend to receive
real-time updates about agent activities, collaboration events, and system state.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from .database.connection import get_db
from .agents.core.base import AgentState
from .services.agent_service import AgentService
from .services.knowledge_graph_service import KnowledgeGraphService


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of subscribed topics
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.subscriptions[client_id]
    
    async def subscribe(self, client_id: str, topics: List[str]):
        """Subscribe client to specific topics"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].update(topics)
    
    async def unsubscribe(self, client_id: str, topics: List[str]):
        """Unsubscribe client from topics"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].difference_update(topics)
    
    async def send_to_client(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast message to all clients subscribed to topic"""
        disconnected_clients = []
        
        for client_id, topics in self.subscriptions.items():
            if topic in topics:
                try:
                    await self.send_to_client(client_id, message)
                except:
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)


# Global WebSocket manager instance
ws_manager = WebSocketManager()


class AgentActivityBroadcaster:
    """Broadcasts agent activities to connected clients"""
    
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.agent_states: Dict[str, Dict[str, Any]] = {}
    
    async def broadcast_agent_state(self, agent_id: str, state: AgentState):
        """Broadcast agent state update"""
        message = {
            "type": "agent_state_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "agent_id": agent_id,
                "state": state.value,
                "details": {
                    "current_task": getattr(state, "current_task", None),
                    "progress": getattr(state, "progress", 0),
                    "resource_usage": getattr(state, "resource_usage", {})
                }
            }
        }
        
        await self.ws_manager.broadcast_to_topic("agents", message)
        
        # Update cached state
        self.agent_states[agent_id] = message["data"]
    
    async def broadcast_collaboration_event(self, event: Dict[str, Any]):
        """Broadcast agent collaboration event"""
        message = {
            "type": "collaboration_event",
            "timestamp": datetime.utcnow().isoformat(),
            "data": event
        }
        
        await self.ws_manager.broadcast_to_topic("collaboration", message)
    
    async def broadcast_generation_progress(self, job_id: str, progress: Dict[str, Any]):
        """Broadcast content generation progress"""
        message = {
            "type": "generation_progress",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "job_id": job_id,
                "progress": progress.get("percentage", 0),
                "current_step": progress.get("current_step", ""),
                "estimated_time_remaining": progress.get("eta_seconds", None),
                "agents_involved": progress.get("agents", [])
            }
        }
        
        await self.ws_manager.broadcast_to_topic(f"generation_{job_id}", message)
        await self.ws_manager.broadcast_to_topic("generation_all", message)
    
    async def broadcast_quality_check_update(self, content_id: str, qa_data: Dict[str, Any]):
        """Broadcast quality check updates"""
        message = {
            "type": "quality_check_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "content_id": content_id,
                "overall_score": qa_data.get("overall_score", 0),
                "checks_completed": qa_data.get("checks_completed", []),
                "issues_found": qa_data.get("issues_found", 0),
                "current_check": qa_data.get("current_check", "")
            }
        }
        
        await self.ws_manager.broadcast_to_topic(f"qa_{content_id}", message)
        await self.ws_manager.broadcast_to_topic("quality_all", message)


# Global broadcaster instance
broadcaster = AgentActivityBroadcaster(ws_manager)


# WebSocket endpoint for real-time updates
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time agent updates"""
    await ws_manager.connect(websocket, client_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "available_topics": [
                "agents",
                "collaboration", 
                "generation_all",
                "quality_all",
                "knowledge_graph"
            ]
        })
        
        # Send current agent states
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "agents": broadcaster.agent_states
            }
        })
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            
            if data["type"] == "subscribe":
                await ws_manager.subscribe(client_id, data["topics"])
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "topics": data["topics"]
                })
            
            elif data["type"] == "unsubscribe":
                await ws_manager.unsubscribe(client_id, data["topics"])
                await websocket.send_json({
                    "type": "unsubscription_confirmed",
                    "topics": data["topics"]
                })
            
            elif data["type"] == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
        ws_manager.disconnect(client_id)


# REST endpoints for dashboard data

class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    total_agents: int
    active_agents: int
    total_generations_today: int
    average_generation_time: float
    quality_score_average: float
    active_users: int
    system_health: str


class AgentStatus(BaseModel):
    """Individual agent status"""
    agent_id: str
    agent_type: str
    state: str
    current_task: Optional[str]
    tasks_completed: int
    success_rate: float
    average_processing_time: float
    last_active: datetime


class CollaborationMetrics(BaseModel):
    """Agent collaboration metrics"""
    total_collaborations: int
    active_collaborations: int
    collaboration_patterns: Dict[str, int]
    average_agents_per_task: float
    collaboration_success_rate: float


class KnowledgeGraphStats(BaseModel):
    """Knowledge graph statistics"""
    total_nodes: int
    total_relationships: int
    domains_covered: int
    concepts_extracted: int
    recent_updates: List[Dict[str, Any]]


async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    agent_manager: AgentManager = Depends(lambda: AgentManager())
) -> DashboardStats:
    """Get real-time dashboard statistics"""
    
    # Get agent statistics
    agents = await agent_manager.get_all_agents()
    active_agents = sum(1 for agent in agents if agent.state == AgentState.BUSY)
    
    # Get generation statistics (mock data for now)
    total_generations_today = 47
    average_generation_time = 245.6  # seconds
    quality_score_average = 0.92
    active_users = 12
    
    # System health check
    system_health = "healthy" if active_agents < len(agents) * 0.8 else "busy"
    
    return DashboardStats(
        total_agents=len(agents),
        active_agents=active_agents,
        total_generations_today=total_generations_today,
        average_generation_time=average_generation_time,
        quality_score_average=quality_score_average,
        active_users=active_users,
        system_health=system_health
    )


async def get_agent_statuses(
    db: AsyncSession = Depends(get_db),
    agent_manager: AgentManager = Depends(lambda: AgentManager())
) -> List[AgentStatus]:
    """Get detailed status of all agents"""
    
    agents = await agent_manager.get_all_agents()
    statuses = []
    
    for agent in agents:
        # Get agent metrics (mock data for demonstration)
        status = AgentStatus(
            agent_id=str(agent.id),
            agent_type=agent.__class__.__name__,
            state=agent.state.value,
            current_task=getattr(agent, "current_task", None),
            tasks_completed=getattr(agent, "tasks_completed", 0),
            success_rate=getattr(agent, "success_rate", 0.95),
            average_processing_time=getattr(agent, "avg_processing_time", 30.5),
            last_active=getattr(agent, "last_active", datetime.utcnow())
        )
        statuses.append(status)
    
    return statuses


async def get_collaboration_metrics(
    db: AsyncSession = Depends(get_db)
) -> CollaborationMetrics:
    """Get agent collaboration metrics"""
    
    # Mock data for demonstration
    return CollaborationMetrics(
        total_collaborations=342,
        active_collaborations=7,
        collaboration_patterns={
            "content_qa": 156,
            "domain_content": 98,
            "qa_export": 88
        },
        average_agents_per_task=2.3,
        collaboration_success_rate=0.94
    )


async def get_knowledge_graph_stats(
    db: AsyncSession = Depends(get_db),
    kg_service: KnowledgeGraphService = Depends(lambda: KnowledgeGraphService())
) -> KnowledgeGraphStats:
    """Get knowledge graph statistics"""
    
    stats = await kg_service.get_statistics()
    
    return KnowledgeGraphStats(
        total_nodes=stats.get("total_nodes", 0),
        total_relationships=stats.get("total_relationships", 0),
        domains_covered=stats.get("domains_covered", 0),
        concepts_extracted=stats.get("concepts_extracted", 0),
        recent_updates=stats.get("recent_updates", [])[:10]  # Last 10 updates
    )


# Integration with main app
def setup_frontend_connector(app):
    """Setup frontend connector routes"""
    
    # WebSocket endpoint
    app.websocket("/ws/agents")(websocket_endpoint)
    
    # REST endpoints
    app.get("/api/v1/dashboard/stats", response_model=DashboardStats)(get_dashboard_stats)
    app.get("/api/v1/dashboard/agents", response_model=List[AgentStatus])(get_agent_statuses)
    app.get("/api/v1/dashboard/collaboration", response_model=CollaborationMetrics)(get_collaboration_metrics)
    app.get("/api/v1/dashboard/knowledge-graph", response_model=KnowledgeGraphStats)(get_knowledge_graph_stats)
    
    return app


# Agent event hooks for real-time updates
async def on_agent_state_change(agent_id: str, new_state: AgentState):
    """Hook called when agent state changes"""
    await broadcaster.broadcast_agent_state(agent_id, new_state)


async def on_collaboration_event(event: Dict[str, Any]):
    """Hook called when agents collaborate"""
    await broadcaster.broadcast_collaboration_event(event)


async def on_generation_progress(job_id: str, progress: Dict[str, Any]):
    """Hook called when generation progresses"""
    await broadcaster.broadcast_generation_progress(job_id, progress)


async def on_quality_check_update(content_id: str, qa_data: Dict[str, Any]):
    """Hook called when quality check updates"""
    await broadcaster.broadcast_quality_check_update(content_id, qa_data)


# Example usage in JavaScript/TypeScript frontend:
"""
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/agents?client_id=frontend-123');

ws.onopen = () => {
    console.log('Connected to agent updates');
    
    // Subscribe to topics
    ws.send(JSON.stringify({
        type: 'subscribe',
        topics: ['agents', 'collaboration', 'generation_all']
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
        case 'agent_state_update':
            updateAgentDisplay(message.data);
            break;
        case 'collaboration_event':
            showCollaborationAnimation(message.data);
            break;
        case 'generation_progress':
            updateProgressBar(message.data);
            break;
    }
};

// REST API calls
async function fetchDashboardStats() {
    const response = await fetch('/api/v1/dashboard/stats');
    const stats = await response.json();
    updateDashboard(stats);
}

async function fetchAgentStatuses() {
    const response = await fetch('/api/v1/dashboard/agents');
    const agents = await response.json();
    renderAgentGrid(agents);
}
"""
