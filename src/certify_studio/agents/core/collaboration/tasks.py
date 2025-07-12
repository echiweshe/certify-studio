"""
Collaboration Tasks

Defines task structures for collaborative work.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class CollaborationTask:
    """Represents a task that requires collaboration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    required_capabilities: List[str] = field(default_factory=list)
    subtasks: List['CollaborationTask'] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Task IDs
    assigned_agents: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, active, completed, failed
    priority: int = 1  # 1 (low) to 5 (high)
    deadline: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_ready(self, completed_tasks: List[str]) -> bool:
        """Check if task is ready to execute based on dependencies."""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def add_subtask(self, subtask: 'CollaborationTask') -> None:
        """Add a subtask."""
        self.subtasks.append(subtask)
    
    def assign_to(self, agent_id: str) -> None:
        """Assign task to an agent."""
        if agent_id not in self.assigned_agents:
            self.assigned_agents.append(agent_id)
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Mark task as completed with result."""
        self.status = "completed"
        self.result = result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required_capabilities": self.required_capabilities,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "dependencies": self.dependencies,
            "assigned_agents": self.assigned_agents,
            "status": self.status,
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "result": self.result,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationTask':
        """Create task from dictionary."""
        task = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            required_capabilities=data.get("required_capabilities", []),
            dependencies=data.get("dependencies", []),
            assigned_agents=data.get("assigned_agents", []),
            status=data.get("status", "pending"),
            priority=data.get("priority", 1),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            result=data.get("result"),
            metadata=data.get("metadata", {})
        )
        
        # Reconstruct subtasks
        for subtask_data in data.get("subtasks", []):
            task.subtasks.append(cls.from_dict(subtask_data))
        
        return task
