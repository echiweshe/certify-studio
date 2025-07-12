"""
Official Icon Library for Cloud Providers

This module provides access to official cloud provider icons with enterprise-grade
quality and consistent styling. Integrates with official AWS, Azure, GCP, and
Kubernetes icon sets.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Union
from urllib.request import urlretrieve
from urllib.parse import urljoin
import hashlib

from manim import SVGMobject, ImageMobject, Group, Text, VGroup
import requests
from PIL import Image
import cairosvg

from ..constants import CertificationProvider, DIMENSIONS


class OfficialIconLibrary:
    """
    Manages official cloud provider icons with caching and validation.
    
    Features:
    - Official provider icon sets (AWS, Azure, GCP, K8s)
    - Automatic icon downloading and caching
    - Icon validation and integrity checking
    - Consistent sizing and styling
    - Fallback icon support
    """
    
    def __init__(self, provider: CertificationProvider):
        """
        Initialize icon library for specific provider.
        
        Args:
            provider: Cloud provider type
        """
        self.provider = provider
        self.cache_dir = Path("assets/icons") / provider.value
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Icon metadata cache
        self.icon_metadata = {}
        self.icon_cache = {}
        
        # Load provider-specific configuration
        self.config = self._load_provider_config()
        
        # Ensure icons are available
        self._ensure_icons_available()
        
    def _load_provider_config(self) -> Dict:
        """Load provider-specific icon configuration."""
        configs = {
            CertificationProvider.AWS: {
                "base_url": "https://d1.awsstatic.com/webteam/architecture-icons/",
                "icon_sets": {
                    "compute": "Arch_Compute/",
                    "storage": "Arch_Storage/", 
                    "database": "Arch_Database/",
                    "networking": "Arch_Networking-Content-Delivery/",
                    "security": "Arch_Security-Identity-Compliance/",
                    "analytics": "Arch_Analytics/",
                    "ml-ai": "Arch_Machine-Learning/",
                    "devtools": "Arch_Developer-Tools/"
                },
                "icon_format": "svg",
                "icon_naming": "Arch_{service}_64.svg"
            },
            CertificationProvider.AZURE: {
                "base_url": "https://docs.microsoft.com/en-us/azure/architecture/icons/",
                "icon_sets": {
                    "compute": "compute/",
                    "storage": "storage/",
                    "database": "databases/",
                    "networking": "networking/",
                    "security": "security/",
                    "analytics": "analytics/",
                    "ai-ml": "ai-machine-learning/",
                    "devops": "devops/"
                },
                "icon_format": "svg",
                "icon_naming": "{service}.svg"
            },
            CertificationProvider.GCP: {
                "base_url": "https://cloud.google.com/icons/",
                "icon_sets": {
                    "compute": "products/compute/",
                    "storage": "products/storage/",
                    "database": "products/databases/",
                    "networking": "products/networking/",
                    "security": "products/security/",
                    "analytics": "products/data-analytics/",
                    "ai-ml": "products/ai/",
                    "devtools": "products/tools/"
                },
                "icon_format": "svg",
                "icon_naming": "{service}.svg"
            },
            CertificationProvider.KUBERNETES: {
                "base_url": "https://github.com/kubernetes/community/tree/master/icons/",
                "icon_sets": {
                    "workloads": "workloads/",
                    "services": "services/",
                    "config": "config-and-storage/",
                    "storage": "config-and-storage/",
                    "security": "security/"
                },
                "icon_format": "svg",
                "icon_naming": "{service}.svg"
            }
        }
        return configs.get(self.provider, configs[CertificationProvider.AWS])
        
    def _ensure_icons_available(self):
        """Ensure required icons are downloaded and cached."""
        metadata_file = self.cache_dir / "metadata.json"
        
        # Load existing metadata
        if metadata_file.exists():
            with open(metadata_file) as f:
                self.icon_metadata = json.load(f)
        else:
            self.icon_metadata = {}
            
        # Download missing icons
        self._download_essential_icons()
        
        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(self.icon_metadata, f, indent=2)
            
    def _download_essential_icons(self):
        """Download essential icons for the provider."""
        essential_icons = self._get_essential_icons()
        
        for category, icons in essential_icons.items():
            category_dir = self.cache_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for icon_name in icons:
                self._download_icon(icon_name, category)
                
    def _get_essential_icons(self) -> Dict[str, List[str]]:
        """Get list of essential icons per provider."""
        essential_sets = {
            CertificationProvider.AWS: {
                "compute": [
                    "ec2", "lambda", "ecs", "eks", "fargate", "batch",
                    "elastic-beanstalk", "lightsail"
                ],
                "storage": [
                    "s3", "ebs", "efs", "fsx", "glacier", "storage-gateway"
                ],
                "database": [
                    "rds", "dynamodb", "redshift", "elasticache", 
                    "documentdb", "neptune", "aurora"
                ],
                "networking": [
                    "vpc", "cloudfront", "route53", "elb", "api-gateway",
                    "direct-connect", "nat-gateway", "internet-gateway"
                ],
                "security": [
                    "iam", "cognito", "secrets-manager", "kms", "guardduty",
                    "shield", "waf", "certificate-manager"
                ]
            },
            CertificationProvider.AZURE: {
                "compute": [
                    "virtual-machines", "app-service", "functions", 
                    "container-instances", "kubernetes-service"
                ],
                "storage": [
                    "storage-accounts", "blob-storage", "file-storage",
                    "disk-storage", "data-lake"
                ],
                "database": [
                    "sql-database", "cosmos-db", "database-mysql",
                    "database-postgresql", "redis-cache"
                ],
                "networking": [
                    "virtual-network", "load-balancer", "application-gateway",
                    "cdn", "dns", "vpn-gateway"
                ],
                "security": [
                    "active-directory", "key-vault", "security-center",
                    "sentinel", "information-protection"
                ]
            },
            CertificationProvider.GCP: {
                "compute": [
                    "compute-engine", "app-engine", "cloud-functions",
                    "cloud-run", "kubernetes-engine"
                ],
                "storage": [
                    "cloud-storage", "persistent-disk", "filestore",
                    "cloud-bigtable"
                ],
                "database": [
                    "cloud-sql", "cloud-spanner", "firestore",
                    "cloud-memorystore", "bigquery"
                ],
                "networking": [
                    "vpc", "cloud-load-balancing", "cloud-cdn",
                    "cloud-dns", "cloud-vpn"
                ],
                "security": [
                    "cloud-iam", "cloud-kms", "cloud-security-center",
                    "identity-platform", "secret-manager"
                ]
            },
            CertificationProvider.KUBERNETES: {
                "workloads": [
                    "pod", "deployment", "statefulset", "daemonset",
                    "job", "cronjob", "replicaset"
                ],
                "services": [
                    "service", "ingress", "endpoint", "network-policy"
                ],
                "config": [
                    "configmap", "secret", "persistent-volume",
                    "persistent-volume-claim"
                ],
                "security": [
                    "rbac", "service-account", "pod-security-policy",
                    "network-policy"
                ]
            }
        }
        return essential_sets.get(self.provider, {})
        
    def _download_icon(self, icon_name: str, category: str) -> bool:
        """
        Download individual icon with validation.
        
        Args:
            icon_name: Name of the icon
            category: Icon category
            
        Returns:
            True if download successful
        """
        icon_filename = self._get_icon_filename(icon_name)
        local_path = self.cache_dir / category / icon_filename
        
        # Skip if already exists and valid
        if local_path.exists() and self._validate_icon(local_path):
            return True
            
        try:
            # Construct download URL
            url = self._construct_icon_url(icon_name, category)
            
            # Download icon
            urlretrieve(url, local_path)
            
            # Validate downloaded icon
            if self._validate_icon(local_path):
                # Update metadata
                self.icon_metadata[f"{category}/{icon_name}"] = {
                    "filename": icon_filename,
                    "url": url,
                    "size": local_path.stat().st_size,
                    "hash": self._calculate_file_hash(local_path),
                    "downloaded_at": str(Path.ctime(local_path))
                }
                return True
            else:
                # Remove invalid file
                local_path.unlink()
                return False
                
        except Exception as e:
            print(f"Failed to download {icon_name}: {e}")
            return False
            
    def _get_icon_filename(self, icon_name: str) -> str:
        """Get standardized icon filename."""
        naming_template = self.config["icon_naming"]
        return naming_template.format(service=icon_name)
        
    def _construct_icon_url(self, icon_name: str, category: str) -> str:
        """Construct download URL for icon."""
        base_url = self.config["base_url"]
        category_path = self.config["icon_sets"].get(category, "")
        filename = self._get_icon_filename(icon_name)
        
        return urljoin(base_url, f"{category_path}{filename}")
        
    def _validate_icon(self, file_path: Path) -> bool:
        """
        Validate icon file integrity and format.
        
        Args:
            file_path: Path to icon file
            
        Returns:
            True if icon is valid
        """
        if not file_path.exists():
            return False
            
        # Check file size (should be > 0)
        if file_path.stat().st_size == 0:
            return False
            
        # Check file format
        try:
            if file_path.suffix.lower() == '.svg':
                # Basic SVG validation
                with open(file_path, 'r') as f:
                    content = f.read()
                    return '<svg' in content and '</svg>' in content
            elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                # Image validation
                with Image.open(file_path) as img:
                    return img.format in ['PNG', 'JPEG']
        except Exception:
            return False
            
        return True
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for integrity checking."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def get_service_icon(self, 
                        service_name: str, 
                        size: int = None,
                        category: str = None) -> SVGMobject:
        """
        Get service icon as Manim object.
        
        Args:
            service_name: Name of the service
            size: Icon size (default from constants)
            category: Service category (auto-detected if None)
            
        Returns:
            SVGMobject containing the icon
        """
        size = size or DIMENSIONS["icon_size"]
        
        # Try cache first
        cache_key = f"{service_name}_{size}_{category}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key].copy()
            
        # Find icon file
        icon_path = self._find_icon_path(service_name, category)
        
        if not icon_path:
            # Return fallback icon
            icon = self._create_fallback_icon(service_name, size)
        else:
            try:
                # Load official icon
                if icon_path.suffix.lower() == '.svg':
                    icon = SVGMobject(str(icon_path))
                else:
                    # Convert to SVG if needed
                    svg_path = self._convert_to_svg(icon_path)
                    icon = SVGMobject(str(svg_path))
                    
                # Apply standard styling
                icon = self._apply_icon_styling(icon, size)
                
            except Exception as e:
                print(f"Error loading icon {service_name}: {e}")
                icon = self._create_fallback_icon(service_name, size)
                
        # Cache the icon
        self.icon_cache[cache_key] = icon
        
        return icon.copy()
        
    def _find_icon_path(self, 
                       service_name: str, 
                       category: str = None) -> Optional[Path]:
        """Find icon file path, searching all categories if needed."""
        
        # If category specified, search there first
        if category:
            search_dirs = [self.cache_dir / category]
        else:
            # Search all categories
            search_dirs = [
                self.cache_dir / cat for cat in self.config["icon_sets"].keys()
                if (self.cache_dir / cat).exists()
            ]
            
        filename = self._get_icon_filename(service_name)
        
        for search_dir in search_dirs:
            icon_path = search_dir / filename
            if icon_path.exists():
                return icon_path
                
        return None
        
    def _convert_to_svg(self, image_path: Path) -> Path:
        """Convert image to SVG format."""
        svg_path = image_path.with_suffix('.svg')
        
        if svg_path.exists():
            return svg_path
            
        # Convert PNG to SVG (basic conversion)
        try:
            with Image.open(image_path) as img:
                # Create simple SVG wrapper
                width, height = img.size
                svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image width="{width}" height="{height}" 
         xlink:href="data:image/png;base64,{self._image_to_base64(image_path)}"/>
</svg>'''
                
                with open(svg_path, 'w') as f:
                    f.write(svg_content)
                    
                return svg_path
                
        except Exception as e:
            print(f"Failed to convert {image_path} to SVG: {e}")
            return image_path
            
    def _image_to_base64(self, image_path: Path) -> str:
        """Convert image to base64 string."""
        import base64
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
            
    def _apply_icon_styling(self, icon: SVGMobject, size: int) -> SVGMobject:
        """Apply consistent styling to icon."""
        # Scale to standard size
        target_height = size / DIMENSIONS["icon_size"]
        icon.scale_to_fit_height(target_height)
        
        # Apply provider-specific styling
        if self.provider == CertificationProvider.AWS:
            # AWS icons are already styled correctly
            pass
        elif self.provider == CertificationProvider.AZURE:
            # Apply Azure blue tint if needed
            pass
        elif self.provider == CertificationProvider.GCP:
            # Apply GCP styling
            pass
            
        return icon
        
    def _create_fallback_icon(self, service_name: str, size: int) -> VGroup:
        """Create fallback icon when official icon unavailable."""
        fallback = VGroup()
        
        # Simple rectangle with service name
        rect = Rectangle(
            width=size/50, height=size/50,
            stroke_width=2,
            stroke_color="#CCCCCC",
            fill_color="#F0F0F0",
            fill_opacity=0.8
        )
        
        # Service name text
        text = Text(
            service_name[:3].upper(),
            font_size=size/8,
            color="#666666"
        )
        text.move_to(rect.get_center())
        
        fallback.add(rect, text)
        return fallback
        
    def get_provider_logo(self) -> SVGMobject:
        """Get provider logo/badge."""
        logo_files = {
            CertificationProvider.AWS: "aws-logo.svg",
            CertificationProvider.AZURE: "azure-logo.svg", 
            CertificationProvider.GCP: "gcp-logo.svg",
            CertificationProvider.KUBERNETES: "kubernetes-logo.svg"
        }
        
        logo_file = logo_files.get(self.provider)
        logo_path = self.cache_dir / logo_file
        
        if logo_path.exists():
            return SVGMobject(str(logo_path))
        else:
            # Return text-based logo
            return Text(
                self.provider.value.upper(),
                font_size=24,
                color="#333333"
            )
            
    def list_available_icons(self, category: str = None) -> List[str]:
        """
        List all available icons.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of available icon names
        """
        icons = []
        
        if category:
            search_dirs = [self.cache_dir / category]
        else:
            search_dirs = [
                self.cache_dir / cat for cat in self.config["icon_sets"].keys()
                if (self.cache_dir / cat).exists()
            ]
            
        for search_dir in search_dirs:
            if search_dir.exists():
                for icon_file in search_dir.glob(f"*.{self.config['icon_format']}"):
                    # Extract service name from filename
                    service_name = self._extract_service_name(icon_file.name)
                    icons.append(service_name)
                    
        return sorted(list(set(icons)))
        
    def _extract_service_name(self, filename: str) -> str:
        """Extract service name from icon filename."""
        # Remove extension
        name = Path(filename).stem
        
        # Provider-specific name extraction
        if self.provider == CertificationProvider.AWS:
            # Remove "Arch_" prefix and "_64" suffix
            if name.startswith("Arch_"):
                name = name[5:]
            if name.endswith("_64"):
                name = name[:-3]
                
        return name.lower().replace("-", "_")
