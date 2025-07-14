"""
Fix startup issues by patching the necessary files.
"""

import sys
from pathlib import Path


def fix_startup_issues():
    """Fix all startup issues."""
    project_root = Path(__file__).parent.parent
    
    # 1. Fix the config.py to add RATE_LIMITS
    config_file = project_root / "src" / "certify_studio" / "config.py"
    config_content = config_file.read_text()
    
    # Add RATE_LIMITS if not present
    if "RATE_LIMITS" not in config_content:
        # Find a good place to insert it (after LOG_RETENTION)
        insertion_point = config_content.find("LOG_RETENTION: str = Field")
        if insertion_point != -1:
            # Find the end of that line
            end_of_line = config_content.find("\n", insertion_point)
            if end_of_line != -1:
                # Insert RATE_LIMITS configuration
                rate_limits_config = '''
    
    # Rate Limiting
    RATE_LIMITS: Dict[str, int] = Field(
        default={"free": 100, "pro": 1000, "enterprise": 10000},
        env="RATE_LIMITS"
    )'''
                new_content = config_content[:end_of_line] + rate_limits_config + config_content[end_of_line:]
                config_file.write_text(new_content)
                print("✅ Added RATE_LIMITS to config.py")
    
    # 2. Install aiosqlite
    import subprocess
    python_path = project_root / ".venv" / "Scripts" / "python.exe"
    try:
        subprocess.run([str(python_path), "-m", "pip", "install", "aiosqlite"], check=True)
        print("✅ Installed aiosqlite")
    except:
        print("⚠️  Could not install aiosqlite")
    
    print("\n🎉 Fixes applied! Try running quickstart.py again.")


if __name__ == "__main__":
    fix_startup_issues()
