"""
NLP Processor - Educational Language Understanding
Part of the AI Agent Orchestration Platform for Educational Excellence

This component understands educational language, extracts learning concepts,
and ensures content is pedagogically sound.
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

import spacy
import nltk
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import numpy as np

from ..core.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)


class TextComplexity(Enum):
    """Text complexity levels for educational content."""
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ConceptType(Enum):
    """Types of educational concepts."""
    DEFINITION = "definition"
    PRINCIPLE = "principle"
    PROCESS = "process"
    EXAMPLE = "example"
    APPLICATION = "application"
    THEORY = "theory"
    FACT = "fact"
    SKILL = "skill"


@dataclass
class ExtractedConcept:
    """An extracted educational concept."""
    text: str
    type: ConceptType
    confidence: float
    context: str
    start_pos: int
    end_pos: int
    related_terms: List[str] = None
    

@dataclass
class Relationship:
    """A relationship between concepts."""
    source: str
    relation: str
    target: str
    confidence: float
    evidence: str


class NLPProcessor:
    """
    Advanced NLP processor for educational content.
    
    This isn't just text processing - it understands how language
    conveys educational concepts and ensures pedagogical clarity.
    """
    
    def __init__(self):
        """Initialize NLP models and resources."""
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model")
        except:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Initialize NLTK resources
        self._initialize_nltk()
        
        # Educational concept patterns
        self._initialize_patterns()
        
        # Readability analyzer
        self.readability_cache = {}
        
        # Concept extraction model (would use fine-tuned model in production)
        try:
            self.ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple"
            )
        except:
            logger.warning("NER model not available")
            self.ner_pipeline = None
        
        logger.info("NLPProcessor initialized")
    
    def _initialize_nltk(self):
        """Initialize NLTK resources."""
        required_resources = ['punkt', 'averaged_perceptron_tagger', 'wordnet']
        for resource in required_resources:
            try:
                nltk.data.find(f'tokenizers/{resource}')
            except LookupError:
                logger.info(f"Downloading NLTK resource: {resource}")
                nltk.download(resource, quiet=True)
    
    def _initialize_patterns(self):
        """Initialize educational concept patterns."""
        # Definition patterns
        self.definition_patterns = [
            re.compile(r'(\w+(?:\s+\w+)*?)\s+(?:is|are)\s+(?:defined as|known as)\s+(.+?)(?:\.|;|$)', re.IGNORECASE),
            re.compile(r'(\w+(?:\s+\w+)*?):\s+(.+?)(?:\.|;|$)', re.IGNORECASE),
            re.compile(r'(?:A|An|The)\s+(\w+(?:\s+\w+)*?)\s+is\s+(?:a|an|the)\s+(.+?)(?:\.|;|$)', re.IGNORECASE),
        ]
        
        # Process patterns
        self.process_patterns = [
            re.compile(r'(?:steps?|process|procedure|method)\s+(?:to|for|of)\s+(.+?)(?:\.|;|$)', re.IGNORECASE),
            re.compile(r'(?:first|then|next|finally|step\s+\d+)[,:]?\s+(.+?)(?:\.|;|$)', re.IGNORECASE),
        ]
        
        # Example patterns
        self.example_patterns = [
            re.compile(r'(?:for example|for instance|such as|e\.g\.|example:)\s*(.+?)(?:\.|;|$)', re.IGNORECASE),
            re.compile(r'(?:consider|take|look at)\s+(?:the\s+)?(?:example|case)\s+(?:of\s+)?(.+?)(?:\.|;|$)', re.IGNORECASE),
        ]
        
        # Relationship patterns
        self.relationship_patterns = [
            (re.compile(r'(\w+(?:\s+\w+)*?)\s+(?:leads to|results in|causes)\s+(\w+(?:\s+\w+)*?)', re.IGNORECASE), "leads_to"),
            (re.compile(r'(\w+(?:\s+\w+)*?)\s+(?:is part of|belongs to|is a component of)\s+(\w+(?:\s+\w+)*?)', re.IGNORECASE), "part_of"),
            (re.compile(r'(\w+(?:\s+\w+)*?)\s+(?:requires|depends on|needs)\s+(\w+(?:\s+\w+)*?)', re.IGNORECASE), "requires"),
            (re.compile(r'(\w+(?:\s+\w+)*?)\s+(?:is similar to|resembles|is like)\s+(\w+(?:\s+\w+)*?)', re.IGNORECASE), "similar_to"),
            (re.compile(r'(\w+(?:\s+\w+)*?)\s+(?:differs from|is different from|contrasts with)\s+(\w+(?:\s+\w+)*?)', re.IGNORECASE), "differs_from"),
        ]
    
    async def extract_concepts(self, 
                             text: str,
                             context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Extract educational concepts from text.
        
        Args:
            text: Input text
            context: Optional context about the domain
            
        Returns:
            List of concept strings
        """
        concepts = set()
        
        # Use NER if available
        if self.ner_pipeline:
            try:
                entities = self.ner_pipeline(text)
                for entity in entities:
                    if entity['score'] > 0.7:
                        concepts.add(entity['word'])
            except:
                pass
        
        # Pattern-based extraction
        extracted = await self._extract_concepts_by_patterns(text)
        concepts.update([c.text for c in extracted])
        
        # SpaCy noun phrases
        if self.nlp:
            doc = self.nlp(text)
            for chunk in doc.noun_chunks:
                if 2 <= len(chunk.text.split()) <= 4:  # Reasonable concept length
                    concepts.add(chunk.text)
        
        # Filter by context if provided
        if context and 'domain' in context:
            concepts = self._filter_by_domain(concepts, context['domain'])
        
        return list(concepts)
    
    async def _extract_concepts_by_patterns(self, text: str) -> List[ExtractedConcept]:
        """Extract concepts using patterns."""
        extracted = []
        
        # Definitions
        for pattern in self.definition_patterns:
            for match in pattern.finditer(text):
                concept = ExtractedConcept(
                    text=match.group(1).strip(),
                    type=ConceptType.DEFINITION,
                    confidence=0.9,
                    context=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                extracted.append(concept)
        
        # Processes
        for pattern in self.process_patterns:
            for match in pattern.finditer(text):
                concept = ExtractedConcept(
                    text=match.group(1).strip(),
                    type=ConceptType.PROCESS,
                    confidence=0.8,
                    context=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                extracted.append(concept)
        
        # Examples
        for pattern in self.example_patterns:
            for match in pattern.finditer(text):
                concept = ExtractedConcept(
                    text=match.group(1).strip(),
                    type=ConceptType.EXAMPLE,
                    confidence=0.85,
                    context=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                extracted.append(concept)
        
        return extracted
    
    async def extract_relationships(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Extract relationships between concepts.
        
        Args:
            text: Input text
            
        Returns:
            List of (source, relation, target) tuples
        """
        relationships = []
        
        for pattern, relation_type in self.relationship_patterns:
            for match in pattern.finditer(text):
                source = match.group(1).strip()
                target = match.group(2).strip()
                relationships.append((source, relation_type, target))
        
        # Use dependency parsing if spaCy available
        if self.nlp:
            doc = self.nlp(text)
            for token in doc:
                if token.dep_ in ["nsubj", "dobj"] and token.head.pos_ == "VERB":
                    # Extract subject-verb-object relationships
                    if token.dep_ == "nsubj":
                        for child in token.head.children:
                            if child.dep_ == "dobj":
                                relationships.append((
                                    token.text,
                                    token.head.text,
                                    child.text
                                ))
        
        return relationships
    
    async def analyze_complexity(self, text: str) -> Dict[str, Any]:
        """
        Analyze text complexity for educational appropriateness.
        
        Args:
            text: Input text
            
        Returns:
            Complexity analysis results
        """
        # Check cache
        text_hash = hash(text)
        if text_hash in self.readability_cache:
            return self.readability_cache[text_hash]
        
        analysis = {
            'complexity_level': TextComplexity.INTERMEDIATE,
            'readability_scores': {},
            'metrics': {},
            'recommendations': []
        }
        
        # Basic metrics
        sentences = nltk.sent_tokenize(text)
        words = nltk.word_tokenize(text)
        syllables = self._count_syllables(text)
        
        analysis['metrics'] = {
            'sentence_count': len(sentences),
            'word_count': len(words),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'avg_word_length': sum(len(w) for w in words) / max(len(words), 1),
            'syllable_count': syllables,
            'unique_words': len(set(words)),
            'lexical_diversity': len(set(words)) / max(len(words), 1)
        }
        
        # Flesch Reading Ease
        if len(sentences) > 0 and len(words) > 0:
            fre = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syllables / len(words))
            analysis['readability_scores']['flesch_reading_ease'] = max(0, min(100, fre))
            
            # Determine complexity level
            if fre >= 90:
                analysis['complexity_level'] = TextComplexity.ELEMENTARY
            elif fre >= 60:
                analysis['complexity_level'] = TextComplexity.INTERMEDIATE
            elif fre >= 30:
                analysis['complexity_level'] = TextComplexity.ADVANCED
            else:
                analysis['complexity_level'] = TextComplexity.EXPERT
        
        # Recommendations
        if analysis['metrics']['avg_sentence_length'] > 25:
            analysis['recommendations'].append("Consider breaking up long sentences")
        
        if analysis['metrics']['lexical_diversity'] < 0.4:
            analysis['recommendations'].append("Increase vocabulary variety")
        
        if analysis['complexity_level'] == TextComplexity.EXPERT:
            analysis['recommendations'].append("Consider simplifying for broader audience")
        
        # Cache result
        self.readability_cache[text_hash] = analysis
        
        return analysis
    
    def _count_syllables(self, text: str) -> int:
        """Count syllables in text."""
        syllable_count = 0
        words = nltk.word_tokenize(text.lower())
        
        for word in words:
            # Simple syllable counting algorithm
            vowels = 'aeiouy'
            word = word.lower().strip(".:;?!")
            count = 0
            previous_was_vowel = False
            
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not previous_was_vowel:
                    count += 1
                previous_was_vowel = is_vowel
            
            # Adjust for silent e
            if word.endswith('e'):
                count -= 1
            
            # Ensure at least one syllable
            if count == 0:
                count = 1
            
            syllable_count += count
        
        return syllable_count
    
    def _filter_by_domain(self, concepts: Set[str], domain: str) -> Set[str]:
        """Filter concepts by domain relevance."""
        # In production, this would use domain-specific vocabularies
        # For now, return all concepts
        return concepts
    
    async def simplify_text(self, 
                          text: str,
                          target_level: TextComplexity = TextComplexity.INTERMEDIATE) -> str:
        """
        Simplify text to target complexity level.
        
        Args:
            text: Input text
            target_level: Target complexity level
            
        Returns:
            Simplified text
        """
        if not self.nlp:
            return text
        
        doc = self.nlp(text)
        simplified_sentences = []
        
        for sent in doc.sents:
            # Check sentence complexity
            if len(sent.text.split()) > 20:
                # Split long sentences
                simplified = self._split_complex_sentence(sent)
                simplified_sentences.extend(simplified)
            else:
                # Simplify vocabulary
                simplified = self._simplify_vocabulary(sent.text, target_level)
                simplified_sentences.append(simplified)
        
        return ' '.join(simplified_sentences)
    
    def _split_complex_sentence(self, sent) -> List[str]:
        """Split complex sentence into simpler ones."""
        # Find conjunctions and split
        conjunctions = ['and', 'but', 'however', 'although', 'while']
        text = sent.text
        
        for conj in conjunctions:
            if f' {conj} ' in text:
                parts = text.split(f' {conj} ', 1)
                if len(parts) == 2:
                    return [parts[0] + '.', parts[1]]
        
        return [text]
    
    def _simplify_vocabulary(self, text: str, target_level: TextComplexity) -> str:
        """Simplify vocabulary based on target level."""
        # In production, use a simplification model or dictionary
        # For now, return original text
        return text
    
    async def generate_summary(self,
                             text: str,
                             max_length: int = 150,
                             educational_focus: bool = True) -> str:
        """
        Generate educational summary of text.
        
        Args:
            text: Input text
            max_length: Maximum summary length in words
            educational_focus: Focus on educational concepts
            
        Returns:
            Summary text
        """
        if educational_focus:
            # Extract key concepts first
            concepts = await self.extract_concepts(text)
            
            # Find sentences containing concepts
            sentences = nltk.sent_tokenize(text)
            concept_sentences = []
            
            for sent in sentences:
                sent_lower = sent.lower()
                for concept in concepts:
                    if concept.lower() in sent_lower:
                        concept_sentences.append(sent)
                        break
            
            # Create summary from concept sentences
            if concept_sentences:
                summary = ' '.join(concept_sentences[:3])  # Top 3 sentences
                
                # Trim to max length
                words = summary.split()
                if len(words) > max_length:
                    summary = ' '.join(words[:max_length]) + '...'
                
                return summary
        
        # Fallback to simple extractive summary
        sentences = nltk.sent_tokenize(text)
        if sentences:
            return sentences[0]
        
        return text[:max_length]
    
    async def extract_learning_objectives(self, text: str) -> List[str]:
        """
        Extract or generate learning objectives from text.
        
        Args:
            text: Educational content
            
        Returns:
            List of learning objectives
        """
        objectives = []
        
        # Pattern matching for explicit objectives
        objective_patterns = [
            re.compile(r'(?:learning objectives?|objectives?|goals?|outcomes?)[:.]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
            re.compile(r'(?:you will|students will|learners will)\s+(?:be able to\s+)?(.+?)(?:\.|$)', re.IGNORECASE),
            re.compile(r'(?:by the end.*?you will|after.*?you will)\s+(?:be able to\s+)?(.+?)(?:\.|$)', re.IGNORECASE),
        ]
        
        for pattern in objective_patterns:
            for match in pattern.finditer(text):
                objective_text = match.group(1).strip()
                # Split if multiple objectives
                if ';' in objective_text:
                    objectives.extend([o.strip() for o in objective_text.split(';')])
                else:
                    objectives.append(objective_text)
        
        # Generate objectives from concepts if none found
        if not objectives:
            concepts = await self.extract_concepts(text)
            for concept in concepts[:5]:  # Top 5 concepts
                objectives.append(f"Understand the concept of {concept}")
        
        return objectives
    
    async def analyze_coherence(self, text: str) -> Dict[str, Any]:
        """
        Analyze text coherence for educational effectiveness.
        
        Args:
            text: Input text
            
        Returns:
            Coherence analysis
        """
        analysis = {
            'coherence_score': 0.0,
            'issues': [],
            'strengths': [],
            'suggestions': []
        }
        
        if not self.nlp:
            analysis['issues'].append("NLP model not available for coherence analysis")
            return analysis
        
        doc = self.nlp(text)
        sentences = list(doc.sents)
        
        if len(sentences) < 2:
            analysis['coherence_score'] = 1.0
            return analysis
        
        # Analyze transitions
        transition_words = {
            'sequential': ['first', 'second', 'then', 'next', 'finally'],
            'causal': ['because', 'therefore', 'thus', 'consequently'],
            'contrast': ['however', 'but', 'although', 'while'],
            'addition': ['furthermore', 'moreover', 'additionally', 'also']
        }
        
        transition_count = 0
        for sent in sentences:
            sent_text = sent.text.lower()
            for category, words in transition_words.items():
                if any(word in sent_text for word in words):
                    transition_count += 1
                    break
        
        transition_ratio = transition_count / len(sentences)
        
        # Analyze topic consistency
        topics = []
        for sent in sentences:
            # Extract main topic (simplified)
            nouns = [token.text for token in sent if token.pos_ == "NOUN"]
            if nouns:
                topics.append(nouns[0])
        
        # Check topic progression
        topic_consistency = len(set(topics)) / max(len(topics), 1)
        
        # Calculate coherence score
        analysis['coherence_score'] = (transition_ratio + (1 - topic_consistency)) / 2
        
        # Generate feedback
        if transition_ratio < 0.3:
            analysis['issues'].append("Low use of transition words")
            analysis['suggestions'].append("Add transition words to connect ideas")
        else:
            analysis['strengths'].append("Good use of transitions")
        
        if topic_consistency < 0.5:
            analysis['issues'].append("Topics change too frequently")
            analysis['suggestions'].append("Maintain focus on core concepts")
        else:
            analysis['strengths'].append("Consistent topic focus")
        
        return analysis
    
    async def extract_prerequisites(self, text: str) -> List[str]:
        """
        Extract prerequisite knowledge from educational text.
        
        Args:
            text: Educational content
            
        Returns:
            List of prerequisites
        """
        prerequisites = []
        
        # Pattern matching
        prereq_patterns = [
            re.compile(r'(?:prerequisites?|prior knowledge|before.*?you should know)[:.]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
            re.compile(r'(?:assumes?|requires?|you should know)(?:\s+knowledge of)?\s+(.+?)(?:\.|$)', re.IGNORECASE),
            re.compile(r'(?:familiar with|understanding of)\s+(.+?)(?:\.|$)', re.IGNORECASE),
        ]
        
        for pattern in prereq_patterns:
            for match in pattern.finditer(text):
                prereq_text = match.group(1).strip()
                # Split if multiple
                if ',' in prereq_text:
                    prerequisites.extend([p.strip() for p in prereq_text.split(',')])
                else:
                    prerequisites.append(prereq_text)
        
        # Extract from context
        if "basic" in text.lower() or "fundamental" in text.lower():
            # This might be foundational content
            prerequisites.append("No prior knowledge required")
        
        return prerequisites
    
    async def validate_educational_content(self, text: str) -> Dict[str, Any]:
        """
        Validate content for educational quality.
        
        Args:
            text: Educational content
            
        Returns:
            Validation results
        """
        validation = {
            'is_valid': True,
            'quality_score': 0.0,
            'issues': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Check length
        word_count = len(text.split())
        if word_count < 50:
            validation['issues'].append("Content too short for effective learning")
            validation['is_valid'] = False
        elif word_count < 100:
            validation['warnings'].append("Consider adding more detail")
        
        # Check for educational elements
        has_examples = bool(re.search(r'(?:for example|e\.g\.|example)', text, re.IGNORECASE))
        has_definitions = bool(self.definition_patterns[0].search(text))
        has_structure = bool(re.search(r'(?:first|second|step \d+)', text, re.IGNORECASE))
        
        quality_factors = []
        
        if has_examples:
            quality_factors.append(1.0)
        else:
            validation['suggestions'].append("Add examples to illustrate concepts")
            quality_factors.append(0.5)
        
        if has_definitions:
            quality_factors.append(1.0)
        else:
            validation['warnings'].append("Consider defining key terms")
            quality_factors.append(0.7)
        
        if has_structure:
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.8)
        
        # Complexity check
        complexity = await self.analyze_complexity(text)
        if complexity['complexity_level'] == TextComplexity.EXPERT:
            validation['warnings'].append("Content may be too complex for general audience")
            quality_factors.append(0.7)
        else:
            quality_factors.append(1.0)
        
        # Coherence check
        coherence = await self.analyze_coherence(text)
        quality_factors.append(coherence['coherence_score'])
        
        # Calculate overall quality
        validation['quality_score'] = np.mean(quality_factors) if quality_factors else 0.5
        
        if validation['quality_score'] < 0.6:
            validation['is_valid'] = False
            validation['issues'].append("Overall quality below acceptable threshold")
        
        return validation
    
    def clean_educational_text(self, text: str) -> str:
        """
        Clean text while preserving educational formatting.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace while preserving paragraphs
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Preserve list formatting
        text = re.sub(r'\n\s*[-*]\s+', '\n• ', text)
        
        # Fix common issues
        text = text.replace('..', '.')
        text = re.sub(r'([.!?])\1+', r'\1', text)
        
        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        return text.strip()
