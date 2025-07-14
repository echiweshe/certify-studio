"""
Test fixtures for Certify Studio tests.
"""

import json
from pathlib import Path
from uuid import uuid4

# Sample PDF content (base64 encoded minimal PDF)
SAMPLE_PDF_BASE64 = """
JVBERi0xLjQKJeLjz9MKNCAwIG9iago8PC9MZW5ndGggNTAvRmlsdGVyL0ZsYXRlRGVjb2RlPj4K
c3RyZWFtCngBKlSPQnMEAEJzBCCECAAZAA8ADQAKACRQIQAhAAoACgAKAAoACgAgASABCmVuZHN0
cmVhbQplbmRvYmoKNSAwIG9iago8PC9UeXBlL1BhZ2UvTWVkaWFCb3hbMCAwIDYxMiA3OTJdL1Jl
c291cmNlczw8L0ZvbnQ8PC9GMSA2IDAgUj4+Pj4vQ29udGVudHMgNCAwIFI+PgplbmRvYmoKNiAw
IG9iago8PC9UeXBlL0ZvbnQvU3VidHlwZS9UeXBlMS9CYXNlRm9udC9IZWx2ZXRpY2E+PgplbmRv
YmoKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKMiAwIG9iago8
PC9UeXBlL1BhZ2VzL0tpZHNbNSAwIFJdL0NvdW50IDE+PgplbmRvYmoKMyAwIG9iago8PC9UeXBl
L1BhZ2VzL0tpZHNbNSAwIFJdL0NvdW50IDE+PgplbmRvYmoKeHJlZgowIDcKMDAwMDAwMDAwMCA2
NTUzNSBmIAowMDAwMDAwMzI2IDAwMDAwIG4gCjAwMDAwMDAzNzQgMDAwMDAgbiAKMDAwMDAwMDQy
MyAwMDAwMCBuIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAwMDAwMDAxMzIgMDAwMDAgbiAKMDAwMDAw
MDI1NyAwMDAwMCBuIAp0cmFpbGVyCjw8L1NpemUgNy9Sb290IDEgMCBSPj4Kc3RhcnR4cmVmCjQ3
MgolJUVPRgo=
"""


def create_sample_pdf(path: Path):
    """Create a sample PDF file for testing."""
    import base64
    
    pdf_content = base64.b64decode(SAMPLE_PDF_BASE64)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf_content)
    return path


def create_sample_certification_data():
    """Create sample certification guide data."""
    return {
        "title": "AWS Solutions Architect - Associate (SAA-C03)",
        "version": "3.0",
        "exam_code": "SAA-C03",
        "domains": [
            {
                "name": "Design Secure Architectures",
                "weight": 0.30,
                "topics": [
                    "Design secure access to AWS resources",
                    "Design secure workloads and applications",
                    "Determine appropriate data security controls"
                ]
            },
            {
                "name": "Design Resilient Architectures",
                "weight": 0.26,
                "topics": [
                    "Design scalable and loosely coupled architectures",
                    "Design highly available and/or fault-tolerant architectures"
                ]
            },
            {
                "name": "Design High-Performing Architectures",
                "weight": 0.24,
                "topics": [
                    "Determine high-performing storage solutions",
                    "Design high-performing and elastic compute solutions",
                    "Determine networking architecture requirements"
                ]
            },
            {
                "name": "Design Cost-Optimized Architectures",
                "weight": 0.20,
                "topics": [
                    "Design cost-effective storage solutions",
                    "Design cost-effective compute solutions",
                    "Design cost-effective network architectures"
                ]
            }
        ],
        "total_questions": 65,
        "duration_minutes": 130,
        "passing_score": 720,
        "score_range": "100-1000"
    }


def create_sample_concepts():
    """Create sample concept data for testing."""
    concepts = []
    
    # EC2 concept
    concepts.append({
        "id": str(uuid4()),
        "name": "Amazon EC2",
        "type": "service",
        "description": "Elastic Compute Cloud - Virtual servers in the cloud",
        "domain": "Compute",
        "difficulty_level": 0.3,
        "prerequisites": [],
        "key_points": [
            "Instance types and families",
            "Pricing models (On-Demand, Reserved, Spot)",
            "Security groups and network ACLs",
            "EBS volumes and instance store"
        ],
        "exam_tips": [
            "Know the different instance types and their use cases",
            "Understand when to use Spot instances",
            "Remember security group rules are stateful"
        ]
    })
    
    # VPC concept
    concepts.append({
        "id": str(uuid4()),
        "name": "Amazon VPC",
        "type": "service",
        "description": "Virtual Private Cloud - Isolated network in AWS",
        "domain": "Networking",
        "difficulty_level": 0.5,
        "prerequisites": ["Basic networking knowledge"],
        "key_points": [
            "Subnets (public and private)",
            "Route tables",
            "Internet Gateway and NAT Gateway",
            "VPC Peering and Transit Gateway"
        ],
        "exam_tips": [
            "Understand CIDR blocks and subnet sizing",
            "Know the difference between IGW and NAT Gateway",
            "Remember VPC Peering limitations"
        ]
    })
    
    # S3 concept
    concepts.append({
        "id": str(uuid4()),
        "name": "Amazon S3",
        "type": "service",
        "description": "Simple Storage Service - Object storage in the cloud",
        "domain": "Storage",
        "difficulty_level": 0.4,
        "prerequisites": [],
        "key_points": [
            "Storage classes (Standard, IA, Glacier)",
            "Bucket policies and ACLs",
            "Versioning and lifecycle policies",
            "Encryption options"
        ],
        "exam_tips": [
            "Know all storage classes and their use cases",
            "Understand lifecycle transitions",
            "Remember S3 is eventually consistent for overwrites"
        ]
    })
    
    return concepts


def create_sample_relationships():
    """Create sample concept relationships."""
    return [
        {
            "source": "Amazon EC2",
            "target": "Amazon VPC",
            "type": "runs_in",
            "strength": 0.9,
            "description": "EC2 instances run within VPC subnets"
        },
        {
            "source": "Amazon EC2",
            "target": "Amazon S3",
            "type": "can_access",
            "strength": 0.8,
            "description": "EC2 instances can read/write to S3 buckets"
        },
        {
            "source": "Amazon VPC",
            "target": "Amazon S3",
            "type": "can_restrict_access",
            "strength": 0.7,
            "description": "VPC endpoints can restrict S3 access"
        }
    ]


def create_sample_learning_path():
    """Create sample learning path."""
    return {
        "id": str(uuid4()),
        "name": "AWS Compute Fundamentals",
        "description": "Learn the basics of AWS compute services",
        "total_duration_hours": 8,
        "difficulty": "beginner",
        "steps": [
            {
                "order": 1,
                "concept": "AWS Global Infrastructure",
                "duration_minutes": 30,
                "activities": ["video", "diagram", "quiz"]
            },
            {
                "order": 2,
                "concept": "Amazon VPC",
                "duration_minutes": 90,
                "activities": ["video", "lab", "diagram", "quiz"]
            },
            {
                "order": 3,
                "concept": "Amazon EC2",
                "duration_minutes": 120,
                "activities": ["video", "lab", "interactive", "quiz"]
            },
            {
                "order": 4,
                "concept": "Amazon S3",
                "duration_minutes": 90,
                "activities": ["video", "lab", "quiz"]
            }
        ]
    }


def create_sample_quality_metrics():
    """Create sample quality metrics."""
    return {
        "overall_score": 0.89,
        "technical_accuracy": 0.94,
        "pedagogical_effectiveness": 0.87,
        "accessibility_compliance": 0.91,
        "certification_alignment": 0.85,
        "issues": [
            {
                "type": "minor",
                "category": "accessibility",
                "description": "Missing alt text on 2 diagrams",
                "severity": "low",
                "location": "module_3_diagrams"
            },
            {
                "type": "suggestion",
                "category": "pedagogy",
                "description": "Consider adding more practice exercises",
                "severity": "medium",
                "location": "module_5"
            }
        ],
        "recommendations": [
            "Add captions to all video content",
            "Include more hands-on labs for complex topics",
            "Review and update content for latest AWS features"
        ]
    }


# Save fixtures to files
def setup_test_fixtures():
    """Set up all test fixtures."""
    fixtures_dir = Path(__file__).parent
    
    # Create directories
    (fixtures_dir / "data").mkdir(exist_ok=True)
    (fixtures_dir / "samples").mkdir(exist_ok=True)
    
    # Save JSON fixtures
    with open(fixtures_dir / "data" / "certification.json", "w") as f:
        json.dump(create_sample_certification_data(), f, indent=2)
    
    with open(fixtures_dir / "data" / "concepts.json", "w") as f:
        json.dump(create_sample_concepts(), f, indent=2)
    
    with open(fixtures_dir / "data" / "relationships.json", "w") as f:
        json.dump(create_sample_relationships(), f, indent=2)
    
    with open(fixtures_dir / "data" / "learning_path.json", "w") as f:
        json.dump(create_sample_learning_path(), f, indent=2)
    
    with open(fixtures_dir / "data" / "quality_metrics.json", "w") as f:
        json.dump(create_sample_quality_metrics(), f, indent=2)
    
    # Create sample PDF
    create_sample_pdf(fixtures_dir / "samples" / "sample_certification.pdf")
    
    print(f"Test fixtures created in {fixtures_dir}")


if __name__ == "__main__":
    setup_test_fixtures()
