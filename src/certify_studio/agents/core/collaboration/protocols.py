"""
Collaboration Protocols

Defines different types of collaboration protocols that agents can use.
"""

from enum import Enum


class CollaborationProtocol(Enum):
    """Types of collaboration protocols agents can use."""
    HIERARCHICAL = "hierarchical"  # One leader, multiple followers
    PEER_TO_PEER = "peer_to_peer"  # Equal agents, distributed decisions
    BLACKBOARD = "blackboard"  # Shared workspace for problem solving
    CONTRACT_NET = "contract_net"  # Task bidding and allocation
    SWARM = "swarm"  # Emergent behavior from simple rules
    CONSENSUS = "consensus"  # Group decision making
