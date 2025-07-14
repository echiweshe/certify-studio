"""
Knowledge Integration Module for GraphRAG.

This module integrates the troubleshooting GraphRAG with the existing
learning knowledge graph, enabling cross-referencing between educational
content and troubleshooting information.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from uuid import UUID, uuid4

from loguru import logger
import networkx as nx

from .models import (
    TroubleshootingIssue,
    Solution,
    RootCause,
    IssueType,
    RelationshipType
)
from .graph_store import Neo4jGraphStore, GraphRAGConfig
from ..agents.specialized.domain_extraction.models import (
    Concept,
    ConceptType,
    DomainCategory
)


class ConceptToIssueMapper:
    """Maps learning concepts to troubleshooting issues."""
    
    def __init__(self):
        # Mapping rules between concept types and issue types
        self.concept_to_issue_mapping = {
            ConceptType.SERVICE: [
                IssueType.CONNECTIVITY,
                IssueType.CONFIGURATION,
                IssueType.PERFORMANCE
            ],
            ConceptType.SECURITY: [
                IssueType.AUTHENTICATION,
                IssueType.SECURITY
            ],
            ConceptType.NETWORKING: [
                IssueType.CONNECTIVITY,
                IssueType.CONFIGURATION
            ],
            ConceptType.STORAGE: [
                IssueType.DATA_INTEGRITY,
                IssueType.PERFORMANCE,
                IssueType.RESOURCE_LIMIT
            ],
            ConceptType.COMPUTE: [
                IssueType.RESOURCE_LIMIT,
                IssueType.PERFORMANCE,
                IssueType.DEPLOYMENT
            ]
        }
        
        # Common issue patterns for concepts
        self.concept_issue_patterns = {
            "EC2": [
                ("Instance not reachable", IssueType.CONNECTIVITY),
                ("Instance running slow", IssueType.PERFORMANCE),
                ("Cannot SSH to instance", IssueType.SECURITY)
            ],
            "S3": [
                ("Access Denied error", IssueType.AUTHENTICATION),
                ("Bucket not found", IssueType.CONFIGURATION),
                ("Upload timeout", IssueType.CONNECTIVITY)
            ],
            "RDS": [
                ("Connection timeout", IssueType.CONNECTIVITY),
                ("Slow queries", IssueType.PERFORMANCE),
                ("Storage full", IssueType.RESOURCE_LIMIT)
            ],
            "Lambda": [
                ("Function timeout", IssueType.PERFORMANCE),
                ("Execution role error", IssueType.AUTHENTICATION),
                ("Cold start issues", IssueType.PERFORMANCE)
            ]
        }
        
    def map_concept_to_issues(self, concept: Concept) -> List[Tuple[str, IssueType]]:
        """Map a learning concept to potential troubleshooting issues."""
        issues = []
        
        # Get issue types based on concept type
        issue_types = self.concept_to_issue_mapping.get(
            concept.type,
            [IssueType.UNKNOWN]
        )
        
        # Check for specific patterns
        if concept.name in self.concept_issue_patterns:
            issues.extend(self.concept_issue_patterns[concept.name])
        else:
            # Generate generic issues based on type
            for issue_type in issue_types:
                issue_title = f"{concept.name} {issue_type.value} issue"
                issues.append((issue_title, issue_type))
                
        return issues
        
    def identify_troubleshooting_topics(
        self,
        concepts: List[Concept]
    ) -> Dict[str, List[Concept]]:
        """Group concepts by troubleshooting relevance."""
        troubleshooting_groups = {
            "connectivity": [],
            "performance": [],
            "security": [],
            "configuration": [],
            "resources": []
        }
        
        for concept in concepts:
            # Categorize based on concept properties
            if concept.type == ConceptType.NETWORKING:
                troubleshooting_groups["connectivity"].append(concept)
            elif concept.type == ConceptType.SECURITY:
                troubleshooting_groups["security"].append(concept)
            elif concept.type in [ConceptType.COMPUTE, ConceptType.STORAGE]:
                troubleshooting_groups["resources"].append(concept)
                troubleshooting_groups["performance"].append(concept)
            elif concept.type == ConceptType.SERVICE:
                troubleshooting_groups["configuration"].append(concept)
                
        return troubleshooting_groups


class KnowledgeGraphIntegrator:
    """Integrates learning and troubleshooting knowledge graphs."""
    
    def __init__(
        self,
        graphrag_store: Neo4jGraphStore,
        learning_graph: nx.DiGraph
    ):
        self.graphrag_store = graphrag_store
        self.learning_graph = learning_graph
        self.concept_mapper = ConceptToIssueMapper()
        self._integration_cache = {}
        
    async def integrate_concept(
        self,
        concept: Concept,
        auto_generate_issues: bool = True
    ) -> List[str]:
        """
        Integrate a learning concept into the troubleshooting graph.
        
        Args:
            concept: Learning concept to integrate
            auto_generate_issues: Whether to auto-generate common issues
            
        Returns:
            List of created issue IDs
        """
        created_issues = []
        
        try:
            # Map concept to potential issues
            potential_issues = self.concept_mapper.map_concept_to_issues(concept)
            
            if auto_generate_issues:
                for issue_title, issue_type in potential_issues:
                    # Create troubleshooting issue
                    issue = TroubleshootingIssue(
                        title=issue_title,
                        description=f"Common {issue_type.value} issue with {concept.name}",
                        symptoms=self._generate_symptoms(concept, issue_type),
                        type=issue_type,
                        affected_components=[concept.name],
                        related_concepts=[concept.name],
                        metadata={
                            "concept_id": str(concept.id),
                            "concept_type": concept.type.value,
                            "auto_generated": True
                        }
                    )
                    
                    # Add to GraphRAG
                    issue_id = await self.graphrag_store.add_issue(issue)
                    created_issues.append(issue_id)
                    
                    # Generate basic root causes
                    causes = self._generate_root_causes(concept, issue_type)
                    for cause in causes:
                        cause.issue_id = UUID(issue_id)
                        await self.graphrag_store.add_root_cause(cause)
                        
                    # Generate basic solutions
                    solutions = self._generate_solutions(concept, issue_type)
                    for solution in solutions:
                        solution.applies_to_issues = [UUID(issue_id)]
                        await self.graphrag_store.add_solution(solution)
                        
            # Create relationships between concept and issues
            await self._create_concept_issue_relationships(
                concept,
                created_issues
            )
            
            logger.info(
                f"Integrated concept '{concept.name}' with "
                f"{len(created_issues)} troubleshooting issues"
            )
            
        except Exception as e:
            logger.error(f"Error integrating concept: {e}")
            raise
            
        return created_issues
        
    def _generate_symptoms(
        self,
        concept: Concept,
        issue_type: IssueType
    ) -> List[str]:
        """Generate common symptoms for a concept-issue combination."""
        symptoms = []
        
        # Base symptoms by issue type
        base_symptoms = {
            IssueType.CONNECTIVITY: [
                "connection timeout",
                "unable to reach",
                "network unreachable"
            ],
            IssueType.PERFORMANCE: [
                "slow response",
                "high latency",
                "timeout errors"
            ],
            IssueType.AUTHENTICATION: [
                "access denied",
                "401 unauthorized",
                "403 forbidden"
            ],
            IssueType.CONFIGURATION: [
                "invalid configuration",
                "missing parameter",
                "incorrect settings"
            ],
            IssueType.RESOURCE_LIMIT: [
                "quota exceeded",
                "out of memory",
                "disk full"
            ]
        }
        
        symptoms.extend(base_symptoms.get(issue_type, []))
        
        # Add concept-specific symptoms
        symptoms.append(f"{concept.name} not working")
        symptoms.append(f"Error with {concept.name}")
        
        return symptoms
        
    def _generate_root_causes(
        self,
        concept: Concept,
        issue_type: IssueType
    ) -> List[RootCause]:
        """Generate common root causes for a concept-issue combination."""
        causes = []
        
        # Common root causes by issue type
        if issue_type == IssueType.CONNECTIVITY:
            causes.append(RootCause(
                title=f"{concept.name} network configuration issue",
                description="Network settings preventing connectivity",
                likelihood=0.7,
                diagnostic_steps=[
                    f"Check {concept.name} network settings",
                    "Verify security group rules",
                    "Test network connectivity"
                ],
                verification_commands=[
                    "ping", "telnet", "nslookup"
                ]
            ))
            
        elif issue_type == IssueType.AUTHENTICATION:
            causes.append(RootCause(
                title=f"{concept.name} permission issue",
                description="Insufficient permissions or incorrect credentials",
                likelihood=0.8,
                diagnostic_steps=[
                    "Verify IAM permissions",
                    "Check access keys",
                    "Review policy attachments"
                ],
                verification_commands=[
                    "aws iam get-user",
                    "aws sts get-caller-identity"
                ]
            ))
            
        return causes
        
    def _generate_solutions(
        self,
        concept: Concept,
        issue_type: IssueType
    ) -> List[Solution]:
        """Generate basic solutions for a concept-issue combination."""
        solutions = []
        
        # Common solutions by issue type
        if issue_type == IssueType.CONNECTIVITY:
            solutions.append(Solution(
                title=f"Fix {concept.name} connectivity",
                description="Steps to resolve connectivity issues",
                steps=[
                    f"Verify {concept.name} is running",
                    "Check network configuration",
                    "Update security group rules",
                    "Test connectivity"
                ],
                prerequisites=["AWS CLI access", "Network access"],
                success_rate=0.75,
                avg_implementation_time=15.0,
                risk_level="low"
            ))
            
        elif issue_type == IssueType.AUTHENTICATION:
            solutions.append(Solution(
                title=f"Resolve {concept.name} authentication",
                description="Fix permission and authentication issues",
                steps=[
                    "Review IAM policies",
                    "Update permissions",
                    "Regenerate credentials if needed",
                    "Test access"
                ],
                prerequisites=["IAM access"],
                success_rate=0.85,
                avg_implementation_time=10.0,
                risk_level="low"
            ))
            
        return solutions
        
    async def _create_concept_issue_relationships(
        self,
        concept: Concept,
        issue_ids: List[str]
    ):
        """Create relationships between learning concepts and issues."""
        # In Neo4j, we'd create a relationship between the concept
        # (from learning graph) and issues (in troubleshooting graph)
        # For now, we store this in issue metadata
        pass
        
    async def find_troubleshooting_for_concept(
        self,
        concept_name: str
    ) -> Dict[str, Any]:
        """
        Find all troubleshooting information related to a concept.
        
        Args:
            concept_name: Name of the learning concept
            
        Returns:
            Dictionary with issues, causes, and solutions
        """
        # Query GraphRAG for issues related to this concept
        query = f"Issues with {concept_name}"
        result = await self.graphrag_store.graph_rag_search({
            "query_text": query,
            "component_filter": [concept_name]
        })
        
        return {
            "concept": concept_name,
            "issues": result.identified_issues,
            "root_causes": result.root_causes,
            "solutions": result.solutions,
            "diagnostic_paths": result.diagnostic_paths
        }
        
    async def generate_troubleshooting_guide(
        self,
        concept: Concept
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive troubleshooting guide for a concept.
        
        Args:
            concept: Learning concept
            
        Returns:
            Troubleshooting guide with common issues and solutions
        """
        guide = {
            "concept": {
                "name": concept.name,
                "type": concept.type.value,
                "description": concept.description
            },
            "common_issues": [],
            "diagnostic_checklist": [],
            "quick_fixes": [],
            "preventive_measures": []
        }
        
        # Get potential issues
        potential_issues = self.concept_mapper.map_concept_to_issues(concept)
        
        for issue_title, issue_type in potential_issues:
            issue_guide = {
                "title": issue_title,
                "type": issue_type.value,
                "symptoms": self._generate_symptoms(concept, issue_type),
                "causes": [],
                "solutions": []
            }
            
            # Add causes and solutions
            causes = self._generate_root_causes(concept, issue_type)
            for cause in causes:
                issue_guide["causes"].append({
                    "title": cause.title,
                    "likelihood": cause.likelihood,
                    "diagnostic_steps": cause.diagnostic_steps
                })
                
            solutions = self._generate_solutions(concept, issue_type)
            for solution in solutions:
                issue_guide["solutions"].append({
                    "title": solution.title,
                    "steps": solution.steps,
                    "time_estimate": solution.avg_implementation_time
                })
                
            guide["common_issues"].append(issue_guide)
            
        # Add diagnostic checklist
        guide["diagnostic_checklist"] = [
            f"Verify {concept.name} is properly configured",
            f"Check {concept.name} status and health",
            "Review recent changes",
            "Check logs for errors",
            "Verify network connectivity",
            "Confirm permissions and access"
        ]
        
        # Add quick fixes
        guide["quick_fixes"] = [
            f"Restart {concept.name} service",
            "Clear cache/temporary files",
            "Verify credentials",
            "Check resource limits"
        ]
        
        # Add preventive measures
        guide["preventive_measures"] = [
            "Set up monitoring and alerts",
            "Regular backups",
            "Document configuration changes",
            "Implement health checks",
            "Plan for capacity"
        ]
        
        return guide
        
    async def sync_learning_to_troubleshooting(
        self,
        concepts: List[Concept],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Sync learning concepts to troubleshooting graph in batches.
        
        Args:
            concepts: List of concepts to sync
            batch_size: Number of concepts to process at once
            
        Returns:
            Sync statistics
        """
        stats = {
            "total_concepts": len(concepts),
            "synced": 0,
            "issues_created": 0,
            "errors": []
        }
        
        # Process in batches
        for i in range(0, len(concepts), batch_size):
            batch = concepts[i:i + batch_size]
            
            for concept in batch:
                try:
                    issue_ids = await self.integrate_concept(concept)
                    stats["synced"] += 1
                    stats["issues_created"] += len(issue_ids)
                except Exception as e:
                    stats["errors"].append({
                        "concept": concept.name,
                        "error": str(e)
                    })
                    
        return stats


class HybridSearchEngine:
    """
    Hybrid search engine that searches both learning and troubleshooting graphs.
    """
    
    def __init__(
        self,
        graphrag_index,
        learning_vector_store
    ):
        self.graphrag_index = graphrag_index
        self.learning_store = learning_vector_store
        
    async def hybrid_search(
        self,
        query: str,
        search_mode: str = "both"  # "learning", "troubleshooting", "both"
    ) -> Dict[str, Any]:
        """
        Perform hybrid search across both knowledge bases.
        
        Args:
            query: Search query
            search_mode: Which graphs to search
            
        Returns:
            Combined search results
        """
        results = {
            "query": query,
            "learning_results": [],
            "troubleshooting_results": [],
            "cross_references": []
        }
        
        # Search learning graph
        if search_mode in ["learning", "both"]:
            learning_results = await self.learning_store.search({
                "query": query,
                "max_results": 5
            })
            results["learning_results"] = [
                {
                    "concept": r.concept.name,
                    "type": r.concept.type.value,
                    "relevance": r.relevance_score,
                    "description": r.concept.description
                }
                for r in learning_results
            ]
            
        # Search troubleshooting graph
        if search_mode in ["troubleshooting", "both"]:
            troubleshooting_results = await self.graphrag_index.troubleshoot(query)
            results["troubleshooting_results"] = {
                "issues": [
                    {
                        "title": issue.title,
                        "type": issue.type.value,
                        "severity": issue.severity.value
                    }
                    for issue in troubleshooting_results.identified_issues
                ],
                "solutions": [
                    {
                        "title": solution.title,
                        "success_rate": solution.success_rate
                    }
                    for solution in troubleshooting_results.solutions
                ]
            }
            
        # Find cross-references
        if search_mode == "both" and results["learning_results"] and results["troubleshooting_results"]["issues"]:
            # Find concepts mentioned in issues
            for learning_result in results["learning_results"]:
                concept_name = learning_result["concept"]
                
                for issue in results["troubleshooting_results"]["issues"]:
                    if concept_name.lower() in issue["title"].lower():
                        results["cross_references"].append({
                            "concept": concept_name,
                            "issue": issue["title"],
                            "relationship": "concept_has_issue"
                        })
                        
        return results
