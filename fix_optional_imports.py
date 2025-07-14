"""
Fix imports more comprehensively
"""

import os
import re

def fix_qa_imports_v2():
    qa_dir = r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio\src\certify_studio\agents\specialized\quality_assurance"
    
    files_to_fix = [
        "performance_monitor.py",
        "feedback_analyzer.py", 
        "benchmark_manager.py",
        "continuous_monitor.py"
    ]
    
    for filename in files_to_fix:
        filepath = os.path.join(qa_dir, filename)
        if os.path.exists(filepath):
            print(f"Fixing {filename}...")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find where to insert the Optional import
            typing_line_idx = None
            for i, line in enumerate(lines):
                if line.startswith('from typing import'):
                    typing_line_idx = i
                    # Add Optional if not present
                    if 'Optional' not in line:
                        lines[i] = line.rstrip() + ', Optional\n'
                    break
            
            # If no typing import found, add one
            if typing_line_idx is None:
                # Insert after other imports
                for i, line in enumerate(lines):
                    if line.startswith('from'):
                        continue
                    else:
                        lines.insert(i, 'from typing import Optional\n')
                        break
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"✓ Fixed {filename}")

if __name__ == "__main__":
    fix_qa_imports_v2()
    print("\nFixed Optional imports!")
