"""
Real-time Agent Monitoring and Data Connection
=============================================
Connects to the backend to monitor real agent collaboration and data flow.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class AgentDataMonitor:
    """Monitor real agent data and collaboration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://") + "/ws"
        self.session: Optional[aiohttp.ClientSession] = None
        self.agents_data = {}
        self.collaboration_events = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        try:
            print("🔌 Connecting to WebSocket for real-time agent data...")
            
            async with self.session.ws_connect(self.ws_url) as ws:
                print("✅ WebSocket connected!")
                
                # Subscribe to agent events
                await ws.send_json({
                    "type": "subscribe",
                    "channels": ["agents", "collaboration", "generation"]
                })
                
                # Listen for messages
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await self.handle_agent_event(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f'❌ WebSocket error: {ws.exception()}')
                        break
                        
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
    
    async def handle_agent_event(self, event: Dict[str, Any]):
        """Process real-time agent events"""
        event_type = event.get("type")
        timestamp = datetime.now().isoformat()
        
        if event_type == "agent_status":
            agent_id = event.get("agent_id")
            status = event.get("status")
            self.agents_data[agent_id] = {
                "status": status,
                "last_update": timestamp,
                "metrics": event.get("metrics", {})
            }
            print(f"🤖 Agent {agent_id}: {status}")
            
        elif event_type == "collaboration":
            collab_data = {
                "timestamp": timestamp,
                "agents": event.get("agents", []),
                "task": event.get("task"),
                "phase": event.get("phase")
            }
            self.collaboration_events.append(collab_data)
            
            agents_str = " + ".join(event.get("agents", []))
            print(f"🤝 Collaboration: {agents_str} -> {event.get('task')}")
            
        elif event_type == "generation_progress":
            progress = event.get("progress", 0)
            stage = event.get("stage", "unknown")
            print(f"📊 Generation Progress: {progress}% - {stage}")
            
        elif event_type == "agent_communication":
            sender = event.get("sender")
            receiver = event.get("receiver")
            message_type = event.get("message_type")
            print(f"💬 {sender} → {receiver}: {message_type}")
    
    async def get_agent_metrics(self) -> Dict[str, Any]:
        """Fetch current agent metrics"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/agents/metrics") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"Failed to get agent metrics: {resp.status}")
                    return {}
        except Exception as e:
            print(f"Error fetching agent metrics: {e}")
            return {}
    
    async def visualize_agent_collaboration(self):
        """Create a visual representation of agent collaboration"""
        print("\n" + "="*60)
        print("AGENT COLLABORATION VISUALIZATION")
        print("="*60)
        
        # Get current agent statuses
        metrics = await self.get_agent_metrics()
        
        agents = metrics.get("agents", {})
        
        # Display agent statuses
        print("\n🤖 AGENT STATUS:")
        for agent_name, agent_data in agents.items():
            status = agent_data.get("status", "unknown")
            load = agent_data.get("cpu_usage", 0)
            tasks = agent_data.get("completed_tasks", 0)
            
            # Status indicator
            if status == "ready":
                status_icon = "🟢"
            elif status == "busy":
                status_icon = "🟡"
            else:
                status_icon = "🔴"
                
            # Load bar
            load_bar = "█" * int(load / 10) + "░" * (10 - int(load / 10))
            
            print(f"{status_icon} {agent_name:20} [{load_bar}] {load:.1f}% | Tasks: {tasks}")
        
        # Display recent collaborations
        if self.collaboration_events:
            print("\n🤝 RECENT COLLABORATIONS:")
            for event in self.collaboration_events[-5:]:  # Last 5 events
                time_str = event["timestamp"].split("T")[1].split(".")[0]
                agents = " + ".join(event["agents"])
                task = event["task"]
                print(f"  {time_str} | {agents:30} | {task}")
        
        # Display communication flow
        print("\n💬 AGENT COMMUNICATION FLOW:")
        print("  ContentAgent ──→ QualityAgent ──→ ExportAgent")
        print("       ↓                ↓                ↓")
        print("  DomainAgent ←──────────┴────────────────┘")
        
    async def simulate_generation_workflow(self):
        """Simulate and monitor a complete generation workflow"""
        print("\n🎬 Starting Generation Workflow Simulation...")
        
        # Simulate workflow stages
        stages = [
            ("Initializing", 5),
            ("Content Analysis", 15),
            ("Domain Extraction", 25),
            ("Knowledge Graph Building", 40),
            ("Content Generation", 60),
            ("Quality Assurance", 75),
            ("Animation Creation", 85),
            ("Final Export", 95),
            ("Complete", 100)
        ]
        
        for stage, progress in stages:
            # Display progress
            bar_length = 40
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            print(f"\r[{bar}] {progress}% - {stage}", end="", flush=True)
            
            # Simulate agent activity
            if progress == 15:
                print(f"\n  → ContentAgent: Analyzing PDF structure")
            elif progress == 25:
                print(f"\n  → DomainAgent: Extracting knowledge domains")
            elif progress == 40:
                print(f"\n  → GraphRAG: Building knowledge connections")
            elif progress == 60:
                print(f"\n  → ContentAgent: Generating educational content")
            elif progress == 75:
                print(f"\n  → QualityAgent: Validating pedagogical quality")
            elif progress == 85:
                print(f"\n  → AnimationAgent: Creating visual explanations")
                
            await asyncio.sleep(0.5)
        
        print("\n\n✅ Workflow Complete!")
    
    async def monitor_dashboard(self):
        """Display a real-time monitoring dashboard"""
        print("\n" + "="*60)
        print("CERTIFY STUDIO - REAL-TIME AGENT MONITORING")
        print("="*60)
        
        try:
            while True:
                # Clear screen (works on Windows)
                print("\033[H\033[J", end="")
                
                # Header
                print("="*60)
                print(f"CERTIFY STUDIO - AGENT MONITOR | {datetime.now().strftime('%H:%M:%S')}")
                print("="*60)
                
                # Get latest metrics
                metrics = await self.get_agent_metrics()
                
                # System overview
                total_agents = len(metrics.get("agents", {}))
                active_agents = sum(1 for a in metrics.get("agents", {}).values() 
                                   if a.get("status") == "busy")
                
                print(f"\n📊 SYSTEM OVERVIEW:")
                print(f"  Total Agents: {total_agents}")
                print(f"  Active Agents: {active_agents}")
                print(f"  Queue Depth: {metrics.get('queue_depth', 0)}")
                print(f"  Avg Response Time: {metrics.get('avg_response_time', 0):.2f}ms")
                
                # Agent details
                print(f"\n🤖 AGENT STATUS:")
                agents = metrics.get("agents", {})
                
                for agent_name, agent_data in agents.items():
                    status = agent_data.get("status", "unknown")
                    
                    # Color coding (simplified for terminal)
                    if status == "ready":
                        status_display = "[READY]"
                    elif status == "busy":
                        status_display = "[BUSY ]"
                    else:
                        status_display = "[ERROR]"
                    
                    print(f"  {status_display} {agent_name:20} | "
                          f"CPU: {agent_data.get('cpu_usage', 0):3.0f}% | "
                          f"RAM: {agent_data.get('memory_usage', 0):3.0f}% | "
                          f"Tasks: {agent_data.get('completed_tasks', 0)}")
                
                # Recent events
                print(f"\n📋 RECENT EVENTS:")
                if self.collaboration_events:
                    for event in self.collaboration_events[-3:]:
                        time_str = event["timestamp"].split("T")[1].split(".")[0]
                        print(f"  {time_str} - {event['task']}")
                else:
                    print("  No recent events")
                
                print(f"\n[Press Ctrl+C to exit]")
                
                # Update every 2 seconds
                await asyncio.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped.")
    
    async def test_agent_collaboration(self):
        """Test real agent collaboration with sample data"""
        print("\n🧪 Testing Agent Collaboration...")
        
        # Simulate a collaboration request
        test_data = {
            "task": "Generate AWS AI Certification Content",
            "agents": ["ContentAgent", "DomainAgent", "QualityAgent"],
            "requirements": {
                "format": "interactive",
                "difficulty": "intermediate",
                "topics": ["Machine Learning", "AI Services", "Best Practices"]
            }
        }
        
        print(f"\n📤 Sending collaboration request:")
        print(json.dumps(test_data, indent=2))
        
        # Make API call to trigger collaboration
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/agents/collaborate",
                json=test_data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"\n✅ Collaboration initiated:")
                    print(f"  Task ID: {result.get('task_id')}")
                    print(f"  Estimated Time: {result.get('estimated_time')}s")
                else:
                    print(f"\n❌ Collaboration failed: {resp.status}")
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")

async def main():
    """Main function to run agent monitoring"""
    print("🚀 Starting Certify Studio Agent Monitor...")
    
    monitor = AgentDataMonitor()
    
    # Menu
    print("\nSelect monitoring mode:")
    print("1. Real-time WebSocket Monitoring")
    print("2. Agent Collaboration Visualization")
    print("3. Workflow Simulation")
    print("4. Live Dashboard")
    print("5. Test Agent Collaboration")
    print("6. Run All Tests")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    async with monitor:
        if choice == "1":
            await monitor.connect_websocket()
        elif choice == "2":
            await monitor.visualize_agent_collaboration()
        elif choice == "3":
            await monitor.simulate_generation_workflow()
        elif choice == "4":
            await monitor.monitor_dashboard()
        elif choice == "5":
            await monitor.test_agent_collaboration()
        elif choice == "6":
            # Run all tests
            await monitor.visualize_agent_collaboration()
            await monitor.simulate_generation_workflow()
            await monitor.test_agent_collaboration()
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    asyncio.run(main())
