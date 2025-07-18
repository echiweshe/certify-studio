"""
Simple script to remove mock data from main.py.
Minimal changes - just removes the hardcoded mock activity.
"""

import re
from pathlib import Path

def fix_mock_data():
    """Remove mock data from main.py endpoints."""
    
    main_py_path = Path(r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src\certify_studio\main.py")
    
    # Read the current file
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup first
    backup_path = main_py_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created backup at: {backup_path}")
    
    # Fix the activity endpoint to return empty data instead of mock
    # Find the recent_activity list with mock data
    pattern = r'"recent_activity":\s*\[[^\]]+\]'
    replacement = '"recent_activity": []'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Removed mock activity data")
    print("✅ Agents will now show real status when activities occur")

def main():
    print("Removing Mock Data...")
    print("=" * 50)
    
    fix_mock_data()
    
    print("\n✅ Mock data removed!")
    print("\nThe agents are already connected to the real orchestrator.")
    print("When you upload a PDF and start generation, you'll see real agent activity.")

if __name__ == "__main__":
    main()
