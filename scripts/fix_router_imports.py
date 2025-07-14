#!/usr/bin/env python
"""
Fix all import issues in routers using UV.
"""

import os
from pathlib import Path

def fix_router_imports():
    """Fix common import issues in all routers."""
    project_root = Path(__file__).parent.parent
    routers_dir = project_root / "src" / "certify_studio" / "api" / "routers"
    
    # Common replacements needed
    replacements = {
        "VerifiedUser": "get_current_verified_user",
        "Database": "AsyncSession",
        "RateLimit": "check_rate_limit",
        "UploadFile as UploadHandler": "FileUploadValidator",
        "from ..dependencies import (": "from sqlalchemy.ext.asyncio import AsyncSession\nfrom ..dependencies import (",
    }
    
    # Fix each router file
    for router_file in routers_dir.glob("*.py"):
        if router_file.name == "__init__.py":
            continue
            
        print(f"Checking {router_file.name}...")
        content = router_file.read_text()
        modified = False
        
        # Apply replacements
        for old, new in replacements.items():
            if old in content and new not in content:
                content = content.replace(old, new)
                modified = True
                print(f"  Fixed: {old} -> {new}")
        
        # Fix type annotations
        if "db: Database" in content:
            content = content.replace("db: Database", "db: AsyncSession")
            modified = True
            print("  Fixed: db type annotation")
        
        if "user: VerifiedUser" in content:
            content = content.replace("user: VerifiedUser", "user: User")
            modified = True
            print("  Fixed: user type annotation")
        
        # Ensure User import if needed
        if "user: User" in content and "from ..schemas import" in content:
            schemas_import = content.find("from ..schemas import")
            if schemas_import != -1:
                # Check if User is imported
                if "User" not in content[schemas_import:content.find("\n", schemas_import)]:
                    # Add User to imports
                    content = content.replace("from ..schemas import (", "from ..schemas import (\n    User,")
                    modified = True
                    print("  Added: User import")
        
        if modified:
            router_file.write_text(content)
            print(f"✅ Fixed {router_file.name}")
        else:
            print(f"  No changes needed")
    
    print("\n✅ Router import fixes complete!")


if __name__ == "__main__":
    fix_router_imports()
