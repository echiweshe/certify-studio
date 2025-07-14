"""
Response Parser - Intelligent LLM Output Understanding
Part of the AI Agent Orchestration Platform for Educational Excellence

This component doesn't just parse responses - it understands the educational
intent, validates pedagogical correctness, and ensures cognitive coherence.
"""

import re
import json
import ast
from typing import Dict, List, Any, Optional, Union, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import xml.etree.ElementTree as ET

from pydantic import BaseModel, ValidationError, Field
import yaml
import markdown
from bs4 import BeautifulSoup

from ...core.logging import get_logger
from ...knowledge.graph import KnowledgeGraph
from ...ml.nlp import NLPProcessor

logger = get_logger(__name__)


class ResponseType(Enum):
    """Types of responses we parse and understand."""
    STRUCTURED_JSON = "structured_json"
    EDUCATIONAL_CONTENT = "educational_content"
    CODE_GENERATION = "code_generation"
    CONCEPT_EXPLANATION = "concept_explanation"
    ASSESSMENT = "assessment"
    DIAGRAM_SPEC = "diagram_spec"
    LEARNING_PATH = "learning_path"
    ERROR_ANALYSIS = "error_analysis"


class ContentQuality(Enum):
    """Quality levels for parsed content."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNACCEPTABLE = "unacceptable"


@dataclass
class ParsedResponse:
    """Rich representation of parsed LLM response."""
    response_type: ResponseType
    content: Any  # The actual parsed content
    quality: ContentQuality
    confidence: float
    
    # Extracted components
    concepts: List[str] = field(default_factory=list)
    relationships: List[Tuple[str, str, str]] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    
    # Educational metadata
    cognitive_level: str = "remember"  # Bloom's taxonomy
    prerequisite_concepts: List[str] = field(default_factory=list)
    difficulty_level: float = 0.5
    
    # Validation results
    validation_errors: List[str] = field(default_factory=list)
    pedagogical_issues: List[str] = field(default_factory=list)
    
    # Improvements
    suggested_refinements: List[str] = field(default_factory=list)
    
    # For tracking
    parse_duration_ms: float = 0
    model_used: Optional[str] = None


@dataclass
class EducationalContent(BaseModel):
    """Model for educational content structure."""
    title: str
    introduction: str
    concepts: List[Dict[str, Any]]
    examples: List[Dict[str, Any]]
    exercises: List[Dict[str, Any]]
    summary: str
    learning_outcomes: List[str]
    
    class Config:
        extra = "allow"  # Allow additional fields


@dataclass 
class ConceptExplanation(BaseModel):
    """Model for concept explanations."""
    concept: str
    definition: str
    explanation: str
    analogies: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


@dataclass
class LearningPath(BaseModel):
    """Model for learning path structure."""
    title: str
    description: str
    target_audience: str
    duration_hours: float
    modules: List[Dict[str, Any]]
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    assessments: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


class ResponseParser:
    """
    Advanced response parser with educational understanding.
    
    This parser doesn't just extract structure - it validates educational
    coherence, ensures pedagogical soundness, and enhances responses for
    optimal learning outcomes.
    """
    
    def __init__(self, 
                 knowledge_graph: Optional[KnowledgeGraph] = None,
                 nlp_processor: Optional[NLPProcessor] = None):
        """
        Initialize response parser with intelligence.
        
        Args:
            knowledge_graph: For validating concepts and relationships
            nlp_processor: For advanced text understanding
        """
        self.knowledge_graph = knowledge_graph
        self.nlp_processor = nlp_processor or NLPProcessor()
        
        # Patterns for different response types
        self._init_patterns()
        
        # Response models
        self.response_models = {
            ResponseType.EDUCATIONAL_CONTENT: EducationalContent,
            ResponseType.CONCEPT_EXPLANATION: ConceptExplanation,
            ResponseType.LEARNING_PATH: LearningPath
        }
        
        # Quality assessment criteria
        self.quality_criteria = {
            'clarity': 0.3,
            'completeness': 0.25,
            'accuracy': 0.25,
            'pedagogy': 0.2
        }
        
        logger.info("ResponseParser initialized with educational intelligence")
    
    def _init_patterns(self):
        """Initialize parsing patterns."""
        # JSON extraction patterns
        self.json_pattern = re.compile(
            r'```(?:json)?\s*(.*?)\s*```', 
            re.DOTALL | re.IGNORECASE
        )
        
        # Code block patterns
        self.code_pattern = re.compile(
            r'```(\w+)?\s*(.*?)\s*```',
            re.DOTALL
        )
        
        # Educational structure patterns
        self.section_pattern = re.compile(
            r'^#{1,3}\s+(.+)$',
            re.MULTILINE
        )
        
        # Concept definition patterns
        self.definition_pattern = re.compile(
            r'(?:(?:A|An|The)\s+)?(\w+(?:\s+\w+)*?)\s+(?:is|are|refers to|means)\s+(.+?)(?:\.|$)',
            re.IGNORECASE
        )
        
        # Learning objective patterns
        self.objective_pattern = re.compile(
            r'(?:learn|understand|be able to|master|grasp)\s+(.+?)(?:\.|$)',
            re.IGNORECASE
        )
        
        # List patterns
        self.list_pattern = re.compile(
            r'^\s*[-*•]\s+(.+)$',
            re.MULTILINE
        )
        
        # Numbered list pattern
        self.numbered_pattern = re.compile(
            r'^\s*\d+\.?\s+(.+)$',
            re.MULTILINE
        )
    
    async def parse_response(self,
                           response: str,
                           expected_type: Optional[ResponseType] = None,
                           context: Optional[Dict[str, Any]] = None) -> ParsedResponse:
        """
        Parse and deeply understand an LLM response.
        
        Args:
            response: Raw LLM response
            expected_type: Expected response type for validation
            context: Educational context for enhanced parsing
            
        Returns:
            Comprehensive parsed response with educational insights
        """
        start_time = datetime.now()
        
        try:
            # Clean and normalize response
            cleaned_response = self._clean_response(response)
            
            # Detect response type if not specified
            if expected_type is None:
                expected_type = self._detect_response_type(cleaned_response)
            
            # Parse based on type
            parsed_content = await self._parse_by_type(
                cleaned_response, expected_type, context
            )
            
            # Extract educational elements
            concepts = await self._extract_concepts(parsed_content, context)
            relationships = await self._extract_relationships(concepts, parsed_content)
            objectives = self._extract_learning_objectives(parsed_content)
            
            # Assess quality
            quality, quality_details = await self._assess_quality(
                parsed_content, expected_type, context
            )
            
            # Validate pedagogical soundness
            pedagogical_issues = await self._validate_pedagogy(
                parsed_content, concepts, objectives, context
            )
            
            # Determine cognitive level
            cognitive_level = self._determine_cognitive_level(parsed_content)
            
            # Extract prerequisites
            prerequisites = await self._extract_prerequisites(concepts, context)
            
            # Calculate difficulty
            difficulty = self._calculate_difficulty(
                concepts, cognitive_level, parsed_content
            )
            
            # Generate improvements
            refinements = self._suggest_refinements(
                quality_details, pedagogical_issues, context
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                quality, len(pedagogical_issues), expected_type
            )
            
            parse_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return ParsedResponse(
                response_type=expected_type,
                content=parsed_content,
                quality=quality,
                confidence=confidence,
                concepts=concepts,
                relationships=relationships,
                learning_objectives=objectives,
                cognitive_level=cognitive_level,
                prerequisite_concepts=prerequisites,
                difficulty_level=difficulty,
                validation_errors=quality_details.get('errors', []),
                pedagogical_issues=pedagogical_issues,
                suggested_refinements=refinements,
                parse_duration_ms=parse_duration,
                model_used=context.get('model') if context else None
            )
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            
            # Return error response
            return ParsedResponse(
                response_type=expected_type or ResponseType.ERROR_ANALYSIS,
                content={"error": str(e), "raw": response[:500]},
                quality=ContentQuality.UNACCEPTABLE,
                confidence=0.0,
                validation_errors=[str(e)],
                parse_duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def _clean_response(self, response: str) -> str:
        """Clean and normalize response."""
        # Remove excessive whitespace
        response = re.sub(r'\n{3,}', '\n\n', response)
        response = re.sub(r' {2,}', ' ', response)
        
        # Fix common formatting issues
        response = response.replace('```\n```', '')
        response = response.strip()
        
        # Normalize quotes
        response = response.replace('"', '"').replace('"', '"')
        response = response.replace(''', "'").replace(''', "'")
        
        return response
    
    def _detect_response_type(self, response: str) -> ResponseType:
        """Detect the type of response."""
        # Check for JSON structure
        if self.json_pattern.search(response) or response.strip().startswith('{'):
            return ResponseType.STRUCTURED_JSON
        
        # Check for code blocks
        code_blocks = self.code_pattern.findall(response)
        if len(code_blocks) > 2:
            return ResponseType.CODE_GENERATION
        
        # Check for educational markers
        if any(marker in response.lower() for marker in 
               ['learning objectives', 'prerequisites', 'module', 'lesson']):
            if 'learning path' in response.lower():
                return ResponseType.LEARNING_PATH
            return ResponseType.EDUCATIONAL_CONTENT
        
        # Check for concept explanation markers
        if self.definition_pattern.search(response):
            return ResponseType.CONCEPT_EXPLANATION
        
        # Check for assessment markers
        if any(marker in response.lower() for marker in 
               ['question', 'quiz', 'test', 'assessment']):
            return ResponseType.ASSESSMENT
        
        # Default to educational content
        return ResponseType.EDUCATIONAL_CONTENT
    
    async def _parse_by_type(self,
                           response: str,
                           response_type: ResponseType,
                           context: Optional[Dict[str, Any]]) -> Any:
        """Parse response based on its type."""
        if response_type == ResponseType.STRUCTURED_JSON:
            return self._parse_json(response)
        
        elif response_type == ResponseType.EDUCATIONAL_CONTENT:
            return await self._parse_educational_content(response, context)
        
        elif response_type == ResponseType.CODE_GENERATION:
            return self._parse_code_generation(response)
        
        elif response_type == ResponseType.CONCEPT_EXPLANATION:
            return await self._parse_concept_explanation(response, context)
        
        elif response_type == ResponseType.LEARNING_PATH:
            return await self._parse_learning_path(response, context)
        
        elif response_type == ResponseType.ASSESSMENT:
            return self._parse_assessment(response)
        
        elif response_type == ResponseType.DIAGRAM_SPEC:
            return self._parse_diagram_spec(response)
        
        else:
            # Generic parsing
            return self._parse_generic(response)
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from response."""
        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Extract from code blocks
        matches = self.json_pattern.findall(response)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                logger.warning("Found JSON block but failed to parse")
        
        # Try to find JSON structure
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(response[start_idx:end_idx + 1])
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to extract structured data
        return self._extract_structure_from_text(response)
    
    async def _parse_educational_content(self,
                                       response: str,
                                       context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse educational content with structure."""
        sections = self._extract_sections(response)
        
        content = {
            'title': self._extract_title(response),
            'introduction': sections.get('introduction', ''),
            'concepts': [],
            'examples': [],
            'exercises': [],
            'summary': sections.get('summary', ''),
            'learning_outcomes': []
        }
        
        # Extract concepts
        if 'concepts' in sections:
            content['concepts'] = await self._parse_concepts_section(
                sections['concepts'], context
            )
        
        # Extract examples
        content['examples'] = self._extract_examples(response)
        
        # Extract exercises
        if 'exercises' in sections or 'practice' in sections:
            content['exercises'] = self._extract_exercises(
                sections.get('exercises', sections.get('practice', ''))
            )
        
        # Extract learning outcomes
        content['learning_outcomes'] = self._extract_learning_objectives(response)
        
        # Try to fit into model if available
        if ResponseType.EDUCATIONAL_CONTENT in self.response_models:
            try:
                return self.response_models[ResponseType.EDUCATIONAL_CONTENT](**content).dict()
            except ValidationError as e:
                logger.warning(f"Validation error: {e}")
        
        return content
    
    async def _parse_concept_explanation(self,
                                       response: str,
                                       context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse concept explanation."""
        # Extract main concept
        concept_match = self.definition_pattern.search(response)
        concept = concept_match.group(1) if concept_match else "Unknown Concept"
        
        explanation = {
            'concept': concept,
            'definition': '',
            'explanation': '',
            'analogies': [],
            'examples': [],
            'common_misconceptions': [],
            'related_concepts': []
        }
        
        # Extract definition
        if concept_match:
            explanation['definition'] = concept_match.group(2)
        
        # Extract detailed explanation
        sections = self._extract_sections(response)
        explanation['explanation'] = sections.get('explanation', 
                                                sections.get('description', response))
        
        # Extract analogies
        analogy_section = sections.get('analogies', sections.get('analogy', ''))
        if analogy_section:
            explanation['analogies'] = self._extract_list_items(analogy_section)
        
        # Extract examples
        explanation['examples'] = self._extract_examples(response)
        
        # Extract misconceptions
        misconception_section = sections.get('misconceptions', 
                                           sections.get('common mistakes', ''))
        if misconception_section:
            explanation['common_misconceptions'] = self._extract_list_items(
                misconception_section
            )
        
        # Extract related concepts
        if self.knowledge_graph and context:
            explanation['related_concepts'] = await self._find_related_concepts(
                concept, context
            )
        
        return explanation
    
    async def _parse_learning_path(self,
                                 response: str,
                                 context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse learning path structure."""
        sections = self._extract_sections(response)
        
        path = {
            'title': self._extract_title(response),
            'description': sections.get('description', ''),
            'target_audience': self._extract_target_audience(response),
            'duration_hours': self._extract_duration(response),
            'modules': [],
            'prerequisites': [],
            'learning_objectives': [],
            'assessments': []
        }
        
        # Extract modules
        modules_section = sections.get('modules', sections.get('curriculum', ''))
        if modules_section:
            path['modules'] = self._parse_modules(modules_section)
        
        # Extract prerequisites
        prereq_section = sections.get('prerequisites', '')
        if prereq_section:
            path['prerequisites'] = self._extract_list_items(prereq_section)
        
        # Extract objectives
        path['learning_objectives'] = self._extract_learning_objectives(response)
        
        # Extract assessments
        assessment_section = sections.get('assessments', sections.get('evaluation', ''))
        if assessment_section:
            path['assessments'] = self._parse_assessments(assessment_section)
        
        return path
    
    def _parse_code_generation(self, response: str) -> Dict[str, Any]:
        """Parse code generation response."""
        code_blocks = self.code_pattern.findall(response)
        
        result = {
            'code_blocks': [],
            'explanation': '',
            'usage_examples': [],
            'dependencies': []
        }
        
        # Extract code blocks
        for lang, code in code_blocks:
            result['code_blocks'].append({
                'language': lang or 'text',
                'code': code.strip(),
                'purpose': self._infer_code_purpose(code)
            })
        
        # Extract explanation
        text_parts = re.split(self.code_pattern, response)
        explanations = [part.strip() for part in text_parts 
                       if part and not any(cb[1] in part for cb in code_blocks)]
        result['explanation'] = '\n\n'.join(explanations)
        
        # Extract dependencies
        result['dependencies'] = self._extract_dependencies(response)
        
        return result
    
    def _parse_assessment(self, response: str) -> Dict[str, Any]:
        """Parse assessment/quiz content."""
        questions = []
        
        # Split into questions
        question_parts = re.split(r'\n\s*\d+\.', response)
        
        for part in question_parts[1:]:  # Skip first split
            question_data = self._parse_question(part)
            if question_data:
                questions.append(question_data)
        
        return {
            'questions': questions,
            'instructions': question_parts[0] if question_parts else '',
            'total_points': sum(q.get('points', 1) for q in questions)
        }
    
    def _parse_diagram_spec(self, response: str) -> Dict[str, Any]:
        """Parse diagram specification."""
        spec = {
            'type': 'diagram',
            'elements': [],
            'connections': [],
            'layout': {},
            'annotations': []
        }
        
        # Extract diagram type
        if 'flowchart' in response.lower():
            spec['type'] = 'flowchart'
        elif 'sequence' in response.lower():
            spec['type'] = 'sequence'
        elif 'class' in response.lower():
            spec['type'] = 'class_diagram'
        
        # Extract elements and connections
        # This would parse specific diagram syntax
        
        return spec
    
    def _parse_generic(self, response: str) -> Dict[str, Any]:
        """Generic parsing for unstructured responses."""
        sections = self._extract_sections(response)
        lists = self._extract_all_lists(response)
        
        return {
            'content': response,
            'sections': sections,
            'lists': lists,
            'key_points': self._extract_key_points(response)
        }
    
    # Extraction methods
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from text based on headers."""
        sections = {}
        current_section = "introduction"
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            header_match = self.section_pattern.match(line)
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = header_match.group(1).lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_title(self, text: str) -> str:
        """Extract title from text."""
        # Look for H1 header
        h1_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if h1_match:
            return h1_match.group(1)
        
        # Look for first line
        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 100:  # Reasonable title length
                return first_line
        
        return "Untitled"
    
    async def _extract_concepts(self,
                              content: Any,
                              context: Optional[Dict[str, Any]]) -> List[str]:
        """Extract key concepts from parsed content."""
        concepts = []
        
        # Extract from different content types
        if isinstance(content, dict):
            # From concepts field
            if 'concepts' in content:
                if isinstance(content['concepts'], list):
                    for concept in content['concepts']:
                        if isinstance(concept, str):
                            concepts.append(concept)
                        elif isinstance(concept, dict) and 'name' in concept:
                            concepts.append(concept['name'])
            
            # From text content
            if 'content' in content:
                text_concepts = await self.nlp_processor.extract_concepts(
                    content['content']
                )
                concepts.extend(text_concepts)
        
        # Validate against knowledge graph
        if self.knowledge_graph and concepts:
            validated_concepts = []
            for concept in concepts:
                if await self.knowledge_graph.validate_concept(concept):
                    validated_concepts.append(concept)
            concepts = validated_concepts
        
        return list(set(concepts))
    
    async def _extract_relationships(self,
                                   concepts: List[str],
                                   content: Any) -> List[Tuple[str, str, str]]:
        """Extract relationships between concepts."""
        relationships = []
        
        if self.nlp_processor and isinstance(content, dict):
            text = content.get('content', '')
            if not text and 'explanation' in content:
                text = content['explanation']
            
            if text:
                # Use NLP to extract relationships
                extracted = await self.nlp_processor.extract_relationships(text)
                relationships.extend(extracted)
        
        # Infer basic relationships from concepts
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                relationships.append((concept1, "related_to", concept2))
        
        return relationships
    
    def _extract_learning_objectives(self, content: Any) -> List[str]:
        """Extract learning objectives."""
        objectives = []
        
        # From structured content
        if isinstance(content, dict) and 'learning_objectives' in content:
            return content['learning_objectives']
        
        # From text
        text = str(content)
        
        # Pattern matching
        objective_matches = self.objective_pattern.findall(text)
        objectives.extend(objective_matches)
        
        # Look for objective sections
        if 'objective' in text.lower():
            lines = text.split('\n')
            in_objectives = False
            
            for line in lines:
                if 'objective' in line.lower():
                    in_objectives = True
                elif in_objectives and line.strip():
                    if line.strip().startswith(('-', '*', '•')) or line[0].isdigit():
                        objectives.append(line.strip().lstrip('-*•0123456789. '))
                elif in_objectives and not line.strip():
                    in_objectives = False
        
        return list(set(objectives))
    
    async def _assess_quality(self,
                            content: Any,
                            response_type: ResponseType,
                            context: Optional[Dict[str, Any]]) -> Tuple[ContentQuality, Dict[str, Any]]:
        """Assess content quality."""
        scores = {}
        details = {'errors': [], 'warnings': [], 'suggestions': []}
        
        # Clarity assessment
        clarity_score = await self._assess_clarity(content)
        scores['clarity'] = clarity_score
        
        # Completeness assessment
        completeness_score = self._assess_completeness(content, response_type)
        scores['completeness'] = completeness_score
        
        if completeness_score < 0.6:
            details['warnings'].append("Content appears incomplete")
        
        # Accuracy assessment (would check against knowledge base)
        accuracy_score = 0.8  # Placeholder
        scores['accuracy'] = accuracy_score
        
        # Pedagogical assessment
        pedagogy_score = await self._assess_pedagogy(content, context)
        scores['pedagogy'] = pedagogy_score
        
        # Calculate weighted score
        total_score = sum(
            scores[criterion] * self.quality_criteria[criterion]
            for criterion in scores
        )
        
        # Determine quality level
        if total_score >= 0.9:
            quality = ContentQuality.EXCELLENT
        elif total_score >= 0.75:
            quality = ContentQuality.GOOD
        elif total_score >= 0.6:
            quality = ContentQuality.ACCEPTABLE
        elif total_score >= 0.4:
            quality = ContentQuality.NEEDS_IMPROVEMENT
        else:
            quality = ContentQuality.UNACCEPTABLE
            details['errors'].append("Content quality below acceptable threshold")
        
        details['scores'] = scores
        details['total_score'] = total_score
        
        return quality, details
    
    async def _assess_clarity(self, content: Any) -> float:
        """Assess content clarity."""
        if not content:
            return 0.0
        
        text = str(content)
        
        # Factors for clarity
        factors = []
        
        # Sentence length
        sentences = text.split('.')
        avg_sentence_length = np.mean([len(s.split()) for s in sentences if s])
        
        # Ideal: 15-20 words per sentence
        if 15 <= avg_sentence_length <= 20:
            factors.append(1.0)
        else:
            factors.append(1.0 - abs(avg_sentence_length - 17.5) / 30)
        
        # Paragraph structure
        paragraphs = text.split('\n\n')
        if 2 <= len(paragraphs) <= 10:
            factors.append(1.0)
        else:
            factors.append(0.7)
        
        # Technical jargon density (simplified)
        jargon_ratio = len([w for w in text.split() if len(w) > 10]) / len(text.split())
        factors.append(1.0 - jargon_ratio)
        
        return np.mean(factors) if factors else 0.5
    
    def _assess_completeness(self, content: Any, response_type: ResponseType) -> float:
        """Assess content completeness."""
        if response_type == ResponseType.EDUCATIONAL_CONTENT:
            required = ['introduction', 'concepts', 'examples', 'summary']
            if isinstance(content, dict):
                present = sum(1 for r in required if r in content and content[r])
                return present / len(required)
        
        elif response_type == ResponseType.CONCEPT_EXPLANATION:
            required = ['concept', 'definition', 'explanation', 'examples']
            if isinstance(content, dict):
                present = sum(1 for r in required if r in content and content[r])
                return present / len(required)
        
        # Generic completeness based on length
        text_length = len(str(content))
        if text_length < 100:
            return 0.3
        elif text_length < 500:
            return 0.6
        else:
            return 0.9
    
    async def _assess_pedagogy(self, content: Any, context: Optional[Dict[str, Any]]) -> float:
        """Assess pedagogical soundness."""
        factors = []
        
        # Check for learning objectives
        objectives = self._extract_learning_objectives(content)
        factors.append(1.0 if objectives else 0.5)
        
        # Check for examples
        if isinstance(content, dict):
            has_examples = bool(content.get('examples'))
            factors.append(1.0 if has_examples else 0.6)
        
        # Check for proper scaffolding
        if isinstance(content, dict) and 'concepts' in content:
            # Concepts should build on each other
            factors.append(0.8)  # Placeholder for scaffolding analysis
        
        # Check for audience appropriateness
        if context and 'audience_level' in context:
            # Would analyze complexity vs. audience
            factors.append(0.85)
        
        return np.mean(factors) if factors else 0.7
    
    async def _validate_pedagogy(self,
                               content: Any,
                               concepts: List[str],
                               objectives: List[str],
                               context: Optional[Dict[str, Any]]) -> List[str]:
        """Validate pedagogical correctness."""
        issues = []
        
        # Check alignment between objectives and content
        if objectives and not concepts:
            issues.append("Learning objectives defined but no concepts extracted")
        
        # Check cognitive load
        if len(concepts) > 7:
            issues.append(f"Too many concepts ({len(concepts)}) for single lesson - consider chunking")
        
        # Check for misconception handling
        if isinstance(content, dict) and not content.get('common_misconceptions'):
            issues.append("Consider addressing common misconceptions")
        
        # Check example quality
        if isinstance(content, dict):
            examples = content.get('examples', [])
            if not examples:
                issues.append("No examples provided - examples enhance understanding")
            elif len(examples) < 2:
                issues.append("Consider providing more examples for better understanding")
        
        return issues
    
    def _determine_cognitive_level(self, content: Any) -> str:
        """Determine cognitive level using Bloom's taxonomy."""
        # Analyze content for cognitive indicators
        text = str(content).lower()
        
        # Bloom's taxonomy levels
        levels = {
            'create': ['create', 'design', 'develop', 'formulate', 'build'],
            'evaluate': ['evaluate', 'assess', 'critique', 'judge', 'justify'],
            'analyze': ['analyze', 'examine', 'compare', 'contrast', 'investigate'],
            'apply': ['apply', 'implement', 'use', 'demonstrate', 'solve'],
            'understand': ['explain', 'describe', 'summarize', 'interpret'],
            'remember': ['define', 'list', 'identify', 'recall', 'name']
        }
        
        # Check for keywords
        for level, keywords in levels.items():
            if any(keyword in text for keyword in keywords):
                return level
        
        return 'understand'  # Default
    
    async def _extract_prerequisites(self,
                                   concepts: List[str],
                                   context: Optional[Dict[str, Any]]) -> List[str]:
        """Extract prerequisite concepts."""
        prerequisites = []
        
        if self.knowledge_graph:
            for concept in concepts:
                prereqs = await self.knowledge_graph.get_prerequisites(concept)
                prerequisites.extend(prereqs)
        
        # Remove duplicates and current concepts
        prerequisites = list(set(prerequisites) - set(concepts))
        
        return prerequisites
    
    def _calculate_difficulty(self,
                            concepts: List[str],
                            cognitive_level: str,
                            content: Any) -> float:
        """Calculate content difficulty level."""
        factors = []
        
        # Concept complexity
        concept_score = min(len(concepts) / 10, 1.0)
        factors.append(concept_score)
        
        # Cognitive level
        level_scores = {
            'remember': 0.2,
            'understand': 0.4,
            'apply': 0.6,
            'analyze': 0.7,
            'evaluate': 0.85,
            'create': 1.0
        }
        factors.append(level_scores.get(cognitive_level, 0.5))
        
        # Content depth (based on length)
        text_length = len(str(content))
        depth_score = min(text_length / 5000, 1.0)
        factors.append(depth_score)
        
        return np.mean(factors)
    
    def _suggest_refinements(self,
                           quality_details: Dict[str, Any],
                           pedagogical_issues: List[str],
                           context: Optional[Dict[str, Any]]) -> List[str]:
        """Suggest content refinements."""
        refinements = []
        
        # Based on quality scores
        scores = quality_details.get('scores', {})
        
        if scores.get('clarity', 1.0) < 0.7:
            refinements.append("Simplify language and use shorter sentences")
            refinements.append("Add more paragraph breaks for better readability")
        
        if scores.get('completeness', 1.0) < 0.7:
            refinements.append("Add more examples to illustrate concepts")
            refinements.append("Include a summary section")
        
        if scores.get('pedagogy', 1.0) < 0.7:
            refinements.append("Add clear learning objectives at the beginning")
            refinements.append("Include practice exercises or self-check questions")
        
        # Based on pedagogical issues
        refinements.extend([f"Address: {issue}" for issue in pedagogical_issues[:3]])
        
        # Context-specific suggestions
        if context and context.get('audience_level') == 'beginner':
            refinements.append("Consider adding more foundational explanations")
        
        return list(set(refinements))[:5]  # Top 5 unique suggestions
    
    def _calculate_confidence(self,
                            quality: ContentQuality,
                            num_issues: int,
                            response_type: ResponseType) -> float:
        """Calculate parsing confidence."""
        # Base confidence from quality
        confidence_map = {
            ContentQuality.EXCELLENT: 0.95,
            ContentQuality.GOOD: 0.85,
            ContentQuality.ACCEPTABLE: 0.7,
            ContentQuality.NEEDS_IMPROVEMENT: 0.5,
            ContentQuality.UNACCEPTABLE: 0.3
        }
        
        base_confidence = confidence_map[quality]
        
        # Adjust for issues
        issue_penalty = min(num_issues * 0.05, 0.3)
        
        # Adjust for response type complexity
        type_factors = {
            ResponseType.STRUCTURED_JSON: 1.0,
            ResponseType.EDUCATIONAL_CONTENT: 0.95,
            ResponseType.CONCEPT_EXPLANATION: 0.9,
            ResponseType.CODE_GENERATION: 0.85,
            ResponseType.LEARNING_PATH: 0.9,
            ResponseType.ASSESSMENT: 0.85,
            ResponseType.DIAGRAM_SPEC: 0.8
        }
        
        type_factor = type_factors.get(response_type, 0.8)
        
        return max(0.1, (base_confidence - issue_penalty) * type_factor)
    
    # Helper methods for specific parsing tasks
    def _extract_structure_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structure from unstructured text."""
        structure = {}
        
        # Extract key-value pairs
        kv_pattern = re.compile(r'^(\w+(?:\s+\w+)*?):\s*(.+)$', re.MULTILINE)
        for key, value in kv_pattern.findall(text):
            structure[key.lower().replace(' ', '_')] = value
        
        return structure
    
    def _extract_examples(self, text: str) -> List[Dict[str, str]]:
        """Extract examples from text."""
        examples = []
        
        # Look for example markers
        example_pattern = re.compile(
            r'(?:Example|For example|For instance)[:.]?\s*(.+?)(?=\n\n|Example|$)',
            re.IGNORECASE | re.DOTALL
        )
        
        for match in example_pattern.findall(text):
            examples.append({
                'content': match.strip(),
                'type': 'text_example'
            })
        
        return examples
    
    def _extract_list_items(self, text: str) -> List[str]:
        """Extract list items from text."""
        items = []
        
        # Bullet points
        items.extend(self.list_pattern.findall(text))
        
        # Numbered lists
        items.extend(self.numbered_pattern.findall(text))
        
        return [item.strip() for item in items if item.strip()]
    
    def _extract_exercises(self, text: str) -> List[Dict[str, Any]]:
        """Extract exercises from text."""
        exercises = []
        
        # Split by exercise markers
        exercise_parts = re.split(r'Exercise \d+|Practice \d+|Task \d+', text)
        
        for part in exercise_parts[1:]:  # Skip first
            exercise = {
                'instructions': part.strip().split('\n')[0],
                'content': part.strip()
            }
            exercises.append(exercise)
        
        return exercises
    
    def _extract_target_audience(self, text: str) -> str:
        """Extract target audience."""
        audience_pattern = re.compile(
            r'(?:target audience|for|designed for|suitable for)[:.]?\s*(.+?)(?:\.|$)',
            re.IGNORECASE
        )
        
        match = audience_pattern.search(text)
        if match:
            return match.group(1)
        
        return "General audience"
    
    def _extract_duration(self, text: str) -> float:
        """Extract duration in hours."""
        duration_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)',
            re.IGNORECASE
        )
        
        match = duration_pattern.search(text)
        if match:
            return float(match.group(1))
        
        # Try minutes
        min_pattern = re.compile(r'(\d+)\s*(?:minutes?|mins?)', re.IGNORECASE)
        min_match = min_pattern.search(text)
        if min_match:
            return float(min_match.group(1)) / 60
        
        return 1.0  # Default 1 hour
    
    def _parse_modules(self, text: str) -> List[Dict[str, Any]]:
        """Parse learning modules."""
        modules = []
        
        # Split by module markers
        module_parts = re.split(r'Module \d+|Lesson \d+|Unit \d+', text)
        
        for i, part in enumerate(module_parts[1:], 1):
            lines = part.strip().split('\n')
            module = {
                'number': i,
                'title': lines[0] if lines else f"Module {i}",
                'content': '\n'.join(lines[1:]) if len(lines) > 1 else '',
                'duration': self._extract_duration(part)
            }
            modules.append(module)
        
        return modules
    
    def _parse_assessments(self, text: str) -> List[Dict[str, Any]]:
        """Parse assessments."""
        assessments = []
        
        # Look for assessment types
        assessment_types = ['quiz', 'test', 'exam', 'project', 'assignment']
        
        for assess_type in assessment_types:
            if assess_type in text.lower():
                assessments.append({
                    'type': assess_type,
                    'description': text.strip()
                })
        
        return assessments
    
    def _parse_question(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a single question."""
        lines = text.strip().split('\n')
        if not lines:
            return None
        
        question = {
            'question': lines[0],
            'type': 'multiple_choice',
            'options': [],
            'correct_answer': None,
            'explanation': None,
            'points': 1
        }
        
        # Extract options
        option_pattern = re.compile(r'^[a-e]\)|[A-E]\)')
        current_option = None
        
        for line in lines[1:]:
            if option_pattern.match(line):
                option_text = line[2:].strip()
                question['options'].append(option_text)
                
                # Check if marked as correct
                if '*' in line or '(correct)' in line.lower():
                    question['correct_answer'] = len(question['options']) - 1
        
        return question if question['options'] else None
    
    def _infer_code_purpose(self, code: str) -> str:
        """Infer the purpose of code block."""
        # Simple heuristics
        if 'def ' in code or 'function ' in code:
            return 'function_definition'
        elif 'class ' in code:
            return 'class_definition'
        elif 'import ' in code or 'require' in code:
            return 'imports'
        elif '=' in code and not '==' in code:
            return 'variable_assignment'
        else:
            return 'code_snippet'
    
    def _extract_dependencies(self, text: str) -> List[str]:
        """Extract code dependencies."""
        dependencies = []
        
        # Python imports
        import_pattern = re.compile(r'import\s+(\w+)|from\s+(\w+)\s+import')
        for match in import_pattern.findall(text):
            dep = match[0] or match[1]
            if dep:
                dependencies.append(dep)
        
        # Package.json style
        package_pattern = re.compile(r'"(\w+)":\s*"[^"]+"')
        dependencies.extend(package_pattern.findall(text))
        
        return list(set(dependencies))
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text."""
        key_points = []
        
        # Look for emphasis markers
        emphasis_pattern = re.compile(
            r'(?:key point|important|note|remember)[:.]?\s*(.+?)(?:\.|$)',
            re.IGNORECASE
        )
        
        key_points.extend(emphasis_pattern.findall(text))
        
        # Look for bold text (markdown)
        bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        key_points.extend(bold_pattern.findall(text))
        
        return list(set(key_points))[:5]  # Top 5 unique points
    
    def _extract_all_lists(self, text: str) -> Dict[str, List[str]]:
        """Extract all lists from text."""
        lists = {}
        
        # Find list sections
        lines = text.split('\n')
        current_list_name = None
        current_items = []
        
        for line in lines:
            # Check if this starts a new list
            if line.strip().endswith(':') and not line.strip().startswith(('-', '*')):
                if current_list_name and current_items:
                    lists[current_list_name] = current_items
                
                current_list_name = line.strip().rstrip(':').lower().replace(' ', '_')
                current_items = []
            
            # Check if this is a list item
            elif line.strip().startswith(('-', '*', '•')) or re.match(r'^\s*\d+\.', line):
                item = re.sub(r'^[-*•\d.]\s*', '', line.strip())
                current_items.append(item)
        
        # Save last list
        if current_list_name and current_items:
            lists[current_list_name] = current_items
        
        return lists
    
    async def _find_related_concepts(self,
                                   concept: str,
                                   context: Optional[Dict[str, Any]]) -> List[str]:
        """Find related concepts using knowledge graph."""
        if not self.knowledge_graph:
            return []
        
        related = await self.knowledge_graph.find_related_concepts(
            concept,
            max_distance=2,
            limit=5
        )
        
        return related
    
    async def enhance_response(self,
                             parsed: ParsedResponse,
                             enhancement_level: str = "moderate") -> ParsedResponse:
        """
        Enhance parsed response for better educational outcomes.
        
        This is where the parser goes beyond extraction to actually
        improve the content based on pedagogical principles.
        """
        if enhancement_level == "none":
            return parsed
        
        enhanced = parsed  # Work on a copy in production
        
        # Enhance based on quality issues
        if parsed.quality in [ContentQuality.NEEDS_IMPROVEMENT, ContentQuality.ACCEPTABLE]:
            # Add missing elements
            if parsed.response_type == ResponseType.EDUCATIONAL_CONTENT:
                content = parsed.content
                
                # Add examples if missing
                if not content.get('examples'):
                    content['examples'] = await self._generate_examples(
                        parsed.concepts, parsed.cognitive_level
                    )
                
                # Add summary if missing
                if not content.get('summary'):
                    content['summary'] = await self._generate_summary(
                        content, parsed.concepts
                    )
                
                # Add learning objectives if missing
                if not parsed.learning_objectives:
                    enhanced.learning_objectives = await self._generate_objectives(
                        parsed.concepts, parsed.cognitive_level
                    )
        
        # Enhance for accessibility
        if enhancement_level == "full":
            # Add alternative representations
            enhanced.content['alternative_formats'] = {
                'simplified': await self._simplify_content(parsed.content),
                'visual_description': await self._generate_visual_description(parsed.content),
                'audio_script': await self._generate_audio_script(parsed.content)
            }
        
        # Update quality after enhancement
        enhanced.quality = ContentQuality.GOOD
        enhanced.suggested_refinements = ["Content has been automatically enhanced"]
        
        return enhanced
    
    async def _generate_examples(self,
                               concepts: List[str],
                               cognitive_level: str) -> List[Dict[str, str]]:
        """Generate examples for concepts."""
        # Placeholder - would use LLM or knowledge base
        examples = []
        
        for concept in concepts[:3]:  # Top 3 concepts
            examples.append({
                'concept': concept,
                'content': f"Example demonstrating {concept}",
                'type': 'generated'
            })
        
        return examples
    
    async def _generate_summary(self,
                              content: Dict[str, Any],
                              concepts: List[str]) -> str:
        """Generate content summary."""
        # Placeholder - would use summarization
        key_points = [
            f"This content covers {len(concepts)} key concepts",
            f"Main topics include: {', '.join(concepts[:3])}"
        ]
        
        return ". ".join(key_points)
    
    async def _generate_objectives(self,
                                 concepts: List[str],
                                 cognitive_level: str) -> List[str]:
        """Generate learning objectives."""
        objectives = []
        
        # Templates based on Bloom's taxonomy
        templates = {
            'remember': "Identify and recall {}",
            'understand': "Explain the concept of {}",
            'apply': "Apply {} to solve problems",
            'analyze': "Analyze the components of {}",
            'evaluate': "Evaluate the effectiveness of {}",
            'create': "Create solutions using {}"
        }
        
        template = templates.get(cognitive_level, templates['understand'])
        
        for concept in concepts[:3]:
            objectives.append(template.format(concept))
        
        return objectives
    
    async def _simplify_content(self, content: Any) -> Dict[str, Any]:
        """Simplify content for accessibility."""
        # Placeholder - would use text simplification
        return {
            'simplified': True,
            'content': str(content)[:500] + "... (simplified)"
        }
    
    async def _generate_visual_description(self, content: Any) -> str:
        """Generate visual description of content."""
        # Placeholder - would analyze structure
        return "Visual representation of the educational content structure"
    
    async def _generate_audio_script(self, content: Any) -> str:
        """Generate audio narration script."""
        # Placeholder - would optimize for audio
        return f"Audio script for: {str(content)[:100]}..."

    # Add numpy import at the top of the file
    import numpy as np
