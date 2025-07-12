"""
AWS Architecture Animations

Specialized animation patterns for AWS certification content.
Provides enterprise-grade animations for AWS services, networking,
and architectural patterns commonly seen in certification exams.
"""

from manim import *
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from ..constants import AWS_COLORS, ANIMATION_TIMING, LAYOUT_CONFIG
from ..scenes.certification_scene import CertificationScene


class AWSArchitectureAnimations:
    """
    Collection of AWS-specific architecture animation patterns.
    
    Provides standardized animations for:
    - VPC creation and configuration
    - Auto Scaling demonstrations
    - Data flow patterns
    - Security group configurations
    - Load balancer operations
    - Database replication patterns
    """
    
    @staticmethod
    def create_vpc_formation(vpc_config: Dict, scene: Scene = None) -> AnimationGroup:
        """
        Animate VPC creation with subnets and security groups.
        
        Args:
            vpc_config: VPC configuration dictionary
            scene: Scene instance for adding elements
            
        Returns:
            AnimationGroup containing VPC formation sequence
        """
        animations = []
        vpc_elements = VGroup()
        
        # 1. VPC boundary appears
        vpc_boundary = Rectangle(
            width=vpc_config.get("width", 12),
            height=vpc_config.get("height", 8),
            stroke_color=AWS_COLORS["vpc_blue"],
            stroke_width=3,
            fill_color=AWS_COLORS["vpc_blue"],
            fill_opacity=0.05
        )
        
        vpc_label = Text(
            f"VPC ({vpc_config.get('cidr', '10.0.0.0/16')})",
            font_size=24,
            color=AWS_COLORS["vpc_blue"]
        )
        vpc_label.next_to(vpc_boundary, UP, buff=0.1)
        
        vpc_elements.add(vpc_boundary, vpc_label)
        animations.append(Create(vpc_boundary, run_time=ANIMATION_TIMING["normal"]))
        animations.append(Write(vpc_label, run_time=ANIMATION_TIMING["fast"]))
        
        # 2. Availability Zones
        az_elements = VGroup()
        azs = vpc_config.get("availability_zones", ["us-east-1a", "us-east-1b"])
        
        for i, az in enumerate(azs):
            az_box = Rectangle(
                width=vpc_config.get("width", 12) / len(azs) - 0.5,
                height=vpc_config.get("height", 8) - 1,
                stroke_color=AWS_COLORS["secondary"],
                stroke_width=2,
                fill_opacity=0.03
            )
            
            # Position AZs side by side
            x_offset = (i - (len(azs) - 1) / 2) * (vpc_config.get("width", 12) / len(azs))
            az_box.shift(RIGHT * x_offset)
            
            az_label = Text(
                f"AZ: {az}",
                font_size=18,
                color=AWS_COLORS["secondary"]
            )
            az_label.next_to(az_box, UP, buff=0.1)
            
            az_group = VGroup(az_box, az_label)
            az_elements.add(az_group)
            
            animations.append(Create(az_box, run_time=ANIMATION_TIMING["fast"]))
            animations.append(Write(az_label, run_time=ANIMATION_TIMING["fast"]))
        
        vpc_elements.add(az_elements)
        
        # 3. Subnets within AZs
        subnet_elements = VGroup()
        subnets = vpc_config.get("subnets", [])
        
        for i, subnet in enumerate(subnets):
            subnet_color = (AWS_COLORS["public_subnet"] 
                          if subnet.get("type") == "public" 
                          else AWS_COLORS["private_subnet"])
            
            subnet_box = Rectangle(
                width=3,
                height=1.5,
                stroke_color=subnet_color,
                fill_color=subnet_color,
                fill_opacity=0.3,
                stroke_width=2
            )
            
            # Position subnets within appropriate AZ
            az_index = i % len(azs)
            subnet_row = i // len(azs)
            
            x_offset = (az_index - (len(azs) - 1) / 2) * (vpc_config.get("width", 12) / len(azs))
            y_offset = subnet_row * -2
            
            subnet_box.shift(RIGHT * x_offset + UP * y_offset)
            
            subnet_label = Text(
                f"{subnet.get('name', f'Subnet-{i+1}')}\n{subnet.get('cidr', f'10.0.{i+1}.0/24')}", 
                font_size=14,
                color=AWS_COLORS["text"]
            )
            subnet_label.move_to(subnet_box.get_center())
            
            subnet_group = VGroup(subnet_box, subnet_label)
            subnet_elements.add(subnet_group)
            
            animations.append(FadeIn(subnet_box, shift=UP * 0.2, run_time=ANIMATION_TIMING["fast"]))
            animations.append(Write(subnet_label, run_time=ANIMATION_TIMING["fast"]))
        
        vpc_elements.add(subnet_elements)
        
        # 4. Internet Gateway (if public subnets exist)
        if any(subnet.get("type") == "public" for subnet in subnets):
            igw = Rectangle(
                width=2, height=0.8,
                stroke_color=AWS_COLORS["networking"],
                fill_color=AWS_COLORS["networking"],
                fill_opacity=0.8
            )
            igw_label = Text("Internet Gateway", font_size=12, color=WHITE)
            igw_label.move_to(igw.get_center())
            
            igw.next_to(vpc_boundary, UP, buff=0.5)
            igw_group = VGroup(igw, igw_label)
            vpc_elements.add(igw_group)
            
            animations.append(Create(igw, run_time=ANIMATION_TIMING["fast"]))
            animations.append(Write(igw_label, run_time=ANIMATION_TIMING["fast"]))
            
            # Connection to VPC
            igw_connection = Line(
                igw.get_bottom(),
                vpc_boundary.get_top(),
                stroke_color=AWS_COLORS["networking"],
                stroke_width=3
            )
            vpc_elements.add(igw_connection)
            animations.append(Create(igw_connection, run_time=ANIMATION_TIMING["fast"]))
        
        # Add to scene if provided
        if scene:
            scene.add(vpc_elements)
            
        return AnimationGroup(*animations, lag_ratio=0.2)
    
    @staticmethod
    def animate_data_flow(source_service: Mobject,
                         target_service: Mobject,
                         flow_type: str = "https",
                         flow_data: str = None,
                         scene: Scene = None) -> AnimationGroup:
        """
        Animate data flow between AWS services.
        
        Args:
            source_service: Source service object
            target_service: Target service object
            flow_type: Type of flow (https, database, s3, etc.)
            flow_data: Optional data description
            scene: Scene instance
            
        Returns:
            AnimationGroup containing flow animation
        """
        flow_animations = []
        
        # Create flow line
        flow_line = Line(
            source_service.get_center(),
            target_service.get_center(),
            stroke_width=4
        )
        
        # Set flow-specific styling
        flow_colors = {
            "https": AWS_COLORS["secure_flow"],
            "database": AWS_COLORS["database_flow"],
            "s3": AWS_COLORS["storage"],
            "vpc": AWS_COLORS["vpc_blue"],
            "default": AWS_COLORS["generic_flow"]
        }
        
        flow_line.set_color(flow_colors.get(flow_type, flow_colors["default"]))
        
        # Create animated particles
        particles = AWSArchitectureAnimations._create_flow_particles(flow_type, flow_line)
        
        # Flow animation sequence
        flow_animations.append(Create(flow_line, run_time=ANIMATION_TIMING["fast"]))
        
        # Animate particles along the path
        for particle in particles:
            move_animation = MoveAlongPath(
                particle, 
                flow_line, 
                run_time=ANIMATION_TIMING["normal"],
                rate_func=smooth
            )
            flow_animations.append(move_animation)
        
        # Add data label if provided
        if flow_data:
            data_label = Text(
                flow_data,
                font_size=12,
                color=flow_line.get_color()
            )
            data_label.next_to(flow_line.get_center(), UP, buff=0.1)
            
            flow_animations.append(Write(data_label, run_time=ANIMATION_TIMING["fast"]))
            
        # Add to scene if provided
        if scene:
            scene.add(flow_line, *particles)
            if flow_data:
                scene.add(data_label)
        
        return AnimationGroup(*flow_animations, lag_ratio=0.1)
    
    @staticmethod
    def _create_flow_particles(flow_type: str, path: Line) -> List[Mobject]:
        """Create flow particles based on flow type."""
        particles = []
        
        if flow_type == "https":
            # Lock icons for secure flow
            for i in range(3):
                particle = Text("🔒", font_size=12)
                particle.move_to(path.get_start())
                particles.append(particle)
                
        elif flow_type == "database":
            # Database cylinders
            for i in range(3):
                particle = Circle(radius=0.05, fill_opacity=1, color=AWS_COLORS["database"])
                particle.move_to(path.get_start())
                particles.append(particle)
                
        elif flow_type == "s3":
            # S3 bucket representations
            for i in range(4):
                particle = Rectangle(
                    width=0.08, height=0.08,
                    fill_opacity=1,
                    color=AWS_COLORS["storage"]
                )
                particle.move_to(path.get_start())
                particles.append(particle)
                
        else:
            # Generic data packets
            for i in range(5):
                particle = Dot(radius=0.03, color=AWS_COLORS["generic_flow"])
                particle.move_to(path.get_start())
                particles.append(particle)
        
        return particles
    
    @staticmethod
    def demonstrate_auto_scaling(original_service: VGroup,
                               scale_from: int,
                               scale_to: int,
                               scene: Scene = None) -> AnimationGroup:
        """
        Demonstrate Auto Scaling group scaling actions.
        
        Args:
            original_service: Original service instance
            scale_from: Starting number of instances
            scale_to: Target number of instances
            scene: Scene instance
            
        Returns:
            AnimationGroup containing scaling animation
        """
        scaling_animations = []
        
        if scale_to > scale_from:
            # Scale out animation
            new_instances = []
            
            for i in range(scale_from, scale_to):
                new_instance = original_service.copy()
                
                # Position new instances
                x_offset = (i % 3) * 1.5
                y_offset = (i // 3) * -1.2
                new_instance.shift(RIGHT * x_offset + DOWN * y_offset)
                
                # Scale in animation
                new_instance.scale(0.1)
                new_instances.append(new_instance)
                
                # Animate appearance
                scaling_animations.append(
                    AnimationGroup(
                        FadeIn(new_instance, shift=UP * 0.3),
                        new_instance.animate.scale(10),  # Scale back to normal
                        run_time=ANIMATION_TIMING["fast"]
                    )
                )
                
            # Add scaling indicator
            scale_indicator = Text(
                f"Scaling: {scale_from} → {scale_to}",
                font_size=16,
                color=AWS_COLORS["primary"]
            )
            scale_indicator.next_to(original_service, UP, buff=1)
            
            scaling_animations.append(Write(scale_indicator, run_time=ANIMATION_TIMING["fast"]))
            
            # Add to scene if provided
            if scene:
                for instance in new_instances:
                    scene.add(instance)
                scene.add(scale_indicator)
                
        else:
            # Scale in animation (remove instances)
            for i in range(scale_to, scale_from):
                scaling_animations.append(
                    FadeOut(original_service, shift=DOWN * 0.3, run_time=ANIMATION_TIMING["fast"])
                )
        
        return AnimationGroup(*scaling_animations, lag_ratio=0.3)
    
    @staticmethod
    def create_load_balancer_distribution(load_balancer: Mobject,
                                        targets: List[Mobject],
                                        distribution_algorithm: str = "round_robin",
                                        scene: Scene = None) -> AnimationGroup:
        """
        Animate load balancer request distribution.
        
        Args:
            load_balancer: Load balancer object
            targets: List of target instances
            distribution_algorithm: LB algorithm (round_robin, least_connections)
            scene: Scene instance
            
        Returns:
            AnimationGroup containing distribution animation
        """
        distribution_animations = []
        
        # Create request indicators
        requests = []
        for i in range(len(targets) * 2):  # Multiple requests
            request = Circle(
                radius=0.08,
                fill_opacity=1,
                color=AWS_COLORS["primary"]
            )
            request.move_to(load_balancer.get_center() + UP * 2)
            requests.append(request)
        
        # Animate requests coming to LB
        for request in requests:
            distribution_animations.append(
                Create(request, run_time=ANIMATION_TIMING["fast"])
            )
            distribution_animations.append(
                request.animate.move_to(load_balancer.get_center()).set_opacity(0.5)
            )
        
        # Distribute requests to targets
        for i, request in enumerate(requests):
            if distribution_algorithm == "round_robin":
                target = targets[i % len(targets)]
            else:  # least_connections or default
                target = targets[i % len(targets)]
            
            distribution_animations.append(
                AnimationGroup(
                    request.animate.move_to(target.get_center()),
                    request.animate.set_color(AWS_COLORS["secure_flow"]),
                    run_time=ANIMATION_TIMING["normal"]
                )
            )
            
            # Fade out request at target
            distribution_animations.append(
                FadeOut(request, run_time=ANIMATION_TIMING["fast"])
            )
        
        # Add algorithm label
        algo_label = Text(
            f"Algorithm: {distribution_algorithm.replace('_', ' ').title()}",
            font_size=14,
            color=AWS_COLORS["text"]
        )
        algo_label.next_to(load_balancer, DOWN, buff=0.5)
        
        distribution_animations.append(Write(algo_label, run_time=ANIMATION_TIMING["fast"]))
        
        # Add to scene if provided
        if scene:
            for request in requests:
                scene.add(request)
            scene.add(algo_label)
        
        return AnimationGroup(*distribution_animations, lag_ratio=0.1)
    
    @staticmethod
    def create_rds_replication(primary_db: Mobject,
                             replica_dbs: List[Mobject],
                             replication_type: str = "async",
                             scene: Scene = None) -> AnimationGroup:
        """
        Animate RDS database replication.
        
        Args:
            primary_db: Primary database instance
            replica_dbs: List of replica database instances
            replication_type: Type of replication (async, sync)
            scene: Scene instance
            
        Returns:
            AnimationGroup containing replication animation
        """
        replication_animations = []
        
        # Create data change indicator on primary
        data_change = Circle(
            radius=0.1,
            fill_opacity=1,
            color=AWS_COLORS["database"]
        )
        data_change.move_to(primary_db.get_center())
        
        replication_animations.append(
            Create(data_change, run_time=ANIMATION_TIMING["fast"])
        )
        
        # Animate replication to each replica
        for replica in replica_dbs:
            # Create replication stream
            replication_stream = Line(
                primary_db.get_center(),
                replica.get_center(),
                stroke_color=AWS_COLORS["database"],
                stroke_width=2
            )
            
            # Data packet animation
            data_packet = data_change.copy()
            data_packet.scale(0.5)
            
            if replication_type == "sync":
                # Synchronous - wait for each replica
                replication_animations.append(Create(replication_stream))
                replication_animations.append(
                    MoveAlongPath(data_packet, replication_stream, run_time=ANIMATION_TIMING["fast"])
                )
                replication_animations.append(FadeOut(replication_stream))
            else:
                # Asynchronous - parallel replication
                replication_animations.append(
                    AnimationGroup(
                        Create(replication_stream),
                        MoveAlongPath(data_packet, replication_stream, run_time=ANIMATION_TIMING["normal"]),
                        FadeOut(replication_stream, run_time=ANIMATION_TIMING["slow"]),
                        lag_ratio=0.3
                    )
                )
        
        # Add replication type label
        repl_label = Text(
            f"Replication: {replication_type.title()}",
            font_size=14,
            color=AWS_COLORS["database"]
        )
        repl_label.next_to(primary_db, UP, buff=0.5)
        
        replication_animations.append(Write(repl_label, run_time=ANIMATION_TIMING["fast"]))
        
        # Clean up data change indicator
        replication_animations.append(FadeOut(data_change, run_time=ANIMATION_TIMING["fast"]))
        
        # Add to scene if provided
        if scene:
            scene.add(data_change, repl_label)
        
        return AnimationGroup(*replication_animations, lag_ratio=0.2)
    
    @staticmethod
    def create_s3_lifecycle_transition(s3_objects: List[Mobject],
                                     storage_classes: List[str],
                                     transition_days: List[int],
                                     scene: Scene = None) -> AnimationGroup:
        """
        Animate S3 lifecycle policy transitions.
        
        Args:
            s3_objects: List of S3 object representations
            storage_classes: List of storage class names
            transition_days: Days after which transition occurs
            scene: Scene instance
            
        Returns:
            AnimationGroup containing lifecycle animation
        """
        lifecycle_animations = []
        
        # Storage class colors
        class_colors = {
            "Standard": AWS_COLORS["storage"],
            "Standard-IA": YELLOW,
            "One Zone-IA": ORANGE,
            "Glacier": BLUE,
            "Glacier Deep Archive": DARK_BLUE
        }
        
        # Create timeline
        timeline = Line(LEFT * 6, RIGHT * 6, stroke_width=2, color=GRAY)
        timeline_label = Text("Time →", font_size=14, color=GRAY)
        timeline_label.next_to(timeline, DOWN, buff=0.2)
        
        lifecycle_animations.append(Create(timeline))
        lifecycle_animations.append(Write(timeline_label))
        
        # Animate each object through lifecycle
        for obj in s3_objects:
            current_pos = timeline.get_start()
            
            for i, (storage_class, days) in enumerate(zip(storage_classes, transition_days)):
                # Move object along timeline
                next_pos = timeline.point_from_proportion(
                    min(i / len(storage_classes), 0.9)
                )
                
                # Change object color for storage class
                lifecycle_animations.append(
                    AnimationGroup(
                        obj.animate.move_to(next_pos + UP * 0.5),
                        obj.animate.set_color(class_colors.get(storage_class, AWS_COLORS["storage"])),
                        run_time=ANIMATION_TIMING["normal"]
                    )
                )
                
                # Add storage class label
                class_label = Text(
                    f"{storage_class}\n(Day {days})",
                    font_size=10,
                    color=class_colors.get(storage_class, AWS_COLORS["storage"])
                )
                class_label.next_to(next_pos, DOWN, buff=0.5)
                
                lifecycle_animations.append(Write(class_label, run_time=ANIMATION_TIMING["fast"]))
                
                current_pos = next_pos
        
        # Add to scene if provided
        if scene:
            scene.add(timeline, timeline_label)
        
        return AnimationGroup(*lifecycle_animations, lag_ratio=0.3)
