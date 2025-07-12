"""
Multi-Agent Collaboration System

Main system for coordinating collaboration between multiple agents.
"""

from typing import List, Dict, Any, Optional
import asyncio
import uuid
import networkx as nx
from loguru import logger
from collections import defaultdict, deque
from datetime import datetime

from certify_studio.agents.core.autonomous_agent import AutonomousAgent
from .protocols import CollaborationProtocol
from .messages import AgentMessage, MessageType
from .tasks import CollaborationTask
from .workspace import SharedWorkspace
from .consensus import ConsensusResult, ConsensusBuilder
from .protocols_impl import (
    HierarchicalProtocolHandler,
    PeerToPeerProtocolHandler,
    BlackboardProtocolHandler,
    ContractNetProtocolHandler,
    SwarmProtocolHandler,
    ConsensusProtocolHandler,
)


class MultiAgentCollaborationSystem:
    """System for coordinating collaboration between multiple agents."""
    
    def __init__(self):
        self.agents: Dict[str, AutonomousAgent] = {}
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.workspaces: Dict[str, SharedWorkspace] = {}
        self.message_queue: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.task_allocations: Dict[str, CollaborationTask] = {}
        self.communication_graph = nx.DiGraph()
        
        # Initialize protocol handlers
        self.protocol_handlers = {
            CollaborationProtocol.HIERARCHICAL: HierarchicalProtocolHandler(self),
            CollaborationProtocol.PEER_TO_PEER: PeerToPeerProtocolHandler(self),
            CollaborationProtocol.BLACKBOARD: BlackboardProtocolHandler(self),
            CollaborationProtocol.CONTRACT_NET: ContractNetProtocolHandler(self),
            CollaborationProtocol.SWARM: SwarmProtocolHandler(self),
            CollaborationProtocol.CONSENSUS: ConsensusProtocolHandler(self),
        }
        
        # Performance metrics
        self.collaboration_metrics = {
            "tasks_completed": 0,
            "average_completion_time": 0,
            "consensus_success_rate": 0,
            "message_efficiency": 0
        }
        
        logger.info("Initialized MultiAgentCollaborationSystem")
    
    def register_agent(self, agent: AutonomousAgent) -> None:
        """Register an agent with the collaboration system."""
        self.agents[agent.id] = agent
        self.communication_graph.add_node(agent.id, capabilities=list(agent.capabilities))
        logger.info(f"Registered agent {agent.name} with ID {agent.id}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the collaboration system."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.communication_graph.remove_node(agent_id)
            # Clean up message queue
            if agent_id in self.message_queue:
                del self.message_queue[agent_id]
            logger.info(f"Unregistered agent {agent_id}")
    
    async def orchestrate_complex_task(
        self,
        task: CollaborationTask,
        protocol: CollaborationProtocol = CollaborationProtocol.PEER_TO_PEER
    ) -> Dict[str, Any]:
        """Orchestrate multiple agents to complete a complex task."""
        logger.info(f"Orchestrating task {task.name} with protocol {protocol.value}")
        
        collaboration_id = str(uuid.uuid4())
        
        # Decompose task if needed
        if not task.subtasks:
            subtasks = await self._decompose_task(task)
            task.subtasks = subtasks
        
        # Select agents for the task
        selected_agents = await self._select_agents_for_task(task)
        
        if not selected_agents:
            return {
                "status": "failed",
                "reason": "No suitable agents found",
                "task": task.to_dict()
            }
        
        # Initialize collaboration
        self.active_collaborations[collaboration_id] = {
            "task": task,
            "agents": selected_agents,
            "protocol": protocol,
            "start_time": datetime.now(),
            "status": "active"
        }
        
        # Execute using selected protocol
        handler = self.protocol_handlers.get(protocol)
        if not handler:
            return {
                "status": "failed",
                "reason": f"Unknown protocol: {protocol}",
                "task": task.to_dict()
            }
        
        try:
            result = await handler.execute(collaboration_id, task, selected_agents)
            
            # Update metrics
            self._update_collaboration_metrics(collaboration_id, result)
            
            # Clean up
            del self.active_collaborations[collaboration_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Collaboration failed: {e}")
            return {
                "status": "failed",
                "reason": str(e),
                "task": task.to_dict()
            }
    
    async def negotiate_consensus(
        self,
        agents: List[AutonomousAgent],
        decision: Dict[str, Any],
        max_rounds: int = 10
    ) -> ConsensusResult:
        """Achieve consensus among agents for a decision."""
        logger.info(f"Starting consensus negotiation for {len(agents)} agents")
        
        conversation_id = str(uuid.uuid4())
        proposals = {}
        votes = {}
        rounds = 0
        
        while rounds < max_rounds:
            rounds += 1
            
            # Collect proposals from each agent
            proposal_message = AgentMessage(
                sender_id="system",
                message_type=MessageType.REQUEST,
                content={
                    "decision": decision,
                    "round": rounds,
                    "previous_proposals": proposals
                },
                conversation_id=conversation_id,
                requires_response=True
            )
            
            # Broadcast and collect responses
            responses = await self._broadcast_and_collect_responses(
                agents, proposal_message, timeout=30.0
            )
            
            # Extract proposals
            for agent_id, response in responses.items():
                if response and response.message_type == MessageType.PROPOSE:
                    proposals[agent_id] = response.content
            
            # Check for consensus
            consensus_check = ConsensusBuilder.check_consensus(proposals)
            
            if consensus_check["consensus_reached"]:
                # Final voting round
                vote_message = AgentMessage(
                    sender_id="system",
                    message_type=MessageType.QUERY,
                    content={
                        "final_proposal": consensus_check["consensus_value"],
                        "action": "vote"
                    },
                    conversation_id=conversation_id,
                    requires_response=True
                )
                
                vote_responses = await self._broadcast_and_collect_responses(
                    agents, vote_message, timeout=15.0
                )
                
                # Extract votes
                for agent_id, response in vote_responses.items():
                    if response:
                        votes[agent_id] = response.content.get("vote", "abstain")
                
                # Calculate agreement level
                positive_votes = sum(1 for v in votes.values() if v == "accept")
                agreement_level = positive_votes / len(agents) if agents else 0
                
                return ConsensusResult(
                    decision=consensus_check["consensus_value"],
                    agreement_level=agreement_level,
                    participants=[a.id for a in agents],
                    votes=votes,
                    proposals=proposals,
                    rounds=rounds
                )
            
            # Share evaluations for next round
            share_message = AgentMessage(
                sender_id="system",
                message_type=MessageType.INFORM,
                content={
                    "all_proposals": proposals,
                    "consensus_metrics": consensus_check["metrics"]
                },
                conversation_id=conversation_id
            )
            
            for agent in agents:
                share_message.recipient_id = agent.id
                await self.send_message(share_message)
        
        # No consensus reached
        return ConsensusResult(
            decision=None,
            agreement_level=0,
            participants=[a.id for a in agents],
            votes={},
            proposals=proposals,
            rounds=max_rounds
        )
    
    async def create_shared_workspace(
        self,
        name: str,
        participants: List[str]
    ) -> SharedWorkspace:
        """Create a shared workspace for collaboration."""
        workspace = SharedWorkspace(
            name=name,
            participants=set(participants)
        )
        
        self.workspaces[workspace.id] = workspace
        
        # Notify participants
        for agent_id in participants:
            message = AgentMessage(
                sender_id="system",
                recipient_id=agent_id,
                message_type=MessageType.INFORM,
                content={
                    "workspace_id": workspace.id,
                    "workspace_name": name,
                    "action": "workspace_created"
                }
            )
            await self.send_message(message)
        
        return workspace
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to an agent or broadcast."""
        if message.recipient_id:
            # Direct message
            self.message_queue[message.recipient_id].append(message)
            
            # Update communication graph
            if message.sender_id != "system":
                self.communication_graph.add_edge(
                    message.sender_id,
                    message.recipient_id,
                    weight=self.communication_graph.get_edge_data(
                        message.sender_id, message.recipient_id, {}
                    ).get("weight", 0) + 1
                )
        else:
            # Broadcast message
            for agent_id in self.agents:
                if agent_id != message.sender_id:
                    self.message_queue[agent_id].append(message)
    
    async def receive_messages(self, agent_id: str, max_messages: int = 10) -> List[AgentMessage]:
        """Receive messages for an agent."""
        messages = []
        queue = self.message_queue[agent_id]
        
        for _ in range(min(len(queue), max_messages)):
            if queue:
                messages.append(queue.popleft())
        
        return messages
    
    async def allocate_task(
        self,
        task: CollaborationTask,
        protocol: CollaborationProtocol = CollaborationProtocol.CONTRACT_NET
    ) -> Dict[str, Any]:
        """Allocate a task to agents using specified protocol."""
        if protocol == CollaborationProtocol.CONTRACT_NET:
            # Use contract net protocol handler
            agents = list(self.agents.values())
            handler = self.protocol_handlers[CollaborationProtocol.CONTRACT_NET]
            return await handler.execute(str(uuid.uuid4()), task, agents)
        else:
            # Default to capability-based allocation
            return await self._capability_based_allocation(task)
    
    # Helper methods
    
    async def _decompose_task(self, task: CollaborationTask) -> List[CollaborationTask]:
        """Decompose a complex task into subtasks."""
        subtasks = []
        
        # Simple decomposition based on required capabilities
        for i, capability in enumerate(task.required_capabilities):
            subtask = CollaborationTask(
                name=f"{task.name}_subtask_{i}",
                description=f"Handle {capability} aspect of {task.name}",
                required_capabilities=[capability],
                priority=task.priority
            )
            subtasks.append(subtask)
        
        # If no specific capabilities, create generic subtasks
        if not subtasks:
            # Divide into analysis, planning, and execution
            phases = ["analysis", "planning", "execution"]
            for phase in phases:
                subtask = CollaborationTask(
                    name=f"{task.name}_{phase}",
                    description=f"{phase.capitalize()} phase of {task.name}",
                    required_capabilities=[],
                    priority=task.priority
                )
                subtasks.append(subtask)
        
        return subtasks
    
    async def _select_agents_for_task(
        self,
        task: CollaborationTask
    ) -> List[AutonomousAgent]:
        """Select suitable agents for a task based on capabilities."""
        selected = []
        
        for agent_id, agent in self.agents.items():
            # Check if agent has required capabilities
            agent_capabilities = set(c.value for c in agent.capabilities)
            required_capabilities = set(task.required_capabilities)
            
            if not required_capabilities or required_capabilities.intersection(agent_capabilities):
                selected.append(agent)
        
        # If no agents match exactly, select best matches
        if not selected and self.agents:
            # Score agents by capability overlap
            scored_agents = []
            for agent_id, agent in self.agents.items():
                agent_capabilities = set(c.value for c in agent.capabilities)
                score = len(agent_capabilities.intersection(set(task.required_capabilities)))
                scored_agents.append((score, agent))
            
            # Select top agents
            scored_agents.sort(key=lambda x: x[0], reverse=True)
            selected = [agent for _, agent in scored_agents[:min(3, len(scored_agents))]]
        
        return selected
    
    async def _broadcast_and_collect_responses(
        self,
        agents: List[AutonomousAgent],
        message: AgentMessage,
        timeout: float = 30.0
    ) -> Dict[str, AgentMessage]:
        """Broadcast message to agents and collect responses."""
        responses = {}
        
        # Send to all agents
        for agent in agents:
            msg = AgentMessage(
                sender_id=message.sender_id,
                recipient_id=agent.id,
                message_type=message.message_type,
                content=message.content,
                conversation_id=message.conversation_id,
                requires_response=message.requires_response
            )
            await self.send_message(msg)
        
        # Collect responses
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout and len(responses) < len(agents):
            for agent in agents:
                if agent.id not in responses:
                    messages = await self.receive_messages(agent.id)
                    
                    for msg in messages:
                        if msg.conversation_id == message.conversation_id:
                            responses[agent.id] = msg
                            break
            
            await asyncio.sleep(0.1)
        
        return responses
    
    async def _capability_based_allocation(self, task: CollaborationTask) -> Dict[str, Any]:
        """Simple capability-based task allocation."""
        # Find best matching agent
        best_agent = None
        best_score = 0
        
        for agent in self.agents.values():
            agent_capabilities = set(c.value for c in agent.capabilities)
            required_capabilities = set(task.required_capabilities)
            
            score = len(agent_capabilities.intersection(required_capabilities))
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if best_agent:
            task.assign_to(best_agent.id)
            self.task_allocations[task.id] = task
            
            # Notify agent
            message = AgentMessage(
                sender_id="system",
                recipient_id=best_agent.id,
                message_type=MessageType.REQUEST,
                content={
                    "action": "execute_task",
                    "task": task.to_dict()
                }
            )
            await self.send_message(message)
            
            return {
                "status": "allocated",
                "agent": best_agent.id,
                "score": best_score
            }
        
        return {
            "status": "failed",
            "reason": "No suitable agent found"
        }
    
    def _update_collaboration_metrics(self, collaboration_id: str, result: Dict[str, Any]):
        """Update collaboration performance metrics."""
        if result.get("status") == "completed":
            self.collaboration_metrics["tasks_completed"] += 1
            
            # Update average completion time
            if collaboration_id in self.active_collaborations:
                duration = (datetime.now() - self.active_collaborations[collaboration_id]["start_time"]).total_seconds()
                
                current_avg = self.collaboration_metrics["average_completion_time"]
                completed = self.collaboration_metrics["tasks_completed"]
                
                # Update running average
                self.collaboration_metrics["average_completion_time"] = (
                    (current_avg * (completed - 1) + duration) / completed
                )
    
    def get_collaboration_metrics(self) -> Dict[str, Any]:
        """Get current collaboration metrics."""
        return self.collaboration_metrics.copy()
    
    def get_workspace(self, workspace_id: str) -> Optional[SharedWorkspace]:
        """Get a workspace by ID."""
        return self.workspaces.get(workspace_id)
    
    def get_active_collaborations(self) -> List[Dict[str, Any]]:
        """Get list of active collaborations."""
        return [
            {
                "id": collab_id,
                "task": collab["task"].name,
                "protocol": collab["protocol"].value,
                "agents": [a.name for a in collab["agents"]],
                "duration": (datetime.now() - collab["start_time"]).total_seconds()
            }
            for collab_id, collab in self.active_collaborations.items()
        ]
