"""
Reasoning Engine for Autonomous Agents

This module implements various reasoning capabilities including:
- Logical reasoning with inference rules
- Causal reasoning with probabilistic models
- Analogical reasoning for knowledge transfer
- Pedagogical reasoning for educational content
"""

from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import networkx as nx
import numpy as np
from enum import Enum
import json
from loguru import logger

from certify_studio.core.llm import MultimodalLLM


class ReasoningType(Enum):
    """Types of reasoning the engine supports."""
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"
    PROBABILISTIC = "probabilistic"
    FUZZY = "fuzzy"


@dataclass
class Concept:
    """Represents a concept in the knowledge graph."""
    id: str
    name: str
    domain: str
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Tuple[str, str]] = field(default_factory=list)  # (relation_type, target_id)
    embedding: Optional[np.ndarray] = None
    confidence: float = 1.0
    
    def add_relationship(self, relation_type: str, target_id: str):
        """Add a relationship to another concept."""
        self.relationships.append((relation_type, target_id))
    
    def get_relationships_by_type(self, relation_type: str) -> List[str]:
        """Get all relationships of a specific type."""
        return [target for rel_type, target in self.relationships if rel_type == relation_type]


@dataclass
class InferenceRule:
    """Represents a logical inference rule."""
    id: str
    name: str
    conditions: List[Dict[str, Any]]  # List of conditions that must be met
    conclusions: List[Dict[str, Any]]  # List of conclusions to draw
    confidence: float = 1.0
    domain: Optional[str] = None
    
    def applies_to(self, facts: Dict[str, Any]) -> bool:
        """Check if this rule applies given current facts."""
        for condition in self.conditions:
            if not self._check_condition(condition, facts):
                return False
        return True
    
    def _check_condition(self, condition: Dict[str, Any], facts: Dict[str, Any]) -> bool:
        """Check if a single condition is met."""
        cond_type = condition.get("type")
        
        if cond_type == "exists":
            return condition["fact"] in facts
        elif cond_type == "equals":
            return facts.get(condition["fact"]) == condition["value"]
        elif cond_type == "greater_than":
            return facts.get(condition["fact"], 0) > condition["value"]
        elif cond_type == "contains":
            return condition["value"] in facts.get(condition["fact"], [])
        else:
            return False


@dataclass
class CausalModel:
    """Represents a causal model for reasoning about cause-effect relationships."""
    id: str
    name: str
    variables: Dict[str, Dict[str, Any]]  # Variable definitions
    causal_graph: nx.DiGraph
    probability_tables: Dict[str, np.ndarray]  # Conditional probability tables
    
    def predict_effect(self, intervention: Dict[str, Any]) -> Dict[str, float]:
        """Predict the effect of an intervention."""
        # Simplified causal inference
        effects = {}
        
        for var, value in intervention.items():
            if var in self.causal_graph:
                # Get downstream variables
                descendants = nx.descendants(self.causal_graph, var)
                
                for desc in descendants:
                    # Calculate effect probability (simplified)
                    path_length = nx.shortest_path_length(self.causal_graph, var, desc)
                    effect_prob = 0.8 ** path_length  # Decay with distance
                    effects[desc] = effect_prob
        
        return effects


class ReasoningEngine:
    """Main reasoning engine that combines multiple reasoning approaches."""
    
    def __init__(self, llm: Optional[MultimodalLLM] = None):
        self.knowledge_graph = nx.DiGraph()
        self.concepts: Dict[str, Concept] = {}
        self.inference_rules: List[InferenceRule] = []
        self.causal_models: Dict[str, CausalModel] = {}
        self.llm = llm
        self.reasoning_history: List[Dict[str, Any]] = []
        
        # Initialize with basic inference rules
        self._initialize_basic_rules()
        
        logger.info("Initialized ReasoningEngine")
    
    def _initialize_basic_rules(self):
        """Initialize basic logical inference rules."""
        # Modus Ponens: If P then Q; P; therefore Q
        self.add_inference_rule(InferenceRule(
            id="modus_ponens",
            name="Modus Ponens",
            conditions=[
                {"type": "exists", "fact": "if_then_rule"},
                {"type": "exists", "fact": "antecedent_true"}
            ],
            conclusions=[
                {"type": "assert", "fact": "consequent_true"}
            ],
            confidence=1.0
        ))
        
        # Transitivity: If A relates to B and B relates to C, then A relates to C
        self.add_inference_rule(InferenceRule(
            id="transitivity",
            name="Transitivity",
            conditions=[
                {"type": "exists", "fact": "relation_a_b"},
                {"type": "exists", "fact": "relation_b_c"}
            ],
            conclusions=[
                {"type": "assert", "fact": "relation_a_c"}
            ],
            confidence=0.9
        ))
    
    async def reason_about_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Apply multiple reasoning approaches to understand content."""
        logger.debug(f"Reasoning about content: {content.get('type', 'unknown')}")
        
        # Extract concepts and build local knowledge graph
        concepts = await self._extract_concepts_from_content(content)
        local_graph = await self._build_local_knowledge_graph(concepts)
        
        # Apply different reasoning types
        deductive_results = await self._deductive_reasoning(local_graph)
        inductive_results = await self._inductive_reasoning(concepts)
        causal_results = await self._causal_reasoning(content)
        
        # Analyze pedagogical implications
        pedagogical_analysis = await self._analyze_pedagogical_implications(
            concepts, deductive_results, inductive_results
        )
        
        # Generate recommendations
        recommendations = await self._generate_content_recommendations(
            pedagogical_analysis, content
        )
        
        result = {
            "concepts": [c.__dict__ for c in concepts],
            "reasoning": {
                "deductive": deductive_results,
                "inductive": inductive_results,
                "causal": causal_results
            },
            "pedagogical_analysis": pedagogical_analysis,
            "recommendations": recommendations
        }
        
        # Add to reasoning history
        self.reasoning_history.append({
            "timestamp": datetime.now().isoformat(),
            "content_type": content.get("type"),
            "result": result
        })
        
        return result
    
    def _estimate_cognitive_load(self, concepts: List[Concept], complexity_scores: Dict[str, float]) -> float:
        """Estimate cognitive load for learning the concepts."""
        if not concepts:
            return 0.0
        
        # Factors: number of concepts, average complexity, interconnectedness
        num_concepts = len(concepts)
        avg_complexity = np.mean(list(complexity_scores.values())) if complexity_scores else 0
        
        # Calculate interconnectedness
        total_relationships = sum(len(c.relationships) for c in concepts)
        avg_relationships = total_relationships / num_concepts if num_concepts > 0 else 0
        
        # Normalize and combine
        load = (min(num_concepts / 10, 1.0) * 0.3 +  # More concepts = higher load
                min(avg_complexity / 20, 1.0) * 0.4 +  # Higher complexity = higher load
                min(avg_relationships / 5, 1.0) * 0.3)  # More connections = higher load
        
        return min(1.0, load)
    
    def _extract_graph_patterns(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Extract structural patterns from a graph."""
        patterns = []
        
        # Find triangles (3-node cycles)
        triangles = [list(clique) for clique in nx.enumerate_all_cliques(graph.to_undirected()) if len(clique) == 3]
        if triangles:
            patterns.append({
                "type": "triangle",
                "count": len(triangles),
                "nodes": triangles
            })
        
        # Find star patterns (one central node with multiple connections)
        for node in graph.nodes():
            degree = graph.degree(node)
            if degree >= 3:
                patterns.append({
                    "type": "star",
                    "center": node,
                    "degree": degree,
                    "connected_nodes": list(graph.neighbors(node))
                })
        
        # Find chains (linear sequences)
        paths = []
        for source in graph.nodes():
            for target in graph.nodes():
                if source != target:
                    try:
                        path = nx.shortest_path(graph, source, target)
                        if len(path) >= 3:
                            paths.append(path)
                    except nx.NetworkXNoPath:
                        pass
        
        if paths:
            patterns.append({
                "type": "chain",
                "count": len(paths),
                "max_length": max(len(p) for p in paths),
                "paths": paths[:5]  # Limit to prevent too much data
            })
        
        return patterns
    
    def _calculate_pattern_similarity(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> float:
        """Calculate similarity between two patterns."""
        if pattern1["type"] != pattern2["type"]:
            return 0.0
        
        similarity = 0.5  # Base similarity for same type
        
        if pattern1["type"] == "triangle":
            # Compare triangle counts
            count_ratio = min(pattern1["count"], pattern2["count"]) / max(pattern1["count"], pattern2["count"])
            similarity += 0.5 * count_ratio
        
        elif pattern1["type"] == "star":
            # Compare degrees
            degree_ratio = min(pattern1["degree"], pattern2["degree"]) / max(pattern1["degree"], pattern2["degree"])
            similarity += 0.5 * degree_ratio
        
        elif pattern1["type"] == "chain":
            # Compare chain lengths
            length_ratio = min(pattern1["max_length"], pattern2["max_length"]) / max(pattern1["max_length"], pattern2["max_length"])
            similarity += 0.5 * length_ratio
        
        return similarity
    
    def _generate_mapping_hint(self, source_pattern: Dict[str, Any], target_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hints for mapping concepts between patterns."""
        hint = {
            "pattern_type": source_pattern["type"],
            "confidence": self._calculate_pattern_similarity(source_pattern, target_pattern)
        }
        
        if source_pattern["type"] == "star":
            # Map central nodes
            hint["concept_pairs"] = [(source_pattern["center"], target_pattern["center"])]
        
        return hint
    
    def _create_embedding_based_mappings(self, source_concepts: List[Concept], target_concepts: List[Concept]) -> Dict[str, str]:
        """Create mappings based on embedding similarity."""
        mappings = {}
        
        for s_concept in source_concepts:
            if s_concept.embedding is not None:
                best_match = None
                best_similarity = -1
                
                for t_concept in target_concepts:
                    if t_concept.embedding is not None:
                        # Cosine similarity
                        similarity = np.dot(s_concept.embedding, t_concept.embedding) / (
                            np.linalg.norm(s_concept.embedding) * np.linalg.norm(t_concept.embedding)
                        )
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = t_concept
                
                if best_match and best_similarity > 0.7:
                    mappings[s_concept.id] = best_match.id
        
        return mappings
    
    def _find_best_name_match(self, source_concept: Concept, target_concepts: List[Concept]) -> Optional[Concept]:
        """Find best matching concept based on name similarity."""
        best_match = None
        best_score = 0
        
        source_tokens = set(source_concept.name.lower().split())
        
        for t_concept in target_concepts:
            target_tokens = set(t_concept.name.lower().split())
            
            # Jaccard similarity
            intersection = len(source_tokens & target_tokens)
            union = len(source_tokens | target_tokens)
            
            if union > 0:
                score = intersection / union
                
                if score > best_score:
                    best_score = score
                    best_match = t_concept
        
        return best_match if best_score > 0.3 else None
    
    def _get_domain_patterns(self, domain: str) -> List[Dict[str, Any]]:
        """Get successful patterns from a domain."""
        # Look through reasoning history for patterns
        patterns = []
        
        for entry in self.reasoning_history:
            if entry.get("domain") == domain:
                reasoning_result = entry.get("result", {})
                if "patterns" in reasoning_result:
                    patterns.extend(reasoning_result["patterns"])
        
        return patterns
    
    def _translate_pattern(self, pattern: Dict[str, Any], mappings: Dict[str, str], target_domain: str) -> Optional[Dict[str, Any]]:
        """Translate a pattern to target domain using mappings."""
        translated = pattern.copy()
        translated["domain"] = target_domain
        
        # Translate concept references
        if "concepts" in pattern:
            translated_concepts = []
            for concept_id in pattern["concepts"]:
                if concept_id in mappings:
                    translated_concepts.append(mappings[concept_id])
            
            if translated_concepts:
                translated["concepts"] = translated_concepts
            else:
                return None  # Cannot translate without concept mappings
        
        return translated
    
    def _generate_adaptation_notes(self, original: Dict[str, Any], translated: Dict[str, Any]) -> List[str]:
        """Generate notes about how pattern was adapted."""
        notes = []
        
        if original["domain"] != translated["domain"]:
            notes.append(f"Adapted from {original['domain']} to {translated['domain']} domain")
        
        if "concepts" in original and "concepts" in translated:
            orig_count = len(original["concepts"])
            trans_count = len(translated["concepts"])
            if orig_count != trans_count:
                notes.append(f"Concept count changed from {orig_count} to {trans_count}")
        
        return notes
    
    async def _assess_likelihood_with_llm(self, evidence: str, hypothesis: str) -> float:
        """Use LLM to assess likelihood of evidence given hypothesis."""
        if not self.llm:
            return 0.5
        
        prompt = f"""
        Assess the likelihood that the following evidence would be observed if the hypothesis is true.
        
        Hypothesis: {hypothesis}
        Evidence: {evidence}
        
        Provide a probability between 0 and 1.
        """
        
        try:
            response = await self.llm.generate(prompt)
            # Extract probability from response
            import re
            numbers = re.findall(r'0?\.\d+|1\.0|0|1', response)
            if numbers:
                return float(numbers[0])
        except Exception as e:
            logger.error(f"LLM likelihood assessment failed: {e}")
        
        return 0.5
    
    def _are_causally_compatible(self, cause_type: str, effect_type: str) -> bool:
        """Check if cause and effect types are compatible."""
        compatible_pairs = {
            ("action", "state_change"),
            ("input", "output"),
            ("trigger", "event"),
            ("condition", "result"),
            ("stimulus", "response"),
            ("command", "execution")
        }
        
        return (cause_type, effect_type) in compatible_pairs
    
    async def _assess_causality_with_llm(self, cause: Dict[str, Any], effect: Dict[str, Any]) -> float:
        """Use LLM to assess causal relationship strength."""
        if not self.llm:
            return 0.5
        
        prompt = f"""
        Assess the strength of causal relationship between:
        
        Cause: {json.dumps(cause, indent=2)}
        Effect: {json.dumps(effect, indent=2)}
        
        Provide a strength score between 0 and 1, where:
        0 = no causal relationship
        1 = definite causal relationship
        """
        
        try:
            response = await self.llm.generate(prompt)
            # Extract score from response
            import re
            numbers = re.findall(r'0?\.\d+|1\.0|0|1', response)
            if numbers:
                return float(numbers[0])
        except Exception as e:
            logger.error(f"LLM causality assessment failed: {e}")
        
        return 0.5
    
    # Continue with remaining methods...
    async def _extract_concepts_from_content(self, content: Dict[str, Any]) -> List[Concept]:
        """Extract concepts from content using multiple methods."""
        concepts = []
        
        # Extract from text if available
        if "text" in content:
            text_concepts = await self._extract_concepts_from_text(content["text"])
            concepts.extend(text_concepts)
        
        # Extract from structured data
        if "data" in content:
            data_concepts = self._extract_concepts_from_data(content["data"])
            concepts.extend(data_concepts)
        
        # Use LLM for advanced extraction if available
        if self.llm and "description" in content:
            llm_concepts = await self._extract_concepts_with_llm(content["description"])
            concepts.extend(llm_concepts)
        
        # Deduplicate concepts
        unique_concepts = {}
        for concept in concepts:
            if concept.name not in unique_concepts:
                unique_concepts[concept.name] = concept
            else:
                # Merge properties and relationships
                existing = unique_concepts[concept.name]
                existing.properties.update(concept.properties)
                existing.relationships.extend(concept.relationships)
        
        return list(unique_concepts.values())
    
    async def _build_local_knowledge_graph(self, concepts: List[Concept]) -> nx.DiGraph:
        """Build a local knowledge graph from concepts."""
        graph = nx.DiGraph()
        
        # Add nodes
        for concept in concepts:
            graph.add_node(concept.id, **concept.properties)
        
        # Add edges
        for concept in concepts:
            for rel_type, target_id in concept.relationships:
                if any(c.id == target_id for c in concepts):
                    graph.add_edge(concept.id, target_id, relation=rel_type)
        
        # Infer additional relationships
        inferred_edges = await self._infer_relationships(concepts)
        for source, target, rel_type in inferred_edges:
            graph.add_edge(source, target, relation=rel_type, inferred=True)
        
        return graph
    
    async def _deductive_reasoning(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Apply deductive reasoning using inference rules."""
        facts = self._extract_facts_from_graph(graph)
        new_facts = {}
        
        # Apply inference rules
        for rule in self.inference_rules:
            if rule.applies_to(facts):
                for conclusion in rule.conclusions:
                    if conclusion["type"] == "assert":
                        new_facts[conclusion["fact"]] = {
                            "value": True,
                            "confidence": rule.confidence,
                            "rule": rule.name
                        }
        
        return {
            "original_facts": len(facts),
            "new_facts": new_facts,
            "rules_applied": [r.name for r in self.inference_rules if r.applies_to(facts)]
        }
    
    async def _inductive_reasoning(self, concepts: List[Concept]) -> Dict[str, Any]:
        """Apply inductive reasoning to find patterns."""
        patterns = []
        
        # Find common properties
        if len(concepts) > 2:
            property_counts = {}
            for concept in concepts:
                for prop, value in concept.properties.items():
                    if prop not in property_counts:
                        property_counts[prop] = []
                    property_counts[prop].append(value)
            
            # Identify patterns
            for prop, values in property_counts.items():
                if len(values) > len(concepts) * 0.6:  # 60% threshold
                    patterns.append({
                        "type": "common_property",
                        "property": prop,
                        "frequency": len(values) / len(concepts),
                        "values": list(set(values))
                    })
        
        # Find relationship patterns
        relationship_patterns = self._find_relationship_patterns(concepts)
        patterns.extend(relationship_patterns)
        
        return {
            "patterns_found": len(patterns),
            "patterns": patterns,
            "confidence": self._calculate_pattern_confidence(patterns, concepts)
        }
    
    async def _causal_reasoning(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Apply causal reasoning to understand cause-effect relationships."""
        causal_chains = []
        
        # Identify potential causes and effects
        if "events" in content:
            events = content["events"]
            for i in range(len(events) - 1):
                cause = events[i]
                effect = events[i + 1]
                
                # Calculate causal strength
                causal_strength = await self._calculate_causal_strength(cause, effect)
                
                if causal_strength > 0.5:
                    causal_chains.append({
                        "cause": cause,
                        "effect": effect,
                        "strength": causal_strength,
                        "mechanism": await self._infer_causal_mechanism(cause, effect)
                    })
        
        return {
            "causal_chains": causal_chains,
            "total_chains": len(causal_chains),
            "average_strength": np.mean([c["strength"] for c in causal_chains]) if causal_chains else 0
        }
    
    async def _analyze_pedagogical_implications(
        self,
        concepts: List[Concept],
        deductive_results: Dict[str, Any],
        inductive_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze implications for teaching and learning."""
        
        # Determine concept complexity
        complexity_scores = {}
        for concept in concepts:
            complexity = len(concept.relationships) + len(concept.properties)
            complexity_scores[concept.name] = complexity
        
        # Identify prerequisite relationships
        prerequisites = self._identify_prerequisites(concepts)
        
        # Determine learning sequence
        learning_sequence = self._determine_learning_sequence(concepts, prerequisites)
        
        # Identify key insights
        key_insights = []
        
        # From deductive reasoning
        if deductive_results["new_facts"]:
            key_insights.append({
                "type": "logical_connections",
                "insight": f"Found {len(deductive_results['new_facts'])} logical implications",
                "importance": "high"
            })
        
        # From inductive reasoning
        if inductive_results["patterns"]:
            key_insights.append({
                "type": "patterns",
                "insight": f"Identified {len(inductive_results['patterns'])} recurring patterns",
                "importance": "medium"
            })
        
        return {
            "complexity_scores": complexity_scores,
            "prerequisites": prerequisites,
            "learning_sequence": learning_sequence,
            "key_insights": key_insights,
            "cognitive_load_estimate": self._estimate_cognitive_load(concepts, complexity_scores)
        }
    
    async def _generate_content_recommendations(
        self,
        pedagogical_analysis: Dict[str, Any],
        content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for content improvement."""
        recommendations = []
        
        # Based on complexity
        avg_complexity = np.mean(list(pedagogical_analysis["complexity_scores"].values()))
        if avg_complexity > 10:
            recommendations.append({
                "type": "simplification",
                "priority": "high",
                "suggestion": "Break down complex concepts into smaller, manageable parts",
                "rationale": f"Average concept complexity ({avg_complexity:.1f}) is high"
            })
        
        # Based on prerequisites
        if len(pedagogical_analysis["prerequisites"]) > 5:
            recommendations.append({
                "type": "structure",
                "priority": "medium",
                "suggestion": "Create a clear prerequisite map or learning path",
                "rationale": "Multiple prerequisite relationships detected"
            })
        
        # Based on cognitive load
        if pedagogical_analysis["cognitive_load_estimate"] > 0.7:
            recommendations.append({
                "type": "pacing",
                "priority": "high",
                "suggestion": "Introduce concepts more gradually with practice between sections",
                "rationale": "High cognitive load estimated"
            })
        
        # Based on patterns
        if pedagogical_analysis.get("key_insights"):
            recommendations.append({
                "type": "emphasis",
                "priority": "medium",
                "suggestion": "Highlight the identified patterns and logical connections",
                "rationale": "Patterns can aid understanding and retention"
            })
        
        return recommendations
    
    # Additional helper methods
    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the knowledge graph."""
        self.concepts[concept.id] = concept
        self.knowledge_graph.add_node(concept.id, **concept.properties)
        
        # Add relationships
        for rel_type, target_id in concept.relationships:
            if target_id in self.concepts:
                self.knowledge_graph.add_edge(
                    concept.id, target_id,
                    relation=rel_type
                )
    
    def add_inference_rule(self, rule: InferenceRule) -> None:
        """Add an inference rule to the engine."""
        self.inference_rules.append(rule)
    
    def add_causal_model(self, model: CausalModel) -> None:
        """Add a causal model to the engine."""
        self.causal_models[model.id] = model
