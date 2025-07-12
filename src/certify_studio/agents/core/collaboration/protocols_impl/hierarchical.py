"""
Hierarchical Protocol Handler

Implements hierarchical collaboration where one agent leads and others follow.
"""

from typing import List, Dict, Any
from loguru import logger

from certify_studio.agents.core.autonomous_agent import AutonomousAgent
from ..tasks import CollaborationTask
from ..messages import AgentMessage, MessageType
from .base import BaseProtocolHandler


class HierarchicalProtocolHandler(BaseProtocolHandler):
    """Handler for hierarchical collaboration protocol."""
    
    async def execute(
        self,
        collaboration_id: str,
        task: CollaborationTask,
        agents: List[AutonomousAgent]
    ) -> Dict[str, Any]:
        """Execute hierarchical protocol with leader-follower structure."""
        logger.info(f"Executing hierarchical protocol for task {task.name}")
        
        # Select leader based on capabilities and experience
        leader = await self._select_leader(agents, task)
        followers = [a for a in agents if a.id != leader.id]
        
        logger.info(f"Selected leader: {leader.name}, followers: {[f.name for f in followers]}")
        
        # Leader creates execution plan
        plan_message = AgentMessage(
            sender_id="system",
            recipient_id=leader.id,
            message_type=MessageType.REQUEST,
            content={
                "action": "create_plan",
                "task": task.to_dict(),
                "available_agents": [{"id": a.id, "capabilities": [c.value for c in a.capabilities]} for a in followers]
            },
            conversation_id=collaboration_id,
            requires_response=True
        )
        
        plan_response = await self.send_message_and_wait(leader, plan_message)
        
        if not plan_response:
            return {"status": "failed", "reason": "Leader failed to create plan"}
        
        execution_plan = plan_response.content.get("plan", {})
        
        # Distribute subtasks to followers
        results = {}
        for subtask_id, subtask_info in execution_plan.items():
            assigned_agent_id = subtask_info.get("assigned_to")
            if assigned_agent_id and assigned_agent_id in [a.id for a in followers]:
                agent = next(a for a in followers if a.id == assigned_agent_id)
                
                # Send subtask to agent
                subtask_message = AgentMessage(
                    sender_id=leader.id,
                    recipient_id=agent.id,
                    message_type=MessageType.REQUEST,
                    content={
                        "action": "execute_subtask",
                        "subtask": subtask_info,
                        "leader_id": leader.id
                    },
                    conversation_id=collaboration_id,
                    requires_response=True
                )
                
                result = await self.send_message_and_wait(agent, subtask_message, timeout=60.0)
                results[subtask_id] = result.content if result else {"status": "failed", "reason": "timeout"}
        
        # Leader aggregates results
        aggregate_message = AgentMessage(
            sender_id="system",
            recipient_id=leader.id,
            message_type=MessageType.REQUEST,
            content={
                "action": "aggregate_results",
                "results": results,
                "original_task": task.to_dict()
            },
            conversation_id=collaboration_id,
            requires_response=True
        )
        
        final_result = await self.send_message_and_wait(leader, aggregate_message, timeout=30.0)
        
        return {
            "status": "completed",
            "protocol": "hierarchical",
            "leader": leader.id,
            "followers": [f.id for f in followers],
            "execution_plan": execution_plan,
            "subtask_results": results,
            "final_result": final_result.content if final_result else results
        }
    
    async def _select_leader(
        self,
        agents: List[AutonomousAgent],
        task: CollaborationTask
    ) -> AutonomousAgent:
        """Select a leader for hierarchical collaboration."""
        # Score agents based on capabilities and performance
        scores = []
        
        for agent in agents:
            score = 0
            
            # Capability match
            agent_capabilities = set(c.value for c in agent.capabilities)
            required_capabilities = set(task.required_capabilities)
            capability_score = len(agent_capabilities.intersection(required_capabilities))
            score += capability_score * 10
            
            # Performance metrics
            if hasattr(agent, 'performance_metrics'):
                avg_performance = sum(agent.performance_metrics.values()) / max(len(agent.performance_metrics), 1)
                score += avg_performance * 5
            
            # Experience (based on memory)
            if hasattr(agent, 'memory') and agent.memory.episodic:
                score += min(len(agent.memory.episodic), 10)
            
            # Leadership capability
            if any(c.value == "leadership" for c in agent.capabilities):
                score += 20
            
            scores.append((score, agent))
        
        # Select agent with highest score
        scores.sort(key=lambda x: x[0], reverse=True)
        selected_leader = scores[0][1]
        
        logger.debug(f"Leader selection scores: {[(a.name, s) for s, a in scores]}")
        
        return selected_leader
