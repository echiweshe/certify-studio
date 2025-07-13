"""
WebSocket handler for real-time updates.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, Depends
from starlette.websockets import WebSocketState

from ..core.logging import get_logger
from .dependencies import get_ws_user
from .schemas import WebSocketMessage, ProgressUpdate

logger = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        # Active connections by user
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        # Task subscriptions
        self.task_subscriptions: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[UUID] = None):
        """Accept WebSocket connection."""
        await websocket.accept()
        
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
            logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[UUID] = None):
        """Remove WebSocket connection."""
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            logger.info(f"User {user_id} disconnected from WebSocket")
        
        # Remove from all task subscriptions
        for task_id in list(self.task_subscriptions.keys()):
            self.task_subscriptions[task_id].discard(websocket)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]
    
    async def send_personal_message(self, message: dict, user_id: UUID):
        """Send message to specific user."""
        if user_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast_task_update(self, task_id: UUID, update: dict):
        """Broadcast update to all subscribers of a task."""
        if task_id in self.task_subscriptions:
            disconnected = []
            
            for connection in self.task_subscriptions[task_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(update)
                except Exception as e:
                    logger.error(f"Error broadcasting task {task_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.task_subscriptions[task_id].discard(conn)
    
    def subscribe_to_task(self, websocket: WebSocket, task_id: UUID):
        """Subscribe WebSocket to task updates."""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(websocket)
    
    def unsubscribe_from_task(self, websocket: WebSocket, task_id: UUID):
        """Unsubscribe WebSocket from task updates."""
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(websocket)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """Main WebSocket endpoint."""
    user = None
    
    try:
        # Authenticate if token provided
        if token:
            from .dependencies import get_db
            async with get_db() as db:
                user = await get_ws_user(token, db)
        
        # Connect
        await manager.connect(websocket, user.id if user else None)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "data": {
                "status": "connected",
                "user_id": str(user.id) if user else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Handle messages
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Process message
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                    "data": {"timestamp": datetime.utcnow().isoformat()}
                })
            
            elif message_type == "subscribe":
                # Subscribe to task updates
                task_id = UUID(data.get("task_id"))
                manager.subscribe_to_task(websocket, task_id)
                
                await websocket.send_json({
                    "type": "subscribed",
                    "data": {"task_id": str(task_id)}
                })
            
            elif message_type == "unsubscribe":
                # Unsubscribe from task updates
                task_id = UUID(data.get("task_id"))
                manager.unsubscribe_from_task(websocket, task_id)
                
                await websocket.send_json({
                    "type": "unsubscribed",
                    "data": {"task_id": str(task_id)}
                })
            
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Unknown message type: {message_type}"}
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id if user else None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user.id if user else None)
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()


async def send_progress_update(
    task_id: UUID,
    phase: str,
    progress: float,
    message: str,
    eta_seconds: Optional[int] = None
):
    """Send progress update to subscribers."""
    update = ProgressUpdate(
        task_id=task_id,
        phase=phase,
        progress=progress,
        message=message,
        eta_seconds=eta_seconds
    )
    
    await manager.broadcast_task_update(
        task_id,
        {
            "type": "progress",
            "data": update.model_dump()
        }
    )


async def send_task_complete(
    task_id: UUID,
    status: str,
    result: Optional[dict] = None
):
    """Send task completion notification."""
    await manager.broadcast_task_update(
        task_id,
        {
            "type": "complete",
            "data": {
                "task_id": str(task_id),
                "status": status,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


async def send_notification(
    user_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    data: Optional[dict] = None
):
    """Send notification to user."""
    await manager.send_personal_message(
        {
            "type": "notification",
            "data": {
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        user_id
    )


# Example usage in other parts of the application:
# 
# from .websocket import send_progress_update, send_task_complete
# 
# # During content generation:
# await send_progress_update(
#     task_id=task_id,
#     phase="extraction",
#     progress=25.0,
#     message="Extracting domain knowledge...",
#     eta_seconds=180
# )
# 
# # When complete:
# await send_task_complete(
#     task_id=task_id,
#     status="completed",
#     result={"content_id": str(content_id)}
# )
