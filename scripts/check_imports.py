"""
Fix common import and initialization issues in Certify Studio.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def check_imports():
    """Check for common import issues."""
    issues = []
    
    # Check if Settings is accessible
    try:
        from certify_studio.config import settings, Settings
        print("✓ Settings import successful")
    except ImportError as e:
        issues.append(f"Settings import failed: {e}")
        
    # Check if core config re-export works
    try:
        from certify_studio.core.config import settings as core_settings
        print("✓ Core config re-export successful")
    except ImportError as e:
        issues.append(f"Core config import failed: {e}")
        
    # Check QA agent imports
    try:
        from certify_studio.agents.specialized.quality_assurance import QualityAssuranceAgent
        print("✓ QualityAssuranceAgent import successful")
    except ImportError as e:
        issues.append(f"QualityAssuranceAgent import failed: {e}")
        
    # Check report generator
    try:
        from certify_studio.agents.specialized.quality_assurance.report_generator import ReportGenerator
        print("✓ ReportGenerator import successful")
    except ImportError as e:
        issues.append(f"ReportGenerator import failed: {e}")
        
    return issues

def test_initialization():
    """Test basic initialization of components."""
    try:
        from certify_studio.config import settings
        from certify_studio.agents.specialized.quality_assurance.report_generator import ReportGenerator
        
        # Try to create ReportGenerator
        rg = ReportGenerator(settings)
        print("✓ ReportGenerator initialization successful")
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Checking imports...")
    issues = check_imports()
    
    if issues:
        print("\nImport issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nAll imports successful!")
        
    print("\nTesting initialization...")
    test_initialization()
