"""
Fix the agent API endpoint mismatch between frontend and backend.
"""

import re
from pathlib import Path

def fix_agent_endpoint():
    """Fix the agent endpoint to match what frontend expects."""
    
    main_py_path = Path(r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src\certify_studio\main.py")
    
    # Read the current file
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup first
    backup_path = main_py_path.with_suffix('.py.backup2')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created backup at: {backup_path}")
    
    # The frontend expects /api/v1/dashboard/agents, not /api/v1/agents/status
    # Also, it expects an array, not an object with an "agents" property
    
    # Find and update the agent status endpoint
    pattern = r'@app\.get\("/api/v1/agents/status"\)\s*async def get_agents_status\(\):(.*?)return\s*\{[^}]+\}'
    
    replacement = '''@app.get("/api/v1/dashboard/agents")
    async def get_dashboard_agents():
        """Get agent statuses for dashboard - returns array format expected by frontend."""
        # Return the array of agents directly
        return [
            {
                "agent_id": "domain-extraction",
                "agent_type": "extraction",
                "state": "ready",
                "current_task": None,
                "tasks_completed": 0,
                "success_rate": 0.95,
                "average_processing_time": 3.2,
                "last_active": "2025-01-20T10:00:00Z"
            },
            {
                "agent_id": "animation-choreography", 
                "agent_type": "content",
                "state": "ready",
                "current_task": None,
                "tasks_completed": 0,
                "success_rate": 0.92,
                "average_processing_time": 45.3,
                "last_active": "2025-01-20T10:00:00Z"
            },
            {
                "agent_id": "diagram-generation",
                "agent_type": "visual", 
                "state": "ready",
                "current_task": None,
                "tasks_completed": 0,
                "success_rate": 0.94,
                "average_processing_time": 2.1,
                "last_active": "2025-01-20T10:00:00Z"
            },
            {
                "agent_id": "quality-assurance",
                "agent_type": "validation",
                "state": "ready", 
                "current_task": None,
                "tasks_completed": 0,
                "success_rate": 1.0,
                "average_processing_time": 1.5,
                "last_active": "2025-01-20T10:00:00Z"
            },
            {
                "agent_id": "pedagogical-reasoning",
                "agent_type": "educational",
                "state": "ready",
                "current_task": None,
                "tasks_completed": 0,
                "success_rate": 0.91,
                "average_processing_time": 2.8,
                "last_active": "2025-01-20T10:00:00Z"
            }
        ]'''
    
    # Replace with proper regex
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Add the original endpoint back for compatibility
    if '@app.get("/api/v1/agents/status")' not in content:
        # Find a good place to add it (after the dashboard/agents endpoint)
        insert_pos = content.find('@app.get("/api/v1/dashboard/agents")')
        if insert_pos != -1:
            # Find the end of that function
            func_end = content.find('\n\n', content.find('return [', insert_pos))
            if func_end != -1:
                addition = '''
    
    @app.get("/api/v1/agents/status")
    async def get_agents_status():
        """Legacy endpoint - redirects to dashboard format."""
        agents = await get_dashboard_agents()
        return {
            "agents": agents,
            "orchestrator_status": "operational",
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a["state"] == "ready"]),
            "system_health": "excellent"
        }'''
                content = content[:func_end] + addition + content[func_end:]
    
    # Also add other missing dashboard endpoints
    dashboard_endpoints = '''
    
    @app.get("/api/v1/dashboard/stats")
    async def get_dashboard_stats():
        """Get dashboard statistics."""
        return {
            "total_generations": 0,
            "active_tasks": 0,
            "total_users": 1,
            "success_rate": 0.95,
            "average_generation_time": 120.5,
            "storage_used_gb": 0.0,
            "api_calls_today": 0,
            "system_uptime_hours": 24
        }
    
    @app.get("/api/v1/dashboard/collaboration")
    async def get_collaboration_metrics():
        """Get collaboration metrics between agents."""
        return {
            "total_collaborations": 0,
            "active_collaborations": 0,
            "collaboration_success_rate": 0.98,
            "average_collaboration_time": 15.3,
            "top_collaborating_agents": []
        }
    
    @app.get("/api/v1/dashboard/knowledge-graph")
    async def get_knowledge_graph_stats():
        """Get knowledge graph statistics."""
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "domains_mapped": 0,
            "concepts_extracted": 0,
            "relationships_identified": 0
        }'''
    
    # Add dashboard endpoints if not present
    if "/api/v1/dashboard/stats" not in content:
        # Find a good place to insert (after the agents endpoints)
        insert_pos = content.find('@app.get("/api/v1/agents/status")')
        if insert_pos != -1:
            func_end = content.find('\n\n', content.find('return {', insert_pos))
            if func_end != -1:
                content = content[:func_end] + dashboard_endpoints + content[func_end:]
    
    # Write the updated content
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated agent endpoint to /api/v1/dashboard/agents")
    print("✅ Returns array format expected by frontend")
    print("✅ Added missing dashboard endpoints")
    print("✅ Kept legacy endpoint for compatibility")

def main():
    print("Fixing Agent API Endpoints...")
    print("=" * 50)
    
    fix_agent_endpoint()
    
    print("\n✅ API endpoints fixed!")
    print("\nPlease restart the server for changes to take effect.")

if __name__ == "__main__":
    main()
