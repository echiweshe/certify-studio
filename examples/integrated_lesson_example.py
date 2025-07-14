"""
Complete Example: AWS VPC Lesson with Integrated Troubleshooting

This example demonstrates how Certify Studio combines:
1. Domain Extraction (for educational content)
2. GraphRAG (for troubleshooting scenarios)

Following the pedagogical continuum from introduction to real-world problem solving.
"""

import asyncio
from datetime import datetime
import json

from certify_studio.agents.specialized.domain_extraction import DomainExtractionAgent
from certify_studio.agents.specialized.domain_extraction.knowledge_graph_builder import KnowledgeGraphBuilder
from certify_studio.graphrag import (
    GraphRAGConfig,
    GraphRAGTroubleshooter,
    IntegratedLessonGenerator,
    LessonOrchestrator,
    TroubleshootingIssue,
    RootCause,
    Solution,
    IssueType,
    Severity,
    RelationshipType
)


async def setup_graphrag_knowledge_base():
    """Populate GraphRAG with VPC troubleshooting knowledge."""
    config = GraphRAGConfig(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="certify-studio-2024"
    )
    
    troubleshooter = GraphRAGTroubleshooter(config)
    await troubleshooter.initialize()
    
    # Add common VPC issues
    issues = [
        TroubleshootingIssue(
            title="EC2 instance cannot connect to internet",
            description="Instance in private subnet cannot reach external services",
            symptoms=[
                "Connection timeouts",
                "Cannot resolve DNS",
                "No route to host",
                "Ping fails to 8.8.8.8"
            ],
            type=IssueType.CONNECTIVITY,
            severity=Severity.HIGH,
            affected_components=["EC2", "VPC", "Internet Gateway", "Route Table", "NAT Gateway"],
            occurrence_count=156,
            resolution_rate=0.92,
            avg_resolution_time=15.5
        ),
        TroubleshootingIssue(
            title="RDS connection refused from EC2",
            description="Application cannot connect to RDS database from EC2 instance",
            symptoms=[
                "Connection refused error",
                "Timeout after 30 seconds",
                "Database unreachable",
                "Application startup fails"
            ],
            type=IssueType.CONNECTIVITY,
            severity=Severity.HIGH,
            affected_components=["RDS", "EC2", "Security Groups", "VPC", "Subnets"],
            occurrence_count=89,
            resolution_rate=0.95,
            avg_resolution_time=12.0
        ),
        TroubleshootingIssue(
            title="Lambda function cannot access VPC resources",
            description="Lambda function times out when trying to access resources in VPC",
            symptoms=[
                "Function timeout",
                "Cannot connect to RDS",
                "Cannot reach EC2 instances",
                "ENI attachment delays"
            ],
            type=IssueType.CONFIGURATION,
            severity=Severity.MEDIUM,
            affected_components=["Lambda", "VPC", "Security Groups", "Subnets", "ENI"],
            occurrence_count=67,
            resolution_rate=0.88,
            avg_resolution_time=20.0
        )
    ]
    
    # Add issues to GraphRAG
    issue_ids = []
    for issue in issues:
        issue_id = await troubleshooter.add_issue(issue)
        issue_ids.append(issue_id)
        print(f"Added issue: {issue.title}")
    
    # Add root causes
    root_causes = [
        # For EC2 internet connectivity
        RootCause(
            issue_id=issue_ids[0],
            title="Missing Internet Gateway",
            description="VPC does not have an Internet Gateway attached",
            likelihood=0.3,
            diagnostic_steps=[
                "Check VPC configuration in console",
                "Verify Internet Gateway exists",
                "Check if IGW is attached to VPC"
            ],
            verification_commands=[
                "aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values=vpc-xxxxx"
            ],
            evidence_patterns=["No IGW attached", "Empty result set"],
            confidence_score=0.95
        ),
        RootCause(
            issue_id=issue_ids[0],
            title="Incorrect Route Table",
            description="Route table missing default route to Internet Gateway",
            likelihood=0.5,
            diagnostic_steps=[
                "Check subnet route table association",
                "Verify 0.0.0.0/0 route exists",
                "Confirm route points to IGW"
            ],
            verification_commands=[
                "aws ec2 describe-route-tables --route-table-ids rtb-xxxxx"
            ],
            evidence_patterns=["No 0.0.0.0/0 route", "Route points to wrong target"],
            confidence_score=0.92
        ),
        # For RDS connectivity
        RootCause(
            issue_id=issue_ids[1],
            title="Security Group Blocking",
            description="Security group not allowing database port from EC2",
            likelihood=0.7,
            diagnostic_steps=[
                "Check RDS security group rules",
                "Verify EC2 security group ID",
                "Confirm port 3306/5432 is open"
            ],
            verification_commands=[
                "aws ec2 describe-security-groups --group-ids sg-xxxxx"
            ],
            evidence_patterns=["No inbound rule for database port", "Wrong source security group"],
            confidence_score=0.98
        )
    ]
    
    # Add root causes
    cause_ids = []
    for cause in root_causes:
        cause_id = await troubleshooter.add_root_cause(cause)
        cause_ids.append(cause_id)
        print(f"Added root cause: {cause.title}")
    
    # Add solutions
    solutions = [
        Solution(
            title="Attach Internet Gateway",
            description="Create and attach an Internet Gateway to enable internet access",
            steps=[
                "Create new Internet Gateway",
                "Attach IGW to VPC",
                "Update route table with 0.0.0.0/0 → IGW",
                "Verify connectivity"
            ],
            commands=[
                "aws ec2 create-internet-gateway",
                "aws ec2 attach-internet-gateway --vpc-id vpc-xxxxx --internet-gateway-id igw-xxxxx",
                "aws ec2 create-route --route-table-id rtb-xxxxx --destination-cidr-block 0.0.0.0/0 --gateway-id igw-xxxxx"
            ],
            prerequisites=["VPC ID", "Admin permissions", "Route table ID"],
            success_rate=0.95,
            avg_implementation_time=5.0,
            risk_level="low",
            verification_steps=["Ping 8.8.8.8", "Curl https://api.ipify.org"],
            applies_to_issues=[issue_ids[0]],
            applies_to_causes=[cause_ids[0]]
        ),
        Solution(
            title="Configure Security Group for RDS",
            description="Update security group to allow database connections from EC2",
            steps=[
                "Identify EC2 security group",
                "Modify RDS security group",
                "Add inbound rule for database port",
                "Test connection"
            ],
            commands=[
                "aws ec2 authorize-security-group-ingress --group-id sg-rds --protocol tcp --port 3306 --source-group sg-ec2"
            ],
            prerequisites=["RDS security group ID", "EC2 security group ID", "Database port"],
            success_rate=0.98,
            avg_implementation_time=3.0,
            risk_level="low",
            verification_steps=["telnet rds-endpoint 3306", "mysql -h rds-endpoint -u admin -p"],
            applies_to_issues=[issue_ids[1]],
            applies_to_causes=[cause_ids[2]]
        )
    ]
    
    # Add solutions
    for solution in solutions:
        await troubleshooter.add_solution(solution)
        print(f"Added solution: {solution.title}")
    
    return troubleshooter


async def generate_vpc_lesson():
    """Generate a complete VPC lesson with troubleshooting."""
    # Initialize components
    domain_extractor = DomainExtractionAgent()
    knowledge_graph_builder = KnowledgeGraphBuilder()
    
    # Setup GraphRAG
    troubleshooter = await setup_graphrag_knowledge_base()
    
    # Initialize lesson generator
    lesson_generator = IntegratedLessonGenerator(
        domain_extractor=domain_extractor,
        knowledge_graph_builder=knowledge_graph_builder,
        troubleshooter=troubleshooter,
        graphrag_config=troubleshooter.config
    )
    
    # Sample VPC content for domain extraction
    vpc_content = """
    Amazon Virtual Private Cloud (VPC) enables you to launch AWS resources into a virtual network 
    that you've defined. This virtual network closely resembles a traditional network that you'd 
    operate in your own data center, with the benefits of using the scalable infrastructure of AWS.
    
    Key VPC Components:
    - Subnets: Range of IP addresses in your VPC
    - Route Tables: Rules that determine where network traffic is directed
    - Internet Gateway: Allows communication between VPC and internet
    - NAT Gateway: Enables outbound internet access for private subnets
    - Security Groups: Virtual firewall controlling inbound and outbound traffic
    - Network ACLs: Additional layer of security at subnet level
    
    Common VPC Configurations:
    1. Public Subnet: Has route to Internet Gateway
    2. Private Subnet: No direct route to internet
    3. VPN-Only Subnet: Connected via VPN to corporate network
    
    Best Practices:
    - Use multiple Availability Zones for high availability
    - Implement least privilege security group rules
    - Use VPC Flow Logs for network monitoring
    - Plan IP address ranges carefully (CIDR blocks)
    """
    
    # Generate the complete lesson
    lesson = await lesson_generator.generate_lesson(
        topic="AWS VPC Configuration and Troubleshooting",
        domain="AWS Solutions Architect",
        source_content=vpc_content,
        difficulty_level="intermediate",
        include_advanced_troubleshooting=True
    )
    
    return lesson


async def demonstrate_integrated_system():
    """Demonstrate the complete integrated system."""
    print("=== Certify Studio Integrated Lesson Generation ===\n")
    
    # Generate VPC lesson
    print("Generating comprehensive VPC lesson...")
    lesson = await generate_vpc_lesson()
    
    # Display lesson structure
    print(f"\nLesson: {lesson.topic}")
    print(f"Duration: {lesson.estimated_duration} minutes")
    print(f"Difficulty: {lesson.difficulty_level}")
    
    print("\nLearning Objectives:")
    for obj in lesson.learning_objectives:
        print(f"  - {obj}")
    
    print("\nLesson Sections:")
    for section, content in lesson.sections.items():
        print(f"  - {section.value}: {len(str(content))} characters")
    
    # Show troubleshooting integration
    print("\nTroubleshooting Scenarios:")
    for scenario in lesson.troubleshooting_scenarios:
        print(f"  - {scenario['issue']}")
        print(f"    Severity: {scenario['severity']}")
        print(f"    Root Causes: {len(scenario.get('root_causes', []))}")
        print(f"    Solution Available: {'Yes' if scenario.get('solution') else 'No'}")
    
    # Export to markdown
    print("\nExporting lesson to markdown...")
    markdown_content = lesson.to_markdown()
    
    # Save the lesson
    with open("example_vpc_lesson.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print("Lesson exported to example_vpc_lesson.md")
    
    # Demonstrate course module generation
    print("\n=== Generating Complete Course Module ===")
    
    orchestrator = LessonOrchestrator(
        IntegratedLessonGenerator(
            domain_extractor=DomainExtractionAgent(),
            knowledge_graph_builder=KnowledgeGraphBuilder(),
            troubleshooter=await setup_graphrag_knowledge_base(),
            graphrag_config=GraphRAGConfig()
        )
    )
    
    # Generate multiple lessons for a module
    module_topics = [
        "VPC Fundamentals",
        "Security Groups and NACLs",
        "VPC Peering and Transit Gateway",
        "VPC Endpoints and PrivateLink"
    ]
    
    print(f"\nGenerating module with {len(module_topics)} lessons...")
    module_lessons = await orchestrator.generate_course_module(
        module_name="Advanced VPC Networking",
        topics=module_topics,
        domain="AWS Solutions Architect"
    )
    
    print("\nModule generation complete!")
    print(f"Total lessons: {len(module_lessons)}")
    total_duration = sum(lesson.estimated_duration for lesson in module_lessons.values())
    print(f"Total module duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
    
    # Export module
    module_path = await orchestrator.export_module_to_markdown(
        module_name="Advanced VPC Networking",
        lessons=module_lessons,
        output_path="./output"
    )
    
    print(f"\nModule exported to: {module_path}")
    
    # Show knowledge graph statistics
    print("\n=== Knowledge Graph Statistics ===")
    for topic, lesson in module_lessons.items():
        kg = lesson.knowledge_graph
        print(f"\n{topic}:")
        print(f"  - Nodes: {len(kg.get('nodes', []))}")
        print(f"  - Edges: {len(kg.get('edges', []))}")
        print(f"  - Troubleshooting Scenarios: {len(lesson.troubleshooting_scenarios)}")


async def interactive_troubleshooting_demo():
    """Demonstrate interactive troubleshooting with GraphRAG."""
    print("\n=== Interactive Troubleshooting Demo ===\n")
    
    # Setup troubleshooter
    troubleshooter = await setup_graphrag_knowledge_base()
    
    # Simulate student queries
    student_queries = [
        "My EC2 instance in a private subnet can't download updates",
        "Database connection timing out from my application",
        "Lambda function fails when trying to connect to RDS"
    ]
    
    for query in student_queries:
        print(f"\nStudent Query: '{query}'")
        
        # Get diagnosis
        result = await troubleshooter.diagnose(
            query,
            context={
                "student_level": "intermediate",
                "previous_attempts": [],
                "environment": "development"
            }
        )
        
        print(f"Identified Issues: {len(result.identified_issues)}")
        print(f"Diagnostic Paths: {len(result.diagnostic_paths)}")
        
        # Show top diagnostic path
        if result.diagnostic_paths:
            top_path = result.diagnostic_paths[0]
            print(f"\nRecommended Diagnostic Path (Confidence: {top_path.confidence:.2f}):")
            
            steps = top_path.get_readable_path()
            for i, step in enumerate(steps, 1):
                print(f"  {i}. {step}")
        
        # Show recommended solution
        if result.solutions:
            solution = result.solutions[0]
            print(f"\nRecommended Solution: {solution.title}")
            print(f"Success Rate: {solution.success_rate:.0%}")
            print(f"Implementation Time: {solution.avg_implementation_time:.0f} minutes")
            
            print("\nSteps:")
            for i, step in enumerate(solution.steps, 1):
                print(f"  {i}. {step}")


if __name__ == "__main__":
    # Run the complete demonstration
    asyncio.run(demonstrate_integrated_system())
    
    # Run interactive troubleshooting demo
    asyncio.run(interactive_troubleshooting_demo())
