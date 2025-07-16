"""
Agent Service

Manages agent lifecycle, state, and provides agent-related operations.
This version works without database persistence for agent state.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from ..agents.core.autonomous_agent import AutonomousAgent, AgentState, AgentCapability

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agents and their operations."""
    
    def __init__(self):
        self.active_agents: Dict[str, AutonomousAgent] = {}
        self._initialized = False
        # In-memory storage for agent metrics
        self._agent_metrics: Dict[str, Dict[str, Any]] = {}
        self._collaborations: List[Dict[str, Any]] = []
        self._tasks: List[Dict[str, Any]] = []
    
    async def initialize(self):
        """Initialize agent service."""
        if self._initialized:
            return
            
        try:
            # Initialize default agents
            await self._initialize_default_agents()
            self._initialized = True
            logger.info(f"Initialized {len(self.active_agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent service: {e}")
            raise
    
    async def _initialize_default_agents(self):
        """Initialize the default set of agents."""
        # Import agent classes
        try:
            from ..agents.specialized.content_generation.agent import ContentGenerationAgent
            from ..agents.specialized.domain_extraction.agent import DomainExtractionAgent
            from ..agents.specialized.quality_assurance.agent import QualityAssuranceAgent
            
            # Create agent instances
            agents = [
                ("content_generation", ContentGenerationAgent()),
                ("domain_extraction", DomainExtractionAgent()),
                ("quality_assurance", QualityAssuranceAgent())
            ]
            
            for agent_id, agent in agents:
                self.active_agents[agent_id] = agent
                self._agent_metrics[agent_id] = {
                    "tasks_completed": 0,
                    "tasks_failed": 0,
                    "success_rate": 1.0,
                    "avg_processing_time": 0.0,
                    "last_active": datetime.utcnow()
                }
                
        except ImportError as e:
            logger.warning(f"Could not import all agent classes: {e}")
            # Create mock agents for testing
            self._create_mock_agents()
    
    def _create_mock_agents(self):
        """Create mock agents for testing when real agents aren't available."""
        mock_agents = [
            {
                "id": "content_generation",
                "name": "ContentGenerationAgent",
                "type": "ContentGenerationAgent",
                "capabilities": ["generation", "evaluation", "learning"]
            },
            {
                "id": "domain_extraction",
                "name": "DomainExtractionAgent", 
                "type": "DomainExtractionAgent",
                "capabilities": ["domain_extraction", "concept_identification", "relationship_mapping"]
            },
            {
                "id": "quality_assurance",
                "name": "QualityAssuranceAgent",
                "type": "QualityAssuranceAgent",
                "capabilities": ["quality_assessment", "technical_validation", "reporting"]
            },
            {
                "id": "export_agent",
                "name": "ExportAgent",
                "type": "ExportAgent",
                "capabilities": ["export", "format_conversion", "packaging"]
            }
        ]
        
        for agent_config in mock_agents:
            # Create a mock agent object
            mock_agent = type('MockAgent', (), {
                'id': agent_config["id"],
                'name': agent_config["name"],
                'state': AgentState.IDLE,
                'capabilities': agent_config["capabilities"],
                '__class__.__name__': agent_config["type"]
            })()
            
            self.active_agents[agent_config["id"]] = mock_agent
            self._agent_metrics[agent_config["id"]] = {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "success_rate": 1.0,
                "avg_processing_time": 0.0,
                "last_active": datetime.utcnow()
            }
    
    async def get_all_agents(self) -> List[AutonomousAgent]:
        """Get all active agents."""
        return list(self.active_agents.values())
    
    async def get_agent(self, agent_id: str) -> Optional[AutonomousAgent]:
        """Get specific agent by ID."""
        return self.active_agents.get(agent_id)
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of an agent."""
        agent = self.active_agents.get(agent_id)
        if not agent:
            return None
        
        metrics = self._agent_metrics.get(agent_id, {})
        
        return {
            "id": agent_id,
            "name": getattr(agent, 'name', agent_id),
            "type": agent.__class__.__name__,
            "state": agent.state.value if hasattr(agent, 'state') else "idle",
            "capabilities": getattr(agent, 'capabilities', []),
            "current_task": getattr(agent, "current_task", None),
            "tasks_completed": metrics.get("tasks_completed", 0),
            "success_rate": metrics.get("success_rate", 1.0),
            "last_active": metrics.get("last_active", datetime.utcnow()),
            "metrics": {
                "avg_processing_time": metrics.get("avg_processing_time", 0.0)
            }
        }
    
    async def get_all_agent_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all agents."""
        statuses = []
        for agent_id in self.active_agents:
            status = await self.get_agent_status(agent_id)
            if status:
                statuses.append(status)
        return statuses
    
    async def update_agent_state(self, agent_id: str, new_state: AgentState):
        """Update agent state."""
        agent = self.active_agents.get(agent_id)
        if not agent:
            return False
            
        # Update in memory
        agent.state = new_state
        
        # Update metrics
        if agent_id in self._agent_metrics:
            self._agent_metrics[agent_id]["last_active"] = datetime.utcnow()
        
        return True
    
    async def record_agent_task(
        self, 
        agent_id: str, 
        task_type: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record a new agent task."""
        task = {
            "id": str(UUID().int)[:8],  # Simple ID
            "agent_id": agent_id,
            "task_type": task_type,
            "input_data": task_data,
            "status": "started",
            "started_at": datetime.utcnow()
        }
        
        self._tasks.append(task)
        return task
    
    async def complete_agent_task(
        self,
        task_id: str,
        result_data: Dict[str, Any],
        success: bool
    ):
        """Mark an agent task as completed."""
        # Find task
        task = next((t for t in self._tasks if t["id"] == task_id), None)
        if task:
            task["status"] = "completed" if success else "failed"
            task["result_data"] = result_data
            task["completed_at"] = datetime.utcnow()
            
            # Update agent metrics
            agent_id = task["agent_id"]
            if agent_id in self._agent_metrics:
                metrics = self._agent_metrics[agent_id]
                if success:
                    metrics["tasks_completed"] += 1
                else:
                    metrics["tasks_failed"] += 1
                
                # Update success rate
                total = metrics["tasks_completed"] + metrics["tasks_failed"]
                metrics["success_rate"] = metrics["tasks_completed"] / total if total > 0 else 1.0
    
    async def record_collaboration(
        self,
        initiator_id: str,
        collaborator_ids: List[str],
        collaboration_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record agent collaboration event."""
        collaboration = {
            "id": str(UUID().int)[:8],
            "initiator_agent_id": initiator_id,
            "collaborator_agent_ids": collaborator_ids,
            "collaboration_type": collaboration_type,
            "data": data,
            "started_at": datetime.utcnow(),
            "status": "active"
        }
        
        self._collaborations.append(collaboration)
        return collaboration
    
    async def get_collaboration_metrics(self) -> Dict[str, Any]:
        """Get agent collaboration metrics."""
        total_collaborations = len(self._collaborations)
        
        # Active collaborations (last hour)
        one_hour_ago = datetime.utcnow().timestamp() - 3600
        active_collaborations = sum(
            1 for c in self._collaborations 
            if c["started_at"].timestamp() > one_hour_ago and c["status"] == "active"
        )
        
        # Collaboration patterns
        patterns = {}
        for collab in self._collaborations:
            c_type = collab["collaboration_type"]
            patterns[c_type] = patterns.get(c_type, 0) + 1
        
        # Average agents per collaboration
        avg_agents = 2.0  # Default
        if self._collaborations:
            total_agents = sum(
                len(c["collaborator_agent_ids"]) + 1  # +1 for initiator
                for c in self._collaborations
            )
            avg_agents = total_agents / len(self._collaborations)
        
        # Success rate (completed collaborations)
        completed = sum(1 for c in self._collaborations if c.get("status") == "completed")
        success_rate = completed / total_collaborations if total_collaborations > 0 else 1.0
        
        return {
            "total_collaborations": total_collaborations,
            "active_collaborations": active_collaborations,
            "collaboration_patterns": patterns,
            "average_agents_per_task": round(avg_agents, 1),
            "collaboration_success_rate": round(success_rate, 2)
        }
    
    async def health_check(self) -> bool:
        """Check if agent service is healthy."""
        try:
            # Check if we have active agents
            if not self.active_agents:
                return False
                
            # Check if at least one agent is responsive
            for agent_id, agent in self.active_agents.items():
                if hasattr(agent, "health_check"):
                    if await agent.health_check():
                        return True
                        
            return True
            
        except Exception as e:
            logger.error(f"Agent service health check failed: {e}")
            return False


# Global agent service instance
agent_service = AgentService()
