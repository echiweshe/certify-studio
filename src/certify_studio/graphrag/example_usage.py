"""
Example usage of the GraphRAG troubleshooting system.

This demonstrates how to use the GraphRAG implementation for
customer support and troubleshooting scenarios.
"""

import asyncio
from uuid import uuid4

from certify_studio.graphrag import (
    GraphRAGConfig,
    GraphRAGIndex,
    GraphRAGTroubleshooter,
    TroubleshootingIssue,
    RootCause,
    Solution,
    IssueType,
    Severity,
    RelationshipType
)
from certify_studio.graphrag.knowledge_integration import (
    KnowledgeGraphIntegrator,
    HybridSearchEngine
)


async def setup_graphrag_system():
    """Initialize the GraphRAG system."""
    
    # Configure GraphRAG
    config = GraphRAGConfig(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="your-password",
        embedding_model="text-embedding-ada-002",
        enable_learning=True
    )
    
    # Create GraphRAG index
    graph_index = GraphRAGIndex(config)
    await graph_index.initialize()
    
    # Create troubleshooter
    troubleshooter = GraphRAGTroubleshooter(graph_index)
    
    return graph_index, troubleshooter


async def populate_sample_data(graph_index: GraphRAGIndex):
    """Populate the graph with sample troubleshooting data."""
    
    # Add EC2 connectivity issue
    ec2_issue = TroubleshootingIssue(
        title="EC2 instance unreachable",
        description="Cannot connect to EC2 instance via SSH or HTTP",
        symptoms=[
            "SSH connection timeout",
            "Cannot ping instance",
            "Website not loading"
        ],
        type=IssueType.CONNECTIVITY,
        severity=Severity.HIGH,
        affected_components=["EC2", "Security Groups", "VPC"]
    )
    
    issue_id = await graph_index.graph_store.add_issue(ec2_issue)
    
    # Add root causes
    security_group_cause = RootCause(
        issue_id=ec2_issue.id,
        title="Security group blocking traffic",
        description="Inbound rules not configured correctly",
        likelihood=0.8,
        diagnostic_steps=[
            "Check security group inbound rules",
            "Verify port 22 (SSH) is open",
            "Verify port 80/443 (HTTP/HTTPS) is open",
            "Check source IP restrictions"
        ],
        verification_commands=[
            "aws ec2 describe-security-groups --group-ids sg-xxx",
            "telnet instance-ip 22"
        ]
    )
    
    await graph_index.graph_store.add_root_cause(security_group_cause)
    
    # Add solution
    sg_solution = Solution(
        title="Update security group rules",
        description="Add inbound rules to allow required traffic",
        steps=[
            "Navigate to EC2 console",
            "Select Security Groups",
            "Find the security group attached to instance",
            "Edit inbound rules",
            "Add rule for SSH (port 22) from your IP",
            "Add rule for HTTP/HTTPS if needed",
            "Save rules"
        ],
        commands=[
            "aws ec2 authorize-security-group-ingress --group-id sg-xxx --protocol tcp --port 22 --cidr your-ip/32"
        ],
        prerequisites=["AWS Console access or CLI credentials"],
        success_rate=0.95,
        avg_implementation_time=5.0,
        risk_level="low",
        applies_to_issues=[ec2_issue.id],
        applies_to_causes=[security_group_cause.id]
    )
    
    await graph_index.graph_store.add_solution(sg_solution)
    
    print("Sample data populated successfully!")


async def demonstrate_troubleshooting():
    """Demonstrate the troubleshooting workflow."""
    
    # Setup system
    graph_index, troubleshooter = await setup_graphrag_system()
    
    # Populate sample data
    await populate_sample_data(graph_index)
    
    print("\n=== GraphRAG Troubleshooting Demo ===\n")
    
    # Example 1: Simple troubleshooting query
    print("Example 1: Basic Troubleshooting")
    print("-" * 40)
    
    query1 = "I cannot SSH into my EC2 instance"
    result1 = await troubleshooter.diagnose(query1)
    
    print(f"Query: {query1}")
    print(f"Diagnosis: {result1['diagnosis']['issue_type']} issue with {result1['diagnosis']['severity']} severity")
    print(f"Confidence: {result1['diagnosis']['confidence']:.2%}")
    
    if result1['recommended_solutions']:
        solution = result1['recommended_solutions'][0]
        print(f"\nRecommended Solution: {solution['title']}")
        print(f"Reasoning: {solution['reasoning']}")
        print(f"Estimated Time: {solution['estimated_time']} minutes")
        print(f"Risk Level: {solution['risk_level']}")
    
    # Example 2: Complex troubleshooting with context
    print("\n\nExample 2: Contextual Troubleshooting")
    print("-" * 40)
    
    query2 = "My website hosted on EC2 is loading very slowly"
    context2 = {
        "affected_systems": ["EC2", "RDS", "CloudFront"],
        "recent_changes": ["Deployed new version yesterday"],
        "business_critical": True
    }
    
    result2 = await troubleshooter.diagnose(query2, context2)
    
    print(f"Query: {query2}")
    print(f"Context: Business critical system with recent deployment")
    print(f"Issue Type: {result2['diagnosis']['issue_type']}")
    
    print("\nDiagnostic Path:")
    for i, path in enumerate(result2['diagnostic_paths'][:2], 1):
        print(f"  Path {i}: {path['complexity']} steps, {path['confidence']:.2%} confidence")
    
    print("\nRoot Causes:")
    for cause in result2['root_causes'][:3]:
        print(f"  - {cause['title']} ({cause['likelihood']:.0%} likely)")
    
    # Example 3: Pattern detection
    print("\n\nExample 3: Pattern Detection")
    print("-" * 40)
    
    # Simulate historical issues
    historical_issues = [
        TroubleshootingIssue(
            title="EC2 high CPU",
            type=IssueType.PERFORMANCE,
            symptoms=["slow response", "high load"]
        ),
        TroubleshootingIssue(
            title="RDS connection issues",
            type=IssueType.CONNECTIVITY,
            symptoms=["timeout", "connection refused"]
        )
    ]
    
    query3 = "Multiple services experiencing timeouts"
    context3 = {"historical_issues": historical_issues}
    
    result3 = await troubleshooter.diagnose(query3, context3)
    
    if result3['patterns_detected']:
        print(f"⚠️ Pattern Detected: {result3['patterns_detected'][0]['name']}")
        print(f"Description: {result3['patterns_detected'][0]['description']}")
        print("\nEarly Warning Signs:")
        for sign in result3['patterns_detected'][0]['early_warnings']:
            print(f"  - {sign}")
    
    # Example 4: Troubleshooting session
    print("\n\nExample 4: Full Troubleshooting Session")
    print("-" * 40)
    
    session = await troubleshooter.start_session(
        "Customer reporting database connection errors in production",
        user_id="support-agent-123",
        context={"environment": "production", "urgency": "high"}
    )
    
    print(f"Session ID: {session.id}")
    print(f"Initial Symptoms: {', '.join(session.symptoms)}")
    
    # Simulate applying a solution
    if session.paths_explored:
        print(f"\nExploring {len(session.paths_explored)} diagnostic paths...")
        
    # Close session
    await troubleshooter.close_session(
        str(session.id),
        resolution_successful=True,
        feedback="Security group was blocking RDS connection"
    )
    
    print("\nSession closed successfully!")
    
    # Cleanup
    await graph_index.close()


async def demonstrate_knowledge_integration():
    """Demonstrate integration with learning graph."""
    
    print("\n\n=== Knowledge Integration Demo ===\n")
    
    # Setup
    config = GraphRAGConfig()
    graph_index = GraphRAGIndex(config)
    await graph_index.initialize()
    
    # Create mock learning graph
    learning_graph = nx.DiGraph()
    
    # Create sample concept
    from certify_studio.agents.specialized.domain_extraction.models import Concept, ConceptType
    
    ec2_concept = Concept(
        id=uuid4(),
        name="Amazon EC2",
        type=ConceptType.SERVICE,
        description="Elastic Compute Cloud - Virtual servers in AWS",
        category="compute",
        importance_score=0.9
    )
    
    # Integrate with troubleshooting
    integrator = KnowledgeGraphIntegrator(
        graph_index.graph_store,
        learning_graph
    )
    
    print("Integrating EC2 concept into troubleshooting graph...")
    issue_ids = await integrator.integrate_concept(ec2_concept)
    print(f"Created {len(issue_ids)} troubleshooting issues")
    
    # Generate troubleshooting guide
    guide = await integrator.generate_troubleshooting_guide(ec2_concept)
    
    print(f"\nTroubleshooting Guide for {guide['concept']['name']}:")
    print("-" * 50)
    
    print("\nCommon Issues:")
    for issue in guide['common_issues'][:2]:
        print(f"  - {issue['title']} ({issue['type']})")
        print(f"    Symptoms: {', '.join(issue['symptoms'][:3])}")
    
    print("\nDiagnostic Checklist:")
    for item in guide['diagnostic_checklist'][:3]:
        print(f"  ✓ {item}")
    
    print("\nQuick Fixes:")
    for fix in guide['quick_fixes'][:3]:
        print(f"  • {fix}")
    
    # Hybrid search demo
    print("\n\nHybrid Search Demo:")
    print("-" * 40)
    
    # Mock learning store
    class MockLearningStore:
        async def search(self, query):
            return []
    
    hybrid_engine = HybridSearchEngine(graph_index, MockLearningStore())
    
    search_result = await hybrid_engine.hybrid_search(
        "EC2 instance connectivity problems",
        search_mode="troubleshooting"
    )
    
    print(f"Query: 'EC2 instance connectivity problems'")
    print(f"Found {len(search_result['troubleshooting_results']['issues'])} issues")
    print(f"Found {len(search_result['troubleshooting_results']['solutions'])} solutions")
    
    await graph_index.close()


async def main():
    """Run all demonstrations."""
    
    print("GraphRAG Troubleshooting System Demonstration")
    print("=" * 60)
    
    # Run troubleshooting demo
    await demonstrate_troubleshooting()
    
    # Run knowledge integration demo
    await demonstrate_knowledge_integration()
    
    print("\n\nDemo completed! 🎉")
    print("\nKey Features Demonstrated:")
    print("✅ GraphRAG search combining vector similarity + graph traversal")
    print("✅ Intelligent diagnostic path generation")
    print("✅ Root cause analysis with confidence scoring")
    print("✅ Solution ranking based on context")
    print("✅ Pattern detection for recurring issues")
    print("✅ Integration with learning knowledge graph")
    print("✅ Hybrid search across both knowledge bases")


if __name__ == "__main__":
    # Note: Requires Neo4j to be running
    # docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/your-password neo4j
    
    asyncio.run(main())
