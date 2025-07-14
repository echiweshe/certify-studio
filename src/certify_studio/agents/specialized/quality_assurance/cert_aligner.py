"""
Certification Alignment Validator for Quality Assurance Agent.

This module ensures content aligns with certification requirements:
- Covers all exam objectives
- Appropriate depth for each topic
- Correct weight distribution
- Exam readiness assessment
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import logging
from collections import defaultdict

from .models import (
    CertificationAlignment,
    ValidationIssue,
    SeverityLevel,
    QualityDimension
)
from ....core.llm import MultimodalLLM
from ....core.llm.multimodal_llm import MultimodalMessage
from ....core.config import settings

logger = logging.getLogger(__name__)


class CertificationAligner:
    """Validates content alignment with certification requirements."""
    
    def __init__(self, llm: Optional[MultimodalLLM] = None):
        """Initialize the certification aligner."""
        self.llm = llm or MultimodalLLM()
        self.certification_database = self._load_certification_database()
        self.objective_mappings = {}
        
    def _load_certification_database(self) -> Dict[str, Any]:
        """Load database of certification requirements."""
        return {
            "AWS-SAA-C03": {
                "name": "AWS Certified Solutions Architect - Associate",
                "domains": {
                    "Design Secure Architectures": {
                        "weight": 0.30,
                        "objectives": [
                            "Design secure access to AWS resources",
                            "Design secure workloads and applications",
                            "Determine appropriate data security controls"
                        ]
                    },
                    "Design Resilient Architectures": {
                        "weight": 0.26,
                        "objectives": [
                            "Design scalable and loosely coupled architectures",
                            "Design highly available and/or fault-tolerant architectures",
                            "Choose reliable/resilient storage",
                            "Design decoupling mechanisms using AWS services"
                        ]
                    },
                    "Design High-Performing Architectures": {
                        "weight": 0.24,
                        "objectives": [
                            "Determine high-performing storage solutions",
                            "Design high-performing compute solutions",
                            "Determine high-performing networking solutions",
                            "Choose high-performing database solutions"
                        ]
                    },
                    "Design Cost-Optimized Architectures": {
                        "weight": 0.20,
                        "objectives": [
                            "Design cost-optimized storage solutions",
                            "Design cost-optimized compute solutions",
                            "Design cost-optimized network architectures",
                            "Design cost-optimized database solutions"
                        ]
                    }
                },
                "passing_score": 720,
                "max_score": 1000,
                "exam_duration": 130,  # minutes
                "question_count": 65
            },
            "AZ-104": {
                "name": "Microsoft Azure Administrator",
                "domains": {
                    "Manage Azure identities and governance": {
                        "weight": 0.20,
                        "objectives": [
                            "Manage Azure AD objects",
                            "Manage role-based access control (RBAC)",
                            "Manage subscriptions and governance"
                        ]
                    },
                    "Implement and manage storage": {
                        "weight": 0.15,
                        "objectives": [
                            "Configure access to storage",
                            "Manage data in Azure storage accounts",
                            "Configure Azure Files and Azure Blob Storage"
                        ]
                    },
                    "Deploy and manage Azure compute resources": {
                        "weight": 0.20,
                        "objectives": [
                            "Automate deployment of resources using templates",
                            "Create and configure VMs",
                            "Create and configure containers",
                            "Create and configure Azure App Service"
                        ]
                    },
                    "Implement and manage virtual networking": {
                        "weight": 0.25,
                        "objectives": [
                            "Implement and manage virtual networks",
                            "Configure name resolution",
                            "Secure virtual networks",
                            "Configure load balancing"
                        ]
                    },
                    "Monitor and maintain Azure resources": {
                        "weight": 0.20,
                        "objectives": [
                            "Monitor resources using Azure Monitor",
                            "Implement backup and recovery",
                            "Monitor and troubleshoot virtual networks"
                        ]
                    }
                },
                "passing_score": 700,
                "max_score": 1000,
                "exam_duration": 120,
                "question_count": 60
            },
            # Add more certifications as needed
        }
        
    async def validate_certification_alignment(
        self,
        content: Dict[str, Any],
        certification_id: str,
        extracted_concepts: Optional[List[str]] = None
    ) -> CertificationAlignment:
        """Validate how well content aligns with certification requirements."""
        logger.info(f"Validating alignment with {certification_id}")
        
        alignment = CertificationAlignment(certification_id=certification_id)
        
        # Get certification requirements
        cert_info = self.certification_database.get(certification_id)
        if not cert_info:
            logger.warning(f"Certification {certification_id} not found in database")
            # Try to fetch from LLM
            cert_info = await self._fetch_certification_info(certification_id)
            
        if not cert_info:
            alignment.alignment_score = 0.0
            return alignment
            
        # Extract topics from content
        content_topics = await self._extract_content_topics(content)
        
        # Map content to certification objectives
        objective_coverage = await self._map_content_to_objectives(
            content_topics,
            cert_info["domains"],
            extracted_concepts
        )
        
        # Calculate coverage metrics
        alignment.covered_objectives = objective_coverage["covered"]
        alignment.missing_objectives = objective_coverage["missing"]
        alignment.partial_objectives = objective_coverage["partial"]
        
        # Analyze depth of coverage
        alignment.depth_analysis = await self._analyze_coverage_depth(
            content,
            objective_coverage["mapping"],
            cert_info
        )
        
        # Calculate weight distribution
        alignment.weight_distribution = await self._calculate_weight_distribution(
            objective_coverage["mapping"],
            cert_info["domains"]
        )
        
        # Calculate overall alignment score
        alignment.alignment_score = self._calculate_alignment_score(
            objective_coverage,
            alignment.depth_analysis,
            alignment.weight_distribution,
            cert_info
        )
        
        # Assess exam readiness
        alignment.exam_readiness_score = await self._assess_exam_readiness(
            alignment,
            content,
            cert_info
        )
        
        logger.info(f"Alignment score: {alignment.alignment_score}, Exam readiness: {alignment.exam_readiness_score}")
        return alignment
        
    async def _fetch_certification_info(self, certification_id: str) -> Optional[Dict[str, Any]]:
        """Fetch certification information using LLM if not in database."""
        try:
            prompt = f"""
            Provide detailed information about the {certification_id} certification:
            1. Full name
            2. Exam domains with weights (percentages)
            3. Key objectives for each domain
            4. Passing score
            5. Number of questions
            6. Exam duration
            
            Format as JSON with structure:
            {{
                "name": "...",
                "domains": {{
                    "Domain Name": {{
                        "weight": 0.XX,
                        "objectives": ["objective1", "objective2", ...]
                    }}
                }},
                "passing_score": XXX,
                "max_score": 1000,
                "exam_duration": XXX,
                "question_count": XX
            }}
            """
            
            response = await self.llm_client.generate(prompt)
            cert_info = json.loads(response)
            
            # Cache for future use
            self.certification_database[certification_id] = cert_info
            return cert_info
            
        except Exception as e:
            logger.error(f"Failed to fetch certification info for {certification_id}: {e}")
            return None
            
    async def _extract_content_topics(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract topics and concepts from content."""
        topics = []
        
        # Extract from different content types
        if "modules" in content:
            for module in content["modules"]:
                topics.extend(await self._extract_module_topics(module))
                
        if "lessons" in content:
            for lesson in content["lessons"]:
                topics.extend(await self._extract_lesson_topics(lesson))
                
        if "concepts" in content:
            topics.extend([
                {
                    "name": concept.get("name", ""),
                    "description": concept.get("description", ""),
                    "depth": concept.get("depth", "medium"),
                    "time_allocation": concept.get("time", 0)
                }
                for concept in content["concepts"]
            ])
            
        # Use LLM to extract additional topics if needed
        if not topics and content.get("text"):
            topics = await self._extract_topics_with_llm(content["text"])
            
        return topics
        
    async def _extract_module_topics(self, module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract topics from a module."""
        topics = []
        
        if module.get("title"):
            topics.append({
                "name": module["title"],
                "description": module.get("description", ""),
                "depth": "high",  # Modules are typically high-level
                "time_allocation": module.get("duration", 0)
            })
            
        # Extract from sub-components
        if module.get("sections"):
            for section in module["sections"]:
                topics.extend(await self._extract_section_topics(section))
                
        return topics
        
    async def _extract_lesson_topics(self, lesson: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract topics from a lesson."""
        topics = []
        
        topics.append({
            "name": lesson.get("title", ""),
            "description": lesson.get("objective", ""),
            "depth": lesson.get("depth", "medium"),
            "time_allocation": lesson.get("duration", 0)
        })
        
        # Extract subtopics
        if lesson.get("topics"):
            for topic in lesson["topics"]:
                topics.append({
                    "name": topic,
                    "description": "",
                    "depth": "low",
                    "time_allocation": 0
                })
                
        return topics
        
    async def _extract_section_topics(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract topics from a section."""
        return [{
            "name": section.get("title", ""),
            "description": section.get("content", "")[:100],
            "depth": "medium",
            "time_allocation": section.get("duration", 0)
        }]
        
    async def _extract_topics_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """Use LLM to extract topics from text content."""
        try:
            prompt = f"""
            Extract the main topics and concepts from this educational content.
            For each topic, identify:
            1. Topic name
            2. Brief description
            3. Depth of coverage (high/medium/low)
            4. Approximate time needed to learn (minutes)
            
            Content:
            {text[:2000]}  # Limit to prevent token overflow
            
            Return as JSON array.
            """
            
            response = await self.llm_client.generate(prompt)
            topics = json.loads(response)
            return topics
            
        except Exception as e:
            logger.error(f"Failed to extract topics with LLM: {e}")
            return []
            
    async def _map_content_to_objectives(
        self,
        content_topics: List[Dict[str, Any]],
        domains: Dict[str, Any],
        extracted_concepts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Map content topics to certification objectives."""
        mapping = defaultdict(list)
        covered_objectives = []
        missing_objectives = []
        partial_objectives = []
        
        all_topics = [topic["name"].lower() for topic in content_topics]
        if extracted_concepts:
            all_topics.extend([c.lower() for c in extracted_concepts])
            
        # Check each domain and objective
        for domain_name, domain_info in domains.items():
            for objective in domain_info["objectives"]:
                objective_lower = objective.lower()
                
                # Calculate coverage score for this objective
                coverage_score = await self._calculate_objective_coverage(
                    objective,
                    all_topics,
                    content_topics
                )
                
                if coverage_score >= 0.8:
                    covered_objectives.append(objective)
                    mapping[domain_name].append({
                        "objective": objective,
                        "coverage": coverage_score,
                        "status": "covered"
                    })
                elif coverage_score >= 0.3:
                    partial_objectives.append({
                        "objective": objective,
                        "coverage": coverage_score
                    })
                    mapping[domain_name].append({
                        "objective": objective,
                        "coverage": coverage_score,
                        "status": "partial"
                    })
                else:
                    missing_objectives.append(objective)
                    mapping[domain_name].append({
                        "objective": objective,
                        "coverage": coverage_score,
                        "status": "missing"
                    })
                    
        return {
            "covered": covered_objectives,
            "missing": missing_objectives,
            "partial": partial_objectives,
            "mapping": dict(mapping)
        }
        
    async def _calculate_objective_coverage(
        self,
        objective: str,
        all_topics: List[str],
        content_topics: List[Dict[str, Any]]
    ) -> float:
        """Calculate how well an objective is covered by content."""
        # Extract key terms from objective
        objective_terms = self._extract_key_terms(objective)
        
        # Direct matching
        direct_matches = sum(1 for term in objective_terms if any(term in topic for topic in all_topics))
        direct_score = direct_matches / len(objective_terms) if objective_terms else 0
        
        # Semantic matching using LLM
        semantic_score = await self._calculate_semantic_coverage(objective, content_topics)
        
        # Weighted combination
        return 0.6 * direct_score + 0.4 * semantic_score
        
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text."""
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "was", "are", "were"}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        return key_terms
        
    async def _calculate_semantic_coverage(
        self,
        objective: str,
        content_topics: List[Dict[str, Any]]
    ) -> float:
        """Calculate semantic coverage using LLM."""
        try:
            topics_text = "\n".join([
                f"- {t['name']}: {t['description']}" 
                for t in content_topics[:20]  # Limit to prevent token overflow
            ])
            
            prompt = f"""
            Assess how well these topics cover this certification objective:
            
            Objective: {objective}
            
            Topics covered:
            {topics_text}
            
            Return a coverage score from 0.0 to 1.0 where:
            - 0.0 = No coverage
            - 0.5 = Partial coverage
            - 1.0 = Complete coverage
            
            Consider both direct matches and related concepts.
            Return only the numeric score.
            """
            
            response = await self.llm_client.generate(prompt)
            score = float(response.strip())
            return min(max(score, 0.0), 1.0)  # Ensure valid range
            
        except Exception as e:
            logger.error(f"Failed to calculate semantic coverage: {e}")
            return 0.0
            
    async def _analyze_coverage_depth(
        self,
        content: Dict[str, Any],
        objective_mapping: Dict[str, List[Dict[str, Any]]],
        cert_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analyze the depth of coverage for each domain."""
        depth_analysis = {}
        
        for domain_name, objectives in objective_mapping.items():
            # Calculate average depth based on coverage and content volume
            covered_objectives = [o for o in objectives if o["status"] in ["covered", "partial"]]
            
            if not covered_objectives:
                depth_analysis[domain_name] = 0.0
                continue
                
            # Estimate depth based on multiple factors
            coverage_scores = [o["coverage"] for o in covered_objectives]
            avg_coverage = sum(coverage_scores) / len(coverage_scores)
            
            # Check for practical examples, exercises, etc.
            depth_indicators = await self._check_depth_indicators(content, domain_name)
            
            # Calculate overall depth score
            depth_score = (
                0.4 * avg_coverage +
                0.3 * depth_indicators["examples"] +
                0.2 * depth_indicators["exercises"] +
                0.1 * depth_indicators["assessments"]
            )
            
            depth_analysis[domain_name] = depth_score
            
        return depth_analysis
        
    async def _check_depth_indicators(
        self,
        content: Dict[str, Any],
        domain_name: str
    ) -> Dict[str, float]:
        """Check for indicators of content depth."""
        indicators = {
            "examples": 0.0,
            "exercises": 0.0,
            "assessments": 0.0
        }
        
        # Convert content to searchable text
        content_text = json.dumps(content).lower()
        domain_lower = domain_name.lower()
        
        # Check for examples
        example_keywords = ["example", "demo", "demonstration", "scenario", "use case"]
        example_count = sum(1 for kw in example_keywords if kw in content_text and domain_lower in content_text)
        indicators["examples"] = min(example_count / 5, 1.0)  # Normalize to 0-1
        
        # Check for exercises
        exercise_keywords = ["exercise", "practice", "hands-on", "lab", "tutorial"]
        exercise_count = sum(1 for kw in exercise_keywords if kw in content_text)
        indicators["exercises"] = min(exercise_count / 3, 1.0)
        
        # Check for assessments
        assessment_keywords = ["quiz", "test", "assessment", "question", "evaluate"]
        assessment_count = sum(1 for kw in assessment_keywords if kw in content_text)
        indicators["assessments"] = min(assessment_count / 3, 1.0)
        
        return indicators
        
    async def _calculate_weight_distribution(
        self,
        objective_mapping: Dict[str, List[Dict[str, Any]]],
        domains: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate actual vs expected weight distribution."""
        actual_weights = {}
        
        # Calculate total coverage across all domains
        total_coverage = 0.0
        domain_coverages = {}
        
        for domain_name, objectives in objective_mapping.items():
            domain_coverage = sum(o["coverage"] for o in objectives)
            domain_coverages[domain_name] = domain_coverage
            total_coverage += domain_coverage
            
        # Calculate actual weight distribution
        if total_coverage > 0:
            for domain_name, coverage in domain_coverages.items():
                actual_weights[domain_name] = coverage / total_coverage
        else:
            # No coverage - set all to 0
            for domain_name in domains:
                actual_weights[domain_name] = 0.0
                
        # Add expected weights for comparison
        for domain_name, domain_info in domains.items():
            if domain_name not in actual_weights:
                actual_weights[domain_name] = 0.0
                
        return actual_weights
        
    def _calculate_alignment_score(
        self,
        objective_coverage: Dict[str, Any],
        depth_analysis: Dict[str, float],
        weight_distribution: Dict[str, float],
        cert_info: Dict[str, Any]
    ) -> float:
        """Calculate overall alignment score."""
        # Coverage score (40%)
        total_objectives = sum(
            len(domain["objectives"]) 
            for domain in cert_info["domains"].values()
        )
        covered_count = len(objective_coverage["covered"])
        partial_count = len(objective_coverage["partial"])
        
        coverage_score = (covered_count + 0.5 * partial_count) / total_objectives if total_objectives > 0 else 0
        
        # Depth score (30%)
        depth_scores = list(depth_analysis.values())
        avg_depth = sum(depth_scores) / len(depth_scores) if depth_scores else 0
        
        # Weight distribution score (30%)
        weight_score = 0.0
        for domain_name, domain_info in cert_info["domains"].items():
            expected_weight = domain_info["weight"]
            actual_weight = weight_distribution.get(domain_name, 0.0)
            
            # Calculate deviation (lower is better)
            deviation = abs(expected_weight - actual_weight)
            domain_score = max(0, 1 - deviation * 2)  # Penalize deviations
            
            weight_score += domain_score * expected_weight  # Weighted by importance
            
        # Combine scores
        alignment_score = (
            0.4 * coverage_score +
            0.3 * avg_depth +
            0.3 * weight_score
        )
        
        return alignment_score
        
    async def _assess_exam_readiness(
        self,
        alignment: CertificationAlignment,
        content: Dict[str, Any],
        cert_info: Dict[str, Any]
    ) -> float:
        """Assess how ready a learner would be for the exam."""
        readiness_factors = {
            "coverage": alignment.alignment_score,
            "practice_questions": 0.0,
            "hands_on_labs": 0.0,
            "exam_tips": 0.0,
            "time_management": 0.0
        }
        
        content_text = json.dumps(content).lower()
        
        # Check for practice questions
        question_keywords = ["practice question", "sample question", "exam question", "mock exam"]
        question_count = sum(1 for kw in question_keywords if kw in content_text)
        readiness_factors["practice_questions"] = min(question_count / 10, 1.0)
        
        # Check for hands-on labs
        lab_keywords = ["hands-on", "lab", "exercise", "practical", "workshop"]
        lab_count = sum(1 for kw in lab_keywords if kw in content_text)
        readiness_factors["hands_on_labs"] = min(lab_count / 5, 1.0)
        
        # Check for exam tips
        tip_keywords = ["exam tip", "test tip", "exam strategy", "exam preparation"]
        tip_count = sum(1 for kw in tip_keywords if kw in content_text)
        readiness_factors["exam_tips"] = min(tip_count / 3, 1.0)
        
        # Check for time management guidance
        time_keywords = ["time management", "pace yourself", "minutes per question", "exam duration"]
        time_count = sum(1 for kw in time_keywords if kw in content_text)
        readiness_factors["time_management"] = min(time_count / 2, 1.0)
        
        # Calculate weighted readiness score
        readiness_score = (
            0.4 * readiness_factors["coverage"] +
            0.3 * readiness_factors["practice_questions"] +
            0.2 * readiness_factors["hands_on_labs"] +
            0.05 * readiness_factors["exam_tips"] +
            0.05 * readiness_factors["time_management"]
        )
        
        return readiness_score
        
    async def generate_alignment_report(
        self,
        alignment: CertificationAlignment,
        cert_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed alignment report."""
        report = {
            "certification": cert_info["name"],
            "overall_alignment": alignment.alignment_score,
            "exam_readiness": alignment.exam_readiness_score,
            "domain_analysis": {},
            "recommendations": []
        }
        
        # Analyze each domain
        for domain_name, domain_info in cert_info["domains"].items():
            expected_weight = domain_info["weight"]
            actual_weight = alignment.weight_distribution.get(domain_name, 0.0)
            depth = alignment.depth_analysis.get(domain_name, 0.0)
            
            report["domain_analysis"][domain_name] = {
                "expected_weight": f"{expected_weight * 100:.0f}%",
                "actual_weight": f"{actual_weight * 100:.0f}%",
                "depth_score": depth,
                "status": self._get_domain_status(actual_weight, expected_weight, depth)
            }
            
        # Generate recommendations
        if alignment.missing_objectives:
            report["recommendations"].append({
                "priority": "high",
                "action": "Add content for missing objectives",
                "details": alignment.missing_objectives[:5]  # Top 5
            })
            
        for domain_name, actual_weight in alignment.weight_distribution.items():
            expected = cert_info["domains"][domain_name]["weight"]
            if actual_weight < expected * 0.8:
                report["recommendations"].append({
                    "priority": "medium",
                    "action": f"Increase content for {domain_name}",
                    "details": f"Current: {actual_weight*100:.0f}%, Expected: {expected*100:.0f}%"
                })
                
        if alignment.exam_readiness_score < 0.7:
            report["recommendations"].append({
                "priority": "medium",
                "action": "Add more practice questions and hands-on exercises",
                "details": "Current exam readiness score is below optimal threshold"
            })
            
        return report
        
    def _get_domain_status(self, actual: float, expected: float, depth: float) -> str:
        """Determine domain coverage status."""
        weight_ratio = actual / expected if expected > 0 else 0
        
        if weight_ratio >= 0.9 and depth >= 0.8:
            return "excellent"
        elif weight_ratio >= 0.7 and depth >= 0.6:
            return "good"
        elif weight_ratio >= 0.5 or depth >= 0.5:
            return "needs_improvement"
        else:
            return "insufficient"
