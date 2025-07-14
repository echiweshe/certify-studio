"""
Run with full stack trace to find the exact import error
"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment
os.environ['CERTIFY_STUDIO_ENV'] = 'development'
os.environ['PYTHONPATH'] = str(project_root / "src")

print("=" * 60)
print("CERTIFY STUDIO - Debug Import")
print("=" * 60)

try:
    print("Importing main app...")
    from certify_studio.main import app
    print("✅ Import successful!")
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Try to get more details
    print("\n" + "=" * 60)
    print("Detailed error information:")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    # Walk through the traceback
    tb = exc_traceback
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        if "certify_studio" in filename and ".venv" not in filename:
            print(f"\nFile: {filename}")
            print(f"Line: {tb.tb_lineno}")
            print(f"Function: {frame.f_code.co_name}")
            
            # Try to show the actual line
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if tb.tb_lineno <= len(lines):
                        print(f"Code: {lines[tb.tb_lineno - 1].strip()}")
            except:
                pass
                
        tb = tb.tb_next
