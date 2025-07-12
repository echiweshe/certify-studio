"""
Learning path optimization algorithms.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .models import (
    LearningObjective,
    LearnerProfile,
    LearningPath,
    DifficultyLevel,
    LearningTheory
)


class LearningPathOptimizer:
    """Optimizes learning paths based on various criteria."""
    
    def __init__(self):
        """Initialize the learning path optimizer."""
        self.optimization_strategies = [
            "prerequisite_ordering",
            "difficulty_progression",
            "cognitive_load_balancing",
            "personalization"
        ]
    
    async def create_optimized_path(
        self,
        objectives: List[LearningObjective],
        learner_profile: Optional[LearnerProfile] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> LearningPath:
        """Create an optimized learning path."""
        try:
            # Apply optimization strategies in sequence
            sequence = self._topological_sort(objectives)
            sequence = self._apply_scaffolding(sequence)
            sequence = self._balance_difficulty(sequence)
            
            if learner_profile:
                sequence = self._personalize_sequence(sequence, learner_profile)
            
            # Create checkpoints
            checkpoints = self._create_checkpoints(sequence)
            
            # Build the learning path
            path = LearningPath(
                id=f"path_{datetime.now().isoformat()}",
                objectives=objectives,
                sequence=[obj.id for obj in sequence],
                estimated_duration=sum(obj.estimated_time for obj in objectives),
                difficulty_progression=self._get_difficulty_progression(sequence),
                personalization_notes=self._generate_notes(learner_profile),
                theories_applied=[
                    LearningTheory.SCAFFOLDING,
                    LearningTheory.COGNITIVE_LOAD
                ],
                checkpoints=checkpoints,
                adaptations={}
            )
            
            return path
            
        except Exception as e:
            logger.error(f"Failed to create optimized learning path: {e}")
            raise
    
    def _topological_sort(self, objectives: List[LearningObjective]) -> List[LearningObjective]:
        """Sort objectives based on prerequisites using topological sort."""
        # Create adjacency list and in-degree map
        obj_map = {obj.id: obj for obj in objectives}
        in_degree = {obj.id: 0 for obj in objectives}
        adj_list = {obj.id: [] for obj in objectives}
        
        # Build dependency graph
        for obj in objectives:
            for prereq in obj.prerequisites:
                if prereq in obj_map:
                    adj_list[prereq].append(obj.id)
                    in_degree[obj.id] += 1
        
        # Kahn's algorithm for topological sort
        queue = [obj_id for obj_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort queue by difficulty to process easier concepts first
            queue.sort(key=lambda x: obj_map[x].difficulty.value)
            current = queue.pop(0)
            result.append(obj_map[current])
            
            # Process neighbors
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Handle any remaining objectives (cycles or disconnected)
        remaining = [obj for obj in objectives if obj not in result]
        if remaining:
            logger.warning(f"Found {len(remaining)} objectives with circular dependencies")
            result.extend(remaining)
        
        return result
    
    def _apply_scaffolding(self, objectives: List[LearningObjective]) -> List[LearningObjective]:
        """Apply scaffolding principle to order by difficulty."""
        # Group objectives by difficulty level
        difficulty_groups = {}
        for obj in objectives:
            if obj.difficulty not in difficulty_groups:
                difficulty_groups[obj.difficulty] = []
            difficulty_groups[obj.difficulty].append(obj)
        
        # Rebuild sequence with gradual difficulty increase
        scaffolded = []
        for difficulty in DifficultyLevel:
            if difficulty in difficulty_groups:
                # Within each difficulty, sort by Bloom's level
                group = difficulty_groups[difficulty]
                group.sort(key=lambda x: self._blooms_level_order(x.level))
                scaffolded.extend(group)
        
        return scaffolded
    
    def _blooms_level_order(self, level: str) -> int:
        """Get numeric order for Bloom's taxonomy level."""
        order = {
            'remember': 1,
            'understand': 2,
            'apply': 3,
            'analyze': 4,
            'evaluate': 5,
            'create': 6
        }
        return order.get(level, 3)
    
    def _balance_difficulty(self, objectives: List[LearningObjective]) -> List[LearningObjective]:
        """Balance difficulty to avoid cognitive overload."""
        balanced = []
        recent_difficulties = []
        
        for obj in objectives:
            # Check if we need a breather
            if len(recent_difficulties) >= 3:
                avg_recent = sum(d.value for d in recent_difficulties[-3:]) / 3
                if avg_recent > 3.5 and obj.difficulty.value > 3:
                    # Insert an easier objective if available
                    easier = self._find_easier_objective(objectives, balanced, obj)
                    if easier:
                        balanced.append(easier)
                        recent_difficulties.append(easier.difficulty)
            
            if obj not in balanced:
                balanced.append(obj)
                recent_difficulties.append(obj.difficulty)
        
        return balanced
    
    def _find_easier_objective(
        self,
        all_objectives: List[LearningObjective],
        already_added: List[LearningObjective],
        current: LearningObjective
    ) -> Optional[LearningObjective]:
        """Find an easier objective that can be inserted."""
        candidates = [
            obj for obj in all_objectives
            if obj not in already_added
            and obj != current
            and obj.difficulty.value <= 2
            and all(prereq in [o.id for o in already_added] for prereq in obj.prerequisites)
        ]
        
        if candidates:
            # Return the one with fewest dependencies
            return min(candidates, key=lambda x: len(x.prerequisites))
        return None
    
    def _personalize_sequence(
        self,
        objectives: List[LearningObjective],
        learner_profile: LearnerProfile
    ) -> List[LearningObjective]:
        """Personalize learning sequence based on learner profile."""
        personalized = objectives.copy()
        
        # Adjust for pace preference
        if learner_profile.pace_preference == 'fast':
            # Remove review objectives for fast learners
            personalized = [
                obj for obj in personalized 
                if not obj.id.startswith('review_')
            ]
        elif learner_profile.pace_preference == 'slow':
            # Add more review points for slow learners
            extended = []
            for i, obj in enumerate(personalized):
                extended.append(obj)
                if i > 0 and i % 3 == 0:
                    # Add review every 3 objectives
                    review = self._create_review_objective(personalized[max(0, i-3):i])
                    extended.append(review)
            personalized = extended
        
        # Prioritize based on goals
        if learner_profile.goals:
            goal_related = []
            others = []
            
            for obj in personalized:
                # Check if objective relates to learner goals
                if any(goal.lower() in obj.description.lower() for goal in learner_profile.goals):
                    goal_related.append(obj)
                else:
                    others.append(obj)
            
            # Put goal-related objectives earlier (but respect prerequisites)
            personalized = self._merge_preserving_order(goal_related, others)
        
        # Adjust for learning style
        if learner_profile.learning_style == 'visual':
            # Prioritize objectives that likely have visual components
            visual_keywords = ['diagram', 'chart', 'visualize', 'illustrate', 'draw']
            personalized.sort(
                key=lambda x: any(kw in x.description.lower() for kw in visual_keywords),
                reverse=True
            )
        
        return personalized
    
    def _merge_preserving_order(
        self,
        priority: List[LearningObjective],
        others: List[LearningObjective]
    ) -> List[LearningObjective]:
        """Merge two lists while preserving prerequisite order."""
        merged = []
        added_ids = set()
        
        # Add priority items first (if prerequisites met)
        for obj in priority:
            if all(prereq in added_ids for prereq in obj.prerequisites):
                merged.append(obj)
                added_ids.add(obj.id)
        
        # Add remaining items
        remaining = [obj for obj in priority if obj.id not in added_ids] + others
        
        while remaining:
            # Find objectives with satisfied prerequisites
            ready = [
                obj for obj in remaining
                if all(prereq in added_ids for prereq in obj.prerequisites)
            ]
            
            if not ready:
                # Handle circular dependencies by taking the first
                ready = [remaining[0]]
            
            for obj in ready:
                merged.append(obj)
                added_ids.add(obj.id)
                remaining.remove(obj)
        
        return merged
    
    def _create_checkpoints(self, sequence: List[LearningObjective]) -> List[Dict[str, Any]]:
        """Create assessment checkpoints in the learning path."""
        checkpoints = []
        
        if not sequence:
            return checkpoints
        
        # Determine checkpoint interval
        total_objectives = len(sequence)
        num_checkpoints = min(5, max(2, total_objectives // 5))
        interval = total_objectives // num_checkpoints
        
        # Create formative assessments
        for i in range(interval, total_objectives, interval):
            checkpoint = {
                "position": i,
                "after_objective": sequence[i-1].id,
                "type": "formative_assessment",
                "assess_objectives": [
                    obj.id for obj in sequence[max(0, i-interval):i]
                ],
                "estimated_time": 10,
                "passing_threshold": 0.8,
                "retry_allowed": True
            }
            checkpoints.append(checkpoint)
        
        # Create final summative assessment
        checkpoints.append({
            "position": total_objectives,
            "after_objective": sequence[-1].id,
            "type": "summative_assessment",
            "assess_objectives": [obj.id for obj in sequence],
            "estimated_time": 30,
            "passing_threshold": 0.85,
            "retry_allowed": True,
            "comprehensive": True
        })
        
        return checkpoints
    
    def _get_difficulty_progression(self, sequence: List[LearningObjective]) -> List[DifficultyLevel]:
        """Extract difficulty progression from sequence."""
        return [obj.difficulty for obj in sequence]
    
    def _generate_notes(self, learner_profile: Optional[LearnerProfile]) -> List[str]:
        """Generate personalization notes."""
        notes = []
        
        if not learner_profile:
            notes.append("Generic learning path - no learner profile provided")
            return notes
        
        notes.append(f"Optimized for {learner_profile.pace_preference} pace learner")
        notes.append(f"Adapted for {learner_profile.learning_style} learning style")
        
        if learner_profile.time_availability:
            notes.append(f"Structured for {learner_profile.time_availability} availability")
        
        if learner_profile.goals:
            notes.append(f"Prioritized goals: {', '.join(learner_profile.goals[:3])}")
        
        return notes
    
    def _create_review_objective(self, recent_objectives: List[LearningObjective]) -> LearningObjective:
        """Create a review objective for recent content."""
        topics = [obj.description for obj in recent_objectives[-3:]]
        
        return LearningObjective(
            id=f"review_{datetime.now().timestamp()}",
            description=f"Review: {', '.join(topics[:2])}{'...' if len(topics) > 2 else ''}",
            domain="cognitive",
            level="understand",
            prerequisites=[obj.id for obj in recent_objectives],
            estimated_time=5,
            difficulty=DifficultyLevel.ELEMENTARY
        )
