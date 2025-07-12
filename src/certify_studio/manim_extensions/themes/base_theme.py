        """Create styled caption text."""
        style = self.get_text_style("caption", **kwargs)
        return Text(text, **style)
        
    def create_code_text(self, text: str, **kwargs) -> Text:
        """Create styled code text."""
        style = self.get_text_style("code", **kwargs)
        return Text(text, **style)
        
    def create_service_box(self, 
                          width: float = 2.0, 
                          height: float = 1.0,
                          service_category: str = "compute",
                          **kwargs) -> Rectangle:
        """
        Create styled service box.
        
        Args:
            width: Box width
            height: Box height
            service_category: Service category for coloring
            **kwargs: Additional Rectangle parameters
            
        Returns:
            Styled Rectangle object
        """
        color = self.get_service_color(service_category)
        
        defaults = {
            "width": width,
            "height": height,
            "stroke_color": color,
            "fill_color": color,
            "fill_opacity": 0.1,
            "stroke_width": 2
        }
        defaults.update(kwargs)
        
        return Rectangle(**defaults)
        
    def create_connection_line(self,
                              start_point: np.ndarray,
                              end_point: np.ndarray,
                              connection_type: str = "default",
                              **kwargs) -> Line:
        """
        Create styled connection line.
        
        Args:
            start_point: Starting point
            end_point: Ending point
            connection_type: Type of connection for styling
            **kwargs: Additional Line parameters
            
        Returns:
            Styled Line object
        """
        connection_colors = {
            "secure": self.colors.success,
            "database": self.colors.info,
            "storage": self.colors.accent,
            "network": self.colors.warning,
            "default": self.colors.border
        }
        
        color = connection_colors.get(connection_type, connection_colors["default"])
        
        defaults = {
            "start": start_point,
            "end": end_point,
            "stroke_color": color,
            "stroke_width": 3
        }
        defaults.update(kwargs)
        
        return Line(**defaults)
        
    def create_group_boundary(self,
                             width: float = 6.0,
                             height: float = 4.0,
                             boundary_type: str = "vpc",
                             **kwargs) -> Rectangle:
        """
        Create styled group boundary (VPC, subnet, etc.).
        
        Args:
            width: Boundary width
            height: Boundary height
            boundary_type: Type of boundary
            **kwargs: Additional Rectangle parameters
            
        Returns:
            Styled Rectangle object
        """
        boundary_styles = {
            "vpc": {
                "stroke_color": self.get_service_color("networking"),
                "stroke_width": 3,
                "fill_opacity": 0.05
            },
            "subnet": {
                "stroke_color": self.colors.accent,
                "stroke_width": 2,
                "fill_opacity": 0.1
            },
            "security_group": {
                "stroke_color": self.colors.error,
                "stroke_width": 2,
                "stroke_dasharray": [5, 5],
                "fill_opacity": 0.05
            },
            "availability_zone": {
                "stroke_color": self.colors.border,
                "stroke_width": 1,
                "fill_opacity": 0.02
            }
        }
        
        style = boundary_styles.get(boundary_type, boundary_styles["vpc"])
        
        defaults = {
            "width": width,
            "height": height,
            **style
        }
        defaults.update(kwargs)
        
        return Rectangle(**defaults)
        
    def create_focus_indicator(self, target_object: Mobject) -> Rectangle:
        """
        Create accessibility focus indicator.
        
        Args:
            target_object: Object to indicate focus for
            
        Returns:
            Focus indicator rectangle
        """
        # Get bounding box of target
        bounds = target_object.get_bounding_box()
        width = bounds[1][0] - bounds[0][0] + 0.2
        height = bounds[2][1] - bounds[0][1] + 0.2
        
        focus_indicator = Rectangle(
            width=width,
            height=height,
            stroke_color=self.colors.primary,
            stroke_width=self.accessibility.focus_indicator_width,
            fill_opacity=0
        )
        focus_indicator.move_to(target_object.get_center())
        
        return focus_indicator
        
    def create_tooltip_background(self, text_width: float, text_height: float) -> VGroup:
        """
        Create tooltip background with pointer.
        
        Args:
            text_width: Width of tooltip text
            text_height: Height of tooltip text
            
        Returns:
            VGroup containing background and pointer
        """
        # Tooltip background
        bg = Rectangle(
            width=text_width + 0.4,
            height=text_height + 0.2,
            fill_color=self.colors.background,
            stroke_color=self.colors.border,
            fill_opacity=0.95,
            stroke_width=1,
            corner_radius=0.05
        )
        
        # Pointer triangle
        pointer = Triangle(
            fill_color=self.colors.background,
            stroke_color=self.colors.border,
            fill_opacity=0.95,
            stroke_width=1
        )
        pointer.scale(0.1)
        pointer.next_to(bg, DOWN, buff=0)
        
        tooltip = VGroup(bg, pointer)
        return tooltip
        
    def create_progress_bar(self,
                           width: float = 4.0,
                           height: float = 0.3,
                           progress: float = 0.0) -> VGroup:
        """
        Create styled progress bar.
        
        Args:
            width: Progress bar width
            height: Progress bar height
            progress: Progress percentage (0.0 to 1.0)
            
        Returns:
            VGroup containing progress bar elements
        """
        # Background
        bg = Rectangle(
            width=width,
            height=height,
            fill_color=self.colors.border,
            stroke_color=self.colors.border,
            fill_opacity=0.3,
            stroke_width=1
        )
        
        # Progress fill
        fill_width = width * max(0, min(1, progress))
        fill = Rectangle(
            width=fill_width,
            height=height,
            fill_color=self.colors.primary,
            stroke_color=self.colors.primary,
            fill_opacity=0.8,
            stroke_width=0
        )
        fill.align_to(bg, LEFT)
        
        progress_bar = VGroup(bg, fill)
        return progress_bar
        
    def create_status_indicator(self, status: str = "active") -> Circle:
        """
        Create status indicator dot.
        
        Args:
            status: Status type (active, inactive, error, warning)
            
        Returns:
            Colored status indicator
        """
        status_colors = {
            "active": self.colors.success,
            "inactive": self.colors.border,
            "error": self.colors.error,
            "warning": self.colors.warning,
            "pending": self.colors.info
        }
        
        color = status_colors.get(status, status_colors["inactive"])
        
        indicator = Circle(
            radius=0.08,
            fill_color=color,
            stroke_color=color,
            fill_opacity=1,
            stroke_width=0
        )
        
        return indicator
        
    def apply_high_contrast_mode(self):
        """Apply high contrast mode for accessibility."""
        if not self.accessibility.high_contrast_mode:
            return
            
        # Increase contrast for better visibility
        self.colors.text = "#000000"
        self.colors.background = "#FFFFFF"
        self.colors.border = "#000000"
        
        # Update accessibility config
        self.accessibility.high_contrast_mode = True
        
    def apply_reduced_motion_mode(self):
        """Apply reduced motion mode for accessibility."""
        if not self.accessibility.reduced_motion:
            return
            
        # Reduce animation durations
        self.animations.fast_duration *= 0.5
        self.animations.normal_duration *= 0.5
        self.animations.slow_duration *= 0.5
        
        # Update accessibility config
        self.accessibility.reduced_motion = True
        
    def get_animation_duration(self, duration_type: str = "normal") -> float:
        """
        Get animation duration based on accessibility settings.
        
        Args:
            duration_type: Type of duration (fast, normal, slow)
            
        Returns:
            Duration in seconds
        """
        durations = {
            "fast": self.animations.fast_duration,
            "normal": self.animations.normal_duration,
            "slow": self.animations.slow_duration
        }
        
        return durations.get(duration_type, self.animations.normal_duration)
        
    def export_theme_config(self) -> Dict[str, Any]:
        """
        Export theme configuration for documentation/debugging.
        
        Returns:
            Dictionary containing complete theme configuration
        """
        return {
            "colors": {
                "primary": self.colors.primary,
                "secondary": self.colors.secondary,
                "background": self.colors.background,
                "text": self.colors.text,
                "border": self.colors.border,
                "accent": self.colors.accent,
                "success": self.colors.success,
                "warning": self.colors.warning,
                "error": self.colors.error,
                "info": self.colors.info
            },
            "typography": {
                "primary_font": self.typography.primary_font,
                "secondary_font": self.typography.secondary_font,
                "monospace_font": self.typography.monospace_font,
                "title_size": self.typography.title_size,
                "subtitle_size": self.typography.subtitle_size,
                "body_size": self.typography.body_size,
                "caption_size": self.typography.caption_size,
                "code_size": self.typography.code_size
            },
            "animations": {
                "fast_duration": self.animations.fast_duration,
                "normal_duration": self.animations.normal_duration,
                "slow_duration": self.animations.slow_duration,
                "ease_function": self.animations.ease_function
            },
            "accessibility": {
                "min_contrast_ratio": self.accessibility.min_contrast_ratio,
                "focus_indicator_width": self.accessibility.focus_indicator_width,
                "high_contrast_mode": self.accessibility.high_contrast_mode,
                "reduced_motion": self.accessibility.reduced_motion
            }
        }

    @property
    def caption_style(self) -> Dict[str, Any]:
        """Get caption styling for accessibility features."""
        return {
            "font_size": self.typography.caption_size,
            "color": self.colors.text,
            "background_color": self.colors.background,
            "border_color": self.colors.border,
            "opacity": 0.9
        }

    @property 
    def quiz_border(self) -> str:
        """Get quiz element border color."""
        return self.colors.primary

    @property
    def quiz_background(self) -> str:
        """Get quiz element background color."""
        return self.colors.background

    @property
    def button_border(self) -> str:
        """Get button border color."""
        return self.colors.border

    @property
    def button_background(self) -> str:
        """Get button background color."""
        return self.colors.background

    @property
    def tooltip_border(self) -> str:
        """Get tooltip border color."""
        return self.colors.border

    @property
    def tooltip_background(self) -> str:
        """Get tooltip background color."""
        return self.colors.background
