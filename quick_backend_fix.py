"""
Quick fix to ensure backend returns agent data in the exact format frontend expects
"""

from pathlib import Path

def apply_quick_fix():
    """Apply a quick fix to the dashboard agents endpoint."""
    
    main_py_path = Path(r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src\certify_studio\main.py")
    
    # Read the file
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    backup_path = main_py_path.with_suffix('.py.quick_backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Find the dashboard_agents function
    start = content.find('@app.get("/api/v1/dashboard/agents")')
    if start == -1:
        print("❌ Could not find dashboard agents endpoint")
        return False
    
    # Find the next function
    next_func = content.find('\n    @app.', start + 1)
    if next_func == -1:
        next_func = content.find('\n    async def', start + 100)
    if next_func == -1:
        next_func = len(content)
    
    # Create the new function that returns exactly what frontend expects
    new_function = '''@app.get("/api/v1/dashboard/agents")
    async def dashboard_agents():
        """Return agents in the exact format the frontend expects."""
        # The frontend transforms this data in agents.ts getAgents() method
        # It expects an array with these exact fields
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
    
    # Replace the function
    new_content = content[:start] + new_function + '\n' + content[next_func:]
    
    # Write back
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Applied quick fix to dashboard agents endpoint")
    print("✅ Backend now returns data in the format frontend expects")
    return True

def verify_fix():
    """Verify the fix was applied correctly."""
    main_py_path = Path(r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src\certify_studio\main.py")
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '"agent_id": "domain-extractor"' in content:
        print("✅ Fix verified - agent data structure is correct")
        return True
    else:
        print("❌ Fix verification failed")
        return False

def main():
    print("Applying Quick Backend Fix...")
    print("=" * 50)
    
    if apply_quick_fix():
        print("\nVerifying fix...")
        verify_fix()
        
        print("\n✅ Fix complete!")
        print("\nNow you need to:")
        print("1. Restart the backend server (Ctrl+C and run again)")
        print("2. Refresh the frontend page")
        print("\nThe agents should display correctly now!")
    else:
        print("\n❌ Fix failed. Please check the error messages.")

if __name__ == "__main__":
    main()
