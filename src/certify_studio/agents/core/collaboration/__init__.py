"""
Collaboration Module

This module provides multi-agent collaboration capabilities including
various protocols, messaging, and coordination mechanisms.
"""

from .protocols import CollaborationProtocol
from .messages import MessageType, AgentMessage
from .tasks import CollaborationTask
from .workspace import SharedWorkspace
from .consensus import ConsensusResult
from .system import MultiAgentCollaborationSystem

__all__ = [
    "CollaborationProtocol",
    "MessageType",
    "AgentMessage",
    "CollaborationTask",
    "SharedWorkspace",
    "ConsensusResult",
    "MultiAgentCollaborationSystem",
]
