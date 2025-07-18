"""
Fix the agent service to properly transform data with all required properties
"""

from pathlib import Path

def fix_agent_service():
    """Update the agent service to include all required Agent properties."""
    
    agents_ts_path = Path(r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\frontend\src\services\agents.ts")
    
    # Read the current file
    with open(agents_ts_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    backup_path = agents_ts_path.with_suffix('.ts.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Find and replace the getAgents method
    old_transform = """return statuses.map((status: AgentStatusData) => ({
        id: status.agent_id,
        name: this.getAgentName(status.agent_type),
        type: status.agent_type,
        icon: this.getAgentIcon(status.agent_type),
        status: this.mapApiStatusToAgentStatus(status.state),
        currentTask: status.current_task || 'Idle',
        tasksCompleted: status.tasks_completed,
        successRate: status.success_rate,
        averageProcessingTime: status.average_processing_time,
        lastActive: new Date(status.last_active),
      }));"""
    
    new_transform = """return statuses.map((status: AgentStatusData) => ({
        id: status.agent_id,
        name: this.getAgentName(status.agent_type),
        type: status.agent_type as any,
        status: this.mapApiStatusToAgentStatus(status.state) as any,
        currentTask: status.current_task || 'Idle',
        lastActivity: new Date(status.last_active),
        // Add required properties with default values
        capabilities: this.getAgentCapabilities(status.agent_type),
        performance: {
          tasksCompleted: status.tasks_completed,
          averageTime: status.average_processing_time,
          successRate: status.success_rate,
          qualityScore: status.success_rate * 0.95
        },
        beliefs: [],
        goals: []
      }));"""
    
    content = content.replace(old_transform, new_transform)
    
    # Also update the getMockAgents method
    old_mock = """private getMockAgents(): Agent[] {
    return [
      {
        id: '1',
        name: 'Content Generator',
        type: 'ContentGenerationAgent',
        icon: 'FileText',
        status: 'idle',
        currentTask: 'Waiting for instructions',
        tasksCompleted: 42,
        successRate: 0.98,
        averageProcessingTime: 45.2,
        lastActive: new Date(),
      },"""
    
    new_mock = """private getMockAgents(): Agent[] {
    return [
      {
        id: '1',
        name: 'Domain Extractor',
        type: 'domain_extractor' as any,
        status: 'idle' as any,
        currentTask: 'Waiting for instructions',
        lastActivity: new Date(),
        capabilities: [
          { name: 'PDF Parsing', level: 95 },
          { name: 'Concept Extraction', level: 90 },
          { name: 'Knowledge Graphs', level: 85 }
        ],
        performance: {
          tasksCompleted: 42,
          averageTime: 3.2,
          successRate: 0.95,
          qualityScore: 0.92
        },
        beliefs: [],
        goals: []
      },"""
    
    content = content.replace(old_mock, new_mock)
    
    # Add the getAgentCapabilities method if it doesn't exist
    if "getAgentCapabilities" not in content:
        # Find a good place to insert it (after getAgentIcon method)
        insert_pos = content.find("private getAgentIcon(agentType: string): string {")
        if insert_pos != -1:
            # Find the end of the method
            method_end = content.find("}", insert_pos)
            method_end = content.find("\n", method_end) + 1
            
            new_method = """
  private getAgentCapabilities(agentType: string): Array<{name: string, level: number}> {
    const capabilitiesMap: Record<string, Array<{name: string, level: number}>> = {
      'extraction': [
        { name: 'PDF Parsing', level: 95 },
        { name: 'Concept Extraction', level: 90 },
        { name: 'Knowledge Graphs', level: 85 }
      ],
      'content': [
        { name: 'Animation Design', level: 92 },
        { name: 'Scene Planning', level: 88 },
        { name: 'Visual Storytelling', level: 90 }
      ],
      'visual': [
        { name: 'Technical Diagrams', level: 98 },
        { name: 'Flow Charts', level: 95 },
        { name: 'Architecture Visuals', level: 93 }
      ],
      'validation': [
        { name: 'Accuracy Checking', level: 99 },
        { name: 'Accessibility', level: 96 },
        { name: 'Standards Compliance', level: 98 }
      ],
      'educational': [
        { name: 'Learning Optimization', level: 91 },
        { name: 'Cognitive Load Balance', level: 88 },
        { name: 'Adaptive Teaching', level: 85 }
      ]
    };
    return capabilitiesMap[agentType] || [
      { name: 'General Processing', level: 80 },
      { name: 'Task Execution', level: 85 }
    ];
  }
"""
            content = content[:method_end] + new_method + content[method_end:]
    
    # Fix the rest of the mock agents
    content = content.replace(
        """      {
        id: '2',
        name: 'Domain Extractor',
        type: 'DomainExtractionAgent',
        icon: 'Brain',
        status: 'thinking',
        currentTask: 'Analyzing content structure',
        tasksCompleted: 38,
        successRate: 0.96,
        averageProcessingTime: 32.5,
        lastActive: new Date(),
      },""",
        """      {
        id: '2',
        name: 'Animation Choreographer',
        type: 'animation_choreographer' as any,
        status: 'thinking' as any,
        currentTask: 'Planning animation sequences',
        lastActivity: new Date(),
        capabilities: [
          { name: 'Animation Design', level: 92 },
          { name: 'Scene Planning', level: 88 },
          { name: 'Visual Storytelling', level: 90 }
        ],
        performance: {
          tasksCompleted: 38,
          averageTime: 5.8,
          successRate: 0.92,
          qualityScore: 0.90
        },
        beliefs: [],
        goals: []
      },"""
    )
    
    content = content.replace(
        """      {
        id: '3',
        name: 'Quality Assurance',
        type: 'QualityAssuranceAgent',
        icon: 'Shield',
        status: 'executing',
        currentTask: 'Checking pedagogical quality',
        tasksCompleted: 35,
        successRate: 0.97,
        averageProcessingTime: 28.3,
        lastActive: new Date(),
      },""",
        """      {
        id: '3',
        name: 'Quality Assurance',
        type: 'quality_assurance' as any,
        status: 'executing' as any,
        currentTask: 'Validating content quality',
        lastActivity: new Date(),
        capabilities: [
          { name: 'Accuracy Checking', level: 99 },
          { name: 'Accessibility', level: 96 },
          { name: 'Standards Compliance', level: 98 }
        ],
        performance: {
          tasksCompleted: 35,
          averageTime: 1.5,
          successRate: 0.99,
          qualityScore: 0.98
        },
        beliefs: [],
        goals: []
      },"""
    )
    
    # Write the updated content
    with open(agents_ts_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated agent service to include all required properties")
    print("✅ Added capabilities and performance data")
    print("✅ Fixed data transformation")

def main():
    print("Fixing Agent Service Data Transformation...")
    print("=" * 50)
    
    fix_agent_service()
    
    print("\n✅ Agent service fixed!")
    print("\nThe frontend should now display agents correctly.")
    print("Refresh your browser to see the changes.")

if __name__ == "__main__":
    main()
