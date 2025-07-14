"""
Weight Calculator Module for Domain Extraction Agent.

Calculates domain weights and exam coverage based on concept frequency,
relationships, and explicit weight indicators in certification guides.
"""

import asyncio
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
import numpy as np

from loguru import logger

from .models import (
    Concept,
    Relationship,
    DomainCategory,
    Document,
    DocumentChunk,
    DomainKnowledge
)
from ....core.llm import MultimodalLLM


class WeightCalculator:
    """Calculate domain weights for certification content."""
    
    def __init__(self):
        self.llm = MultimodalLLM()
        
        # Weight indicator patterns
        self.weight_patterns = [
            # Percentage patterns
            (r'(\d+)%\s*of\s*(?:the\s*)?(?:exam|test|assessment)', 'percentage'),
            (r'accounts?\s*for\s*(\d+)%', 'percentage'),
            (r'worth\s*(\d+)%', 'percentage'),
            (r'(\d+)%\s*weight', 'percentage'),
            
            # Importance indicators
            (r'(?:very\s*)?important|critical|essential|key|crucial', 'high_importance'),
            (r'moderate(?:ly)?\s*important|significant', 'medium_importance'),
            (r'less\s*important|minor|optional', 'low_importance'),
            
            # Question count patterns
            (r'(\d+)\s*questions?\s*(?:on|about|covering)', 'question_count'),
            (r'expect\s*(\d+)\s*questions?', 'question_count'),
            
            # Time allocation patterns
            (r'(\d+)\s*(?:hours?|minutes?)\s*(?:of\s*)?study', 'time_allocation'),
            (r'spend\s*(\d+)\s*(?:hours?|minutes?)', 'time_allocation')
        ]
        
        # Default weights if not specified
        self.default_weights = {
            DomainCategory.FUNDAMENTALS: 0.15,
            DomainCategory.SERVICES: 0.25,
            DomainCategory.SECURITY: 0.20,
            DomainCategory.ARCHITECTURE: 0.15,
            DomainCategory.BEST_PRACTICES: 0.10,
            DomainCategory.TROUBLESHOOTING: 0.05,
            DomainCategory.COST_OPTIMIZATION: 0.05,
            DomainCategory.PERFORMANCE: 0.03,
            DomainCategory.GOVERNANCE: 0.01,
            DomainCategory.MIGRATION: 0.01
        }
        
    async def calculate_weights(
        self,
        concepts: List[Concept],
        relationships: List[Relationship],
        documents: List[Document],
        chunks: List[DocumentChunk]
    ) -> Dict[DomainCategory, float]:
        """Calculate weights for each domain category."""
        try:
            logger.info("Calculating domain weights")
            
            # Extract explicit weights from documents
            explicit_weights = await self._extract_explicit_weights(documents, chunks)
            
            # Calculate implicit weights from concept distribution
            implicit_weights = self._calculate_implicit_weights(concepts, relationships)
            
            # Analyze emphasis in content
            emphasis_weights = await self._analyze_content_emphasis(chunks)
            
            # Combine weights
            final_weights = self._combine_weights(
                explicit_weights,
                implicit_weights,
                emphasis_weights
            )
            
            # Normalize weights to sum to 1.0
            normalized_weights = self._normalize_weights(final_weights)
            
            logger.info(f"Calculated weights for {len(normalized_weights)} domains")
            return normalized_weights
            
        except Exception as e:
            logger.error(f"Error calculating weights: {str(e)}")
            return self.default_weights
            
    async def _extract_explicit_weights(
        self,
        documents: List[Document],
        chunks: List[DocumentChunk]
    ) -> Dict[DomainCategory, float]:
        """Extract explicitly stated weights from documents."""
        weights = {}
        
        # Look for weight tables or sections
        weight_sections = await self._find_weight_sections(documents, chunks)
        
        for section in weight_sections:
            # Apply weight patterns
            for pattern, pattern_type in self.weight_patterns:
                matches = re.finditer(pattern, section, re.IGNORECASE)
                
                for match in matches:
                    # Extract context around match
                    start = max(0, match.start() - 100)
                    end = min(len(section), match.end() + 100)
                    context = section[start:end]
                    
                    # Determine which domain this refers to
                    domain = self._identify_domain_from_context(context)
                    
                    if domain and pattern_type == 'percentage':
                        try:
                            percentage = float(match.group(1))
                            weights[domain] = percentage / 100.0
                        except:
                            pass
                            
        # Use LLM to extract weights if pattern matching fails
        if not weights:
            weights = await self._extract_weights_with_llm(weight_sections)
            
        return weights
        
    async def _find_weight_sections(
        self,
        documents: List[Document],
        chunks: List[DocumentChunk]
    ) -> List[str]:
        """Find sections that likely contain weight information."""
        weight_sections = []
        
        # Keywords that indicate weight information
        weight_keywords = [
            'weight', 'percentage', 'distribution', 'breakdown',
            'exam topics', 'exam domains', 'exam objectives',
            'scoring', 'allocation', 'coverage'
        ]
        
        # Check document sections
        for doc in documents:
            for section in doc.sections:
                section_lower = section['content'].lower()
                if any(keyword in section_lower for keyword in weight_keywords):
                    weight_sections.append(section['content'])
                    
        # Check chunks if no sections found
        if not weight_sections:
            for chunk in chunks[:20]:  # Check first 20 chunks
                chunk_lower = chunk.content.lower()
                if any(keyword in chunk_lower for keyword in weight_keywords):
                    weight_sections.append(chunk.content)
                    
        return weight_sections
        
    def _identify_domain_from_context(self, context: str) -> Optional[DomainCategory]:
        """Identify which domain category the context refers to."""
        context_lower = context.lower()
        
        # Map keywords to domains
        domain_mappings = {
            DomainCategory.FUNDAMENTALS: ['fundamental', 'basic', 'introduction', 'overview', 'concept'],
            DomainCategory.SERVICES: ['service', 'product', 'platform', 'solution', 'offering'],
            DomainCategory.SECURITY: ['security', 'encryption', 'authentication', 'compliance', 'iam'],
            DomainCategory.ARCHITECTURE: ['architecture', 'design', 'pattern', 'structure', 'blueprint'],
            DomainCategory.BEST_PRACTICES: ['best practice', 'recommendation', 'guideline', 'standard'],
            DomainCategory.TROUBLESHOOTING: ['troubleshoot', 'debug', 'error', 'issue', 'problem'],
            DomainCategory.COST_OPTIMIZATION: ['cost', 'pricing', 'optimization', 'savings', 'budget'],
            DomainCategory.PERFORMANCE: ['performance', 'speed', 'latency', 'throughput', 'scale'],
            DomainCategory.GOVERNANCE: ['governance', 'compliance', 'policy', 'audit', 'control'],
            DomainCategory.MIGRATION: ['migration', 'transfer', 'move', 'transition', 'modernization']
        }
        
        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in domain_mappings.items():
            score = sum(1 for keyword in keywords if keyword in context_lower)
            if score > 0:
                domain_scores[domain] = score
                
        # Return domain with highest score
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
            
        return None
        
    async def _extract_weights_with_llm(self, sections: List[str]) -> Dict[DomainCategory, float]:
        """Use LLM to extract weights from text."""
        if not sections:
            return {}
            
        combined_text = "\n\n".join(sections[:3])  # Limit to first 3 sections
        
        prompt = f"""
        Extract the exam domain weights from this certification guide text.
        Look for percentages, weights, or importance indicators for different domains.
        
        Text:
        {combined_text[:2000]}  # Limit context
        
        Return as JSON with domain categories and their weights (0.0 to 1.0):
        {{
            "fundamentals": 0.0,
            "services": 0.0,
            "security": 0.0,
            "architecture": 0.0,
            "best_practices": 0.0,
            "troubleshooting": 0.0,
            "cost_optimization": 0.0,
            "performance": 0.0,
            "governance": 0.0,
            "migration": 0.0
        }}
        """
        
        try:
            response = await self.llm.generate(prompt)
            
            # Parse JSON response
            import json
            weights_dict = json.loads(response)
            
            # Convert to DomainCategory enum
            weights = {}
            for domain_str, weight in weights_dict.items():
                try:
                    domain = DomainCategory(domain_str)
                    weights[domain] = float(weight)
                except:
                    pass
                    
            return weights
            
        except Exception as e:
            logger.warning(f"Error extracting weights with LLM: {str(e)}")
            return {}
            
    def _calculate_implicit_weights(
        self,
        concepts: List[Concept],
        relationships: List[Relationship]
    ) -> Dict[DomainCategory, float]:
        """Calculate weights based on concept distribution and relationships."""
        # Count concepts per category
        category_counts = Counter(concept.category for concept in concepts)
        
        # Weight by importance scores
        category_importance = defaultdict(float)
        for concept in concepts:
            category_importance[concept.category] += concept.importance_score
            
        # Consider relationship density
        category_relationships = defaultdict(int)
        for rel in relationships:
            # Find concepts for this relationship
            source_concept = next((c for c in concepts if c.id == rel.source_concept_id), None)
            target_concept = next((c for c in concepts if c.id == rel.target_concept_id), None)
            
            if source_concept:
                category_relationships[source_concept.category] += 1
            if target_concept:
                category_relationships[target_concept.category] += 1
                
        # Calculate weights
        weights = {}
        total_concepts = len(concepts)
        
        for category in DomainCategory:
            count_weight = category_counts.get(category, 0) / total_concepts if total_concepts > 0 else 0
            importance_weight = category_importance.get(category, 0) / len(concepts) if concepts else 0
            relationship_weight = category_relationships.get(category, 0) / (len(relationships) * 2) if relationships else 0
            
            # Combined weight
            weights[category] = (
                count_weight * 0.4 +
                importance_weight * 0.4 +
                relationship_weight * 0.2
            )
            
        return weights
        
    async def _analyze_content_emphasis(
        self,
        chunks: List[DocumentChunk]
    ) -> Dict[DomainCategory, float]:
        """Analyze emphasis given to different domains in content."""
        emphasis_scores = defaultdict(float)
        
        # Analyze chunk distribution
        for chunk in chunks:
            # Determine primary domain for chunk
            chunk_domain = self._identify_chunk_domain(chunk)
            if chunk_domain:
                # Weight by chunk position (earlier chunks often more important)
                position_weight = 1.0 - (chunk.chunk_index / chunk.total_chunks)
                emphasis_scores[chunk_domain] += position_weight
                
        # Normalize scores
        total_score = sum(emphasis_scores.values())
        if total_score > 0:
            weights = {
                domain: score / total_score
                for domain, score in emphasis_scores.items()
            }
        else:
            weights = {}
            
        return weights
        
    def _identify_chunk_domain(self, chunk: DocumentChunk) -> Optional[DomainCategory]:
        """Identify the primary domain category for a chunk."""
        # Use concepts extracted from chunk
        if chunk.concepts:
            # This is simplified - in production, you'd look up actual concept objects
            # and determine their categories
            return self._identify_domain_from_context(chunk.content)
            
        return None
        
    def _combine_weights(
        self,
        explicit_weights: Dict[DomainCategory, float],
        implicit_weights: Dict[DomainCategory, float],
        emphasis_weights: Dict[DomainCategory, float]
    ) -> Dict[DomainCategory, float]:
        """Combine different weight sources."""
        combined = {}
        
        # If we have explicit weights, they take precedence
        if explicit_weights:
            # Start with explicit weights
            combined = explicit_weights.copy()
            
            # Fill in missing domains with implicit weights
            for domain in DomainCategory:
                if domain not in combined:
                    # Average of implicit and emphasis
                    implicit = implicit_weights.get(domain, 0)
                    emphasis = emphasis_weights.get(domain, 0)
                    combined[domain] = (implicit + emphasis) / 2
                    
        else:
            # No explicit weights, combine implicit and emphasis
            for domain in DomainCategory:
                implicit = implicit_weights.get(domain, 0)
                emphasis = emphasis_weights.get(domain, 0)
                default = self.default_weights.get(domain, 0)
                
                # Weighted average
                combined[domain] = (
                    implicit * 0.4 +
                    emphasis * 0.3 +
                    default * 0.3
                )
                
        return combined
        
    def _normalize_weights(self, weights: Dict[DomainCategory, float]) -> Dict[DomainCategory, float]:
        """Normalize weights to sum to 1.0."""
        total = sum(weights.values())
        
        if total > 0:
            normalized = {
                domain: weight / total
                for domain, weight in weights.items()
            }
        else:
            # Use defaults if no weights
            normalized = self.default_weights.copy()
            
        # Ensure all domains have a weight
        for domain in DomainCategory:
            if domain not in normalized:
                normalized[domain] = 0.0
                
        return normalized
        
    async def calculate_exam_coverage(
        self,
        concepts: List[Concept],
        exam_objectives: List[str]
    ) -> Dict[str, float]:
        """Calculate how well extracted concepts cover exam objectives."""
        coverage = {}
        
        for objective in exam_objectives:
            # Find concepts related to this objective
            related_concepts = []
            objective_lower = objective.lower()
            
            for concept in concepts:
                concept_text = f"{concept.name} {concept.description}".lower()
                
                # Simple matching - could be enhanced with semantic similarity
                if any(word in concept_text for word in objective_lower.split()):
                    related_concepts.append(concept)
                    
            # Calculate coverage score
            if related_concepts:
                # Consider both quantity and quality (importance scores)
                coverage_score = sum(c.importance_score for c in related_concepts) / len(related_concepts)
            else:
                coverage_score = 0.0
                
            coverage[objective] = coverage_score
            
        return coverage
