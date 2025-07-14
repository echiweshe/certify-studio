"""
Prompt management for multimodal LLM interactions.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import json
from pathlib import Path

from ..logging import get_logger

logger = get_logger(__name__)


class PromptType(Enum):
    """Types of prompts for different tasks."""
    CONCEPT_EXTRACTION = "concept_extraction"
    VISUAL_METAPHOR_SELECTION = "visual_metaphor_selection"
    ANIMATION_PLANNING = "animation_planning"
    DIAGRAM_ANALYSIS = "diagram_analysis"
    CONTENT_SYNTHESIS = "content_synthesis"
    QUALITY_ASSESSMENT = "quality_assessment"
    LEARNING_PATH_OPTIMIZATION = "learning_path_optimization"


class PromptManager:
    """Manages prompts for multimodal LLM interactions."""
    
    def __init__(self):
        self.prompt_templates = self._load_prompt_templates()
        self.few_shot_examples = self._load_few_shot_examples()
    
    def _load_prompt_templates(self) -> Dict[PromptType, str]:
        """Load prompt templates."""
        
        return {
            PromptType.CONCEPT_EXTRACTION: """
You are an expert educational content analyzer specializing in technical certifications.

Analyze the provided certification content and extract key concepts with the following structure:

1. **Concept Identification**: Find all important concepts, services, patterns, and practices
2. **Importance Scoring**: Rate each concept's importance (0.0-1.0) based on:
   - Frequency of mention
   - Emphasis in the text
   - Relationship to exam objectives
3. **Complexity Assessment**: Rate complexity (1-10) based on:
   - Prerequisites required
   - Technical depth
   - Abstract vs concrete nature
4. **Visual Metaphor Suggestions**: Suggest appropriate visual metaphors for each concept
5. **Relationships**: Identify how concepts relate to each other

Output Format:
```json
{
  "concepts": [
    {
      "id": "unique_identifier",
      "name": "Concept Name",
      "type": "service|feature|pattern|practice|principle",
      "description": "Clear description",
      "importance": 0.0-1.0,
      "complexity": 1-10,
      "prerequisites": ["concept_id1", "concept_id2"],
      "visual_metaphors": ["metaphor1", "metaphor2"],
      "examples": ["example1", "example2"]
    }
  ],
  "relationships": [
    {
      "source": "concept_id1",
      "target": "concept_id2",
      "type": "depends_on|enables|contains|extends",
      "strength": 0.0-1.0
    }
  ],
  "key_themes": ["theme1", "theme2", "theme3"]
}
```

Remember to:
- Focus on concepts that would benefit from visual explanation
- Identify hierarchical relationships
- Consider the target audience (technical professionals)
- Extract actionable learning objectives
""",

            PromptType.VISUAL_METAPHOR_SELECTION: """
You are a visual learning expert who selects the most effective visual metaphors for technical concepts.

Given the following concept and context:
- Concept: {concept_name}
- Type: {concept_type}
- Description: {description}
- Complexity: {complexity}/10
- Target Audience: {audience}

Select and design visual metaphors that will:
1. Make abstract concepts concrete and memorable
2. Use culturally universal symbols when possible
3. Build on familiar mental models
4. Support progressive disclosure for complex topics

Consider these visual metaphor categories:
- CONTAINER: For grouping, isolation, security boundaries
- FLOW: For data movement, processes, pipelines
- TRANSFORMATION: For state changes, processing, computation
- CONNECTION: For relationships, networking, integration
- HIERARCHY: For structure, organization, inheritance
- CYCLE: For loops, recurring processes, lifecycles
- GROWTH: For scaling, expansion, evolution
- BARRIER: For security, access control, filtering

Provide your response in this format:
```json
{
  "primary_metaphor": {
    "type": "FLOW|CONTAINER|etc",
    "rationale": "Why this metaphor works for this concept",
    "visual_elements": ["element1", "element2"],
    "animation_suggestions": ["suggestion1", "suggestion2"]
  },
  "supporting_metaphors": [
    {
      "type": "metaphor_type",
      "usage": "How this supports understanding",
      "visual_elements": ["element1", "element2"]
    }
  ],
  "color_associations": {
    "primary": "#hex_color",
    "secondary": "#hex_color",
    "semantic_meaning": "What the colors represent"
  },
  "complexity_handling": {
    "initial_view": "What to show first",
    "progressive_reveals": ["reveal1", "reveal2", "reveal3"],
    "interaction_points": ["interaction1", "interaction2"]
  }
}
```
""",

            PromptType.ANIMATION_PLANNING: """
You are an expert in educational animation and visual storytelling for technical content.

Create an animation plan for teaching the following concept:
- Concept: {concept_name}
- Learning Objectives: {objectives}
- Time Budget: {duration} seconds
- Audience Expertise: {expertise_level}

Your animation plan should follow these principles:
1. **Progressive Disclosure**: Start simple, add complexity gradually
2. **Visual Hierarchy**: Guide attention to important elements
3. **Motion Consistency**: Use consistent animation patterns
4. **Cognitive Load Management**: Don't overwhelm the viewer
5. **Narrative Flow**: Tell a coherent story

Structure your response as:
```json
{
  "narrative_arc": {
    "hook": "Opening that grabs attention",
    "problem_statement": "What challenge does this solve?",
    "solution_reveal": "How the concept addresses the problem",
    "reinforcement": "Key takeaway"
  },
  "scenes": [
    {
      "scene_id": "unique_id",
      "duration": seconds,
      "purpose": "What this scene teaches",
      "elements": [
        {
          "element_type": "text|shape|icon|particle|composite",
          "content": "Element details",
          "enter_time": 0.0,
          "exit_time": 0.0,
          "animations": {
            "enter": {"type": "fade|slide|grow", "duration": 1.0},
            "emphasis": {"type": "pulse|glow|shake", "trigger": "condition"},
            "exit": {"type": "fade|slide|shrink", "duration": 0.5}
          }
        }
      ],
      "camera_movements": [
        {"type": "zoom|pan|orbit", "target": "element_id", "duration": 1.0}
      ],
      "narration": "What to explain during this scene",
      "interaction_prompts": ["Click to explore", "Hover for details"]
    }
  ],
  "visual_consistency": {
    "color_scheme": "How colors are used meaningfully",
    "motion_language": "Consistent animation patterns",
    "spatial_organization": "How elements are arranged"
  },
  "accessibility": {
    "audio_descriptions": ["description1", "description2"],
    "visual_alternatives": "How to convey info without animation"
  }
}
```
""",

            PromptType.DIAGRAM_ANALYSIS: """
You are an expert at analyzing and optimizing technical diagrams for educational purposes.

Analyze this diagram specification and suggest improvements:
{diagram_spec}

Consider:
1. **Clarity**: Is the diagram easy to understand at first glance?
2. **Information Hierarchy**: Are important elements emphasized?
3. **Relationship Clarity**: Are connections clear and meaningful?
4. **Cognitive Load**: Is there too much information?
5. **Visual Balance**: Is the layout aesthetically pleasing?

Provide analysis and improvements:
```json
{
  "current_strengths": ["strength1", "strength2"],
  "issues_identified": [
    {
      "issue": "Description of the problem",
      "severity": "high|medium|low",
      "impact": "How this affects understanding"
    }
  ],
  "layout_improvements": {
    "algorithm_suggestion": "force_directed|hierarchical|etc",
    "rationale": "Why this layout works better",
    "specific_adjustments": [
        {"element": "element_id", "suggestion": "Move to..."}
    ]
  },
  "visual_improvements": {
    "color_usage": "How to use color more effectively",
    "size_hierarchy": "How to size elements by importance",
    "connection_styling": "How to clarify relationships"
  },
  "simplification_suggestions": {
    "elements_to_group": [["id1", "id2"], ["id3", "id4"]],
    "elements_to_remove": ["id5", "id6"],
    "progressive_disclosure": "What to show in stages"
  },
  "interaction_design": {
    "hover_behaviors": "What happens on hover",
    "click_behaviors": "What happens on click",
    "animation_opportunities": "Where animation would help"
  }
}
```
""",

            PromptType.CONTENT_SYNTHESIS: """
You are a master educator who synthesizes complex technical information into clear, engaging narratives.

Synthesize the following technical concepts into a cohesive learning experience:
- Concepts: {concepts}
- Learning Objectives: {objectives}
- Target Duration: {duration}
- Audience: {audience}

Create a synthesis that:
1. Tells a compelling story
2. Builds knowledge progressively
3. Uses analogies effectively
4. Maintains engagement
5. Ensures retention

Structure your response as:
```json
{
  "narrative_theme": {
    "central_metaphor": "Overarching metaphor that ties everything together",
    "story_arc": "Beginning -> Middle -> End progression",
    "emotional_hooks": ["hook1", "hook2"]
  },
  "content_modules": [
    {
      "module_id": "unique_id",
      "title": "Module Title",
      "concepts_covered": ["concept1", "concept2"],
      "duration": seconds,
      "learning_approach": "How this module teaches",
      "visual_strategy": "Primary visual approach",
      "check_understanding": "How to verify learning"
    }
  ],
  "transitions": [
    {
      "from_module": "module1",
      "to_module": "module2",
      "transition_type": "conceptual_bridge|recap|preview",
      "narrative_link": "How the story connects"
    }
  ],
  "reinforcement_strategy": {
    "key_takeaways": ["takeaway1", "takeaway2"],
    "memorable_moments": "What will stick with learners",
    "practice_opportunities": ["practice1", "practice2"]
  },
  "multimodal_elements": {
    "visual_anchors": "Recurring visual elements",
    "audio_cues": "Sound design strategy",
    "interaction_patterns": "Consistent interaction language"
  }
}
```
""",

            PromptType.QUALITY_ASSESSMENT: """
You are an expert in educational content quality assessment.

Assess the quality of this educational content:
{content_spec}

Evaluate based on:
1. **Educational Effectiveness**: Will learners achieve the objectives?
2. **Engagement**: Will learners stay interested?
3. **Clarity**: Is the content clear and unambiguous?
4. **Pacing**: Is the timing appropriate?
5. **Accessibility**: Can diverse learners access this?
6. **Technical Accuracy**: Is the information correct?

Provide your assessment:
```json
{
  "overall_score": 0-100,
  "dimension_scores": {
    "educational_effectiveness": 0-100,
    "engagement": 0-100,
    "clarity": 0-100,
    "pacing": 0-100,
    "accessibility": 0-100,
    "technical_accuracy": 0-100
  },
  "strengths": [
    {
      "aspect": "What works well",
      "impact": "Why this is effective",
      "examples": ["specific example"]
    }
  ],
  "improvements_needed": [
    {
      "issue": "What needs work",
      "priority": "critical|high|medium|low",
      "suggestion": "How to fix it",
      "effort": "small|medium|large"
    }
  ],
  "learner_experience_prediction": {
    "engagement_curve": "How engagement changes over time",
    "difficulty_progression": "How difficulty ramps up",
    "retention_likelihood": "high|medium|low",
    "completion_likelihood": "high|medium|low"
  },
  "recommendations": {
    "immediate_fixes": ["fix1", "fix2"],
    "enhancement_opportunities": ["enhancement1", "enhancement2"],
    "future_iterations": ["idea1", "idea2"]
  }
}
```
"""
        }
    
    def _load_few_shot_examples(self) -> Dict[PromptType, List[Dict[str, Any]]]:
        """Load few-shot examples for each prompt type."""
        
        return {
            PromptType.CONCEPT_EXTRACTION: [
                {
                    "input": "Amazon S3 (Simple Storage Service) is a scalable object storage service that offers industry-leading durability, availability, performance, and security. S3 provides easy-to-use management features so you can organize your data and configure access controls. S3 storage classes include S3 Standard for frequently accessed data, S3 Standard-IA for infrequently accessed data, and S3 Glacier for archival storage.",
                    "output": {
                        "concepts": [
                            {
                                "id": "s3_core",
                                "name": "Amazon S3",
                                "type": "service",
                                "description": "Scalable object storage service with high durability and availability",
                                "importance": 0.95,
                                "complexity": 4,
                                "prerequisites": [],
                                "visual_metaphors": ["warehouse", "filing_cabinet", "cloud_container"],
                                "examples": ["Website hosting", "Data backup", "Content distribution"]
                            },
                            {
                                "id": "s3_storage_classes",
                                "name": "S3 Storage Classes",
                                "type": "feature",
                                "description": "Different storage tiers optimized for access patterns and cost",
                                "importance": 0.8,
                                "complexity": 5,
                                "prerequisites": ["s3_core"],
                                "visual_metaphors": ["temperature_zones", "storage_hierarchy", "cost_ladder"],
                                "examples": ["S3 Standard", "S3 Standard-IA", "S3 Glacier"]
                            }
                        ],
                        "relationships": [
                            {
                                "source": "s3_storage_classes",
                                "target": "s3_core",
                                "type": "contains",
                                "strength": 0.9
                            }
                        ],
                        "key_themes": ["Object Storage", "Durability", "Cost Optimization"]
                    }
                }
            ],
            
            PromptType.VISUAL_METAPHOR_SELECTION: [
                {
                    "input": {
                        "concept_name": "Load Balancer",
                        "concept_type": "service",
                        "description": "Distributes incoming traffic across multiple targets",
                        "complexity": 5,
                        "audience": "intermediate_developers"
                    },
                    "output": {
                        "primary_metaphor": {
                            "type": "FLOW",
                            "rationale": "Traffic distribution is fundamentally about flow management, making this intuitive",
                            "visual_elements": ["traffic_splitter", "multiple_lanes", "flow_indicators"],
                            "animation_suggestions": ["Animate packets flowing through different paths", "Show load distribution in real-time"]
                        },
                        "supporting_metaphors": [
                            {
                                "type": "BARRIER",
                                "usage": "Shows how the load balancer protects backend servers",
                                "visual_elements": ["shield", "gatekeeper"]
                            }
                        ],
                        "color_associations": {
                            "primary": "#2196F3",
                            "secondary": "#4CAF50",
                            "semantic_meaning": "Blue for traffic flow, green for healthy targets"
                        },
                        "complexity_handling": {
                            "initial_view": "Simple traffic splitter with 3 targets",
                            "progressive_reveals": ["Add health checks", "Show algorithms", "Include auto-scaling"],
                            "interaction_points": ["Click to see traffic distribution", "Hover to view health status"]
                        }
                    }
                }
            ]
        }
    
    def get_prompt(
        self,
        prompt_type: PromptType,
        variables: Dict[str, Any],
        include_examples: bool = True
    ) -> str:
        """Get a formatted prompt with variables filled in."""
        
        # Get base template
        template = self.prompt_templates.get(prompt_type, "")
        
        # Fill in variables
        prompt = template.format(**variables)
        
        # Add few-shot examples if requested
        if include_examples and prompt_type in self.few_shot_examples:
            examples_text = "\n\nHere are some examples:\n\n"
            for example in self.few_shot_examples[prompt_type]:
                examples_text += f"Input: {json.dumps(example['input'], indent=2)}\n"
                examples_text += f"Output: {json.dumps(example['output'], indent=2)}\n\n"
            
            prompt = examples_text + prompt
        
        return prompt
    
    def create_multimodal_prompt(
        self,
        prompt_type: PromptType,
        text_content: str,
        images: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a prompt that references multimodal content."""
        
        parts = []
        
        # Add context if provided
        if context:
            parts.append(f"Context: {json.dumps(context, indent=2)}")
        
        # Add image references
        if images:
            parts.append(f"\nAnalyzing {len(images)} images provided.")
            for i, img_info in enumerate(images):
                parts.append(f"Image {i+1}: {img_info.get('description', 'No description')}")
        
        # Add main content
        parts.append(f"\nContent to analyze:\n{text_content}")
        
        # Add the prompt template
        template_vars = {
            "content": text_content,
            "image_count": len(images) if images else 0,
            **(context if context else {})
        }
        
        prompt = self.get_prompt(prompt_type, template_vars)
        parts.append(f"\n{prompt}")
        
        return "\n".join(parts)
    
    def create_chain_of_thought_prompt(
        self,
        task: str,
        steps: List[str]
    ) -> str:
        """Create a chain-of-thought prompt for complex reasoning."""
        
        prompt = f"Task: {task}\n\n"
        prompt += "Let's think through this step by step:\n\n"
        
        for i, step in enumerate(steps, 1):
            prompt += f"Step {i}: {step}\n"
        
        prompt += "\nNow, let's work through each step:"
        
        return prompt
    
    def create_critique_prompt(
        self,
        content: str,
        criteria: List[str]
    ) -> str:
        """Create a prompt for critiquing content."""
        
        prompt = "Please critique the following content based on these criteria:\n\n"
        
        for criterion in criteria:
            prompt += f"- {criterion}\n"
        
        prompt += f"\nContent to critique:\n{content}\n\n"
        prompt += "Provide specific, actionable feedback for each criterion."
        
        return prompt
