"""
Frontend-Backend Real-time Data Connector
This module handles real-time data synchronization between the backend agents and frontend
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from certify_studio.core.events import EventBus, Event, EventType
from certify_studio.core.logging import get_logger
from certify_studio.db.session import get_db
from certify_studio.services.agent_service import AgentService

logger = get_logger(__name__)


class AgentDataBroadcaster:
    """Broadcasts real-time agent data to connected frontend clients"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.event_bus = EventBus()
        self.agent_service = AgentService()
        
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection from frontend"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send initial agent states
        await self._send_initial_state(websocket)
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        
    async def _send_initial_state(self, websocket: WebSocket):
        """Send current agent states to newly connected client"""
        try:
            # Get current agent states
            agent_states = await self.agent_service.get_all_agent_states()
            
            initial_data = {
                "type": "initial_state",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "agents": agent_states,
                    "active_generations": await self._get_active_generations(),
                    "metrics": await self._get_current_metrics()
                }
            }
            
            await websocket.send_json(initial_data)
            logger.info("Sent initial state to frontend client")
            
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")
            
    async def broadcast_agent_update(self, agent_id: str, update_data: Dict[str, Any]):
        """Broadcast agent update to all connected clients"""
        message = {
            "type": "agent_update",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "data": update_data
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
                
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
                
    async def broadcast_generation_progress(self, generation_id: str, progress: Dict[str, Any]):
        """Broadcast generation progress updates"""
        message = {
            "type": "generation_progress",
            "timestamp": datetime.utcnow().isoformat(),
            "generation_id": generation_id,
            "data": progress
        }
        
        await self._broadcast_to_all(message)
        
    async def broadcast_collaboration_event(self, event: Dict[str, Any]):
        """Broadcast agent collaboration events"""
        message = {
            "type": "collaboration_event",
            "timestamp": datetime.utcnow().isoformat(),
            "data": event
        }
        
        await self._broadcast_to_all(message)
        
    async def _broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
                
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
                
    async def _get_active_generations(self) -> List[Dict[str, Any]]:
        """Get list of active content generations"""
        # This would query the database for active generations
        return []
        
    async def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            "total_generations": 0,
            "active_agents": 4,
            "avg_generation_time": 0,
            "quality_score": 0
        }


class AgentEventListener:
    """Listens to agent events and forwards them to the broadcaster"""
    
    def __init__(self, broadcaster: AgentDataBroadcaster):
        self.broadcaster = broadcaster
        self.event_bus = EventBus()
        self._setup_listeners()
        
    def _setup_listeners(self):
        """Setup event listeners for agent events"""
        
        # Agent state changes
        self.event_bus.subscribe(
            EventType.AGENT_STATE_CHANGED,
            self._handle_agent_state_change
        )
        
        # Generation progress
        self.event_bus.subscribe(
            EventType.GENERATION_PROGRESS,
            self._handle_generation_progress
        )
        
        # Agent collaboration
        self.event_bus.subscribe(
            EventType.AGENT_COLLABORATION,
            self._handle_collaboration_event
        )
        
        # Task completion
        self.event_bus.subscribe(
            EventType.TASK_COMPLETED,
            self._handle_task_completion
        )
        
    async def _handle_agent_state_change(self, event: Event):
        """Handle agent state change events"""
        await self.broadcaster.broadcast_agent_update(
            event.data["agent_id"],
            {
                "state": event.data["new_state"],
                "previous_state": event.data.get("previous_state"),
                "reason": event.data.get("reason")
            }
        )
        
    async def _handle_generation_progress(self, event: Event):
        """Handle generation progress events"""
        await self.broadcaster.broadcast_generation_progress(
            event.data["generation_id"],
            {
                "stage": event.data["stage"],
                "progress": event.data["progress"],
                "current_agent": event.data.get("current_agent"),
                "message": event.data.get("message")
            }
        )
        
    async def _handle_collaboration_event(self, event: Event):
        """Handle agent collaboration events"""
        await self.broadcaster.broadcast_collaboration_event({
            "agents": event.data["agents"],
            "action": event.data["action"],
            "details": event.data.get("details", {})
        })
        
    async def _handle_task_completion(self, event: Event):
        """Handle task completion events"""
        await self.broadcaster.broadcast_agent_update(
            event.data["agent_id"],
            {
                "task_completed": True,
                "task_id": event.data["task_id"],
                "duration": event.data.get("duration"),
                "result": event.data.get("result")
            }
        )


class FrontendDataProvider:
    """Provides formatted data for frontend consumption"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_service = AgentService()
        
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for frontend"""
        return {
            "platform_metrics": await self._get_platform_metrics(),
            "agent_status": await self._get_agent_status(),
            "recent_activities": await self._get_recent_activities(),
            "generation_stats": await self._get_generation_stats()
        }
        
    async def get_agent_collaboration_data(self) -> Dict[str, Any]:
        """Get agent collaboration visualization data"""
        return {
            "nodes": await self._get_agent_nodes(),
            "edges": await self._get_collaboration_edges(),
            "activities": await self._get_collaboration_timeline()
        }
        
    async def get_knowledge_graph_data(self) -> Dict[str, Any]:
        """Get knowledge graph data for visualization"""
        return {
            "concepts": await self._get_concepts(),
            "relationships": await self._get_relationships(),
            "statistics": await self._get_graph_statistics()
        }
        
    async def _get_platform_metrics(self) -> Dict[str, Any]:
        """Get platform-wide metrics"""
        # Query database for actual metrics
        return {
            "total_generations": 150,
            "active_users": 45,
            "avg_quality_score": 92.5,
            "total_content_hours": 320
        }
        
    async def _get_agent_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        agents = await self.agent_service.get_all_agent_states()
        return [
            {
                "id": agent["id"],
                "name": agent["name"],
                "type": agent["type"],
                "status": agent["status"],
                "current_task": agent.get("current_task"),
                "utilization": agent.get("utilization", 0)
            }
            for agent in agents
        ]
        
    async def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Get recent platform activities"""
        # This would query the activity log
        return [
            {
                "id": "1",
                "type": "generation_completed",
                "title": "AWS AI Practitioner Course Generated",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"duration": "45 minutes", "quality_score": 95}
            }
        ]
        
    async def _get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            "by_format": {
                "video": 45,
                "interactive": 60,
                "pdf": 30,
                "vr": 15
            },
            "by_domain": {
                "aws": 40,
                "azure": 35,
                "gcp": 25,
                "general": 50
            },
            "trend": [
                {"date": "2025-01-01", "count": 12},
                {"date": "2025-01-02", "count": 15},
                {"date": "2025-01-03", "count": 18},
                {"date": "2025-01-04", "count": 22},
                {"date": "2025-01-05", "count": 20}
            ]
        }
        
    async def _get_agent_nodes(self) -> List[Dict[str, Any]]:
        """Get agent nodes for visualization"""
        agents = await self.agent_service.get_all_agent_states()
        return [
            {
                "id": agent["id"],
                "label": agent["name"],
                "type": agent["type"],
                "x": 0,  # Will be calculated by frontend
                "y": 0,  # Will be calculated by frontend
                "status": agent["status"]
            }
            for agent in agents
        ]
        
    async def _get_collaboration_edges(self) -> List[Dict[str, Any]]:
        """Get collaboration edges between agents"""
        # This would query actual collaboration data
        return [
            {
                "id": "edge-1",
                "source": "content-generator",
                "target": "quality-assurance",
                "label": "Review Request",
                "weight": 10
            }
        ]
        
    async def _get_collaboration_timeline(self) -> List[Dict[str, Any]]:
        """Get collaboration timeline events"""
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "agents": ["content-generator", "domain-extractor"],
                "event": "Knowledge extraction started",
                "duration": 5.2
            }
        ]
        
    async def _get_concepts(self) -> List[Dict[str, Any]]:
        """Get concepts from knowledge graph"""
        # This would query the knowledge graph
        return [
            {
                "id": "aws-ai-services",
                "label": "AWS AI Services",
                "category": "aws",
                "difficulty": 0.6,
                "connections": 12
            }
        ]
        
    async def _get_relationships(self) -> List[Dict[str, Any]]:
        """Get relationships from knowledge graph"""
        return [
            {
                "source": "aws-ai-services",
                "target": "amazon-rekognition",
                "type": "includes",
                "weight": 0.8
            }
        ]
        
    async def _get_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return {
            "total_concepts": 245,
            "total_relationships": 580,
            "domains": 12,
            "avg_connections_per_concept": 4.7
        }


# Global instances
broadcaster = AgentDataBroadcaster()
event_listener = AgentEventListener(broadcaster)


async def setup_frontend_connector(app):
    """Setup frontend connector on app startup"""
    logger.info("Setting up frontend connector...")
    
    # WebSocket endpoint for real-time updates
    @app.websocket("/ws/agents")
    async def websocket_endpoint(websocket: WebSocket):
        await broadcaster.connect(websocket)
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                # Handle frontend requests if needed
                logger.debug(f"Received from frontend: {data}")
        except WebSocketDisconnect:
            broadcaster.disconnect(websocket)
            logger.info("Frontend client disconnected")
            
    # REST endpoints for frontend data
    @app.get("/api/v1/frontend/dashboard")
    async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
        """Get dashboard data for frontend"""
        provider = FrontendDataProvider(db)
        return await provider.get_dashboard_data()
        
    @app.get("/api/v1/frontend/agents/collaboration")
    async def get_collaboration_data(db: AsyncSession = Depends(get_db)):
        """Get agent collaboration data"""
        provider = FrontendDataProvider(db)
        return await provider.get_agent_collaboration_data()
        
    @app.get("/api/v1/frontend/knowledge-graph")
    async def get_knowledge_graph(db: AsyncSession = Depends(get_db)):
        """Get knowledge graph data"""
        provider = FrontendDataProvider(db)
        return await provider.get_knowledge_graph_data()
        
    logger.info("Frontend connector setup complete")
