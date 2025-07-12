"""
Cognitive load assessment and management.
"""

from typing import List, Dict, Any
from loguru import logger

from .models import (
    LearningObjective, 
    CognitiveLoadAssessment,
    DifficultyLevel
)


class CognitiveLoadManager:
    """Manages cognitive load assessment and optimization."""
    
    def __init__(self):
        """Initialize the cognitive load manager."""
        self.load_factors = self._initialize_load_factors()
        self.optimization_strategies = self._initialize_strategies()
    
    def _initialize_load_factors(self) -> Dict[str, float]:
        """Initialize factors affecting cognitive load."""
        return {
            "element_interactivity": 0.3,
            "prior_knowledge": -0.4,  # reduces load
            "presentation_modality": 0.2,
            "temporal_spacing": -0.2,  # reduces load
            "worked_examples": -0.3,  # reduces load
            "redundancy": 0.2,
            "split_attention": 0.3,
            "goal_free_problems": -0.2,  # reduces load
            "completion_problems": -0.15  # reduces load
        }
    
    def _initialize_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cognitive load optimization strategies."""
        return {
            "chunking": {
                "description": "Break complex information into smaller units",
                "effectiveness": 0.8,
                "applicable_when": ["high_intrinsic_load", "novice_learners"]
            },
            "worked_examples": {
                "description": "Provide step-by-step solutions",
                "effectiveness": 0.85,
                "applicable_when": ["procedural_knowledge", "problem_solving"]
            },
            "split_attention_reduction": {
                "description": "Integrate related information spatially",
                "effectiveness": 0.7,
                "applicable_when": ["multiple_information_sources"]
            },
            "modality_principle": {
                "description": "Use both visual and auditory channels",
                "effectiveness": 0.75,
                "applicable_when": ["high_visual_complexity"]
            }
        }
    
    async def assess_cognitive_load(
        self,
        objectives: List[LearningObjective],
        sequence: List[LearningObjective]
    ) -> CognitiveLoadAssessment:
        """Assess cognitive load of a learning path."""
        try:
            intrinsic_load = self._calculate_intrinsic_load(objectives)
            extraneous_load = self._calculate_extraneous_load(sequence)
            germane_load = self._calculate_germane_load(objectives)
            
            total_load = (intrinsic_load + extraneous_load + germane_load) / 3
            
            recommendations = self._generate_recommendations(
                intrinsic_load, extraneous_load, germane_load
            )
            
            optimizations = self._identify_optimizations(
                objectives, intrinsic_load, extraneous_load
            )
            
            return CognitiveLoadAssessment(
                intrinsic_load=intrinsic_load,
                extraneous_load=extraneous_load,
                germane_load=germane_load,
                total_load=total_load,
                recommendations=recommendations,
                optimizations=optimizations
            )
            
        except Exception as e:
            logger.error(f"Failed to assess cognitive load: {e}")
            raise
    
    def _calculate_intrinsic_load(self, objectives: List[LearningObjective]) -> float:
        """Calculate intrinsic cognitive load based on content complexity."""
        if not objectives:
            return 0.0
        
        # Factors contributing to intrinsic load
        complexity_score = 0.0
        interactivity_score = 0.0
        
        for obj in objectives:
            # Difficulty contributes to complexity
            complexity_score += obj.difficulty.value / 5.0
            
            # Higher Bloom's levels have more element interactivity
            bloom_weights = {
                'remember': 0.2,
                'understand': 0.3,
                'apply': 0.5,
                'analyze': 0.7,
                'evaluate': 0.8,
                'create': 0.9
            }
            interactivity_score += bloom_weights.get(obj.level, 0.5)
        
        # Average the scores
        avg_complexity = complexity_score / len(objectives)
        avg_interactivity = interactivity_score / len(objectives)
        
        # Weighted combination
        intrinsic_load = (avg_complexity * 0.6) + (avg_interactivity * 0.4)
        
        return min(intrinsic_load, 1.0)
    
    def _calculate_extraneous_load(self, sequence: List[LearningObjective]) -> float:
        """Calculate extraneous load from presentation and sequencing."""
        if not sequence:
            return 0.0
        
        load = 0.0
        
        # Context switching penalty
        prev_level = None
        switches = 0
        for obj in sequence:
            if prev_level and obj.level != prev_level:
                switches += 1
            prev_level = obj.level
        
        context_switch_load = min(switches / len(sequence), 0.3)
        load += context_switch_load
        
        # Difficulty jump penalty
        prev_diff = None
        large_jumps = 0
        for obj in sequence:
            if prev_diff and abs(obj.difficulty.value - prev_diff.value) > 1:
                large_jumps += 1
            prev_diff = obj.difficulty
        
        difficulty_jump_load = min(large_jumps / len(sequence), 0.3)
        load += difficulty_jump_load
        
        # Prerequisite violation penalty
        seen_ids = set()
        violations = 0
        for obj in sequence:
            for prereq in obj.prerequisites:
                if prereq not in seen_ids:
                    violations += 1
            seen_ids.add(obj.id)
        
        prerequisite_load = min(violations / len(sequence), 0.2)
        load += prerequisite_load
        
        return min(load, 1.0)
    
    def _calculate_germane_load(self, objectives: List[LearningObjective]) -> float:
        """Calculate germane load (beneficial for schema construction)."""
        if not objectives:
            return 0.0
        
        # Schema building activities (higher Bloom's levels)
        schema_building = sum(
            1 for obj in objectives 
            if obj.level in ['analyze', 'evaluate', 'create']
        )
        
        # Transfer-appropriate activities
        transfer_activities = sum(
            1 for obj in objectives
            if obj.level in ['apply', 'analyze']
        )
        
        # Elaboration opportunities
        elaboration = sum(
            1 for obj in objectives
            if obj.estimated_time > 15  # Longer activities allow elaboration
        )
        
        # Calculate germane load (we want this to be moderately high)
        germane_factors = (
            (schema_building / len(objectives)) * 0.4 +
            (transfer_activities / len(objectives)) * 0.3 +
            (elaboration / len(objectives)) * 0.3
        )
        
        return min(germane_factors, 1.0)
    
    def _generate_recommendations(
        self,
        intrinsic: float,
        extraneous: float,
        germane: float
    ) -> List[str]:
        """Generate recommendations based on load assessment."""
        recommendations = []
        
        # High intrinsic load
        if intrinsic > 0.7:
            recommendations.append("Break complex topics into smaller, manageable chunks")
            recommendations.append("Provide more worked examples before practice")
            recommendations.append("Use pre-training for component concepts")
        
        # High extraneous load
        if extraneous > 0.6:
            recommendations.append("Improve sequencing to reduce context switches")
            recommendations.append("Ensure prerequisites are met before introducing concepts")
            recommendations.append("Use consistent presentation formats")
        
        # Low germane load
        if germane < 0.3:
            recommendations.append("Add more schema-building activities")
            recommendations.append("Include reflection and elaboration exercises")
            recommendations.append("Provide opportunities for knowledge transfer")
        
        # Total load too high
        total = (intrinsic + extraneous + germane) / 3
        if total > 0.8:
            recommendations.append("Consider spreading content over more sessions")
            recommendations.append("Remove non-essential information")
            recommendations.append("Increase support for novice learners")
        
        return recommendations
    
    def _identify_optimizations(
        self,
        objectives: List[LearningObjective],
        intrinsic_load: float,
        extraneous_load: float
    ) -> List[Dict[str, Any]]:
        """Identify specific optimizations for the content."""
        optimizations = []
        
        if intrinsic_load > 0.7:
            # Chunking strategy
            optimizations.append({
                "strategy": "chunking",
                "target_objectives": [
                    obj.id for obj in objectives 
                    if obj.difficulty.value >= 4
                ],
                "implementation": "Break each concept into 3-5 sub-concepts",
                "expected_reduction": 0.2
            })
            
            # Worked examples
            optimizations.append({
                "strategy": "worked_examples",
                "target_objectives": [
                    obj.id for obj in objectives
                    if obj.level in ['apply', 'analyze', 'create']
                ],
                "implementation": "Provide 2-3 worked examples per concept",
                "expected_reduction": 0.25
            })
        
        if extraneous_load > 0.6:
            # Split attention reduction
            optimizations.append({
                "strategy": "integrated_format",
                "description": "Integrate text and diagrams spatially",
                "expected_reduction": 0.15
            })
            
            # Consistent formatting
            optimizations.append({
                "strategy": "consistent_design",
                "description": "Use standardized templates and layouts",
                "expected_reduction": 0.1
            })
        
        return optimizations
    
    def optimize_for_cognitive_load(
        self,
        objectives: List[LearningObjective]
    ) -> List[LearningObjective]:
        """Optimize learning sequence to manage cognitive load."""
        optimized = []
        current_load = 0.0
        max_load = 0.7  # threshold
        
        for obj in objectives:
            # Estimate cognitive load for this objective
            obj_load = self._estimate_objective_load(obj)
            
            # If adding this would exceed threshold, add a break/review
            if current_load + obj_load > max_load and optimized:
                # Insert a review/consolidation objective
                review_obj = self._create_review_objective(optimized[-3:])
                optimized.append(review_obj)
                current_load = 0.2  # Reset with small base load
            
            optimized.append(obj)
            current_load += obj_load
        
        return optimized
    
    def _estimate_objective_load(self, objective: LearningObjective) -> float:
        """Estimate cognitive load for a single objective."""
        base_load = 0.2
        
        # Difficulty factor
        difficulty_factor = objective.difficulty.value * 0.1
        
        # Bloom's level factor
        blooms_factor = {
            'remember': 0.1,
            'understand': 0.2,
            'apply': 0.3,
            'analyze': 0.4,
            'evaluate': 0.5,
            'create': 0.6
        }.get(objective.level, 0.3)
        
        # Time factor (longer = more load)
        time_factor = min(objective.estimated_time / 60, 0.3)
        
        # Prerequisites factor
        prereq_factor = len(objective.prerequisites) * 0.05
        
        return min(
            base_load + difficulty_factor + blooms_factor + time_factor + prereq_factor,
            1.0
        )
    
    def _create_review_objective(
        self,
        recent_objectives: List[LearningObjective]
    ) -> LearningObjective:
        """Create a review/consolidation objective."""
        from datetime import datetime
        
        topics = [obj.description for obj in recent_objectives]
        
        return LearningObjective(
            id=f"review_{datetime.now().timestamp()}",
            description=f"Review and consolidate: {', '.join(topics[:2])}...",
            domain="cognitive",
            level="understand",
            prerequisites=[obj.id for obj in recent_objectives],
            estimated_time=5,
            difficulty=DifficultyLevel.ELEMENTARY
        )
    
    def chunk_complex_concept(
        self,
        concept: Dict[str, Any],
        chunk_size: int = 3
    ) -> List[Dict[str, Any]]:
        """Break a complex concept into smaller chunks."""
        chunks = []
        base_chunk = {
            "parent_id": concept.get("id"),
            "type": "chunk",
            "difficulty": max(1, concept.get("difficulty", 3) - 1)
        }
        
        # Create chunks based on subtopics
        subtopics = concept.get("subtopics", [])
        
        for i in range(0, len(subtopics), chunk_size):
            chunk = base_chunk.copy()
            chunk["id"] = f"{concept.get('id')}_chunk_{i//chunk_size}"
            chunk["subtopics"] = subtopics[i:i+chunk_size]
            chunk["name"] = f"{concept.get('name')} - Part {i//chunk_size + 1}"
            chunk["estimated_time"] = concept.get("estimated_time", 10) // len(chunks) if chunks else 10
            chunks.append(chunk)
        
        return chunks
