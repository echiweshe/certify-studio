"""
Integrated Lesson Generator that combines Domain Extraction and GraphRAG.

This module creates complete lessons following the pedagogical continuum:
1. Introduction (Interest Arousal)
2. Technology & Benefits  
3. How It Works
4. Critical Subsystems & Relationships
5. Common Commands & Implementation
6. Troubleshooting Issues & Resolution
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from ...agents.specialized.domain_extraction import DomainExtractionAgent
from ...agents.specialized.domain_extraction.knowledge_graph_builder import KnowledgeGraphBuilder
from ..troubleshooting_engine import GraphRAGTroubleshooter
from ..models import GraphRAGConfig, IssueType, Severity


class LessonSection(Enum):
    """Lesson sections following the pedagogical continuum."""
    INTRODUCTION = "introduction"
    TECHNOLOGY_BENEFITS = "technology_benefits"
    HOW_IT_WORKS = "how_it_works"
    CRITICAL_SUBSYSTEMS = "critical_subsystems"
    COMMON_COMMANDS = "common_commands"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class IntegratedLesson:
    """Complete lesson with all pedagogical sections."""
    topic: str
    domain: str
    sections: Dict[LessonSection, Dict[str, Any]]
    knowledge_graph: Dict[str, Any]
    troubleshooting_scenarios: List[Dict[str, Any]]
    learning_objectives: List[str]
    prerequisites: List[str]
    estimated_duration: int  # minutes
    difficulty_level: str
    created_at: datetime
    
    def to_markdown(self) -> str:
        """Convert lesson to markdown format."""
        md = f"# {self.topic}\n\n"
        md += f"**Domain**: {self.domain}\n"
        md += f"**Difficulty**: {self.difficulty_level}\n"
        md += f"**Duration**: {self.estimated_duration} minutes\n\n"
        
        # Learning objectives
        md += "## Learning Objectives\n\n"
        for obj in self.learning_objectives:
            md += f"- {obj}\n"
        md += "\n"
        
        # Prerequisites
        if self.prerequisites:
            md += "## Prerequisites\n\n"
            for prereq in self.prerequisites:
                md += f"- {prereq}\n"
            md += "\n"
        
        # Sections
        section_titles = {
            LessonSection.INTRODUCTION: "Introduction",
            LessonSection.TECHNOLOGY_BENEFITS: "Technology & Benefits",
            LessonSection.HOW_IT_WORKS: "How It Works",
            LessonSection.CRITICAL_SUBSYSTEMS: "Critical Subsystems & Relationships",
            LessonSection.COMMON_COMMANDS: "Common Commands & Implementation",
            LessonSection.TROUBLESHOOTING: "Troubleshooting Guide"
        }
        
        for section, title in section_titles.items():
            if section in self.sections:
                md += f"## {title}\n\n"
                content = self.sections[section]
                
                if section == LessonSection.INTRODUCTION:
                    md += content.get("hook", "") + "\n\n"
                    md += content.get("overview", "") + "\n\n"
                    
                elif section == LessonSection.TECHNOLOGY_BENEFITS:
                    md += content.get("description", "") + "\n\n"
                    if "benefits" in content:
                        md += "### Key Benefits\n\n"
                        for benefit in content["benefits"]:
                            md += f"- **{benefit['title']}**: {benefit['description']}\n"
                        md += "\n"
                        
                elif section == LessonSection.HOW_IT_WORKS:
                    md += content.get("explanation", "") + "\n\n"
                    if "steps" in content:
                        md += "### Process Steps\n\n"
                        for i, step in enumerate(content["steps"], 1):
                            md += f"{i}. {step}\n"
                        md += "\n"
                        
                elif section == LessonSection.CRITICAL_SUBSYSTEMS:
                    if "components" in content:
                        for comp in content["components"]:
                            md += f"### {comp['name']}\n\n"
                            md += f"{comp['description']}\n\n"
                            if "relationships" in comp:
                                md += "**Relationships**:\n"
                                for rel in comp["relationships"]:
                                    md += f"- {rel}\n"
                                md += "\n"
                                
                elif section == LessonSection.COMMON_COMMANDS:
                    if "commands" in content:
                        for cmd in content["commands"]:
                            md += f"### {cmd['name']}\n\n"
                            md += f"{cmd['description']}\n\n"
                            md += f"```bash\n{cmd['syntax']}\n```\n\n"
                            if "example" in cmd:
                                md += f"**Example**:\n```bash\n{cmd['example']}\n```\n\n"
                                
                elif section == LessonSection.TROUBLESHOOTING:
                    if "scenarios" in content:
                        for scenario in content["scenarios"]:
                            md += f"### Issue: {scenario['issue']}\n\n"
                            md += f"**Symptoms**: {', '.join(scenario['symptoms'])}\n\n"
                            md += "**Diagnostic Steps**:\n"
                            for i, step in enumerate(scenario['diagnostic_steps'], 1):
                                md += f"{i}. {step}\n"
                            md += "\n**Solution**:\n"
                            md += f"{scenario['solution']}\n\n"
                            
        return md


class IntegratedLessonGenerator:
    """Generates complete lessons using both domain extraction and GraphRAG."""
    
    def __init__(
        self,
        domain_extractor: DomainExtractionAgent,
        knowledge_graph_builder: KnowledgeGraphBuilder,
        troubleshooter: GraphRAGTroubleshooter,
        graphrag_config: GraphRAGConfig
    ):
        self.domain_extractor = domain_extractor
        self.knowledge_graph_builder = knowledge_graph_builder
        self.troubleshooter = troubleshooter
        self.graphrag_config = graphrag_config
        
    async def generate_lesson(
        self,
        topic: str,
        domain: str,
        source_content: Optional[str] = None,
        difficulty_level: str = "intermediate",
        include_advanced_troubleshooting: bool = True
    ) -> IntegratedLesson:
        """
        Generate a complete lesson following the pedagogical continuum.
        
        Args:
            topic: Main topic of the lesson
            domain: Domain context (e.g., "AWS Solutions Architect")
            source_content: Optional source material
            difficulty_level: beginner/intermediate/advanced
            include_advanced_troubleshooting: Include GraphRAG scenarios
            
        Returns:
            Complete integrated lesson
        """
        logger.info(f"Generating integrated lesson for: {topic}")
        
        # Extract domain knowledge if source content provided
        domain_knowledge = {}
        if source_content:
            extraction_result = await self.domain_extractor.extract_domain(
                source_content,
                {"domain": domain, "topic": topic}
            )
            domain_knowledge = extraction_result
            
        # Build knowledge graph
        kg_data = await self._build_topic_knowledge_graph(topic, domain_knowledge)
        
        # Generate lesson sections
        sections = {}
        
        # 1. Introduction (Interest Arousal)
        sections[LessonSection.INTRODUCTION] = await self._generate_introduction(
            topic, domain, domain_knowledge
        )
        
        # 2. Technology & Benefits
        sections[LessonSection.TECHNOLOGY_BENEFITS] = await self._generate_technology_benefits(
            topic, domain, domain_knowledge
        )
        
        # 3. How It Works
        sections[LessonSection.HOW_IT_WORKS] = await self._generate_how_it_works(
            topic, domain, domain_knowledge
        )
        
        # 4. Critical Subsystems & Relationships
        sections[LessonSection.CRITICAL_SUBSYSTEMS] = await self._generate_subsystems(
            topic, kg_data, domain_knowledge
        )
        
        # 5. Common Commands & Implementation
        sections[LessonSection.COMMON_COMMANDS] = await self._generate_commands(
            topic, domain, domain_knowledge
        )
        
        # 6. Troubleshooting (GraphRAG)
        troubleshooting_scenarios = []
        if include_advanced_troubleshooting:
            sections[LessonSection.TROUBLESHOOTING], troubleshooting_scenarios = \
                await self._generate_troubleshooting_section(topic, domain)
        
        # Extract learning objectives and prerequisites
        learning_objectives = self._extract_learning_objectives(sections)
        prerequisites = self._extract_prerequisites(kg_data, domain_knowledge)
        
        # Estimate duration based on content
        estimated_duration = self._estimate_lesson_duration(sections, difficulty_level)
        
        return IntegratedLesson(
            topic=topic,
            domain=domain,
            sections=sections,
            knowledge_graph=kg_data,
            troubleshooting_scenarios=troubleshooting_scenarios,
            learning_objectives=learning_objectives,
            prerequisites=prerequisites,
            estimated_duration=estimated_duration,
            difficulty_level=difficulty_level,
            created_at=datetime.utcnow()
        )
        
    async def _generate_introduction(
        self,
        topic: str,
        domain: str,
        domain_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate engaging introduction section."""
        # Interest arousal techniques
        hooks = [
            f"What if you could master {topic} and transform your {domain} skills?",
            f"Imagine solving complex {topic} challenges with confidence.",
            f"Every expert in {domain} started exactly where you are now.",
            f"The journey to mastering {topic} begins with understanding why it matters."
        ]
        
        return {
            "hook": hooks[0],  # Select appropriate hook
            "overview": f"This lesson explores {topic} in the context of {domain}. "
                       f"You'll gain practical skills and deep understanding that "
                       f"will serve you throughout your career.",
            "why_it_matters": "Understanding this topic is crucial for modern cloud architecture.",
            "real_world_relevance": "Companies rely on these skills for their critical systems."
        }
        
    async def _generate_technology_benefits(
        self,
        topic: str,
        domain: str,
        domain_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technology and benefits section."""
        # Extract benefits from domain knowledge
        concepts = domain_knowledge.get("concepts", [])
        
        benefits = []
        for concept in concepts[:5]:  # Top 5 concepts
            if concept.get("importance_score", 0) > 0.7:
                benefits.append({
                    "title": concept.get("name", ""),
                    "description": concept.get("description", ""),
                    "business_impact": "Reduces costs and improves efficiency"
                })
                
        return {
            "description": f"{topic} is a fundamental technology in {domain} that enables...",
            "benefits": benefits,
            "use_cases": ["Enterprise applications", "Scalable systems", "Modern architectures"],
            "industry_adoption": "Widely adopted by Fortune 500 companies"
        }
        
    async def _generate_how_it_works(
        self,
        topic: str,
        domain: str,
        domain_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate how it works section."""
        procedures = domain_knowledge.get("procedures", [])
        
        # Create step-by-step explanation
        steps = []
        for proc in procedures:
            if proc.get("relevance_score", 0) > 0.6:
                steps.extend(proc.get("steps", []))
                
        return {
            "explanation": f"Understanding how {topic} works requires grasping key concepts...",
            "core_principles": ["Principle 1", "Principle 2", "Principle 3"],
            "steps": steps[:7],  # Limit to 7 key steps
            "architecture_overview": "System components work together to achieve..."
        }
        
    async def _generate_subsystems(
        self,
        topic: str,
        knowledge_graph: Dict[str, Any],
        domain_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate critical subsystems section using knowledge graph."""
        # Extract components from knowledge graph
        nodes = knowledge_graph.get("nodes", [])
        edges = knowledge_graph.get("edges", [])
        
        # Find central components
        components = []
        for node in nodes:
            if node.get("centrality", 0) > 0.5:
                # Find relationships
                relationships = []
                for edge in edges:
                    if edge["source"] == node["id"] or edge["target"] == node["id"]:
                        relationships.append(
                            f"Connected to {edge['target'] if edge['source'] == node['id'] else edge['source']} "
                            f"via {edge.get('type', 'relationship')}"
                        )
                        
                components.append({
                    "name": node["name"],
                    "description": node.get("description", ""),
                    "criticality": "High" if node.get("centrality", 0) > 0.7 else "Medium",
                    "relationships": relationships[:3]
                })
                
        return {
            "overview": f"The {topic} ecosystem consists of several critical components...",
            "components": components[:5],  # Top 5 components
            "interaction_patterns": "Components communicate through well-defined interfaces...",
            "dependency_graph": knowledge_graph
        }
        
    async def _generate_commands(
        self,
        topic: str,
        domain: str,
        domain_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate common commands section."""
        procedures = domain_knowledge.get("procedures", [])
        
        commands = []
        for proc in procedures:
            if "command" in proc or "code" in proc:
                commands.append({
                    "name": proc.get("name", "Command"),
                    "description": proc.get("description", ""),
                    "syntax": proc.get("command", proc.get("code", "")),
                    "example": proc.get("example", ""),
                    "options": proc.get("options", []),
                    "best_practices": proc.get("best_practices", "")
                })
                
        return {
            "overview": f"Common {topic} commands and implementations...",
            "commands": commands[:10],  # Top 10 commands
            "implementation_patterns": "Follow these patterns for best results...",
            "security_considerations": "Always consider security when implementing..."
        }
        
    async def _generate_troubleshooting_section(
        self,
        topic: str,
        domain: str
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Generate troubleshooting section using GraphRAG."""
        # Query GraphRAG for common issues related to topic
        common_issues_query = f"What are common {topic} issues in {domain}?"
        
        result = await self.troubleshooter.diagnose(
            common_issues_query,
            context={
                "mode": "educational",
                "topic": topic,
                "domain": domain
            }
        )
        
        # Convert GraphRAG results to educational scenarios
        scenarios = []
        for issue in result.identified_issues[:5]:  # Top 5 issues
            # Get diagnostic path for this issue
            path = next(
                (p for p in result.diagnostic_paths if p.starting_issue == str(issue.id)),
                None
            )
            
            if path:
                scenario = {
                    "issue": issue.title,
                    "symptoms": issue.symptoms,
                    "severity": issue.severity.value,
                    "diagnostic_steps": [],
                    "root_causes": [],
                    "solution": "",
                    "prevention_tips": []
                }
                
                # Extract diagnostic steps
                for edge in path.edges:
                    if edge[2] == "DIAGNOSED_BY":
                        scenario["diagnostic_steps"].append(
                            f"Check {edge[1]} configuration"
                        )
                        
                # Find root causes and solutions
                for cause in result.root_causes:
                    if str(cause.issue_id) == str(issue.id):
                        scenario["root_causes"].append(cause.title)
                        
                for solution in result.solutions:
                    if str(issue.id) in [str(i) for i in solution.applies_to_issues]:
                        scenario["solution"] = solution.description
                        scenario["prevention_tips"] = solution.prerequisites
                        break
                        
                scenarios.append(scenario)
                
        section = {
            "overview": f"Common {topic} troubleshooting scenarios and solutions...",
            "diagnostic_approach": "Follow systematic diagnosis: Observe → Hypothesize → Test → Resolve",
            "scenarios": scenarios,
            "tools_and_commands": ["Diagnostic tool 1", "Monitoring command 2"],
            "escalation_guide": "When to seek additional help..."
        }
        
        return section, scenarios
        
    def _extract_learning_objectives(self, sections: Dict[LessonSection, Dict[str, Any]]) -> List[str]:
        """Extract learning objectives from lesson sections."""
        objectives = [
            f"Understand the fundamentals and benefits of the technology",
            f"Explain how the system works and its core components",
            f"Identify and describe critical subsystems and their relationships",
            f"Execute common commands and implementations",
            f"Diagnose and resolve common issues using systematic troubleshooting"
        ]
        
        return objectives
        
    def _extract_prerequisites(
        self,
        knowledge_graph: Dict[str, Any],
        domain_knowledge: Dict[str, Any]
    ) -> List[str]:
        """Extract prerequisites from knowledge graph."""
        prerequisites = []
        
        # Look for prerequisite relationships in graph
        edges = knowledge_graph.get("edges", [])
        for edge in edges:
            if edge.get("type") == "prerequisite":
                prerequisites.append(edge.get("source"))
                
        # Add basic prerequisites
        prerequisites.extend([
            "Basic understanding of cloud computing",
            "Familiarity with command line interfaces"
        ])
        
        return list(set(prerequisites))[:5]  # Unique, max 5
        
    def _estimate_lesson_duration(
        self,
        sections: Dict[LessonSection, Dict[str, Any]],
        difficulty_level: str
    ) -> int:
        """Estimate lesson duration in minutes."""
        base_duration = {
            LessonSection.INTRODUCTION: 5,
            LessonSection.TECHNOLOGY_BENEFITS: 10,
            LessonSection.HOW_IT_WORKS: 15,
            LessonSection.CRITICAL_SUBSYSTEMS: 20,
            LessonSection.COMMON_COMMANDS: 25,
            LessonSection.TROUBLESHOOTING: 30
        }
        
        # Adjust for difficulty
        difficulty_multiplier = {
            "beginner": 1.5,
            "intermediate": 1.0,
            "advanced": 0.8
        }
        
        total_duration = sum(
            base_duration.get(section, 10)
            for section in sections.keys()
        )
        
        return int(total_duration * difficulty_multiplier.get(difficulty_level, 1.0))
        
    async def _build_topic_knowledge_graph(
        self,
        topic: str,
        domain_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build knowledge graph for the topic."""
        # Use existing knowledge graph builder
        concepts = domain_knowledge.get("concepts", [])
        
        # Create simplified graph representation
        nodes = []
        edges = []
        
        for i, concept in enumerate(concepts[:10]):  # Limit to 10 nodes
            nodes.append({
                "id": f"concept_{i}",
                "name": concept.get("name", f"Concept {i}"),
                "description": concept.get("description", ""),
                "centrality": concept.get("importance_score", 0.5)
            })
            
        # Create relationships
        for i in range(len(nodes) - 1):
            for j in range(i + 1, min(i + 3, len(nodes))):
                edges.append({
                    "source": nodes[i]["id"],
                    "target": nodes[j]["id"],
                    "type": "related_to",
                    "weight": 0.7
                })
                
        return {
            "nodes": nodes,
            "edges": edges,
            "clusters": [],
            "metadata": {
                "topic": topic,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }


class LessonOrchestrator:
    """Orchestrates lesson generation across multiple topics."""
    
    def __init__(self, lesson_generator: IntegratedLessonGenerator):
        self.lesson_generator = lesson_generator
        self.generated_lessons = {}
        
    async def generate_course_module(
        self,
        module_name: str,
        topics: List[str],
        domain: str,
        source_materials: Optional[Dict[str, str]] = None
    ) -> Dict[str, IntegratedLesson]:
        """Generate a complete course module with multiple lessons."""
        logger.info(f"Generating course module: {module_name}")
        
        lessons = {}
        
        for topic in topics:
            source_content = None
            if source_materials and topic in source_materials:
                source_content = source_materials[topic]
                
            lesson = await self.lesson_generator.generate_lesson(
                topic=topic,
                domain=domain,
                source_content=source_content,
                difficulty_level="intermediate",
                include_advanced_troubleshooting=True
            )
            
            lessons[topic] = lesson
            self.generated_lessons[f"{module_name}:{topic}"] = lesson
            
        return lessons
        
    async def export_module_to_markdown(
        self,
        module_name: str,
        lessons: Dict[str, IntegratedLesson],
        output_path: str
    ) -> str:
        """Export course module to markdown files."""
        import os
        
        # Create module directory
        module_dir = os.path.join(output_path, module_name.lower().replace(" ", "_"))
        os.makedirs(module_dir, exist_ok=True)
        
        # Create index file
        index_content = f"# {module_name}\n\n"
        index_content += "## Course Contents\n\n"
        
        for topic, lesson in lessons.items():
            # Generate lesson file
            lesson_filename = f"{topic.lower().replace(' ', '_')}.md"
            lesson_path = os.path.join(module_dir, lesson_filename)
            
            with open(lesson_path, 'w', encoding='utf-8') as f:
                f.write(lesson.to_markdown())
                
            # Add to index
            index_content += f"- [{topic}]({lesson_filename})\n"
            index_content += f"  - Duration: {lesson.estimated_duration} minutes\n"
            index_content += f"  - Difficulty: {lesson.difficulty_level}\n\n"
            
        # Write index file
        index_path = os.path.join(module_dir, "README.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
            
        return module_dir
