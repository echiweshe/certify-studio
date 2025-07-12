"""
Consensus Building

Provides consensus mechanisms for group decision making.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import numpy as np


@dataclass
class ConsensusResult:
    """Result of a consensus-building process."""
    decision: Any
    agreement_level: float  # 0 to 1
    participants: List[str]
    votes: Dict[str, Any]
    proposals: Dict[str, Any] = field(default_factory=dict)
    rounds: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    method: str = "voting"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def consensus_reached(self) -> bool:
        """Check if consensus was reached."""
        return self.decision is not None and self.agreement_level > 0.5
    
    @property
    def participation_rate(self) -> float:
        """Calculate participation rate."""
        if not self.participants:
            return 0.0
        return len(self.votes) / len(self.participants)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "decision": self.decision,
            "agreement_level": self.agreement_level,
            "participants": self.participants,
            "votes": self.votes,
            "proposals": self.proposals,
            "rounds": self.rounds,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "metadata": self.metadata,
            "consensus_reached": self.consensus_reached,
            "participation_rate": self.participation_rate
        }


class ConsensusBuilder:
    """Utilities for building consensus among agents."""
    
    @staticmethod
    def check_consensus(proposals: Dict[str, Any], threshold: float = 0.7) -> Dict[str, Any]:
        """Check if consensus has been reached among proposals."""
        if not proposals:
            return {"consensus_reached": False, "metrics": {}}
        
        # Extract proposal values
        values = list(proposals.values())
        
        # Check for exact matches
        unique_values = set(str(v) for v in values)
        if len(unique_values) == 1:
            return {
                "consensus_reached": True,
                "consensus_value": values[0],
                "metrics": {"agreement": 1.0, "unique_proposals": 1}
            }
        
        # Check for similar proposals
        if len(unique_values) <= len(proposals) * (1 - threshold):
            # Find most common proposal
            value_counts = Counter(str(v) for v in values)
            most_common = value_counts.most_common(1)[0]
            
            agreement = most_common[1] / len(proposals)
            if agreement >= threshold:
                return {
                    "consensus_reached": True,
                    "consensus_value": next(v for v in values if str(v) == most_common[0]),
                    "metrics": {
                        "agreement": agreement,
                        "unique_proposals": len(unique_values)
                    }
                }
        
        return {
            "consensus_reached": False,
            "metrics": {
                "unique_proposals": len(unique_values),
                "total_proposals": len(proposals),
                "max_agreement": max(Counter(str(v) for v in values).values()) / len(proposals) if proposals else 0
            }
        }
    
    @staticmethod
    def calculate_agreement_matrix(votes: Dict[str, Any]) -> np.ndarray:
        """Calculate pairwise agreement matrix between voters."""
        voters = list(votes.keys())
        n = len(voters)
        
        if n == 0:
            return np.array([])
        
        matrix = np.zeros((n, n))
        
        for i, voter1 in enumerate(voters):
            for j, voter2 in enumerate(voters):
                if i == j:
                    matrix[i, j] = 1.0
                else:
                    # Calculate agreement based on vote similarity
                    vote1 = str(votes[voter1])
                    vote2 = str(votes[voter2])
                    matrix[i, j] = 1.0 if vote1 == vote2 else 0.0
        
        return matrix
    
    @staticmethod
    def find_compromise(proposals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find a compromise solution from multiple proposals."""
        if not proposals:
            return None
        
        # For dictionaries, try to merge
        if all(isinstance(p, dict) for p in proposals):
            compromise = {}
            
            # Find common keys
            all_keys = set()
            for p in proposals:
                all_keys.update(p.keys())
            
            for key in all_keys:
                values = [p.get(key) for p in proposals if key in p]
                
                if not values:
                    continue
                
                # For numeric values, take average
                if all(isinstance(v, (int, float)) for v in values):
                    compromise[key] = sum(values) / len(values)
                # For strings, take most common
                elif all(isinstance(v, str) for v in values):
                    compromise[key] = Counter(values).most_common(1)[0][0]
                # For lists, combine unique elements
                elif all(isinstance(v, list) for v in values):
                    unique_items = set()
                    for v in values:
                        unique_items.update(v)
                    compromise[key] = list(unique_items)
                else:
                    # Default to first non-None value
                    compromise[key] = next((v for v in values if v is not None), None)
            
            return compromise
        
        # For other types, return most common
        return Counter(proposals).most_common(1)[0][0]
    
    @staticmethod
    def weighted_voting(votes: Dict[str, Any], weights: Dict[str, float]) -> Any:
        """Perform weighted voting to determine outcome."""
        if not votes:
            return None
        
        # Calculate weighted scores for each option
        option_scores = {}
        
        for voter, vote in votes.items():
            weight = weights.get(voter, 1.0)
            
            if vote not in option_scores:
                option_scores[vote] = 0.0
            option_scores[vote] += weight
        
        # Return option with highest score
        return max(option_scores.items(), key=lambda x: x[1])[0]
