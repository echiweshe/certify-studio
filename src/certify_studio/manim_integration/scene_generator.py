"""
Manim scene generator that converts agent output to Manim scenes.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json

from manim import *
from ..core.logging import get_logger
from ..agents.content.animation_choreography_agent import AnimationScene, AnimationElement
from ..agents.content.diagram_generation.models import Diagram, DiagramElement, DiagramEdge

logger = get_logger(__name__)


class AgentGeneratedScene(Scene):
    """Base scene class for agent-generated content."""
    
    def __init__(self, scene_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.scene_data = scene_data
        self.mobjects_map = {}
        self.animation_queue = []
    
    def construct(self):
        """Construct the scene from agent data."""
        
        scene_type = self.scene_data.get("type", "animation")
        
        if scene_type == "animation":
            self.construct_animation_scene()
        elif scene_type == "diagram":
            self.construct_diagram_scene()
        else:
            logger.warning(f"Unknown scene type: {scene_type}")
    
    def construct_animation_scene(self):
        """Construct scene from animation agent output."""
        
        content = self.scene_data.get("content", {})
        if "scenes" in content:
            # Multiple scenes in animation
            for scene_spec in content["scenes"]:
                self.render_animation_scene(scene_spec)
        else:
            # Single scene
            self.render_animation_scene(content)
    
    def construct_diagram_scene(self):
        """Construct scene from diagram agent output."""
        
        diagram_data = self.scene_data.get("content", {}).get("diagram", {})
        self.render_diagram(diagram_data)
    
    def render_animation_scene(self, scene_spec: Dict[str, Any]):
        """Render a single animation scene."""
        
        # Create elements
        for element_data in scene_spec.get("elements", []):
            mobject = self.create_element(element_data)
            if mobject:
                self.mobjects_map[element_data["id"]] = mobject
        
        # Apply animations based on timing
        elements_by_time = sorted(
            scene_spec.get("elements", []),
            key=lambda e: e.get("timing", {}).get("start", 0)
        )
        
        current_time = 0
        animations_to_play = []
        
        for element_data in elements_by_time:
            start_time = element_data.get("timing", {}).get("start", 0)
            
            # Wait if needed
            if start_time > current_time:
                if animations_to_play:
                    self.play(*animations_to_play)
                    animations_to_play = []
                self.wait(start_time - current_time)
                current_time = start_time
            
            # Create animations for this element
            element_id = element_data["id"]
            if element_id in self.mobjects_map:
                mobject = self.mobjects_map[element_id]
                
                # Enter animation
                enter_anim = self.create_animation(
                    mobject,
                    element_data.get("animations", {}).get("enter", {})
                )
                if enter_anim:
                    animations_to_play.append(enter_anim)
        
        # Play remaining animations
        if animations_to_play:
            self.play(*animations_to_play)
        
        # Handle exit animations
        self.handle_exit_animations(scene_spec.get("elements", []))
    
    def create_element(self, element_data: Dict[str, Any]) -> Optional[Mobject]:
        """Create a Manim mobject from element data."""
        
        element_type = element_data.get("type", "default_node")
        properties = element_data.get("properties", {})
        
        if element_type == "text":
            return self.create_text_element(properties)
        elif element_type == "shape":
            return self.create_shape_element(properties)
        elif element_type == "composite":
            return self.create_composite_element(properties)
        elif element_type == "particle":
            return self.create_particle_element(properties)
        elif element_type == "line":
            return self.create_line_element(properties)
        elif "node" in element_type:
            return self.create_node_element(element_data)
        else:
            logger.warning(f"Unknown element type: {element_type}")
            return None
    
    def create_text_element(self, properties: Dict[str, Any]) -> Text:
        """Create text element."""
        
        text = Text(
            properties.get("content", ""),
            font_size=properties.get("font_size", 24),
            color=properties.get("color", WHITE)
        )
        
        # Position
        pos = properties.get("position", {"x": 0.5, "y": 0.5})
        text.move_to(self.relative_to_absolute(pos))
        
        return text
    
    def create_shape_element(self, properties: Dict[str, Any]) -> Mobject:
        """Create shape element."""
        
        shape_type = properties.get("shape", "circle")
        
        if shape_type == "circle":
            shape = Circle(
                radius=properties.get("radius", 0.5),
                color=properties.get("color", BLUE),
                fill_opacity=0.7 if properties.get("color") else 0
            )
        elif shape_type == "square":
            shape = Square(
                side_length=properties.get("size", 1),
                color=properties.get("color", BLUE),
                fill_opacity=0.7 if properties.get("color") else 0
            )
        elif shape_type == "rounded_rect":
            shape = RoundedRectangle(
                width=properties.get("width", 2),
                height=properties.get("height", 1),
                corner_radius=0.1,
                color=properties.get("color", BLUE),
                fill_opacity=0.7 if properties.get("color") else 0
            )
        else:
            shape = Dot(color=properties.get("color", BLUE))
        
        # Position
        pos = properties.get("position", {"x": 0.5, "y": 0.5})
        shape.move_to(self.relative_to_absolute(pos))
        
        # Add label if provided
        if "label" in properties:
            label = Text(properties["label"], font_size=16, color=WHITE)
            label.move_to(shape.get_center())
            return VGroup(shape, label)
        
        return shape
    
    def create_composite_element(self, properties: Dict[str, Any]) -> VGroup:
        """Create composite element with multiple components."""
        
        group = VGroup()
        
        for component in properties.get("components", []):
            if component["type"] == "shape":
                element = self.create_shape_element(component)
            elif component["type"] == "text":
                element = self.create_text_element(component)
            elif component["type"] == "icon":
                # For now, create a simple shape as placeholder
                element = self.create_icon_placeholder(component)
            else:
                continue
            
            if element:
                group.add(element)
        
        return group
    
    def create_icon_placeholder(self, properties: Dict[str, Any]) -> Mobject:
        """Create icon placeholder."""
        
        icon_name = properties.get("name", "default")
        icon_map = {
            "server": Square,
            "database": Circle,
            "shield": Triangle,
            "network": Dot
        }
        
        IconClass = icon_map.get(icon_name, Square)
        icon = IconClass(color=BLUE, fill_opacity=0.7)
        icon.scale(0.3)
        
        pos = properties.get("position", {"x": 0.5, "y": 0.5})
        icon.move_to(self.relative_to_absolute(pos))
        
        return icon
    
    def create_particle_element(self, properties: Dict[str, Any]) -> Dot:
        """Create particle element."""
        
        particle = Dot(
            radius=properties.get("size", 0.05),
            color=properties.get("color", BLUE)
        )
        
        # Initial position
        path = properties.get("path", {})
        if "points" in path and path["points"]:
            start_pos = path["points"][0]
            particle.move_to(self.relative_to_absolute(start_pos))
        
        return particle
    
    def create_line_element(self, properties: Dict[str, Any]) -> Line:
        """Create line element."""
        
        start = properties.get("start", {"x": 0, "y": 0})
        end = properties.get("end", {"x": 1, "y": 1})
        
        line = Line(
            start=self.relative_to_absolute(start),
            end=self.relative_to_absolute(end),
            color=properties.get("color", WHITE),
            stroke_width=properties.get("width", 2)
        )
        
        return line
    
    def create_node_element(self, element_data: Dict[str, Any]) -> VGroup:
        """Create node element for diagrams."""
        
        properties = element_data.get("properties", {})
        style = element_data.get("style", {})
        
        # Create shape based on node type
        shape = RoundedRectangle(
            width=properties.get("size", {}).get("width", 2) * 10,
            height=properties.get("size", {}).get("height", 1) * 10,
            corner_radius=0.2,
            color=style.get("stroke", BLUE),
            fill_color=style.get("fill", BLUE),
            fill_opacity=0.7,
            stroke_width=style.get("stroke_width", 2)
        )
        
        # Add label
        label = Text(
            properties.get("label", ""),
            font_size=20,
            color=WHITE
        )
        label.move_to(shape.get_center())
        
        # Position
        pos = properties.get("position", {"x": 0.5, "y": 0.5})
        node = VGroup(shape, label)
        node.move_to(self.relative_to_absolute(pos))
        
        return node
    
    def create_animation(
        self,
        mobject: Mobject,
        anim_spec: Dict[str, Any]
    ) -> Optional[Animation]:
        """Create animation from specification."""
        
        anim_type = anim_spec.get("type", "fade")
        duration = anim_spec.get("duration", 1.0)
        
        if anim_type == "fade":
            return FadeIn(mobject, run_time=duration)
        elif anim_type == "fade_scale":
            return FadeIn(mobject, scale=anim_spec.get("from", {}).get("scale", 0.8), run_time=duration)
        elif anim_type == "grow":
            return GrowFromCenter(mobject, run_time=duration)
        elif anim_type == "slide_fade":
            from_x = anim_spec.get("from", {}).get("x", -1)
            return FadeIn(mobject, shift=RIGHT * from_x * 5, run_time=duration)
        elif anim_type == "draw":
            return Create(mobject, run_time=duration)
        elif anim_type == "draw_line":
            return Create(mobject, run_time=duration)
        elif anim_type == "path_follow":
            # This would need custom implementation
            return FadeIn(mobject, run_time=duration)
        else:
            return FadeIn(mobject, run_time=duration)
    
    def handle_exit_animations(self, elements: List[Dict[str, Any]]):
        """Handle exit animations for elements."""
        
        exit_anims = []
        
        for element_data in elements:
            element_id = element_data["id"]
            if element_id in self.mobjects_map:
                mobject = self.mobjects_map[element_id]
                exit_spec = element_data.get("animations", {}).get("exit", {})
                
                if exit_spec:
                    if exit_spec.get("type") == "fade":
                        exit_anims.append(FadeOut(mobject))
                    elif exit_spec.get("type") == "shrink_fade":
                        exit_anims.append(FadeOut(mobject, scale=0.5))
        
        if exit_anims:
            self.play(*exit_anims)
    
    def render_diagram(self, diagram_data: Dict[str, Any]):
        """Render diagram from agent output."""
        
        # Create all elements
        elements = diagram_data.get("elements", {})
        for element_id, element_data in elements.items():
            mobject = self.create_node_element(element_data)
            if mobject:
                self.mobjects_map[element_id] = mobject
                self.add(mobject)
        
        # Create edges
        edges = diagram_data.get("edges", [])
        for edge_data in edges:
            edge = self.create_edge(edge_data)
            if edge:
                self.add(edge)
        
        # Animate appearance
        all_mobjects = list(self.mobjects_map.values())
        if all_mobjects:
            self.play(*[FadeIn(mob) for mob in all_mobjects])
        
        # Add annotations
        annotations = diagram_data.get("annotations", [])
        for ann_data in annotations:
            self.add_annotation(ann_data)
        
        # Wait for viewing
        self.wait(self.scene_data.get("duration", 3))
    
    def create_edge(self, edge_data: Dict[str, Any]) -> Optional[Mobject]:
        """Create edge between nodes."""
        
        source_id = edge_data.get("source")
        target_id = edge_data.get("target")
        
        if source_id not in self.mobjects_map or target_id not in self.mobjects_map:
            return None
        
        source = self.mobjects_map[source_id]
        target = self.mobjects_map[target_id]
        
        # Create arrow or line
        style = edge_data.get("style", {})
        
        if style.get("arrow", False):
            edge = Arrow(
                start=source.get_center(),
                end=target.get_center(),
                color=style.get("stroke", GRAY),
                stroke_width=style.get("stroke_width", 2),
                buff=0.1
            )
        else:
            edge = Line(
                start=source.get_center(),
                end=target.get_center(),
                color=style.get("stroke", GRAY),
                stroke_width=style.get("stroke_width", 2)
            )
        
        # Add label if present
        if edge_data.get("label"):
            label = Text(edge_data["label"], font_size=14, color=GRAY)
            label.move_to(edge.get_center())
            return VGroup(edge, label)
        
        return edge
    
    def add_annotation(self, ann_data: Dict[str, Any]):
        """Add annotation to scene."""
        
        ann_type = ann_data.get("type")
        
        if ann_type == "title":
            title = Text(
                ann_data.get("content", ""),
                font_size=ann_data.get("style", {}).get("font_size", 36),
                color=WHITE
            )
            title.to_edge(UP)
            self.play(Write(title))
        
        elif ann_type == "legend":
            # Create simple legend
            legend_items = VGroup()
            for i, item in enumerate(ann_data.get("items", [])):
                item_text = Text(
                    f"• {item.get('label', '')}",
                    font_size=16,
                    color=GRAY_B
                )
                item_text.shift(DOWN * i * 0.5)
                legend_items.add(item_text)
            
            legend_items.to_edge(RIGHT).shift(UP)
            self.play(FadeIn(legend_items))
    
    def relative_to_absolute(self, pos: Dict[str, float]) -> np.ndarray:
        """Convert relative position (0-1) to absolute scene coordinates."""
        
        x = (pos.get("x", 0.5) - 0.5) * config.frame_width
        y = (pos.get("y", 0.5) - 0.5) * config.frame_height
        return np.array([x, y, 0])


class ManimSceneGenerator:
    """Generator that creates Manim scenes from agent output."""
    
    def __init__(self):
        self.scene_cache = {}
    
    def generate_scene_file(
        self,
        scene_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate a Python file containing the Manim scene."""
        
        scene_id = scene_data.get("id", "generated_scene")
        scene_class_name = f"Scene_{scene_id}".replace("-", "_")
        
        # Create scene file content
        scene_content = f'''
"""
Auto-generated Manim scene from agent output.
Generated at: 2024-01-20T10:00:00Z
"""

from manim import *
import json

# Scene data embedded
SCENE_DATA = {json.dumps(scene_data, indent=4)}

class {scene_class_name}(Scene):
    """Generated scene: {scene_data.get("title", "Untitled")}"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scene_data = SCENE_DATA
        self.mobjects_map = {{}}
    
    def construct(self):
        """Construct the scene."""
        # Scene construction logic would go here
        # This is a simplified version
        
        title = Text(self.scene_data.get("title", "Generated Scene"))
        self.play(Write(title))
        self.wait(2)
        self.play(FadeOut(title))

if __name__ == "__main__":
    from manim import config
    config.quality = "high_quality"
    scene = {scene_class_name}()
    scene.render()
'''
        
        # Write scene file
        scene_file = output_path / f"{scene_class_name}.py"
        scene_file.write_text(scene_content)
        
        logger.info(f"Generated scene file: {scene_file}")
        return scene_file
    
    def create_scene_instance(
        self,
        scene_data: Dict[str, Any]
    ) -> AgentGeneratedScene:
        """Create a scene instance from agent data."""
        
        return AgentGeneratedScene(scene_data)
    
    def render_scenes(
        self,
        scenes_data: List[Dict[str, Any]],
        output_dir: Path,
        quality: str = "high_quality"
    ) -> List[Path]:
        """Render multiple scenes."""
        
        rendered_files = []
        
        for i, scene_data in enumerate(scenes_data):
            logger.info(f"Rendering scene {i+1}/{len(scenes_data)}")
            
            # Configure Manim
            config.quality = quality
            config.output_file = f"scene_{i:03d}"
            
            # Create and render scene
            scene = self.create_scene_instance(scene_data)
            scene.render()
            
            # Get output file
            output_file = self._get_latest_output_file(output_dir)
            if output_file:
                rendered_files.append(output_file)
        
        return rendered_files
    
    def _get_latest_output_file(self, output_dir: Path) -> Optional[Path]:
        """Get the most recently created output file."""
        
        # This would check Manim's output directory
        # For now, return a placeholder
        return output_dir / "rendered_scene.mp4"
