"""
Base Protocol Handler

Abstract base class for all protocol handlers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from certify_studio.agents.core.autonomous_agent import AutonomousAgent
from ..tasks import CollaborationTask
from ..messages import AgentMessage, MessageType


class BaseProtocolHandler(ABC):
    """Base class for protocol handlers."""
    
    def __init__(self, collaboration_system):
        """Initialize handler with reference to collaboration system."""
        self.collaboration_system = collaboration_system
    
    @abstractmethod
    async def execute(
        self,
        collaboration_id: str,
        task: CollaborationTask,
        agents: List[AutonomousAgent]
    ) -> Dict[str, Any]:
        """Execute the protocol for the given task and agents."""
        pass
    
    async def send_message_and_wait(
        self,
        agent: AutonomousAgent,
        message: AgentMessage,
        timeout: float = 30.0
    ) -> Optional[AgentMessage]:
        """Send a message and wait for response."""
        # Send message
        await self.collaboration_system.send_message(message)
        
        # Wait for response
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            messages = await self.collaboration_system.receive_messages(agent.id)
            
            for msg in messages:
                if msg.conversation_id == message.conversation_id:
                    return msg
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def broadcast_and_collect(
        self,
        agents: List[AutonomousAgent],
        message: AgentMessage,
        timeout: float = 30.0
    ) -> Dict[str, AgentMessage]:
        """Broadcast message to all agents and collect responses."""
        responses = {}
        
        # Send to all agents
        for agent in agents:
            msg = AgentMessage(
                sender_id=message.sender_id,
                recipient_id=agent.id,
                message_type=message.message_type,
                content=message.content,
                conversation_id=message.conversation_id,
                requires_response=True
            )
            await self.collaboration_system.send_message(msg)
        
        # Collect responses
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout and len(responses) < len(agents):
            for agent in agents:
                if agent.id not in responses:
                    messages = await self.collaboration_system.receive_messages(agent.id)
                    
                    for msg in messages:
                        if msg.conversation_id == message.conversation_id:
                            responses[agent.id] = msg
                            break
            
            await asyncio.sleep(0.1)
        
        return responses
