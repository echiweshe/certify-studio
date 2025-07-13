"""
Concept Extractor Module for Domain Extraction Agent.

Identifies and extracts technical concepts, services, features, and principles
from processed documentation using NLP and pattern matching.
"""

import asyncio
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter, defaultdict
import numpy as np
from datetime import datetime

from loguru import logger
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import (
    Concept,
    ConceptType,
    DomainCategory,
    DocumentChunk,
    Document
)
from ....core.llm import MultiModalLLM
from ....config import settings


class ConceptExtractor:
    """Extract concepts from documentation."""
    
    def __init__(self):
        self.llm = MultiModalLLM()
        self._nlp = None
        self._tfidf_vectorizer = None
        
        # Pattern definitions for different concept types
        self.concept_patterns = {
            ConceptType.SERVICE: [
                re.compile(r'\b(?:AWS|Azure|GCP|Google Cloud)\s+([A-Z][a-zA-Z\s]+)', re.IGNORECASE),
                re.compile(r'\b([A-Z][a-zA-Z]+)\s+(?:Service|Platform|Solution)\b'),
                re.compile(r'\b(?:Amazon|Microsoft|Google)\s+([A-Z][a-zA-Z\s]+)\b')
            ],
            ConceptType.FEATURE: [
                re.compile(r'(?:feature|capability|functionality):\s*([^.]+)', re.IGNORECASE),
                re.compile(r'(?:supports?|provides?|enables?)\s+([^.]+)', re.IGNORECASE)
            ],
            ConceptType.PRINCIPLE: [
                re.compile(r'(?:principle|rule|guideline):\s*([^.]+)', re.IGNORECASE),
                re.compile(r'(?:should|must|always|never)\s+([^.]+)', re.IGNORECASE)
            ],
            ConceptType.BEST_PRACTICE: [
                re.compile(r'(?:best practice|recommendation):\s*([^.]+)', re.IGNORECASE),
                re.compile(r'(?:recommended to|advisable to)\s+([^.]+)', re.IGNORECASE)
            ]
        }
        
        # Domain category keywords
        self.domain_keywords = {
            DomainCategory.FUNDAMENTALS: ['basic', 'fundamental', 'introduction', 'overview', 'concept', 'principle'],
            DomainCategory.SERVICES: ['service', 'platform', 'solution', 'product', 'offering'],
            DomainCategory.SECURITY: ['security', 'encryption', 'authentication', 'authorization', 'compliance', 'privacy'],
            DomainCategory.ARCHITECTURE: ['architecture', 'design', 'pattern', 'structure', 'component', 'layer'],
            DomainCategory.BEST_PRACTICES: ['best practice', 'recommendation', 'guideline', 'standard', 'convention'],
            DomainCategory.TROUBLESHOOTING: ['troubleshoot', 'debug', 'error', 'issue', 'problem', 'solution'],
            DomainCategory.COST_OPTIMIZATION: ['cost', 'pricing', 'optimization', 'savings', 'budget', 'efficiency'],
            DomainCategory.PERFORMANCE: ['performance', 'speed', 'latency', 'throughput', 'scalability', 'optimization'],
            DomainCategory.GOVERNANCE: ['governance', 'compliance', 'policy', 'audit', 'control', 'regulation'],
            DomainCategory.MIGRATION: ['migration', 'transfer', 'move', 'transition', 'upgrade', 'modernization']
        }
        
    async def initialize(self):
        """Initialize NLP models."""
        try:
            # Load spaCy model
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except:
                logger.warning("spaCy model not found, using basic extraction")
                self._nlp = None
                
            # Initialize TF-IDF vectorizer
            self._tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 3)
            )
            
            logger.info("Concept extractor initialized")
            
        except Exception as e:
            logger.error(f"Error initializing concept extractor: {str(e)}")
            
    async def extract_concepts(
        self,
        documents: List[Document],
        chunks: List[DocumentChunk],
        min_frequency: int = 2
    ) -> List[Concept]:
        """Extract concepts from documents and chunks."""
        try:
            logger.info(f"Extracting concepts from {len(documents)} documents")
            
            # Extract concepts using multiple methods
            pattern_concepts = await self._extract_pattern_based_concepts(chunks)
            nlp_concepts = await self._extract_nlp_based_concepts(chunks) if self._nlp else []
            llm_concepts = await self._extract_llm_based_concepts(chunks)
            
            # Merge and deduplicate concepts
            all_concepts = self._merge_concepts(
                pattern_concepts + nlp_concepts + llm_concepts
            )
            
            # Filter by frequency
            filtered_concepts = self._filter_by_frequency(all_concepts, min_frequency)
            
            # Enrich concepts with additional information
            enriched_concepts = await self._enrich_concepts(filtered_concepts, chunks)
            
            # Calculate importance scores
            final_concepts = await self._calculate_importance_scores(enriched_concepts, chunks)
            
            logger.info(f"Extracted {len(final_concepts)} concepts")
            return final_concepts
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            raise
            
    async def _extract_pattern_based_concepts(
        self,
        chunks: List[DocumentChunk]
    ) -> List[Concept]:
        """Extract concepts using regex patterns."""
        concepts = []
        concept_occurrences = defaultdict(list)
        
        for chunk in chunks:
            content = chunk.content
            
            # Apply patterns for each concept type
            for concept_type, patterns in self.concept_patterns.items():
                for pattern in patterns:
                    matches = pattern.findall(content)
                    for match in matches:
                        # Clean up match
                        if isinstance(match, tuple):
                            match = match[0]
                        match = match.strip()
                        
                        if len(match) > 3 and len(match) < 100:
                            concept_occurrences[match.lower()].append({
                                'chunk_id': chunk.id,
                                'type': concept_type,
                                'original': match
                            })
                            
        # Create concepts from occurrences
        for concept_text, occurrences in concept_occurrences.items():
            if len(occurrences) >= 1:  # Will be filtered by frequency later
                # Determine most common type
                type_counts = Counter(occ['type'] for occ in occurrences)
                concept_type = type_counts.most_common(1)[0][0]
                
                # Use most common original form
                original_forms = Counter(occ['original'] for occ in occurrences)
                concept_name = original_forms.most_common(1)[0][0]
                
                # Determine category
                category = self._determine_category(concept_text)
                
                concept = Concept(
                    name=concept_name,
                    type=concept_type,
                    category=category,
                    description=f"Extracted from pattern matching",
                    source_chunks=[occ['chunk_id'] for occ in occurrences],
                    importance_score=0.5  # Default, will be updated
                )
                concepts.append(concept)
                
        return concepts
        
    async def _extract_nlp_based_concepts(
        self,
        chunks: List[DocumentChunk]
    ) -> List[Concept]:
        """Extract concepts using NLP techniques."""
        if not self._nlp:
            return []
            
        concepts = []
        entity_occurrences = defaultdict(list)
        
        for chunk in chunks:
            # Process with spaCy
            doc = self._nlp(chunk.content)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'TECH', 'LOC']:
                    entity_occurrences[ent.text.lower()].append({
                        'chunk_id': chunk.id,
                        'label': ent.label_,
                        'original': ent.text
                    })
                    
            # Extract noun phrases
            for chunk_text in doc.noun_chunks:
                text = chunk_text.text.strip()
                if len(text) > 5 and len(text.split()) <= 4:
                    # Check if it contains technical terms
                    if any(token.pos_ in ['PROPN', 'NOUN'] for token in chunk_text):
                        entity_occurrences[text.lower()].append({
                            'chunk_id': chunk.id,
                            'label': 'NOUN_PHRASE',
                            'original': text
                        })
                        
        # Create concepts from entities
        for entity_text, occurrences in entity_occurrences.items():
            if len(occurrences) >= 1:
                # Determine concept type based on label
                labels = [occ['label'] for occ in occurrences]
                if 'PRODUCT' in labels or 'TECH' in labels:
                    concept_type = ConceptType.SERVICE
                elif 'ORG' in labels:
                    concept_type = ConceptType.SERVICE
                else:
                    concept_type = ConceptType.CONCEPT
                    
                # Use most common original form
                original_forms = Counter(occ['original'] for occ in occurrences)
                concept_name = original_forms.most_common(1)[0][0]
                
                category = self._determine_category(entity_text)
                
                concept = Concept(
                    name=concept_name,
                    type=concept_type,
                    category=category,
                    description=f"Extracted using NLP",
                    source_chunks=[occ['chunk_id'] for occ in occurrences],
                    importance_score=0.5
                )
                concepts.append(concept)
                
        return concepts
        
    async def _extract_llm_based_concepts(
        self,
        chunks: List[DocumentChunk],
        sample_size: int = 10
    ) -> List[Concept]:
        """Extract concepts using LLM analysis."""
        concepts = []
        
        # Sample chunks for LLM analysis (to manage costs)
        sample_chunks = chunks[:sample_size] if len(chunks) > sample_size else chunks
        
        for chunk in sample_chunks:
            prompt = f"""
            Extract key technical concepts from this documentation excerpt.
            Focus on:
            - Services and platforms
            - Features and capabilities
            - Principles and best practices
            - Technical terms and acronyms
            
            Text:
            {chunk.content[:1000]}  # Limit context size
            
            Return as JSON list with format:
            [
                {{
                    "name": "concept name",
                    "type": "service|feature|principle|concept",
                    "description": "brief description",
                    "category": "fundamentals|services|security|architecture|etc"
                }}
            ]
            """
            
            try:
                response = await self.llm.generate(prompt)
                extracted = self._parse_llm_response(response)
                
                for item in extracted:
                    concept = Concept(
                        name=item['name'],
                        type=ConceptType(item.get('type', 'concept')),
                        category=DomainCategory(item.get('category', 'fundamentals')),
                        description=item.get('description', ''),
                        source_chunks=[chunk.id],
                        importance_score=0.6  # Higher for LLM-extracted
                    )
                    concepts.append(concept)
                    
            except Exception as e:
                logger.warning(f"Error in LLM concept extraction: {str(e)}")
                continue
                
        return concepts
        
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract concepts."""
        try:
            # Try to parse as JSON
            import json
            
            # Find JSON array in response
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return []
                
        except:
            # Fallback to text parsing
            concepts = []
            lines = response.split('\n')
            
            for line in lines:
                if '-' in line or '•' in line:
                    # Extract concept name
                    parts = re.split(r'[-•:]', line, 1)
                    if len(parts) >= 2:
                        name = parts[1].strip()
                        if name:
                            concepts.append({
                                'name': name,
                                'type': 'concept',
                                'description': '',
                                'category': 'fundamentals'
                            })
                            
            return concepts
            
    def _merge_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Merge similar concepts."""
        merged = {}
        
        for concept in concepts:
            # Normalize name for comparison
            normalized = concept.name.lower().strip()
            
            if normalized in merged:
                # Merge with existing concept
                existing = merged[normalized]
                existing.source_chunks.extend(concept.source_chunks)
                existing.aliases.extend([concept.name] if concept.name != existing.name else [])
                
                # Update type if more specific
                if concept.type != ConceptType.CONCEPT and existing.type == ConceptType.CONCEPT:
                    existing.type = concept.type
                    
                # Merge descriptions
                if concept.description and concept.description != existing.description:
                    existing.description += f" {concept.description}"
                    
            else:
                merged[normalized] = concept
                
        # Deduplicate source chunks and aliases
        for concept in merged.values():
            concept.source_chunks = list(set(concept.source_chunks))
            concept.aliases = list(set(concept.aliases))
            
        return list(merged.values())
        
    def _filter_by_frequency(
        self,
        concepts: List[Concept],
        min_frequency: int
    ) -> List[Concept]:
        """Filter concepts by occurrence frequency."""
        return [c for c in concepts if len(c.source_chunks) >= min_frequency]
        
    async def _enrich_concepts(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk]
    ) -> List[Concept]:
        """Enrich concepts with additional information."""
        # Create chunk lookup
        chunk_lookup = {chunk.id: chunk for chunk in chunks}
        
        for concept in concepts:
            # Extract examples from chunks
            examples = []
            for chunk_id in concept.source_chunks[:3]:  # First 3 occurrences
                if chunk_id in chunk_lookup:
                    chunk = chunk_lookup[chunk_id]
                    # Find sentence containing concept
                    sentences = chunk.content.split('.')
                    for sent in sentences:
                        if concept.name.lower() in sent.lower():
                            examples.append(sent.strip() + '.')
                            break
                            
            concept.examples = examples[:2]  # Max 2 examples
            
            # Generate better description if needed
            if not concept.description or concept.description == "Extracted from pattern matching":
                concept.description = await self._generate_concept_description(
                    concept.name,
                    concept.type,
                    examples
                )
                
        return concepts
        
    async def _generate_concept_description(
        self,
        name: str,
        concept_type: ConceptType,
        examples: List[str]
    ) -> str:
        """Generate description for concept using context."""
        if not examples:
            return f"A {concept_type.value} in the domain"
            
        context = " ".join(examples[:2])
        
        prompt = f"""
        Generate a brief description for the {concept_type.value} "{name}" based on this context:
        {context}
        
        Description (one sentence):
        """
        
        try:
            response = await self.llm.generate(prompt)
            return response.strip()
        except:
            return f"A {concept_type.value} mentioned in the documentation"
            
    async def _calculate_importance_scores(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk]
    ) -> List[Concept]:
        """Calculate importance scores for concepts."""
        if not concepts:
            return concepts
            
        # Calculate TF-IDF scores
        all_text = [chunk.content for chunk in chunks]
        
        try:
            # Fit TF-IDF on all chunks
            tfidf_matrix = self._tfidf_vectorizer.fit_transform(all_text)
            
            # Get feature names
            feature_names = self._tfidf_vectorizer.get_feature_names_out()
            
            # Calculate importance for each concept
            for concept in concepts:
                # Find concept in feature names
                concept_lower = concept.name.lower()
                
                # Calculate frequency-based score
                frequency_score = len(concept.source_chunks) / len(chunks)
                
                # Calculate TF-IDF based score
                tfidf_score = 0
                for i, feature in enumerate(feature_names):
                    if concept_lower in feature or feature in concept_lower:
                        # Average TF-IDF score across all documents
                        tfidf_score = max(tfidf_score, tfidf_matrix[:, i].mean())
                        
                # Calculate position-based score (concepts appearing early are often more important)
                position_score = 1.0 - (min(int(c.split('_')[0]) for c in concept.source_chunks if '_' in c) / len(chunks))
                
                # Combine scores
                concept.importance_score = (
                    frequency_score * 0.3 +
                    tfidf_score * 0.4 +
                    position_score * 0.3
                )
                
                # Boost certain types
                if concept.type == ConceptType.SERVICE:
                    concept.importance_score *= 1.2
                elif concept.type == ConceptType.PRINCIPLE:
                    concept.importance_score *= 1.1
                    
                # Clamp to [0, 1]
                concept.importance_score = min(1.0, max(0.0, concept.importance_score))
                
        except Exception as e:
            logger.warning(f"Error calculating TF-IDF scores: {str(e)}")
            # Fall back to frequency-based scoring
            max_frequency = max(len(c.source_chunks) for c in concepts)
            for concept in concepts:
                concept.importance_score = len(concept.source_chunks) / max_frequency
                
        return concepts
        
    def _determine_category(self, text: str) -> DomainCategory:
        """Determine domain category for concept."""
        text_lower = text.lower()
        
        # Check each category's keywords
        category_scores = {}
        for category, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            category_scores[category] = score
            
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
                
        # Default to fundamentals
        return DomainCategory.FUNDAMENTALS
        
    async def identify_prerequisites(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk]
    ) -> None:
        """Identify prerequisite relationships between concepts."""
        # Create concept lookup
        concept_lookup = {c.name.lower(): c for c in concepts}
        
        # Look for prerequisite patterns in chunks
        prerequisite_patterns = [
            re.compile(r'(?:before|prior to|prerequisite).*?([A-Z][a-zA-Z\s]+)', re.IGNORECASE),
            re.compile(r'([A-Z][a-zA-Z\s]+).*?(?:required for|needed for)', re.IGNORECASE),
            re.compile(r'(?:understand|know|learn).*?([A-Z][a-zA-Z\s]+).*?first', re.IGNORECASE)
        ]
        
        for chunk in chunks:
            for pattern in prerequisite_patterns:
                matches = pattern.findall(chunk.content)
                for match in matches:
                    match_lower = match.strip().lower()
                    if match_lower in concept_lookup:
                        # Find what this is a prerequisite for
                        # This is simplified - could be enhanced
                        for concept in concepts:
                            if concept.name.lower() in chunk.content.lower():
                                if match_lower != concept.name.lower():
                                    concept.prerequisites.append(concept_lookup[match_lower].id)
                                    
        # Deduplicate prerequisites
        for concept in concepts:
            concept.prerequisites = list(set(concept.prerequisites))
