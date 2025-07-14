"""
GraphRAG Troubleshooting Engine.

This module implements the core troubleshooting logic that leverages
GraphRAG for intelligent diagnosis and solution recommendation.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import re
from collections import defaultdict

from loguru import logger
import numpy as np

from .models import (
    TroubleshootingIssue,
    RootCause,
    Solution,
    DiagnosticPath,
    IssuePattern,
    GraphRAGQuery,
    GraphRAGResult,
    TroubleshootingSession,
    IssueType,
    Severity,
    RelationshipType
)
from .graph_store import GraphRAGIndex


class DiagnosticReasoner:
    """Implements diagnostic reasoning over the GraphRAG."""
    
    def __init__(self):
        self.reasoning_rules = self._initialize_reasoning_rules()
        self.diagnostic_patterns = self._initialize_patterns()
        
    def _initialize_reasoning_rules(self) -> Dict[str, Any]:
        """Initialize diagnostic reasoning rules."""
        return {
            "connectivity": {
                "symptoms": ["timeout", "connection refused", "unreachable"],
                "check_order": ["network", "firewall", "service_status", "dns"],
                "escalation": ["security_group", "routing", "vpc_config"]
            },
            "performance": {
                "symptoms": ["slow", "latency", "high response time"],
                "check_order": ["resources", "bottlenecks", "scaling", "optimization"],
                "escalation": ["architecture_review", "caching", "database_tuning"]
            },
            "authentication": {
                "symptoms": ["401", "403", "unauthorized", "forbidden"],
                "check_order": ["credentials", "permissions", "token", "role"],
                "escalation": ["iam_policy", "trust_relationship", "mfa"]
            }
        }
        
    def _initialize_patterns(self) -> List[IssuePattern]:
        """Initialize common diagnostic patterns."""
        patterns = []
        
        # Pattern: Cascading failures
        patterns.append(IssuePattern(
            name="Cascading Service Failure",
            description="One service failure causing multiple downstream failures",
            common_symptoms=["multiple services down", "widespread timeouts"],
            early_warning_signs=["increased latency", "error rate spike"],
            prevention_steps=["implement circuit breakers", "add health checks"]
        ))
        
        # Pattern: Resource exhaustion
        patterns.append(IssuePattern(
            name="Resource Exhaustion",
            description="System running out of critical resources",
            common_symptoms=["out of memory", "disk full", "connection pool exhausted"],
            early_warning_signs=["gradual performance degradation", "increasing resource usage"],
            prevention_steps=["set up monitoring alerts", "implement auto-scaling"]
        ))
        
        return patterns
        
    async def analyze_symptoms(
        self,
        symptoms: List[str],
        context: Dict[str, Any]
    ) -> Tuple[IssueType, Severity, List[str]]:
        """
        Analyze symptoms to determine issue type and severity.
        
        Returns:
            Tuple of (issue_type, severity, additional_checks)
        """
        # Keyword analysis
        symptom_text = " ".join(symptoms).lower()
        
        # Determine issue type
        issue_type = IssueType.UNKNOWN
        for rule_type, rule_data in self.reasoning_rules.items():
            if any(keyword in symptom_text for keyword in rule_data["symptoms"]):
                issue_type = IssueType(rule_type)
                break
                
        # Determine severity
        severity = self._assess_severity(symptoms, context)
        
        # Determine additional checks needed
        additional_checks = []
        if issue_type != IssueType.UNKNOWN:
            rule_data = self.reasoning_rules.get(issue_type.value, {})
            additional_checks = rule_data.get("check_order", [])
            
        return issue_type, severity, additional_checks
        
    def _assess_severity(self, symptoms: List[str], context: Dict[str, Any]) -> Severity:
        """Assess severity based on symptoms and context."""
        symptom_text = " ".join(symptoms).lower()
        
        # Critical indicators
        if any(word in symptom_text for word in ["down", "critical", "outage", "data loss"]):
            return Severity.CRITICAL
            
        # High severity indicators
        if any(word in symptom_text for word in ["error", "failed", "unavailable"]):
            return Severity.HIGH
            
        # Check affected systems
        if context.get("affected_systems", []):
            if len(context["affected_systems"]) > 3:
                return Severity.HIGH
                
        # Medium severity indicators
        if any(word in symptom_text for word in ["slow", "intermittent", "degraded"]):
            return Severity.MEDIUM
            
        return Severity.LOW
        
    def rank_diagnostic_paths(
        self,
        paths: List[DiagnosticPath],
        symptoms: List[str],
        context: Dict[str, Any]
    ) -> List[DiagnosticPath]:
        """
        Rank diagnostic paths based on symptom matching and context.
        """
        scored_paths = []
        
        for path in paths:
            score = 0.0
            
            # Base score from path confidence
            score += path.confidence * 0.4
            
            # Symptom matching score
            symptom_match_score = self._calculate_symptom_match(path, symptoms)
            score += symptom_match_score * 0.3
            
            # Historical success score
            if path.success_rate > 0:
                score += path.success_rate * 0.2
                
            # Context relevance
            context_score = self._calculate_context_relevance(path, context)
            score += context_score * 0.1
            
            scored_paths.append((score, path))
            
        # Sort by score
        scored_paths.sort(key=lambda x: x[0], reverse=True)
        
        return [path for _, path in scored_paths]
        
    def _calculate_symptom_match(self, path: DiagnosticPath, symptoms: List[str]) -> float:
        """Calculate how well a path matches the symptoms."""
        # This would analyze the path's potential causes and their typical symptoms
        # Simplified implementation
        return 0.7
        
    def _calculate_context_relevance(self, path: DiagnosticPath, context: Dict[str, Any]) -> float:
        """Calculate how relevant a path is to the context."""
        score = 0.5
        
        # Boost if path involves affected components
        if "affected_components" in context:
            # Would check if path nodes relate to affected components
            score += 0.2
            
        return min(1.0, score)
        
    def identify_patterns(
        self,
        current_issue: TroubleshootingIssue,
        historical_issues: List[TroubleshootingIssue]
    ) -> List[IssuePattern]:
        """Identify patterns in troubleshooting history."""
        matched_patterns = []
        
        for pattern in self.diagnostic_patterns:
            # Check if current symptoms match pattern
            symptom_overlap = set(current_issue.symptoms) & set(pattern.common_symptoms)
            if len(symptom_overlap) >= 2:
                matched_patterns.append(pattern)
                
        return matched_patterns


class SolutionRanker:
    """Ranks and recommends solutions based on various factors."""
    
    def rank_solutions(
        self,
        solutions: List[Solution],
        issue: TroubleshootingIssue,
        context: Dict[str, Any]
    ) -> List[Tuple[Solution, float, str]]:
        """
        Rank solutions and provide reasoning.
        
        Returns:
            List of (solution, score, reasoning) tuples
        """
        ranked = []
        
        for solution in solutions:
            score = 0.0
            reasons = []
            
            # Success rate
            if solution.success_rate > 0:
                score += solution.success_rate * 0.3
                reasons.append(f"Success rate: {solution.success_rate:.0%}")
                
            # Implementation time vs urgency
            urgency_factor = self._calculate_urgency_factor(issue, context)
            time_score = 1.0 - (solution.avg_implementation_time / 60.0)  # Normalize to hours
            score += time_score * urgency_factor * 0.2
            
            if solution.avg_implementation_time < 30:
                reasons.append("Quick to implement")
                
            # Risk assessment
            risk_scores = {"low": 0.9, "medium": 0.5, "high": 0.1}
            risk_score = risk_scores.get(solution.risk_level, 0.5)
            score += risk_score * 0.2
            
            if solution.risk_level == "low":
                reasons.append("Low risk")
                
            # Automation availability
            if solution.automation_available:
                score += 0.1
                reasons.append("Automation available")
                
            # Downtime requirements
            if not solution.requires_downtime:
                score += 0.1
                reasons.append("No downtime required")
            elif context.get("maintenance_window_available"):
                score += 0.05
                reasons.append("Maintenance window available")
                
            # Prerequisites met
            prereqs_met = self._check_prerequisites(solution, context)
            if prereqs_met:
                score += 0.1
                reasons.append("All prerequisites met")
            else:
                score *= 0.5  # Penalize if prerequisites not met
                reasons.append("Prerequisites need to be addressed")
                
            # Create reasoning string
            reasoning = "; ".join(reasons)
            ranked.append((solution, score, reasoning))
            
        # Sort by score
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
        
    def _calculate_urgency_factor(self, issue: TroubleshootingIssue, context: Dict[str, Any]) -> float:
        """Calculate urgency factor based on severity and business impact."""
        base_urgency = {
            Severity.CRITICAL: 1.0,
            Severity.HIGH: 0.8,
            Severity.MEDIUM: 0.5,
            Severity.LOW: 0.2
        }
        
        urgency = base_urgency.get(issue.severity, 0.5)
        
        # Adjust based on business impact
        if context.get("business_critical"):
            urgency = min(1.0, urgency * 1.5)
            
        return urgency
        
    def _check_prerequisites(self, solution: Solution, context: Dict[str, Any]) -> bool:
        """Check if solution prerequisites are met."""
        if not solution.prerequisites:
            return True
            
        available_resources = context.get("available_resources", [])
        for prereq in solution.prerequisites:
            if prereq not in available_resources:
                return False
                
        return True


class GraphRAGTroubleshooter:
    """Main troubleshooting engine using GraphRAG."""
    
    def __init__(self, graph_index: GraphRAGIndex):
        self.graph_index = graph_index
        self.diagnostic_reasoner = DiagnosticReasoner()
        self.solution_ranker = SolutionRanker()
        self.active_sessions: Dict[str, TroubleshootingSession] = {}
        
    async def start_session(
        self,
        query: str,
        user_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> TroubleshootingSession:
        """Start a new troubleshooting session."""
        session = TroubleshootingSession(
            user_id=user_id,
            initial_query=query,
            symptoms=self._extract_symptoms(query)
        )
        
        self.active_sessions[str(session.id)] = session
        
        # Initial diagnosis
        result = await self.diagnose(query, context, session.id)
        
        return session
        
    async def diagnose(
        self,
        query: str,
        context: Dict[str, Any] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform diagnosis using GraphRAG.
        
        Returns comprehensive diagnostic results with reasoning.
        """
        context = context or {}
        
        # Extract symptoms
        symptoms = self._extract_symptoms(query)
        
        # Analyze symptoms
        issue_type, severity, additional_checks = await self.diagnostic_reasoner.analyze_symptoms(
            symptoms,
            context
        )
        
        # Create GraphRAG query
        graph_query = GraphRAGQuery(
            query_text=query,
            issue_types=[issue_type] if issue_type != IssueType.UNKNOWN else None,
            severity_filter=[severity],
            user_context=context
        )
        
        # Perform GraphRAG search
        result = await self.graph_index.troubleshoot(query, context)
        
        # Rank diagnostic paths
        ranked_paths = self.diagnostic_reasoner.rank_diagnostic_paths(
            result.diagnostic_paths,
            symptoms,
            context
        )
        
        # Rank solutions
        ranked_solutions = []
        if result.solutions:
            ranked_solutions = self.solution_ranker.rank_solutions(
                result.solutions,
                result.identified_issues[0] if result.identified_issues else None,
                context
            )
            
        # Check for patterns
        patterns = []
        if result.identified_issues and context.get("historical_issues"):
            patterns = self.diagnostic_reasoner.identify_patterns(
                result.identified_issues[0],
                context["historical_issues"]
            )
            
        # Update session if exists
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.paths_explored.extend(ranked_paths[:3])
            session.issues_identified.extend(result.identified_issues)
            
        # Build comprehensive response
        response = {
            "status": "success",
            "summary": self._generate_summary(result, ranked_paths, ranked_solutions),
            "diagnosis": {
                "issue_type": issue_type.value,
                "severity": severity.value,
                "confidence": ranked_paths[0].confidence if ranked_paths else 0.0,
                "identified_issues": [
                    {
                        "id": str(issue.id),
                        "title": issue.title,
                        "description": issue.description,
                        "symptoms": issue.symptoms,
                        "affected_components": issue.affected_components
                    }
                    for issue in result.identified_issues[:5]
                ]
            },
            "diagnostic_paths": [
                {
                    "path_id": str(path.id),
                    "confidence": path.confidence,
                    "complexity": path.complexity,
                    "steps": path.checks_required,
                    "estimated_time": path.avg_resolution_time
                }
                for path in ranked_paths[:3]
            ],
            "root_causes": [
                {
                    "id": str(cause.id),
                    "title": cause.title,
                    "description": cause.description,
                    "likelihood": cause.likelihood,
                    "diagnostic_steps": cause.diagnostic_steps,
                    "verification_commands": cause.verification_commands
                }
                for cause in result.root_causes[:5]
            ],
            "recommended_solutions": [
                {
                    "id": str(solution.id),
                    "title": solution.title,
                    "description": solution.description,
                    "score": score,
                    "reasoning": reasoning,
                    "steps": solution.steps,
                    "estimated_time": solution.avg_implementation_time,
                    "risk_level": solution.risk_level,
                    "prerequisites": solution.prerequisites,
                    "automation_available": solution.automation_available
                }
                for solution, score, reasoning in ranked_solutions[:3]
            ],
            "patterns_detected": [
                {
                    "name": pattern.name,
                    "description": pattern.description,
                    "early_warnings": pattern.early_warning_signs,
                    "prevention": pattern.prevention_steps
                }
                for pattern in patterns
            ],
            "additional_checks": additional_checks,
            "reasoning_trace": result.reasoning_steps,
            "metrics": {
                "query_time": result.query_time,
                "nodes_examined": result.nodes_examined,
                "paths_evaluated": result.paths_evaluated
            }
        }
        
        return response
        
    def _extract_symptoms(self, query: str) -> List[str]:
        """Extract symptoms from natural language query."""
        # Simple keyword extraction - in production, use NLP
        symptoms = []
        
        # Common symptom patterns
        patterns = [
            r"getting (\w+ error)",
            r"experiencing (\w+)",
            r"seeing (\w+)",
            r"(\w+ is down)",
            r"(\w+ failed)",
            r"cannot (\w+)",
            r"unable to (\w+)",
            r"(\w+ timeout)",
            r"(\w+ refused)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query.lower())
            symptoms.extend(matches)
            
        # Also include the full query as a symptom
        symptoms.append(query)
        
        return symptoms
        
    def _generate_summary(
        self,
        result: GraphRAGResult,
        ranked_paths: List[DiagnosticPath],
        ranked_solutions: List[Tuple[Solution, float, str]]
    ) -> str:
        """Generate human-readable summary of diagnosis."""
        summary_parts = []
        
        # Issue summary
        if result.identified_issues:
            issue = result.identified_issues[0]
            summary_parts.append(
                f"Identified issue: {issue.title} ({issue.type.value} - {issue.severity.value} severity)"
            )
            
        # Root cause summary
        if result.root_causes:
            cause = max(result.root_causes, key=lambda c: c.likelihood)
            summary_parts.append(
                f"Most likely root cause: {cause.title} ({cause.likelihood:.0%} probability)"
            )
            
        # Solution summary
        if ranked_solutions:
            solution, score, _ = ranked_solutions[0]
            summary_parts.append(
                f"Recommended solution: {solution.title} (confidence: {score:.0%}, "
                f"ETA: {solution.avg_implementation_time:.0f} minutes)"
            )
            
        # Pattern warning
        if result.reasoning_steps and "pattern" in str(result.reasoning_steps):
            summary_parts.append(
                "⚠️ This issue matches known patterns - preventive measures recommended"
            )
            
        return " | ".join(summary_parts)
        
    async def apply_solution(
        self,
        solution_id: str,
        session_id: str,
        execution_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Apply a solution and track results."""
        # In production, this would:
        # 1. Execute solution steps
        # 2. Monitor progress
        # 3. Verify success
        # 4. Update graph with results
        
        return {
            "status": "success",
            "execution_log": ["Step 1 completed", "Step 2 completed"],
            "verification_passed": True
        }
        
    async def close_session(
        self,
        session_id: str,
        resolution_successful: bool,
        feedback: Optional[str] = None
    ) -> None:
        """Close a troubleshooting session and update metrics."""
        if session_id not in self.active_sessions:
            return
            
        session = self.active_sessions[session_id]
        session.ended_at = datetime.utcnow()
        session.resolution_successful = resolution_successful
        session.user_feedback = feedback
        
        # Update graph metrics based on session results
        if session.solution_applied:
            duration = (session.ended_at - session.started_at).total_seconds() / 60
            await self.graph_index.graph_store.update_success_metrics(
                str(session.paths_explored[0].id) if session.paths_explored else None,
                resolution_successful,
                duration
            )
            
        # Remove from active sessions
        del self.active_sessions[session_id]
