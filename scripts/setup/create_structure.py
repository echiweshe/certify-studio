#!/usr/bin/env python3
"""Script to create the complete Certify Studio project structure"""

import os
from pathlib import Path

def create_project_structure():
    base_path = Path("C:/ZBDuo_Share/Labs/src/BttlnsCldMCP/certify-studio")
    
    # All directories to create
    directories = [
        # Source code structure
        "src/certify_studio/api/v1/endpoints",
        "src/certify_studio/core/domain",
        "src/certify_studio/core/services",
        "src/certify_studio/core/repositories",
        "src/certify_studio/agents/certification",
        "src/certify_studio/agents/content",
        "src/certify_studio/agents/quality",
        "src/certify_studio/agents/bedrock",
        "src/certify_studio/manim_extensions/scenes",
        "src/certify_studio/manim_extensions/icons",
        "src/certify_studio/manim_extensions/animations",
        "src/certify_studio/manim_extensions/themes",
        "src/certify_studio/manim_extensions/interactive",
        "src/certify_studio/manim_extensions/accessibility",
        "src/certify_studio/manim_extensions/exports",
        "src/certify_studio/diagrams/providers",
        "src/certify_studio/diagrams/templates",
        "src/certify_studio/diagrams/renderers",
        "src/certify_studio/database/migrations",
        "src/certify_studio/integrations/aws",
        "src/certify_studio/integrations/azure",
        "src/certify_studio/integrations/gcp",
        "src/certify_studio/integrations/storage",
        "src/certify_studio/integrations/observability",
        "src/certify_studio/utils",
        
        # Frontend structure
        "frontend/src/components/ui",
        "frontend/src/components/certification",
        "frontend/src/components/content",
        "frontend/src/components/export",
        "frontend/src/components/layout",
        "frontend/src/pages",
        "frontend/src/hooks",
        "frontend/src/services",
        "frontend/src/types",
        "frontend/src/utils",
        "frontend/src/styles",
        "frontend/public",
        
        # Documentation
        "docs/architecture",
        "docs/api",
        "docs/deployment",
        "docs/development",
        "docs/user-guide",
        "docs/examples",
        
        # Tests
        "tests/unit/core",
        "tests/unit/agents",
        "tests/unit/manim_extensions",
        "tests/unit/diagrams",
        "tests/unit/api",
        "tests/integration",
        "tests/performance",
        "tests/e2e",
        "tests/fixtures",
        "tests/data/sample_exam_guides",
        "tests/data/expected_outputs",
        
        # Scripts
        "scripts/setup",
        "scripts/deployment",
        "scripts/data",
        "scripts/maintenance",
        "scripts/development",
        
        # Configuration
        "config/settings",
        "config/docker",
        "config/kubernetes",
        "config/aws/cloudformation",
        "config/aws/terraform",
        "config/monitoring",
        
        # Assets
        "assets/icons/aws/compute",
        "assets/icons/aws/storage",
        "assets/icons/aws/database",
        "assets/icons/aws/networking",
        "assets/icons/aws/security",
        "assets/icons/aws/analytics",
        "assets/icons/aws/ml-ai",
        "assets/icons/aws/devtools",
        "assets/icons/azure/compute",
        "assets/icons/azure/storage",
        "assets/icons/azure/database",
        "assets/icons/azure/networking",
        "assets/icons/azure/security",
        "assets/icons/azure/analytics",
        "assets/icons/azure/ai-ml",
        "assets/icons/azure/devops",
        "assets/icons/gcp/compute",
        "assets/icons/gcp/storage",
        "assets/icons/gcp/database",
        "assets/icons/gcp/networking",
        "assets/icons/gcp/security",
        "assets/icons/gcp/analytics",
        "assets/icons/gcp/ai-ml",
        "assets/icons/gcp/devtools",
        "assets/icons/kubernetes/workloads",
        "assets/icons/kubernetes/services",
        "assets/icons/kubernetes/config",
        "assets/icons/kubernetes/storage",
        "assets/icons/kubernetes/security",
        "assets/templates/certification/aws",
        "assets/templates/certification/azure",
        "assets/templates/certification/gcp",
        "assets/templates/certification/kubernetes",
        "assets/templates/animations/transitions",
        "assets/templates/animations/effects",
        "assets/templates/animations/patterns",
        "assets/templates/exports/powerpoint",
        "assets/templates/exports/web",
        "assets/templates/exports/pdf",
        "assets/fonts",
        "assets/images",
        "assets/videos",
        "assets/audio",
        
        # CI/CD
        ".github/workflows",
        ".github/ISSUE_TEMPLATE",
        
        # Security
        ".security",
        
        # Runtime directories
        "logs",
        "temp",
        "uploads",
        "exports"
    ]
    
    # Create all directories
    created_count = 0
    for directory in directories:
        dir_path = base_path / directory
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created: {directory}")
            created_count += 1
        except Exception as e:
            print(f"✗ Failed to create {directory}: {e}")
    
    print(f"\nCreated {created_count} directories successfully!")
    return base_path

if __name__ == "__main__":
    create_project_structure()
