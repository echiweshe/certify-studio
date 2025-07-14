"""
Autonomous Agent Base Class

This module implements the core autonomous agent framework that enables
agents to think, plan, act, reflect, and collaborate independently.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
from loguru import logger

from certify_studio.core.llm import MultimodalLLM


class AgentState(Enum):
    """Possible states an agent can be in."""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COLLABORATING = "collaborating"
    LEARNING = "learning"
    WAITING = "waiting"
    ERROR = "error"


class AgentCapability(Enum):
    """Standard capabilities agents can possess."""
    REASONING = "reasoning"
    PLANNING = "planning"
    LEARNING = "learning"
    VISION = "vision"
    AUDIO = "audio"
    GENERATION = "generation"
    EVALUATION = "evaluation"
    COLLABORATION = "collaboration"
    TEACHING = "teaching"
    OPTIMIZATION = "optimization"
    # Domain extraction capabilities
    DOMAIN_EXTRACTION = "domain_extraction"
    KNOWLEDGE_GRAPH_BUILDING = "knowledge_graph_building"
    CONCEPT_IDENTIFICATION = "concept_identification"
    RELATIONSHIP_MAPPING = "relationship_mapping"
    MULTIMODAL_UNDERSTANDING = "multimodal_understanding"
    # Quality assurance capabilities
    QUALITY_ASSESSMENT = "quality_assessment"
    TECHNICAL_VALIDATION = "technical_validation"
    PERFORMANCE_MONITORING = "performance_monitoring"
    CONTINUOUS_IMPROVEMENT = "continuous_improvement"
    REPORTING = "reporting"
    CRITICAL_ANALYSIS = "critical_analysis"


@dataclass
class AgentGoal:
    """Represents a goal the agent is trying to achieve."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: float = 1.0
    deadline: Optional[datetime] = None
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    parent_goal_id: Optional[str] = None
    status: str = "active"
    progress: float = 0.0


@dataclass
class AgentBelief:
    """Represents a belief the agent holds about the world."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "observation"
    timestamp: datetime = field(default_factory=datetime.now)
    evidence: List[str] = field(default_factory=list)


@dataclass
class AgentPlan:
    """Represents a plan to achieve a goal."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    estimated_duration: float = 0.0
    required_resources: List[str] = field(default_factory=list)
    success_probability: float = 0.0
    alternative_plans: List[str] = field(default_factory=list)


@dataclass
class AgentMemory:
    """Multi-level memory system for agents."""
    short_term: List[Dict[str, Any]] = field(default_factory=list)  # Current context
    long_term: Dict[str, Any] = field(default_factory=dict)  # Learned patterns
    episodic: List[Dict[str, Any]] = field(default_factory=list)  # Past experiences
    semantic: Dict[str, Any] = field(default_factory=dict)  # Domain knowledge
    procedural: Dict[str, Any] = field(default_factory=dict)  # How-to knowledge
    
    def add_to_short_term(self, item: Dict[str, Any], max_items: int = 10):
        """Add item to short-term memory with size limit."""
        self.short_term.append(item)
        if len(self.short_term) > max_items:
            self.short_term.pop(0)
    
    def consolidate_to_long_term(self, pattern: str, data: Any):
        """Move important patterns to long-term memory."""
        if pattern not in self.long_term:
            self.long_term[pattern] = []
        self.long_term[pattern].append({
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0
        })
    
    def recall_from_episodic(self, query: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Recall similar experiences from episodic memory."""
        # Simple similarity based on matching keys
        # In production, use vector similarity
        relevant = []
        for episode in self.episodic:
            similarity = len(set(query.keys()) & set(episode.keys()))
            if similarity > 0:
                relevant.append((similarity, episode))
        
        relevant.sort(key=lambda x: x[0], reverse=True)
        return [episode for _, episode in relevant[:limit]]


class AutonomousAgent(ABC):
    """Base class for all autonomous agents in the system."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[AgentCapability],
        llm: Optional[MultimodalLLM] = None
    ):
        self.id = agent_id
        self.name = name
        self.state = AgentState.IDLE
        self.capabilities = set(capabilities)
        self.memory = AgentMemory()
        self.goals: List[AgentGoal] = []
        self.beliefs: Dict[str, AgentBelief] = {}
        self.plans: List[AgentPlan] = []
        self.current_plan: Optional[AgentPlan] = None
        self.llm = llm
        self.performance_metrics: Dict[str, float] = {}
        self.collaboration_partners: Set[str] = set()
        
        logger.info(f"Initialized agent {self.name} with capabilities: {[c.value for c in capabilities]}")
    
    async def perceive(self, observation: Dict[str, Any]) -> None:
        """Process new observations from the environment."""
        logger.debug(f"Agent {self.name} perceiving: {observation}")
        
        # Add to short-term memory
        self.memory.add_to_short_term({
            "type": "observation",
            "data": observation,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update beliefs based on observation
        await self._update_beliefs(observation)
    
    async def think(self) -> Dict[str, Any]:
        """Main cognitive loop - analyze situation and decide what to do."""
        self.state = AgentState.THINKING
        
        try:
            # Analyze current situation
            situation_analysis = await self._analyze_situation()
            
            # Generate or update goals based on situation
            await self._update_goals(situation_analysis)
            
            # Generate intentions (desired states)
            intentions = await self._generate_intentions()
            
            # Create or update plans
            await self._update_plans(intentions)
            
            # Select best plan
            selected_plan = await self._select_plan()
            
            self.current_plan = selected_plan
            
            return {
                "situation": situation_analysis,
                "intentions": intentions,
                "selected_plan": selected_plan.id if selected_plan else None,
                "confidence": self._calculate_confidence()
            }
            
        except Exception as e:
            logger.error(f"Error during thinking: {e}")
            self.state = AgentState.ERROR
            raise
    
    async def act(self) -> Dict[str, Any]:
        """Execute the current plan."""
        if not self.current_plan:
            return {"status": "no_action", "reason": "no_current_plan"}
        
        self.state = AgentState.EXECUTING
        
        try:
            # Get next step from plan
            if not self.current_plan.steps:
                return {"status": "complete", "plan_id": self.current_plan.id}
            
            next_step = self.current_plan.steps[0]
            
            # Execute the step
            result = await self._execute_step(next_step)
            
            # Remove completed step
            self.current_plan.steps.pop(0)
            
            # Add to episodic memory
            self.memory.episodic.append({
                "action": next_step,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "plan_id": self.current_plan.id
            })
            
            # Update performance metrics
            await self._update_performance_metrics(next_step, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during action: {e}")
            self.state = AgentState.ERROR
            return {"status": "error", "error": str(e)}
    
    async def reflect(self, outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from actions and outcomes."""
        self.state = AgentState.REFLECTING
        
        try:
            # Evaluate outcome against expectations
            evaluation = await self._evaluate_outcome(outcome)
            
            # Extract lessons learned
            lessons = await self._extract_lessons(evaluation)
            
            # Update long-term memory
            for lesson in lessons:
                self.memory.consolidate_to_long_term(
                    lesson["pattern"],
                    lesson["data"]
                )
            
            # Update beliefs based on outcome
            await self._update_beliefs_from_outcome(outcome, evaluation)
            
            # Adjust future strategies
            strategy_adjustments = await self._adjust_strategies(evaluation)
            
            return {
                "evaluation": evaluation,
                "lessons_learned": lessons,
                "strategy_adjustments": strategy_adjustments
            }
            
        except Exception as e:
            logger.error(f"Error during reflection: {e}")
            self.state = AgentState.ERROR
            raise
    
    async def collaborate(
        self,
        partners: List['AutonomousAgent'],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collaborate with other agents on a task."""
        self.state = AgentState.COLLABORATING
        
        try:
            # Share relevant knowledge
            shared_knowledge = await self._prepare_knowledge_share(task)
            
            # Negotiate roles based on capabilities
            role_assignment = await self._negotiate_roles(partners, task)
            
            # Create coordination plan
            coordination_plan = await self._create_coordination_plan(
                role_assignment, task
            )
            
            # Update collaboration partners
            self.collaboration_partners.update([p.id for p in partners])
            
            return {
                "shared_knowledge": shared_knowledge,
                "role_assignment": role_assignment,
                "coordination_plan": coordination_plan
            }
            
        except Exception as e:
            logger.error(f"Error during collaboration: {e}")
            self.state = AgentState.ERROR
            raise
    
    async def learn(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Learn from training data to improve performance."""
        self.state = AgentState.LEARNING
        
        try:
            # Analyze patterns in training data
            patterns = await self._analyze_patterns(training_data)
            
            # Update procedural knowledge
            procedures = await self._extract_procedures(training_data)
            for proc in procedures:
                self.memory.procedural[proc["name"]] = proc["steps"]
            
            # Update semantic knowledge
            concepts = await self._extract_concepts(training_data)
            for concept in concepts:
                self.memory.semantic[concept["name"]] = concept["definition"]
            
            # Adjust internal models
            model_updates = await self._update_internal_models(patterns)
            
            return {
                "patterns_learned": len(patterns),
                "procedures_learned": len(procedures),
                "concepts_learned": len(concepts),
                "model_updates": model_updates
            }
            
        except Exception as e:
            logger.error(f"Error during learning: {e}")
            self.state = AgentState.ERROR
            raise
    
    def _calculate_confidence(self) -> float:
        """Calculate overall confidence in current decisions."""
        if not self.current_plan:
            return 0.0
        
        # Factors: plan success probability, belief confidence, past performance
        plan_confidence = self.current_plan.success_probability
        
        belief_confidence = sum(b.confidence for b in self.beliefs.values()) / max(len(self.beliefs), 1)
        
        performance_confidence = sum(self.performance_metrics.values()) / max(len(self.performance_metrics), 1)
        
        # Weighted average
        weights = [0.4, 0.3, 0.3]
        values = [plan_confidence, belief_confidence, performance_confidence]
        
        return sum(w * v for w, v in zip(weights, values))
    
    # Abstract methods that subclasses must implement
    
    @abstractmethod
    async def _analyze_situation(self) -> Dict[str, Any]:
        """Analyze current situation based on observations and beliefs."""
        pass
    
    @abstractmethod
    async def _update_beliefs(self, observation: Dict[str, Any]) -> None:
        """Update beliefs based on new observations."""
        pass
    
    @abstractmethod
    async def _generate_intentions(self) -> List[Dict[str, Any]]:
        """Generate intentions based on goals and beliefs."""
        pass
    
    @abstractmethod
    async def _update_plans(self, intentions: List[Dict[str, Any]]) -> None:
        """Create or update plans to achieve intentions."""
        pass
    
    @abstractmethod
    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step from a plan."""
        pass
    
    @abstractmethod
    async def _evaluate_outcome(self, outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the outcome of an action."""
        pass
    
    # Helper methods with default implementations
    
    async def _update_goals(self, situation: Dict[str, Any]) -> None:
        """Update goals based on situation analysis."""
        # Default: Keep existing goals
        pass
    
    async def _select_plan(self) -> Optional[AgentPlan]:
        """Select the best plan from available options."""
        if not self.plans:
            return None
        
        # Default: Select plan with highest success probability
        return max(self.plans, key=lambda p: p.success_probability)
    
    async def _extract_lessons(self, evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract lessons from evaluation."""
        lessons = []
        
        if evaluation.get("success", False):
            lessons.append({
                "pattern": "successful_action",
                "data": {
                    "action": evaluation.get("action"),
                    "context": evaluation.get("context"),
                    "outcome": evaluation.get("outcome")
                }
            })
        else:
            lessons.append({
                "pattern": "failed_action",
                "data": {
                    "action": evaluation.get("action"),
                    "context": evaluation.get("context"),
                    "failure_reason": evaluation.get("failure_reason")
                }
            })
        
        return lessons
    
    async def _update_beliefs_from_outcome(
        self,
        outcome: Dict[str, Any],
        evaluation: Dict[str, Any]
    ) -> None:
        """Update beliefs based on action outcomes."""
        # Default implementation: Adjust confidence based on success
        if evaluation.get("success", False):
            # Increase confidence in related beliefs
            for belief in self.beliefs.values():
                if belief.source == "prediction":
                    belief.confidence = min(1.0, belief.confidence * 1.1)
        else:
            # Decrease confidence in related beliefs
            for belief in self.beliefs.values():
                if belief.source == "prediction":
                    belief.confidence = max(0.1, belief.confidence * 0.9)
    
    async def _adjust_strategies(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust strategies based on evaluation."""
        adjustments = {}
        
        if not evaluation.get("success", False):
            adjustments["risk_tolerance"] = "decrease"
            adjustments["exploration_rate"] = "increase"
        else:
            adjustments["risk_tolerance"] = "maintain"
            adjustments["exploration_rate"] = "decrease"
        
        return adjustments
    
    async def _update_performance_metrics(
        self,
        action: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Update performance metrics based on action results."""
        action_type = action.get("type", "unknown")
        success = result.get("status") == "success"
        
        if action_type not in self.performance_metrics:
            self.performance_metrics[action_type] = 0.5
        
        # Exponential moving average
        alpha = 0.1
        current = self.performance_metrics[action_type]
        new_value = 1.0 if success else 0.0
        self.performance_metrics[action_type] = alpha * new_value + (1 - alpha) * current
    
    async def _prepare_knowledge_share(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare relevant knowledge to share with collaborators."""
        relevant_knowledge = {
            "beliefs": {k: v for k, v in self.beliefs.items() if self._is_relevant_to_task(k, task)},
            "procedures": {k: v for k, v in self.memory.procedural.items() if self._is_relevant_to_task(k, task)},
            "past_experiences": self.memory.recall_from_episodic(task, limit=3)
        }
        
        return relevant_knowledge
    
    async def _negotiate_roles(
        self,
        partners: List['AutonomousAgent'],
        task: Dict[str, Any]
    ) -> Dict[str, str]:
        """Negotiate role assignment with partners."""
        # Simple capability-based assignment
        role_assignment = {}
        required_capabilities = task.get("required_capabilities", [])
        
        # Assign self
        my_capabilities = [c.value for c in self.capabilities]
        my_roles = [cap for cap in required_capabilities if cap in my_capabilities]
        if my_roles:
            role_assignment[self.id] = my_roles[0]
        
        # Assign partners
        for partner in partners:
            partner_capabilities = [c.value for c in partner.capabilities]
            partner_roles = [cap for cap in required_capabilities if cap in partner_capabilities and cap not in role_assignment.values()]
            if partner_roles:
                role_assignment[partner.id] = partner_roles[0]
        
        return role_assignment
    
    async def _create_coordination_plan(
        self,
        role_assignment: Dict[str, str],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a coordination plan for collaborative task."""
        plan = {
            "task_id": task.get("id", str(uuid.uuid4())),
            "roles": role_assignment,
            "communication_protocol": "async_message_passing",
            "checkpoints": self._generate_checkpoints(task),
            "conflict_resolution": "consensus_voting"
        }
        
        return plan
    
    def _is_relevant_to_task(self, knowledge_key: str, task: Dict[str, Any]) -> bool:
        """Check if knowledge is relevant to task."""
        # Simple keyword matching - can be enhanced with embeddings
        task_keywords = set(task.get("keywords", []))
        knowledge_keywords = set(knowledge_key.lower().split("_"))
        
        return bool(task_keywords & knowledge_keywords)
    
    def _generate_checkpoints(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate checkpoints for task coordination."""
        duration = task.get("estimated_duration", 3600)  # Default 1 hour
        num_checkpoints = min(5, max(2, int(duration / 900)))  # Every 15 min, max 5
        
        checkpoints = []
        for i in range(num_checkpoints):
            checkpoints.append({
                "id": f"checkpoint_{i}",
                "time_offset": (i + 1) * (duration / num_checkpoints),
                "required_updates": ["status", "progress", "blockers"]
            })
        
        return checkpoints
    
    async def _analyze_patterns(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze patterns in data."""
        # Placeholder - implement pattern recognition
        return []
    
    async def _extract_procedures(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract procedural knowledge from data."""
        # Placeholder - implement procedure extraction
        return []
    
    async def _extract_concepts(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract conceptual knowledge from data."""
        # Placeholder - implement concept extraction
        return []
    
    async def _update_internal_models(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update internal models based on patterns."""
        # Placeholder - implement model updates
        return {"models_updated": 0}
