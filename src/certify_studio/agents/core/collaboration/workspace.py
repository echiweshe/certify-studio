"""
Shared Workspace

Provides shared workspace functionality for collaborative problem solving.
"""

from typing import Set, Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import threading


@dataclass
class WorkspaceEntry:
    """Entry in the workspace history."""
    action: str
    key: str
    value: Any
    agent_id: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "action": self.action,
            "key": self.key,
            "value": self.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SharedWorkspace:
    """Shared workspace for collaborative problem solving."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    participants: Set[str] = field(default_factory=set)
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[WorkspaceEntry] = field(default_factory=list)
    locks: Dict[str, str] = field(default_factory=dict)  # resource -> agent_id
    created_at: datetime = field(default_factory=datetime.now)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, compare=False)
    
    def add_participant(self, agent_id: str) -> None:
        """Add a participant to the workspace."""
        with self._lock:
            self.participants.add(agent_id)
    
    def remove_participant(self, agent_id: str) -> None:
        """Remove a participant from the workspace."""
        with self._lock:
            self.participants.discard(agent_id)
            # Release any locks held by this agent
            for resource in list(self.locks.keys()):
                if self.locks[resource] == agent_id:
                    del self.locks[resource]
    
    def add_data(self, key: str, value: Any, agent_id: str) -> None:
        """Add data to workspace with history tracking."""
        with self._lock:
            self.data[key] = value
            entry = WorkspaceEntry(
                action="add",
                key=key,
                value=value,
                agent_id=agent_id,
                timestamp=datetime.now()
            )
            self.history.append(entry)
    
    def get_data(self, key: str) -> Optional[Any]:
        """Get data from workspace."""
        with self._lock:
            return self.data.get(key)
    
    def update_data(self, key: str, value: Any, agent_id: str) -> bool:
        """Update existing data in workspace."""
        with self._lock:
            if key in self.data:
                self.data[key] = value
                entry = WorkspaceEntry(
                    action="update",
                    key=key,
                    value=value,
                    agent_id=agent_id,
                    timestamp=datetime.now()
                )
                self.history.append(entry)
                return True
            return False
    
    def delete_data(self, key: str, agent_id: str) -> bool:
        """Delete data from workspace."""
        with self._lock:
            if key in self.data:
                value = self.data.pop(key)
                entry = WorkspaceEntry(
                    action="delete",
                    key=key,
                    value=value,
                    agent_id=agent_id,
                    timestamp=datetime.now()
                )
                self.history.append(entry)
                return True
            return False
    
    def acquire_lock(self, resource: str, agent_id: str) -> bool:
        """Try to acquire a lock on a resource."""
        with self._lock:
            if resource not in self.locks:
                self.locks[resource] = agent_id
                return True
            return self.locks[resource] == agent_id
    
    def release_lock(self, resource: str, agent_id: str) -> bool:
        """Release a lock on a resource."""
        with self._lock:
            if self.locks.get(resource) == agent_id:
                del self.locks[resource]
                return True
            return False
    
    def is_locked(self, resource: str) -> bool:
        """Check if a resource is locked."""
        with self._lock:
            return resource in self.locks
    
    def get_lock_owner(self, resource: str) -> Optional[str]:
        """Get the owner of a lock."""
        with self._lock:
            return self.locks.get(resource)
    
    def get_history(self, agent_id: Optional[str] = None, limit: Optional[int] = None) -> List[WorkspaceEntry]:
        """Get workspace history, optionally filtered by agent."""
        with self._lock:
            history = self.history
            if agent_id:
                history = [e for e in history if e.agent_id == agent_id]
            if limit:
                history = history[-limit:]
            return history.copy()
    
    def clear(self) -> None:
        """Clear all data from workspace."""
        with self._lock:
            self.data.clear()
            self.locks.clear()
            # Don't clear history - keep for audit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workspace to dictionary."""
        with self._lock:
            return {
                "id": self.id,
                "name": self.name,
                "participants": list(self.participants),
                "data": self.data.copy(),
                "history": [e.to_dict() for e in self.history],
                "locks": self.locks.copy(),
                "created_at": self.created_at.isoformat()
            }
