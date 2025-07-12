"""
Agent Messaging System

Defines message types and structures for inter-agent communication.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class MessageType(Enum):
    """Types of messages agents can exchange."""
    INFORM = "inform"  # Share information
    REQUEST = "request"  # Ask for help or resources
    PROPOSE = "propose"  # Suggest a plan or solution
    ACCEPT = "accept"  # Agree to a proposal
    REJECT = "reject"  # Decline a proposal
    QUERY = "query"  # Ask for information
    RESPONSE = "response"  # Reply to query
    BROADCAST = "broadcast"  # Message to all agents
    NEGOTIATE = "negotiate"  # Negotiation message
    COMMIT = "commit"  # Commitment to action
    CANCEL = "cancel"  # Cancel previous commitment


@dataclass
class AgentMessage:
    """Message exchanged between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcasts
    message_type: MessageType = MessageType.INFORM
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    conversation_id: Optional[str] = None
    priority: int = 1  # 1 (low) to 5 (high)
    requires_response: bool = False
    response_deadline: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "conversation_id": self.conversation_id,
            "priority": self.priority,
            "requires_response": self.requires_response,
            "response_deadline": self.response_deadline.isoformat() if self.response_deadline else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id"),
            message_type=MessageType(data.get("message_type", "inform")),
            content=data.get("content", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            conversation_id=data.get("conversation_id"),
            priority=data.get("priority", 1),
            requires_response=data.get("requires_response", False),
            response_deadline=datetime.fromisoformat(data["response_deadline"]) if data.get("response_deadline") else None
        )
