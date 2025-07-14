# Unified Knowledge System

## Overview

Certify Studio uses a **Unified GraphRAG** (Graph-based Retrieval-Augmented Generation) system that combines educational content and troubleshooting knowledge in ONE powerful knowledge graph.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Documents (PDFs, Guides)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Domain Extraction Agent                         │
│  • Extracts concepts, procedures, relationships              │
│  • Identifies prerequisites and learning paths               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Unified GraphRAG (Neo4j)                        │
│  • Stores ALL knowledge in one graph                        │
│  • Vector embeddings for semantic search                     │
│  • Graph relationships for connected reasoning               │
│  • Handles educational AND troubleshooting queries           │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. unified_graphrag.py
The core system that:
- Manages the Neo4j graph database
- Performs vector similarity search
- Traverses graph relationships
- Ranks results by relevance
- Handles all query types (educational, troubleshooting, general)

### 2. setup.py
Simple setup for new deployments:
```python
from certify_studio.knowledge import setup_unified_system

# One line to set up everything!
graphrag, domain_agent = await setup_unified_system()
```

## Node Types

The unified graph contains diverse but connected node types:

**Educational Nodes:**
- `CONCEPT` - Core concepts (e.g., "VPC", "EC2 Instance")
- `PROCEDURE` - How-to steps
- `LEARNING_OBJECTIVE` - What students should learn
- `PREREQUISITE` - Required prior knowledge

**Troubleshooting Nodes:**
- `ISSUE` - Common problems
- `CAUSE` - Root causes
- `SOLUTION` - Step-by-step fixes
- `DIAGNOSTIC_STEP` - How to diagnose

**Content Nodes:**
- `CHUNK` - Text segments from documents
- `DOCUMENT` - Source documents
- `SECTION` - Document sections

## Relationship Types

Nodes are connected via meaningful relationships:
- `PREREQUISITE_OF` - Learning dependencies
- `RELATES_TO` - General relationships
- `CAUSES` - Issue → Root cause
- `RESOLVES` - Solution → Issue
- `TEACHES` - Content → Concept
- `DEMONSTRATES` - Example → Concept

## Query Types

### Educational Query
```python
result = await graphrag.search(GraphRAGQuery(
    query_text="How does VPC networking work?",
    query_type="educational"
))
```

### Troubleshooting Query
```python
result = await graphrag.search(GraphRAGQuery(
    query_text="EC2 instance cannot connect to internet",
    query_type="troubleshooting"
))
```

### General Query (finds everything)
```python
result = await graphrag.search(GraphRAGQuery(
    query_text="security groups",
    query_type="general"
))
```

## Usage Example

```python
from certify_studio.knowledge import setup_unified_system
from certify_studio.agents.specialized.domain_extraction.models import ExtractionRequest

# Setup
graphrag, domain_agent = await setup_unified_system()

# Extract knowledge from document
request = ExtractionRequest(
    document_paths=["aws-cert-guide.pdf"],
    domain_name="AWS Solutions Architect"
)
result = await domain_agent.extract_domain_knowledge(request)

# Query the unified system
from certify_studio.knowledge import GraphRAGQuery

# Find both educational content AND related troubleshooting
query = GraphRAGQuery(
    query_text="VPC security",
    query_type="general",
    max_results=10,
    include_explanations=True
)
result = await graphrag.search(query)

# Results include concepts, procedures, common issues, and solutions!
for node in result.nodes:
    print(f"{node.name} ({node.type.value})")
```

## Benefits

1. **One System**: No separate RAG and troubleshooting systems
2. **Connected Knowledge**: Educational concepts linked to real-world issues
3. **Intelligent Search**: Graph traversal finds related knowledge
4. **Scalable**: Handles millions of nodes and relationships
5. **Extensible**: Easy to add new node and relationship types

## Requirements

- Neo4j 5.x with vector index support
- Python 3.11+
- OpenAI API key for embeddings

## Setup

```bash
# Install Neo4j with vector support
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/certify-studio-2024 \
    -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
    neo4j:5.x

# Install Python dependencies
pip install neo4j openai numpy
```

## Architecture Decision

We chose a unified GraphRAG approach because:
- **Follows the Vision**: One AI Agent Operating System
- **Reduces Complexity**: One system instead of multiple
- **Better Knowledge Integration**: Everything is connected
- **True GraphRAG Power**: Leverages relationships between all knowledge types

This is not just a technical improvement - it fundamentally changes how the system understands and retrieves knowledge.
