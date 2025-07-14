"""
WebSocket handler for real-time updates.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from ..core.logging import get_logger
from .dependencies import get_ws_user
from .schemas import WebSocketMessage, ProgressUpdate, StatusEnum

logger = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        # Active connections by user ID
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        # Task subscriptions: task_id -> set of user_ids
        self.task_subscriptions: Dict[UUID, Set[UUID]] = {}
        # User to tasks mapping
        self.user_tasks: Dict[UUID, Set[UUID]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[UUID] = None):
        """Accept and register connection."""
        await websocket.accept()
        
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
            logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[UUID] = None):
        """Remove connection."""
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Clean up subscriptions
                if user_id in self.user_tasks:
                    for task_id in self.user_tasks[user_id]:
                        if task_id in self.task_subscriptions:
                            self.task_subscriptions[task_id].discard(user_id)
                    del self.user_tasks[user_id]
            
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(
        self,
        message: str,
        user_id: UUID
    ):
        """Send message to specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
    
    async def send_json_to_user(
        self,
        data: dict,
        user_id: UUID
    ):
        """Send JSON data to specific user."""
        message = json.dumps(data)
        await self.send_personal_message(message, user_id)
    
    async def broadcast_to_task(
        self,
        task_id: UUID,
        data: dict
    ):
        """Broadcast message to all users subscribed to a task."""
        if task_id in self.task_subscriptions:
            for user_id in self.task_subscriptions[task_id]:
                await self.send_json_to_user(data, user_id)
    
    def subscribe_to_task(self, user_id: UUID, task_id: UUID):
        """Subscribe user to task updates."""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(user_id)
        
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = set()
        self.user_tasks[user_id].add(task_id)
        
        logger.info(f"User {user_id} subscribed to task {task_id}")
    
    def unsubscribe_from_task(self, user_id: UUID, task_id: UUID):
        """Unsubscribe user from task updates."""
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(user_id)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]
        
        if user_id in self.user_tasks:
            self.user_tasks[user_id].discard(task_id)
        
        logger.info(f"User {user_id} unsubscribed from task {task_id}")


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint."""
    user = None
    user_id = None
    
    try:
        # Try to authenticate
        # In production, get auth token from query params or headers
        token = websocket.query_params.get("token")
        if token:
            from .dependencies import get_db
            async with get_db() as db:
                user = await get_ws_user(token, db)
                if user:
                    user_id = user.id
        
        # Accept connection
        await manager.connect(websocket, user_id)
        
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type="connection",
            data={
                "status": "connected",
                "user_id": str(user_id) if user_id else None,
                "server_time": datetime.utcnow().isoformat()
            }
        )
        await websocket.send_json(welcome_msg.model_dump())
        
        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()
                
                # Process message based on type
                message_type = data.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    pong_msg = WebSocketMessage(
                        type="pong",
                        data={"timestamp": datetime.utcnow().isoformat()}
                    )
                    await websocket.send_json(pong_msg.model_dump())
                
                elif message_type == "subscribe":
                    # Subscribe to task updates
                    task_id = data.get("task_id")
                    if task_id and user_id:
                        try:
                            task_uuid = UUID(task_id)
                            manager.subscribe_to_task(user_id, task_uuid)
                            
                            response = WebSocketMessage(
                                type="subscribed",
                                data={
                                    "task_id": task_id,
                                    "status": "success"
                                }
                            )
                            await websocket.send_json(response.model_dump())
                        except ValueError:
                            error_msg = WebSocketMessage(
                                type="error",
                                data={
                                    "message": "Invalid task ID format",
                                    "code": "INVALID_TASK_ID"
                                }
                            )
                            await websocket.send_json(error_msg.model_dump())
                    else:
                        error_msg = WebSocketMessage(
                            type="error",
                            data={
                                "message": "Authentication required for subscriptions",
                                "code": "AUTH_REQUIRED"
                            }
                        )
                        await websocket.send_json(error_msg.model_dump())
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from task updates
                    task_id = data.get("task_id")
                    if task_id and user_id:
                        try:
                            task_uuid = UUID(task_id)
                            manager.unsubscribe_from_task(user_id, task_uuid)
                            
                            response = WebSocketMessage(
                                type="unsubscribed",
                                data={
                                    "task_id": task_id,
                                    "status": "success"
                                }
                            )
                            await websocket.send_json(response.model_dump())
                        except ValueError:
                            pass
                
                else:
                    # Unknown message type
                    error_msg = WebSocketMessage(
                        type="error",
                        data={
                            "message": f"Unknown message type: {message_type}",
                            "code": "UNKNOWN_MESSAGE_TYPE"
                        }
                    )
                    await websocket.send_json(error_msg.model_dump())
                    
            except json.JSONDecodeError:
                error_msg = WebSocketMessage(
                    type="error",
                    data={
                        "message": "Invalid JSON",
                        "code": "INVALID_JSON"
                    }
                )
                await websocket.send_json(error_msg.model_dump())
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                error_msg = WebSocketMessage(
                    type="error",
                    data={
                        "message": "Internal server error",
                        "code": "INTERNAL_ERROR"
                    }
                )
                await websocket.send_json(error_msg.model_dump())
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


async def send_progress_update(
    task_id: UUID,
    phase: str,
    progress: float,
    message: str,
    eta_seconds: Optional[float] = None
):
    """Send progress update to all subscribed users."""
    update = ProgressUpdate(
        task_id=task_id,
        phase=phase,
        progress=progress,
        message=message,
        eta_seconds=eta_seconds
    )
    
    msg = WebSocketMessage(
        type="progress_update",
        data=update.model_dump(),
        task_id=task_id,
        progress=progress,
        phase=phase
    )
    
    await manager.broadcast_to_task(task_id, msg.model_dump())


async def send_task_complete(
    task_id: UUID,
    status: StatusEnum,
    result: Optional[Dict] = None,
    error: Optional[str] = None
):
    """Send task completion notification."""
    data = {
        "task_id": str(task_id),
        "status": status.value,
        "completed_at": datetime.utcnow().isoformat()
    }
    
    if result:
        data["result"] = result
    if error:
        data["error"] = error
    
    msg = WebSocketMessage(
        type="task_complete",
        data=data,
        task_id=task_id
    )
    
    await manager.broadcast_to_task(task_id, msg.model_dump())


async def send_quality_alert(
    content_id: UUID,
    alert_type: str,
    severity: str,
    message: str,
    metrics: Dict[str, float]
):
    """Send quality alert to content owner."""
    # In production, look up content owner
    # For now, broadcast to all connections
    
    alert_data = {
        "content_id": str(content_id),
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    msg = WebSocketMessage(
        type="quality_alert",
        data=alert_data
    )
    
    # Send to all connected users (in production, only to content owner)
    for user_id, connections in manager.active_connections.items():
        for connection in connections:
            try:
                await connection.send_json(msg.model_dump())
            except Exception as e:
                logger.error(f"Error sending quality alert: {e}")


# Background task to clean up stale connections
async def cleanup_stale_connections():
    """Periodically clean up stale WebSocket connections."""
    while True:
        try:
            stale_connections = []
            
            for user_id, connections in manager.active_connections.items():
                for connection in connections:
                    if connection.client_state != WebSocketState.CONNECTED:
                        stale_connections.append((user_id, connection))
            
            for user_id, connection in stale_connections:
                manager.disconnect(connection, user_id)
            
            if stale_connections:
                logger.info(f"Cleaned up {len(stale_connections)} stale connections")
            
        except Exception as e:
            logger.error(f"Error in connection cleanup: {e}")
        
        # Run every 5 minutes
        await asyncio.sleep(300)


# Cleanup task should be started by the application lifespan handler, not at import time
# This function can be called from the FastAPI app's lifespan context
