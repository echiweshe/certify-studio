"""
Component Library System

This module implements the core component library that enables rapid content
assembly rather than generation from scratch. It's the foundation of the
"Component Assembly Over Generation" principle.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import asyncio
from datetime import datetime
import hashlib

from loguru import logger
from pydantic import BaseModel, Field

from certify_studio.core.llm import MultimodalLLM


class ComponentType(str, Enum):
    """Types of reusable components."""
    SERVICE_CARD = "service_card"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    FLOW_CHART = "flow_chart"
    COMPARISON_TABLE = "comparison_table"
    CONCEPT_VISUALIZER = "concept_visualizer"
    NETWORK_TOPOLOGY = "network_topology"
    SEQUENCE_DIAGRAM = "sequence_diagram"
    STATE_MACHINE = "state_machine"
    DEPLOYMENT_DIAGRAM = "deployment_diagram"
    SECURITY_DIAGRAM = "security_diagram"
    DATA_FLOW = "data_flow"
    INTERACTION_DIAGRAM = "interaction_diagram"
    TIMELINE = "timeline"
    PROCESS_FLOW = "process_flow"
    HIERARCHY_CHART = "hierarchy_chart"


class Provider(str, Enum):
    """Supported cloud providers and generic category."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    GENERIC = "generic"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    TERRAFORM = "terraform"
    NETWORKING = "networking"
    SECURITY = "security"
    DATABASE = "database"


class AnimationType(str, Enum):
    """Available animation types for components."""
    FADE_IN = "fade_in"
    SCALE_IN = "scale_in"
    SLIDE_IN = "slide_in"
    DRAW = "draw"
    MORPH = "morph"
    HIGHLIGHT = "highlight"
    PULSE = "pulse"
    ROTATE = "rotate"
    GLOW = "glow"
    BOUNCE = "bounce"
    TYPEWRITER = "typewriter"
    PARTICLE = "particle"
    CONNECTION_FLOW = "connection_flow"
    DATA_STREAM = "data_stream"


@dataclass
class ComponentMetadata:
    """Metadata for each component."""
    id: str
    name: str
    description: str
    provider: Provider
    type: ComponentType
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    complexity: int = 1  # 1-5 scale
    render_time: float = 1.0  # seconds
    file_size: int = 0  # bytes
    last_used: Optional[datetime] = None
    usage_count: int = 0
    quality_score: float = 0.85
    accessibility_score: float = 0.90


@dataclass
class AnimationParameters:
    """Parameters for component animations."""
    duration: float = 1.0
    delay: float = 0.0
    easing: str = "ease_in_out"
    direction: str = "normal"
    repeat: int = 1
    start_opacity: float = 0.0
    end_opacity: float = 1.0
    start_scale: float = 0.8
    end_scale: float = 1.0
    start_position: Tuple[float, float] = (0.0, 0.0)
    end_position: Tuple[float, float] = (0.0, 0.0)
    color_transition: Optional[Dict[str, str]] = None


@dataclass
class ComponentStyle:
    """Visual style configuration for components."""
    primary_color: str = "#232F3E"  # AWS dark blue
    secondary_color: str = "#FF9900"  # AWS orange
    background_color: str = "#FFFFFF"
    text_color: str = "#232F3E"
    accent_color: str = "#146EB4"
    border_color: str = "#D5DBDB"
    border_width: int = 2
    border_radius: int = 8
    shadow: bool = True
    shadow_blur: int = 10
    font_family: str = "Amazon Ember, Arial, sans-serif"
    font_size: int = 14
    padding: int = 16
    margin: int = 8


class AnimationComponent(BaseModel):
    """Base model for all animation components."""
    metadata: ComponentMetadata
    style: ComponentStyle = Field(default_factory=ComponentStyle)
    animations: List[AnimationType] = Field(default_factory=list)
    default_animation: AnimationType = AnimationType.FADE_IN
    parameters: AnimationParameters = Field(default_factory=AnimationParameters)
    manim_class: str = "VMobject"
    manim_config: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class ComponentLibrary:
    """
    High-quality reusable component library.
    Central to the Component Assembly Over Generation principle.
    """
    
    def __init__(self, library_path: Path = Path("assets/components")):
        self.library_path = library_path
        self.components: Dict[str, Dict[str, AnimationComponent]] = {}
        self.animation_patterns: Dict[str, List[AnimationType]] = {}
        self.style_guides: Dict[Provider, ComponentStyle] = {}
        self.llm = MultimodalLLM()
        self._initialize_library()
    
    def _initialize_library(self):
        """Initialize component library with base components."""
        # Initialize provider-specific style guides
        self._initialize_style_guides()
        
        # Initialize animation patterns
        self._initialize_animation_patterns()
        
        # Load AWS components
        self._load_aws_components()
        
        # Load Azure components
        self._load_azure_components()
        
        # Load GCP components
        self._load_gcp_components()
        
        # Load generic components
        self._load_generic_components()
        
        logger.info(f"Component library initialized with {self._count_components()} components")
    
    def _initialize_style_guides(self):
        """Initialize provider-specific style guides."""
        self.style_guides = {
            Provider.AWS: ComponentStyle(
                primary_color="#232F3E",
                secondary_color="#FF9900",
                accent_color="#146EB4",
                font_family="Amazon Ember, Arial, sans-serif"
            ),
            Provider.AZURE: ComponentStyle(
                primary_color="#0078D4",
                secondary_color="#00BCF2",
                accent_color="#FFB900",
                font_family="Segoe UI, Arial, sans-serif"
            ),
            Provider.GCP: ComponentStyle(
                primary_color="#4285F4",
                secondary_color="#34A853",
                accent_color="#EA4335",
                font_family="Google Sans, Arial, sans-serif"
            ),
            Provider.GENERIC: ComponentStyle(
                primary_color="#2C3E50",
                secondary_color="#3498DB",
                accent_color="#E74C3C",
                font_family="Inter, Arial, sans-serif"
            )
        }
    
    def _initialize_animation_patterns(self):
        """Initialize reusable animation patterns."""
        self.animation_patterns = {
            "service_introduction": [
                AnimationType.FADE_IN,
                AnimationType.SCALE_IN,
                AnimationType.GLOW
            ],
            "architecture_reveal": [
                AnimationType.DRAW,
                AnimationType.FADE_IN,
                AnimationType.CONNECTION_FLOW
            ],
            "concept_explanation": [
                AnimationType.TYPEWRITER,
                AnimationType.HIGHLIGHT,
                AnimationType.MORPH
            ],
            "comparison": [
                AnimationType.SLIDE_IN,
                AnimationType.HIGHLIGHT,
                AnimationType.PULSE
            ],
            "data_flow": [
                AnimationType.CONNECTION_FLOW,
                AnimationType.DATA_STREAM,
                AnimationType.PARTICLE
            ],
            "state_transition": [
                AnimationType.MORPH,
                AnimationType.FADE_IN,
                AnimationType.HIGHLIGHT
            ]
        }
    
    def _load_aws_components(self):
        """Load AWS-specific components."""
        aws_components = {
            "ec2": AnimationComponent(
                metadata=ComponentMetadata(
                    id="aws-ec2-instance",
                    name="EC2 Instance",
                    description="Elastic Compute Cloud virtual server",
                    provider=Provider.AWS,
                    type=ComponentType.SERVICE_CARD,
                    tags=["compute", "server", "virtual-machine"],
                    keywords=["ec2", "instance", "vm", "server"],
                    complexity=2,
                    render_time=0.8
                ),
                style=self.style_guides[Provider.AWS],
                animations=[AnimationType.FADE_IN, AnimationType.SCALE_IN, AnimationType.PULSE],
                manim_class="EC2Instance",
                manim_config={
                    "width": 2.0,
                    "height": 1.5,
                    "icon": "aws/ec2.svg",
                    "show_status": True
                }
            ),
            "s3": AnimationComponent(
                metadata=ComponentMetadata(
                    id="aws-s3-bucket",
                    name="S3 Bucket",
                    description="Simple Storage Service bucket",
                    provider=Provider.AWS,
                    type=ComponentType.SERVICE_CARD,
                    tags=["storage", "object-storage", "bucket"],
                    keywords=["s3", "storage", "bucket", "object"],
                    complexity=1,
                    render_time=0.6
                ),
                style=self.style_guides[Provider.AWS],
                animations=[AnimationType.FADE_IN, AnimationType.BOUNCE],
                manim_class="S3Bucket",
                manim_config={
                    "width": 1.8,
                    "height": 1.8,
                    "icon": "aws/s3.svg",
                    "show_objects": True
                }
            ),
            "rds": AnimationComponent(
                metadata=ComponentMetadata(
                    id="aws-rds-database",
                    name="RDS Database",
                    description="Relational Database Service",
                    provider=Provider.AWS,
                    type=ComponentType.SERVICE_CARD,
                    tags=["database", "sql", "relational"],
                    keywords=["rds", "database", "mysql", "postgres"],
                    complexity=3,
                    render_time=1.0
                ),
                style=self.style_guides[Provider.AWS],
                animations=[AnimationType.FADE_IN, AnimationType.ROTATE],
                manim_class="RDSDatabase",
                manim_config={
                    "width": 2.0,
                    "height": 2.0,
                    "icon": "aws/rds.svg",
                    "engine": "mysql"
                }
            ),
            "lambda": AnimationComponent(
                metadata=ComponentMetadata(
                    id="aws-lambda-function",
                    name="Lambda Function",
                    description="Serverless compute function",
                    provider=Provider.AWS,
                    type=ComponentType.SERVICE_CARD,
                    tags=["compute", "serverless", "function"],
                    keywords=["lambda", "function", "serverless", "faas"],
                    complexity=2,
                    render_time=0.7
                ),
                style=self.style_guides[Provider.AWS],
                animations=[AnimationType.FADE_IN, AnimationType.PULSE, AnimationType.GLOW],
                manim_class="LambdaFunction",
                manim_config={
                    "width": 1.5,
                    "height": 1.5,
                    "icon": "aws/lambda.svg",
                    "runtime": "python3.9"
                }
            ),
            "vpc": AnimationComponent(
                metadata=ComponentMetadata(
                    id="aws-vpc-network",
                    name="VPC Network",
                    description="Virtual Private Cloud network",
                    provider=Provider.AWS,
                    type=ComponentType.NETWORK_TOPOLOGY,
                    tags=["network", "vpc", "subnet"],
                    keywords=["vpc", "network", "subnet", "routing"],
                    complexity=4,
                    render_time=2.0
                ),
                style=self.style_guides[Provider.AWS],
                animations=[AnimationType.DRAW, AnimationType.CONNECTION_FLOW],
                manim_class="VPCNetwork",
                manim_config={
                    "width": 6.0,
                    "height": 4.0,
                    "show_subnets": True,
                    "show_routes": True
                }
            ),
            # Add more AWS components...
        }
        
        self.components[Provider.AWS] = aws_components
    
    def _load_azure_components(self):
        """Load Azure-specific components."""
        azure_components = {
            "vm": AnimationComponent(
                metadata=ComponentMetadata(
                    id="azure-virtual-machine",
                    name="Virtual Machine",
                    description="Azure Virtual Machine",
                    provider=Provider.AZURE,
                    type=ComponentType.SERVICE_CARD,
                    tags=["compute", "server", "virtual-machine"],
                    keywords=["vm", "virtual machine", "compute"],
                    complexity=2,
                    render_time=0.8
                ),
                style=self.style_guides[Provider.AZURE],
                animations=[AnimationType.FADE_IN, AnimationType.SCALE_IN],
                manim_class="AzureVM",
                manim_config={
                    "width": 2.0,
                    "height": 1.5,
                    "icon": "azure/vm.svg"
                }
            ),
            # Add more Azure components...
        }
        
        self.components[Provider.AZURE] = azure_components
    
    def _load_gcp_components(self):
        """Load GCP-specific components."""
        gcp_components = {
            "compute_engine": AnimationComponent(
                metadata=ComponentMetadata(
                    id="gcp-compute-engine",
                    name="Compute Engine",
                    description="Google Compute Engine VM",
                    provider=Provider.GCP,
                    type=ComponentType.SERVICE_CARD,
                    tags=["compute", "server", "virtual-machine"],
                    keywords=["gce", "compute engine", "vm"],
                    complexity=2,
                    render_time=0.8
                ),
                style=self.style_guides[Provider.GCP],
                animations=[AnimationType.FADE_IN, AnimationType.SLIDE_IN],
                manim_class="GCPComputeEngine",
                manim_config={
                    "width": 2.0,
                    "height": 1.5,
                    "icon": "gcp/compute_engine.svg"
                }
            ),
            # Add more GCP components...
        }
        
        self.components[Provider.GCP] = gcp_components
    
    def _load_generic_components(self):
        """Load generic components usable across providers."""
        generic_components = {
            "server": AnimationComponent(
                metadata=ComponentMetadata(
                    id="generic-server",
                    name="Generic Server",
                    description="Generic server component",
                    provider=Provider.GENERIC,
                    type=ComponentType.SERVICE_CARD,
                    tags=["compute", "server"],
                    keywords=["server", "compute", "machine"],
                    complexity=1,
                    render_time=0.5
                ),
                style=self.style_guides[Provider.GENERIC],
                animations=[AnimationType.FADE_IN],
                manim_class="GenericServer",
                manim_config={
                    "width": 2.0,
                    "height": 1.5,
                    "style": "modern"
                }
            ),
            "database": AnimationComponent(
                metadata=ComponentMetadata(
                    id="generic-database",
                    name="Generic Database",
                    description="Generic database component",
                    provider=Provider.GENERIC,
                    type=ComponentType.SERVICE_CARD,
                    tags=["database", "storage"],
                    keywords=["database", "db", "storage"],
                    complexity=1,
                    render_time=0.5
                ),
                style=self.style_guides[Provider.GENERIC],
                animations=[AnimationType.FADE_IN, AnimationType.ROTATE],
                manim_class="GenericDatabase",
                manim_config={
                    "width": 2.0,
                    "height": 2.0,
                    "style": "cylinder"
                }
            ),
            "user": AnimationComponent(
                metadata=ComponentMetadata(
                    id="generic-user",
                    name="User",
                    description="User/client representation",
                    provider=Provider.GENERIC,
                    type=ComponentType.SERVICE_CARD,
                    tags=["user", "client", "person"],
                    keywords=["user", "client", "person", "actor"],
                    complexity=1,
                    render_time=0.3
                ),
                style=self.style_guides[Provider.GENERIC],
                animations=[AnimationType.FADE_IN, AnimationType.BOUNCE],
                manim_class="UserIcon",
                manim_config={
                    "width": 1.5,
                    "height": 1.5,
                    "style": "modern"
                }
            ),
            "flow_arrow": AnimationComponent(
                metadata=ComponentMetadata(
                    id="generic-flow-arrow",
                    name="Flow Arrow",
                    description="Directional flow arrow",
                    provider=Provider.GENERIC,
                    type=ComponentType.FLOW_CHART,
                    tags=["arrow", "flow", "connection"],
                    keywords=["arrow", "flow", "direction", "connection"],
                    complexity=1,
                    render_time=0.2
                ),
                style=self.style_guides[Provider.GENERIC],
                animations=[AnimationType.DRAW, AnimationType.CONNECTION_FLOW],
                manim_class="FlowArrow",
                manim_config={
                    "arrow_style": "modern",
                    "animated": True
                }
            ),
            # Add more generic components...
        }
        
        self.components[Provider.GENERIC] = generic_components
    
    def get_component(
        self, 
        provider: Provider, 
        service: str,
        fallback_to_generic: bool = True
    ) -> Optional[AnimationComponent]:
        """
        Retrieve a component with optional fallback to generic.
        
        Args:
            provider: The cloud provider
            service: The service name
            fallback_to_generic: Whether to fallback to generic if not found
            
        Returns:
            The animation component or None if not found
        """
        # Try to get provider-specific component
        if provider in self.components and service in self.components[provider]:
            component = self.components[provider][service]
            component.metadata.usage_count += 1
            component.metadata.last_used = datetime.now()
            return component
        
        # Fallback to generic if enabled
        if fallback_to_generic:
            # Map common services to generic equivalents
            generic_mapping = {
                "ec2": "server",
                "vm": "server",
                "compute_engine": "server",
                "rds": "database",
                "sql_database": "database",
                "cloud_sql": "database",
                "s3": "storage",
                "blob_storage": "storage",
                "cloud_storage": "storage"
            }
            
            generic_service = generic_mapping.get(service, service)
            if generic_service in self.components.get(Provider.GENERIC, {}):
                component = self.components[Provider.GENERIC][generic_service]
                component.metadata.usage_count += 1
                component.metadata.last_used = datetime.now()
                logger.info(f"Using generic component '{generic_service}' as fallback for {provider}:{service}")
                return component
        
        logger.warning(f"Component not found: {provider}:{service}")
        return None
    
    def search_components(
        self,
        query: str,
        providers: Optional[List[Provider]] = None,
        types: Optional[List[ComponentType]] = None,
        max_results: int = 10
    ) -> List[AnimationComponent]:
        """
        Search for components by query, providers, and types.
        
        Args:
            query: Search query string
            providers: Filter by specific providers
            types: Filter by component types
            max_results: Maximum number of results
            
        Returns:
            List of matching components sorted by relevance
        """
        results = []
        query_lower = query.lower()
        
        # Search across all or specified providers
        search_providers = providers or list(self.components.keys())
        
        for provider in search_providers:
            if provider not in self.components:
                continue
                
            for service, component in self.components[provider].items():
                # Filter by type if specified
                if types and component.metadata.type not in types:
                    continue
                
                # Calculate relevance score
                score = 0.0
                
                # Check name
                if query_lower in component.metadata.name.lower():
                    score += 1.0
                
                # Check description
                if query_lower in component.metadata.description.lower():
                    score += 0.7
                
                # Check tags
                for tag in component.metadata.tags:
                    if query_lower in tag.lower():
                        score += 0.5
                
                # Check keywords
                for keyword in component.metadata.keywords:
                    if query_lower in keyword.lower():
                        score += 0.8
                
                if score > 0:
                    results.append((score, component))
        
        # Sort by relevance and quality
        results.sort(key=lambda x: (x[0], x[1].metadata.quality_score), reverse=True)
        
        # Return top results
        return [component for _, component in results[:max_results]]
    
    def get_animation_pattern(self, pattern_name: str) -> List[AnimationType]:
        """
        Get a predefined animation pattern.
        
        Args:
            pattern_name: Name of the animation pattern
            
        Returns:
            List of animation types in the pattern
        """
        return self.animation_patterns.get(pattern_name, [AnimationType.FADE_IN])
    
    def select_optimal_components(
        self,
        concept: Dict[str, Any],
        max_components: int = 5
    ) -> List[AnimationComponent]:
        """
        Select optimal components for visualizing a concept.
        
        Args:
            concept: The concept to visualize
            max_components: Maximum number of components to select
            
        Returns:
            List of selected components
        """
        selected = []
        
        # Extract concept details
        concept_name = concept.get("name", "")
        concept_type = concept.get("type", "")
        provider = concept.get("provider", Provider.GENERIC)
        tags = concept.get("tags", [])
        
        # Search for relevant components
        all_components = []
        for comp_provider in self.components:
            for service, component in self.components[comp_provider].items():
                score = self._calculate_relevance_score(
                    component, concept_name, concept_type, provider, tags
                )
                if score > 0:
                    all_components.append((score, component))
        
        # Sort by score and quality
        all_components.sort(
            key=lambda x: (x[0], x[1].metadata.quality_score), 
            reverse=True
        )
        
        # Select diverse components
        selected_types = set()
        for score, component in all_components:
            # Ensure variety in component types
            if component.metadata.type not in selected_types or score > 0.8:
                selected.append(component)
                selected_types.add(component.metadata.type)
                
                if len(selected) >= max_components:
                    break
        
        return selected
    
    def _calculate_relevance_score(
        self,
        component: AnimationComponent,
        concept_name: str,
        concept_type: str,
        provider: Provider,
        tags: List[str]
    ) -> float:
        """Calculate relevance score between component and concept."""
        score = 0.0
        
        # Provider matching
        if component.metadata.provider == provider:
            score += 0.3
        elif component.metadata.provider == Provider.GENERIC:
            score += 0.1
        
        # Name similarity
        if concept_name.lower() in component.metadata.name.lower():
            score += 0.4
        
        # Type matching
        if concept_type and concept_type.lower() in str(component.metadata.type.value):
            score += 0.3
        
        # Tag matching
        component_tags = set(component.metadata.tags)
        concept_tags = set(tags)
        if component_tags & concept_tags:
            score += 0.2 * len(component_tags & concept_tags) / len(concept_tags)
        
        # Keyword matching
        for keyword in component.metadata.keywords:
            if keyword.lower() in concept_name.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def create_custom_component(
        self,
        name: str,
        description: str,
        provider: Provider,
        component_type: ComponentType,
        manim_class: str,
        **kwargs
    ) -> AnimationComponent:
        """
        Create a custom component and add it to the library.
        
        Args:
            name: Component name
            description: Component description
            provider: Provider category
            component_type: Type of component
            manim_class: Manim class name
            **kwargs: Additional component configuration
            
        Returns:
            The created component
        """
        # Generate unique ID
        component_id = f"{provider.value}-{name.lower().replace(' ', '-')}"
        component_id = hashlib.md5(component_id.encode()).hexdigest()[:8]
        
        # Create metadata
        metadata = ComponentMetadata(
            id=component_id,
            name=name,
            description=description,
            provider=provider,
            type=component_type,
            tags=kwargs.get("tags", []),
            keywords=kwargs.get("keywords", []),
            complexity=kwargs.get("complexity", 2),
            render_time=kwargs.get("render_time", 1.0)
        )
        
        # Create component
        component = AnimationComponent(
            metadata=metadata,
            style=kwargs.get("style", self.style_guides.get(provider, ComponentStyle())),
            animations=kwargs.get("animations", [AnimationType.FADE_IN]),
            manim_class=manim_class,
            manim_config=kwargs.get("manim_config", {})
        )
        
        # Add to library
        if provider not in self.components:
            self.components[provider] = {}
        
        service_key = name.lower().replace(" ", "_")
        self.components[provider][service_key] = component
        
        logger.info(f"Created custom component: {provider}:{service_key}")
        
        return component
    
    def export_component_catalog(self, output_path: Path) -> None:
        """Export component catalog to JSON file."""
        catalog = {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "total_components": self._count_components(),
            "providers": {}
        }
        
        for provider, components in self.components.items():
            catalog["providers"][provider.value] = {
                "total": len(components),
                "components": {
                    service: {
                        "id": comp.metadata.id,
                        "name": comp.metadata.name,
                        "description": comp.metadata.description,
                        "type": comp.metadata.type.value,
                        "tags": comp.metadata.tags,
                        "complexity": comp.metadata.complexity,
                        "quality_score": comp.metadata.quality_score
                    }
                    for service, comp in components.items()
                }
            }
        
        with open(output_path, "w") as f:
            json.dump(catalog, f, indent=2)
        
        logger.info(f"Exported component catalog to {output_path}")
    
    def _count_components(self) -> int:
        """Count total number of components in library."""
        return sum(len(components) for components in self.components.values())
    
    async def generate_component_preview(
        self,
        component: AnimationComponent,
        output_path: Path
    ) -> None:
        """
        Generate a preview image for a component.
        
        Args:
            component: The component to preview
            output_path: Path to save the preview image
        """
        # This would integrate with Manim to generate actual preview
        # For now, we'll create a placeholder
        logger.info(f"Generating preview for {component.metadata.name} at {output_path}")
        
        # TODO: Implement actual Manim preview generation
        pass


# Animation pattern functions
class AnimationPatterns:
    """Reusable animation patterns for consistent animations."""
    
    @staticmethod
    def service_introduction(
        component: AnimationComponent,
        duration: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Pattern for introducing a new service."""
        return [
            {
                "type": AnimationType.FADE_IN,
                "duration": duration * 0.3,
                "params": {"start_opacity": 0, "end_opacity": 1}
            },
            {
                "type": AnimationType.SCALE_IN,
                "duration": duration * 0.3,
                "params": {"start_scale": 0.8, "end_scale": 1.0}
            },
            {
                "type": AnimationType.GLOW,
                "duration": duration * 0.4,
                "params": {"intensity": 0.5, "color": component.style.accent_color}
            }
        ]
    
    @staticmethod
    def architecture_reveal(
        components: List[AnimationComponent],
        total_duration: float = 5.0
    ) -> List[Dict[str, Any]]:
        """Pattern for revealing architecture layer by layer."""
        animations = []
        delay_per_component = total_duration / len(components)
        
        for i, component in enumerate(components):
            delay = i * delay_per_component
            animations.extend([
                {
                    "component": component,
                    "type": AnimationType.FADE_IN,
                    "duration": delay_per_component * 0.5,
                    "delay": delay,
                    "params": {"start_opacity": 0, "end_opacity": 1}
                },
                {
                    "component": component,
                    "type": AnimationType.CONNECTION_FLOW,
                    "duration": delay_per_component * 0.5,
                    "delay": delay + delay_per_component * 0.5,
                    "params": {"flow_speed": 0.5}
                }
            ])
        
        return animations
    
    @staticmethod
    def concept_deep_dive(
        concept_component: AnimationComponent,
        detail_components: List[AnimationComponent],
        total_duration: float = 4.0
    ) -> List[Dict[str, Any]]:
        """Pattern for explaining complex concepts."""
        animations = [
            # Title introduction
            {
                "component": concept_component,
                "type": AnimationType.TYPEWRITER,
                "duration": total_duration * 0.25,
                "params": {"speed": 0.05}
            }
        ]
        
        # Detail components appear
        for i, detail in enumerate(detail_components):
            animations.append({
                "component": detail,
                "type": AnimationType.MORPH,
                "duration": total_duration * 0.15,
                "delay": total_duration * 0.25 + i * 0.1,
                "params": {"morph_type": "smooth"}
            })
        
        # Highlight key points
        animations.append({
            "type": AnimationType.HIGHLIGHT,
            "duration": total_duration * 0.2,
            "delay": total_duration * 0.8,
            "params": {"highlight_color": concept_component.style.accent_color}
        })
        
        return animations
    
    @staticmethod
    def comparison_animation(
        components: List[AnimationComponent],
        duration: float = 3.0
    ) -> List[Dict[str, Any]]:
        """Pattern for comparing multiple components."""
        animations = []
        
        # Slide in from sides
        for i, component in enumerate(components):
            side = "left" if i % 2 == 0 else "right"
            animations.append({
                "component": component,
                "type": AnimationType.SLIDE_IN,
                "duration": duration * 0.3,
                "delay": i * 0.1,
                "params": {"direction": side}
            })
        
        # Highlight differences
        animations.append({
            "type": AnimationType.HIGHLIGHT,
            "duration": duration * 0.4,
            "delay": duration * 0.4,
            "params": {"highlight_differences": True}
        })
        
        return animations


# Export main classes
__all__ = [
    "ComponentLibrary",
    "AnimationComponent",
    "ComponentMetadata",
    "ComponentStyle",
    "AnimationParameters",
    "AnimationPatterns",
    "ComponentType",
    "Provider",
    "AnimationType"
]
