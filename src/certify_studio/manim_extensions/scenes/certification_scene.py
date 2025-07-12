        """
        Add audio description for accessibility.
        
        Args:
            description: Description text
            timestamp: When to play (None for current time)
            priority: Priority level (low, normal, high)
        """
        if not self.enable_accessibility:
            return
            
        audio_desc = {
            "text": description,
            "timestamp": timestamp or self.renderer.time,
            "priority": priority,
            "type": "description"
        }
        self.audio_descriptions.append(audio_desc)
        
    def add_caption(self, 
                   text: str, 
                   start_time: float, 
                   end_time: float,
                   position: str = "bottom"):
        """
        Add closed caption.
        
        Args:
            text: Caption text
            start_time: Start time in seconds
            end_time: End time in seconds
            position: Caption position (top, bottom, center)
        """
        if not self.enable_accessibility:
            return
            
        caption = {
            "text": text,
            "start_time": start_time,
            "end_time": end_time,
            "position": position,
            "style": self.theme.caption_style
        }
        self.captions.append(caption)
        
    def add_tooltip(self, target_object: Mobject, tooltip_text: str):
        """
        Add hover tooltip to object.
        
        Args:
            target_object: Object to attach tooltip to
            tooltip_text: Tooltip text content
        """
        if not self.enable_interactivity:
            return
            
        tooltip = self._create_tooltip(tooltip_text)
        tooltip.next_to(target_object, UP, buff=0.1)
        tooltip.set_opacity(0)  # Hidden by default
        
        self.tooltips[target_object] = tooltip
        
    def _create_tooltip(self, text: str) -> VGroup:
        """Create styled tooltip element."""
        tooltip_group = VGroup()
        
        # Background
        bg = Rectangle(
            width=len(text) * 0.15 + 0.5,
            height=0.6,
            fill_color=self.color_scheme["background"],
            stroke_color=self.color_scheme["border"],
            fill_opacity=0.95,
            stroke_width=1
        )
        
        # Text
        tooltip_text = Text(
            text,
            font_size=16,
            color=self.color_scheme["text"]
        )
        tooltip_text.move_to(bg.get_center())
        
        tooltip_group.add(bg, tooltip_text)
        return tooltip_group
        
    def create_architecture_diagram(self, 
                                  components: List[Dict],
                                  connections: List[Dict] = None) -> VGroup:
        """
        Create architecture diagram from component specification.
        
        Args:
            components: List of component specifications
            connections: List of connection specifications
            
        Returns:
            VGroup containing the complete diagram
        """
        diagram = VGroup()
        component_objects = {}
        
        # Create components
        for comp in components:
            comp_obj = self._create_component(comp)
            component_objects[comp["id"]] = comp_obj
            diagram.add(comp_obj)
            
        # Create connections
        if connections:
            for conn in connections:
                source = component_objects[conn["source"]]
                target = component_objects[conn["target"]]
                flow = self.create_connection_flow(
                    source, target, 
                    conn.get("type", "default"),
                    conn.get("animated", True)
                )
                diagram.add(flow)
                
        # Apply layout
        self._apply_diagram_layout(diagram, component_objects)
        
        return diagram
        
    def _create_component(self, spec: Dict) -> VGroup:
        """Create component from specification."""
        comp_type = spec.get("type", "service")
        
        if comp_type == "service":
            return self.create_service_icon(
                spec["service"], 
                spec.get("label")
            )
        elif comp_type == "group":
            return self._create_component_group(spec)
        elif comp_type == "vpc":
            return self._create_vpc_boundary(spec)
        else:
            # Generic rectangle for unknown types
            return Rectangle(
                width=2, height=1,
                stroke_color=self.color_scheme["border"],
                fill_opacity=0.1
            )
            
    def _create_component_group(self, spec: Dict) -> VGroup:
        """Create component group (e.g., availability zone)."""
        group = VGroup()
        
        # Group boundary
        boundary = Rectangle(
            width=spec.get("width", 4),
            height=spec.get("height", 3),
            stroke_color=self.color_scheme["border"],
            fill_color=self.color_scheme["background"],
            fill_opacity=0.1,
            stroke_width=2
        )
        group.add(boundary)
        
        # Group label
        if "label" in spec:
            label = Text(
                spec["label"],
                font_size=TEXT_STYLES["caption"]["font_size"],
                color=self.color_scheme["text"]
            )
            label.move_to(boundary.get_top() + DOWN * 0.3)
            group.add(label)
            
        return group
        
    def _create_vpc_boundary(self, spec: Dict) -> VGroup:
        """Create VPC boundary with AWS styling."""
        vpc = VGroup()
        
        # VPC boundary
        boundary = Rectangle(
            width=spec.get("width", 10),
            height=spec.get("height", 6),
            stroke_color=self.color_scheme.get("vpc_blue", BLUE),
            stroke_width=3,
            fill_opacity=0.05
        )
        vpc.add(boundary)
        
        # VPC label
        vpc_label = Text(
            f"VPC ({spec.get('cidr', '10.0.0.0/16')})",
            font_size=20,
            color=self.color_scheme.get("vpc_blue", BLUE)
        )
        vpc_label.move_to(boundary.get_top() + DOWN * 0.4)
        vpc.add(vpc_label)
        
        return vpc
        
    def _apply_diagram_layout(self, diagram: VGroup, components: Dict):
        """Apply automatic layout to diagram components."""
        # This would integrate with the layout engine
        # For now, simple arrangement
        if len(components) > 1:
            diagram.arrange(RIGHT, buff=LAYOUT_CONFIG["spacing"])
            
    def add_learning_objective(self, objective: str):
        """
        Add learning objective to scene metadata.
        
        Args:
            objective: Learning objective description
        """
        if "learning_objectives" not in self.metadata:
            self.metadata["learning_objectives"] = []
        self.metadata["learning_objectives"].append(objective)
        
    def add_key_concept(self, concept: str, definition: str):
        """
        Add key concept definition.
        
        Args:
            concept: Concept name
            definition: Concept definition
        """
        if "key_concepts" not in self.metadata:
            self.metadata["key_concepts"] = {}
        self.metadata["key_concepts"][concept] = definition
        
    def update_quality_metrics(self):
        """Update quality control metrics."""
        self.quality_metrics.update({
            "animations_count": len(self.animations),
            "objects_count": len(self.mobjects),
            "render_time": (datetime.now() - self.quality_metrics["start_time"]).total_seconds()
        })
        
        # Calculate accessibility score
        if self.enable_accessibility:
            score = 0.0
            if self.audio_descriptions:
                score += 0.3
            if self.captions:
                score += 0.3
            if self.tooltips:
                score += 0.2
            # Add more accessibility checks
            self.quality_metrics["accessibility_score"] = min(score, 1.0)
            
    def export_metadata(self) -> Dict[str, Any]:
        """
        Export scene metadata for quality control and documentation.
        
        Returns:
            Dictionary containing scene metadata
        """
        self.update_quality_metrics()
        
        return {
            **self.metadata,
            "quality_metrics": self.quality_metrics,
            "accessibility_features": {
                "audio_descriptions": len(self.audio_descriptions),
                "captions": len(self.captions),
                "tooltips": len(self.tooltips),
                "enabled": self.enable_accessibility
            },
            "interactive_features": {
                "clickable_regions": len(self.clickable_regions),
                "quiz_elements": len(self.quiz_elements),
                "enabled": self.enable_interactivity
            },
            "export_formats": self.export_formats
        }
        
    def save_metadata(self, filepath: str):
        """
        Save scene metadata to file.
        
        Args:
            filepath: Path to save metadata JSON
        """
        metadata = self.export_metadata()
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
            
    def construct(self):
        """
        Main scene construction method.
        Override this method in subclasses to create content.
        """
        # Default implementation creates a title slide
        title = self.create_title_slide(
            f"{self.provider.value.upper()} {self.certification}",
            f"{self.domain} - {self.concept}"
        )
        
        self.play(FadeIn(title))
        self.wait(2)
        
        # Add completion tracking
        self.add_audio_description(
            f"Completed {self.concept} overview for {self.certification}",
            priority="low"
        )
