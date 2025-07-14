"""
Unified GraphRAG Example - The ONE System for Everything

This example demonstrates how Certify Studio uses ONE unified GraphRAG system
for all knowledge operations, following the IMMUTABLE VISION.
"""

import asyncio
from pathlib import Path
from datetime import datetime

from certify_studio.knowledge import (
    UnifiedGraphRAG,
    UnifiedGraphNode,
    UnifiedGraphEdge,
    UnifiedNodeType,
    UnifiedRelationType,
    GraphRAGQuery,
    GraphRAGResult
)
from certify_studio.knowledge.migration import create_unified_system
from certify_studio.agents.specialized.domain_extraction.models import ExtractionRequest


async def demonstrate_unified_system():
    """Demonstrate the unified GraphRAG system."""
    print("=== Certify Studio Unified GraphRAG Demo ===\n")
    
    # Create unified system
    print("1. Creating unified GraphRAG system...")
    graphrag, domain_agent = await create_unified_system()
    print("✓ Unified system initialized\n")
    
    # Extract domain knowledge
    print("2. Extracting domain knowledge from certification guide...")
    
    # Sample AWS content
    sample_content = """
    # AWS EC2 and VPC Fundamentals
    
    ## EC2 Instances
    Amazon EC2 provides scalable computing capacity in the AWS cloud. 
    Key concepts include instance types, AMIs, and security groups.
    
    Common issues:
    - Instance cannot connect to internet: Check Internet Gateway and route tables
    - SSH connection refused: Verify security group rules allow port 22
    
    ## VPC Networking
    Amazon VPC lets you provision a logically isolated section of the AWS cloud.
    
    Prerequisites: Understanding of networking concepts, subnets, and routing.
    
    Common issues:
    - Resources in different subnets cannot communicate: Check NACLs and routing
    - Cannot reach RDS from EC2: Ensure security groups allow database port
    
    ## Best Practices
    - Use separate subnets for different tiers (web, app, database)
    - Implement least privilege security group rules
    - Enable VPC Flow Logs for troubleshooting
    """
    
    # Create temporary file
    temp_file = Path("temp_aws_guide.md")
    temp_file.write_text(sample_content)
    
    try:
        # Extract knowledge
        request = ExtractionRequest(
            document_paths=[str(temp_file)],
            domain_name="AWS Solutions Architect",
            certification_name="AWS-SAA-C03"
        )
        
        result = await domain_agent.extract_domain_knowledge(request)
        
        if result.success:
            print(f"✓ Extracted {len(result.domain_knowledge.concepts)} concepts")
            print(f"✓ Found {len(result.domain_knowledge.relationships)} relationships")
            print(f"✓ Imported into unified graph: {result.metadata.get('unified_graph_stats', {})}\n")
        else:
            print(f"✗ Extraction failed: {result.error}\n")
            
    finally:
        # Clean up
        temp_file.unlink(missing_ok=True)
        
    # Demonstrate unified search capabilities
    print("3. Demonstrating unified search capabilities...\n")
    
    # Educational search
    print("a) Educational Query: 'How do EC2 instances connect to the internet?'")
    edu_query = GraphRAGQuery(
        query_text="How do EC2 instances connect to the internet?",
        query_type="educational",
        max_results=5,
        include_explanations=True
    )
    
    edu_result = await graphrag.search(edu_query)
    print(f"   Found {len(edu_result.nodes)} relevant concepts:")
    for i, node in enumerate(edu_result.nodes[:3]):
        print(f"   {i+1}. {node.name} ({node.type.value}) - Score: {node.confidence_score:.2f}")
    if edu_result.explanations:
        print(f"   Explanation: {edu_result.explanations[0]}\n")
    
    # Troubleshooting search
    print("b) Troubleshooting Query: 'EC2 instance cannot connect to RDS database'")
    trouble_query = GraphRAGQuery(
        query_text="EC2 instance cannot connect to RDS database",
        query_type="troubleshooting",
        max_results=5,
        include_paths=True
    )
    
    trouble_result = await graphrag.search(trouble_query)
    print(f"   Found {len(trouble_result.nodes)} nodes in diagnostic path:")
    
    # Show diagnostic path
    if trouble_result.paths:
        print("   Diagnostic Path:")
        for path in trouble_result.paths[:1]:  # First path
            for i, node_id in enumerate(path):
                node = next((n for n in trouble_result.nodes if n.id == node_id), None)
                if node:
                    print(f"   {i+1}. {node.name} ({node.type.value})")
    print()
    
    # General search (combines everything)
    print("c) General Query: 'VPC security best practices'")
    general_query = GraphRAGQuery(
        query_text="VPC security best practices",
        query_type="general",
        max_results=5
    )
    
    general_result = await graphrag.search(general_query)
    print(f"   Found {len(general_result.nodes)} relevant results:")
    for i, node in enumerate(general_result.nodes[:3]):
        print(f"   {i+1}. {node.name} - Type: {node.type.value}")
    print()
    
    # Add custom knowledge (troubleshooting scenario)
    print("4. Adding custom troubleshooting knowledge...")
    
    # Add an issue
    issue_node = UnifiedGraphNode(
        type=UnifiedNodeType.ISSUE,
        name="EC2 Connection Timeout to RDS",
        description="EC2 instance experiences timeout when connecting to RDS database",
        content={
            "symptoms": ["Connection timeout after 30s", "No response from database"],
            "severity": "high",
            "frequency": "common"
        },
        importance_score=0.9
    )
    issue_id = await graphrag.add_node(issue_node)
    
    # Add root cause
    cause_node = UnifiedGraphNode(
        type=UnifiedNodeType.CAUSE,
        name="Security Group Misconfiguration",
        description="RDS security group not allowing inbound traffic from EC2",
        content={
            "diagnostic_steps": [
                "Check RDS security group rules",
                "Verify EC2 security group ID",
                "Ensure port 3306/5432 is allowed"
            ]
        }
    )
    cause_id = await graphrag.add_node(cause_node)
    
    # Add solution
    solution_node = UnifiedGraphNode(
        type=UnifiedNodeType.SOLUTION,
        name="Update RDS Security Group",
        description="Add inbound rule to allow database port from EC2 security group",
        content={
            "steps": [
                "Navigate to RDS instance security group",
                "Add inbound rule for database port",
                "Set source to EC2 security group ID",
                "Save and test connection"
            ],
            "success_rate": 0.95
        },
        success_rate=0.95
    )
    solution_id = await graphrag.add_node(solution_node)
    
    # Connect them
    await graphrag.add_edge(UnifiedGraphEdge(
        source_id=issue_id,
        target_id=cause_id,
        type=UnifiedRelationType.CAUSES
    ))
    
    await graphrag.add_edge(UnifiedGraphEdge(
        source_id=cause_id,
        target_id=solution_id,
        type=UnifiedRelationType.RESOLVES
    ))
    
    print("✓ Added troubleshooting scenario to unified graph\n")
    
    # Test the new knowledge
    print("5. Testing integrated knowledge...")
    test_query = GraphRAGQuery(
        query_text="EC2 timeout connecting to RDS",
        query_type="troubleshooting",
        max_results=5
    )
    
    test_result = await graphrag.search(test_query)
    print(f"   Found complete diagnostic path with {len(test_result.nodes)} nodes")
    print(f"   Confidence: {test_result.confidence:.2f}\n")
    
    # Show unified nature
    print("6. Demonstrating unified knowledge graph...")
    
    # This query will find BOTH educational concepts AND troubleshooting info
    unified_query = GraphRAGQuery(
        query_text="security groups",
        query_type="general",
        max_results=10,
        max_depth=2  # Explore relationships
    )
    
    unified_result = await graphrag.search(unified_query)
    
    # Group by type
    by_type = {}
    for node in unified_result.nodes:
        node_type = node.type.value
        if node_type not in by_type:
            by_type[node_type] = []
        by_type[node_type].append(node.name)
        
    print("   Found knowledge across multiple types:")
    for node_type, names in by_type.items():
        print(f"   - {node_type}: {', '.join(names[:3])}")
        if len(names) > 3:
            print(f"     ... and {len(names) - 3} more")
    print()
    
    print("=== Demo Complete ===")
    print("\nKey Insights:")
    print("1. ONE unified system handles all knowledge types")
    print("2. Educational content and troubleshooting are connected")
    print("3. No separate RAG and GraphRAG - just GraphRAG")
    print("4. Follows the IMMUTABLE VISION of one AI Operating System")
    
    # Close the connection
    await graphrag.close()


async def show_migration_path():
    """Show how to migrate existing systems."""
    print("\n=== Migration Path ===\n")
    
    print("For existing deployments with separate ChromaDB + Knowledge Base:")
    print("""
    from certify_studio.knowledge.migration import migrate_to_unified_system
    
    # This will:
    # 1. Create unified GraphRAG system
    # 2. Migrate Domain Extraction Agent to use it
    # 3. Import existing data
    # 4. Validate the migration
    
    unified_system = await migrate_to_unified_system()
    """)
    
    print("\nFor new deployments:")
    print("""
    from certify_studio.knowledge.migration import create_unified_system
    
    # This creates a fresh unified system
    graphrag, domain_agent = await create_unified_system()
    """)
    
    print("\nThe beauty: Same interface, but ONE system underneath!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demonstrate_unified_system())
    
    # Show migration information
    asyncio.run(show_migration_path())
