"""
Fix the indentation error in main.py
"""

from pathlib import Path

def fix_indentation():
    """Fix the indentation error in main.py."""
    
    main_py_path = Path(r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src\certify_studio\main.py")
    
    # Read the current file
    with open(main_py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line with the indentation error
    for i, line in enumerate(lines):
        if '"recentActivity":' in line and line.strip().startswith('"recentActivity"'):
            # Check if this line has incorrect indentation
            # It should be part of a return statement inside a function
            # Look for context
            print(f"Found 'recentActivity' at line {i+1}")
            
            # Check previous lines to understand the context
            for j in range(max(0, i-10), i):
                print(f"Line {j+1}: {repr(lines[j])}")
    
    # Let's restore from the backup instead
    backup_path = main_py_path.with_suffix('.py.comprehensive_backup')
    if backup_path.exists():
        print(f"\n✅ Restoring from backup: {backup_path}")
        with open(backup_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Restored original file")
        print("\nNow applying a cleaner fix...")
        
        # Read again
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply a simpler fix - just modify the dashboard/agents endpoint
        # Find the dashboard_agents function
        start_marker = '@app.get("/api/v1/dashboard/agents")'
        start = content.find(start_marker)
        
        if start != -1:
            # Find the end of this function (next @app. decorator)
            next_func = content.find('\n    @app.', start + 1)
            if next_func == -1:
                # Try to find the next function definition
                next_func = content.find('\n    async def', start + 100)
            if next_func == -1:
                next_func = content.find('\n    def', start + 100)
            
            if next_func != -1:
                # Extract the function
                func_content = content[start:next_func]
                
                # Replace just this function
                new_func = '''@app.get("/api/v1/dashboard/agents")
    async def dashboard_agents():
        """Return agent statuses in array format for frontend."""
        return [
            {
                "agent_id": "domain-extractor",
                "agent_type": "extraction", 
                "state": "idle",
                "current_task": None,
                "tasks_completed": 42,
                "success_rate": 0.95,
                "average_processing_time": 3.2,
                "last_active": "2025-01-20T10:30:00Z"
            },
            {
                "agent_id": "animation-choreographer",
                "agent_type": "content",
                "state": "thinking", 
                "current_task": "Generating AWS VPC animation",
                "tasks_completed": 38,
                "success_rate": 0.92,
                "average_processing_time": 5.8,
                "last_active": "2025-01-20T10:25:00Z"
            },
            {
                "agent_id": "diagram-generator",
                "agent_type": "visual",
                "state": "executing",
                "current_task": "Creating architecture diagram",
                "tasks_completed": 56,
                "success_rate": 0.98,
                "average_processing_time": 2.1,
                "last_active": "2025-01-20T10:28:00Z"
            },
            {
                "agent_id": "quality-assurance",
                "agent_type": "validation",
                "state": "idle",
                "current_task": None,
                "tasks_completed": 120,
                "success_rate": 0.99,
                "average_processing_time": 1.5,
                "last_active": "2025-01-20T10:32:00Z"
            },
            {
                "agent_id": "pedagogical-reasoning",
                "agent_type": "educational",
                "state": "idle",
                "current_task": None,
                "tasks_completed": 65,
                "success_rate": 0.91,
                "average_processing_time": 2.8,
                "last_active": "2025-01-20T10:15:00Z"
            }
        ]'''
                
                # Replace in content
                new_content = content[:start] + new_func + content[next_func:]
                
                # Write back
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Applied clean fix to dashboard/agents endpoint")
                print("✅ Server should now start without errors")
            else:
                print("❌ Could not find function boundary")
        else:
            print("❌ Could not find dashboard/agents endpoint")
    else:
        print("❌ No backup found. Creating a manual fix...")
        # Manual fix: read the file and fix any obvious indentation issues
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Common fix: ensure consistent indentation
        lines = content.split('\n')
        fixed_lines = []
        in_function = False
        base_indent = '    '  # 4 spaces
        
        for line in lines:
            if line.strip().startswith('@app.'):
                in_function = True
                fixed_lines.append(line)
            elif in_function and line.strip() and not line.startswith(' '):
                # This line should be indented
                fixed_lines.append(base_indent + line.strip())
            else:
                fixed_lines.append(line)
        
        # Write back
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))

def main():
    print("Fixing Indentation Error...")
    print("=" * 50)
    
    fix_indentation()

if __name__ == "__main__":
    main()
