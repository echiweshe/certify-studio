"""
Neo4j Graph Store with Vector Index support for GraphRAG.

This module provides a unified graph and vector store using Neo4j,
enabling true GraphRAG capabilities with integrated vector search
and graph traversal.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import json
import numpy as np

from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import Neo4jError
import openai
from loguru import logger

from .models import (
    GraphNode,
    GraphEdge,
    TroubleshootingIssue,
    RootCause,
    Solution,
    DiagnosticPath,
    RelationshipType,
    GraphRAGConfig,
    GraphRAGQuery,
    GraphRAGResult,
    IssueType,
    Severity
)


class Neo4jGraphStore:
    """Neo4j-based graph store with vector index support."""
    
    def __init__(self, config: GraphRAGConfig):
        self.config = config
        self._driver = None
        self._embedding_cache = {}
        
    async def initialize(self):
        """Initialize Neo4j connection and create indexes."""
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info("Connected to Neo4j successfully")
            
            # Create indexes and constraints
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
            raise
            
    async def _create_indexes(self):
        """Create necessary indexes and constraints."""
        async with self._driver.session() as session:
            # Create vector indexes for each node type
            queries = [
                # Constraints
                "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Cause) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Solution) REQUIRE s.id IS UNIQUE",
                
                # Regular indexes
                "CREATE INDEX IF NOT EXISTS FOR (i:Issue) ON (i.type)",
                "CREATE INDEX IF NOT EXISTS FOR (i:Issue) ON (i.severity)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Cause) ON (c.likelihood)",
                "CREATE INDEX IF NOT EXISTS FOR (s:Solution) ON (s.success_rate)",
                
                # Vector indexes (Neo4j 5.x syntax)
                """
                CREATE VECTOR INDEX issue_embeddings IF NOT EXISTS
                FOR (i:Issue) ON (i.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """,
                """
                CREATE VECTOR INDEX solution_embeddings IF NOT EXISTS
                FOR (s:Solution) ON (s.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """,
                """
                CREATE VECTOR INDEX cause_embeddings IF NOT EXISTS
                FOR (c:Cause) ON (c.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """
            ]
            
            for query in queries:
                try:
                    await session.run(query)
                except Neo4jError as e:
                    # Index might already exist
                    logger.warning(f"Index creation warning: {e}")
                    
    async def close(self):
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            
    async def add_issue(self, issue: TroubleshootingIssue) -> str:
        """Add a troubleshooting issue to the graph."""
        async with self._driver.session() as session:
            # Generate embedding if not provided
            if issue.embedding is None:
                issue.embedding = await self._generate_embedding(
                    f"{issue.title} {issue.description} {' '.join(issue.symptoms)}"
                )
                
            query = """
            CREATE (i:Issue {
                id: $id,
                title: $title,
                description: $description,
                symptoms: $symptoms,
                type: $type,
                severity: $severity,
                affected_components: $affected_components,
                embedding: $embedding,
                metadata: $metadata,
                occurrence_count: $occurrence_count,
                resolution_rate: $resolution_rate,
                avg_resolution_time: $avg_resolution_time,
                created_at: datetime()
            })
            RETURN i.id as id
            """
            
            result = await session.run(
                query,
                id=str(issue.id),
                title=issue.title,
                description=issue.description,
                symptoms=issue.symptoms,
                type=issue.type.value,
                severity=issue.severity.value,
                affected_components=issue.affected_components,
                embedding=issue.embedding.tolist(),
                metadata=json.dumps(issue.metadata),
                occurrence_count=issue.occurrence_count,
                resolution_rate=issue.resolution_rate,
                avg_resolution_time=issue.avg_resolution_time
            )
            
            record = await result.single()
            return record["id"]
            
    async def add_root_cause(self, cause: RootCause) -> str:
        """Add a root cause to the graph."""
        async with self._driver.session() as session:
            # Generate embedding
            embedding = await self._generate_embedding(
                f"{cause.title} {cause.description}"
            )
            
            query = """
            CREATE (c:Cause {
                id: $id,
                issue_id: $issue_id,
                title: $title,
                description: $description,
                likelihood: $likelihood,
                diagnostic_steps: $diagnostic_steps,
                verification_commands: $verification_commands,
                expected_outputs: $expected_outputs,
                evidence_patterns: $evidence_patterns,
                confidence_score: $confidence_score,
                embedding: $embedding,
                created_at: datetime()
            })
            RETURN c.id as id
            """
            
            result = await session.run(
                query,
                id=str(cause.id),
                issue_id=str(cause.issue_id),
                title=cause.title,
                description=cause.description,
                likelihood=cause.likelihood,
                diagnostic_steps=cause.diagnostic_steps,
                verification_commands=cause.verification_commands,
                expected_outputs=json.dumps(cause.expected_outputs),
                evidence_patterns=cause.evidence_patterns,
                confidence_score=cause.confidence_score,
                embedding=embedding.tolist()
            )
            
            record = await result.single()
            
            # Create relationship to issue
            await self.add_relationship(
                str(cause.issue_id),
                str(cause.id),
                RelationshipType.CAUSED_BY,
                {"likelihood": cause.likelihood}
            )
            
            return record["id"]
            
    async def add_solution(self, solution: Solution) -> str:
        """Add a solution to the graph."""
        async with self._driver.session() as session:
            # Generate embedding if not provided
            if solution.embedding is None:
                solution.embedding = await self._generate_embedding(
                    f"{solution.title} {solution.description} {' '.join(solution.steps)}"
                )
                
            query = """
            CREATE (s:Solution {
                id: $id,
                title: $title,
                description: $description,
                steps: $steps,
                commands: $commands,
                code_snippets: $code_snippets,
                prerequisites: $prerequisites,
                success_rate: $success_rate,
                avg_implementation_time: $avg_implementation_time,
                risk_level: $risk_level,
                verification_steps: $verification_steps,
                rollback_procedure: $rollback_procedure,
                requires_restart: $requires_restart,
                requires_downtime: $requires_downtime,
                automation_available: $automation_available,
                embedding: $embedding,
                created_at: datetime()
            })
            RETURN s.id as id
            """
            
            result = await session.run(
                query,
                id=str(solution.id),
                title=solution.title,
                description=solution.description,
                steps=solution.steps,
                commands=solution.commands,
                code_snippets=json.dumps(solution.code_snippets),
                prerequisites=solution.prerequisites,
                success_rate=solution.success_rate,
                avg_implementation_time=solution.avg_implementation_time,
                risk_level=solution.risk_level,
                verification_steps=solution.verification_steps,
                rollback_procedure=solution.rollback_procedure,
                requires_restart=solution.requires_restart,
                requires_downtime=solution.requires_downtime,
                automation_available=solution.automation_available,
                embedding=solution.embedding.tolist()
            )
            
            record = await result.single()
            
            # Create relationships to issues and causes
            for issue_id in solution.applies_to_issues:
                await self.add_relationship(
                    str(solution.id),
                    str(issue_id),
                    RelationshipType.RESOLVES,
                    {"success_rate": solution.success_rate}
                )
                
            for cause_id in solution.applies_to_causes:
                await self.add_relationship(
                    str(solution.id),
                    str(cause_id),
                    RelationshipType.RESOLVES,
                    {"success_rate": solution.success_rate}
                )
                
            return record["id"]
            
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Add a relationship between nodes."""
        async with self._driver.session() as session:
            # Build property string
            prop_str = ""
            if properties:
                props = [f"{k}: ${k}" for k in properties.keys()]
                prop_str = f" {{{', '.join(props)}}}"
                
            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:{relationship_type.value}{prop_str}]->(b)
            RETURN r
            """
            
            params = {
                "source_id": source_id,
                "target_id": target_id
            }
            if properties:
                params.update(properties)
                
            result = await session.run(query, **params)
            return await result.single() is not None
            
    async def graph_rag_search(self, query: GraphRAGQuery) -> GraphRAGResult:
        """
        Perform GraphRAG search combining vector similarity and graph traversal.
        
        This is the core GraphRAG functionality that:
        1. Finds similar nodes using vector search
        2. Traverses the graph following relationships
        3. Ranks paths based on combined vector + graph scores
        """
        start_time = datetime.utcnow()
        result = GraphRAGResult()
        
        async with self._driver.session() as session:
            # Step 1: Vector search for initial nodes
            if query.query_embedding is None:
                query.query_embedding = await self._generate_embedding(query.query_text)
                
            initial_nodes = await self._vector_search(
                session,
                query.query_embedding,
                query.max_results,
                query.issue_types,
                query.severity_filter
            )
            
            # Step 2: Graph traversal from initial nodes
            diagnostic_paths = []
            for node in initial_nodes:
                paths = await self._traverse_diagnostic_paths(
                    session,
                    node["id"],
                    query.max_depth,
                    query.allowed_relationships,
                    query.min_confidence
                )
                diagnostic_paths.extend(paths)
                
            # Step 3: Rank paths by hybrid score
            ranked_paths = await self._rank_diagnostic_paths(
                diagnostic_paths,
                query.query_embedding,
                query.user_context
            )
            
            # Step 4: Extract solutions and root causes
            for path in ranked_paths[:query.max_results]:
                result.diagnostic_paths.append(path)
                
                # Collect unique issues, causes, and solutions
                for node_id in path.nodes:
                    node_data = await self._get_node_details(session, node_id)
                    
                    if node_data["type"] == "Issue":
                        issue = self._node_to_issue(node_data)
                        if issue not in result.identified_issues:
                            result.identified_issues.append(issue)
                            
                    elif node_data["type"] == "Cause":
                        cause = self._node_to_cause(node_data)
                        if cause not in result.root_causes:
                            result.root_causes.append(cause)
                            
                    elif node_data["type"] == "Solution":
                        solution = self._node_to_solution(node_data)
                        if solution not in result.solutions:
                            result.solutions.append(solution)
                            
            # Calculate metrics
            result.query_time = (datetime.utcnow() - start_time).total_seconds()
            result.nodes_examined = len(result.traversed_nodes)
            result.paths_evaluated = len(diagnostic_paths)
            
        return result
        
    async def _vector_search(
        self,
        session: AsyncSession,
        embedding: np.ndarray,
        limit: int,
        issue_types: Optional[List[IssueType]],
        severity_filter: Optional[List[Severity]]
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        # Build filters
        where_clause = ""
        params = {
            "embedding": embedding.tolist(),
            "limit": limit
        }
        
        filters = []
        if issue_types:
            filters.append("i.type IN $issue_types")
            params["issue_types"] = [t.value for t in issue_types]
            
        if severity_filter:
            filters.append("i.severity IN $severities")
            params["severities"] = [s.value for s in severity_filter]
            
        if filters:
            where_clause = f"WHERE {' AND '.join(filters)}"
            
        query = f"""
        CALL db.index.vector.queryNodes(
            'issue_embeddings',
            $limit,
            $embedding
        ) YIELD node, score
        WITH node as i, score
        {where_clause}
        RETURN i {{.*, similarity: score}}
        ORDER BY score DESC
        LIMIT $limit
        """
        
        result = await session.run(query, **params)
        nodes = []
        async for record in result:
            nodes.append(dict(record["i"]))
            
        return nodes
        
    async def _traverse_diagnostic_paths(
        self,
        session: AsyncSession,
        start_node_id: str,
        max_depth: int,
        allowed_relationships: List[RelationshipType],
        min_confidence: float
    ) -> List[DiagnosticPath]:
        """Traverse graph to find diagnostic paths."""
        rel_types = "|".join([r.value for r in allowed_relationships])
        
        query = f"""
        MATCH path = (start {{id: $start_id}})-[:{rel_types}*1..{max_depth}]-(end)
        WHERE end:Solution OR end:Cause
        WITH path, 
             [node in nodes(path) | node.id] as node_ids,
             [rel in relationships(path) | type(rel)] as rel_types,
             reduce(conf = 1.0, rel in relationships(path) | 
                    conf * coalesce(rel.confidence, rel.likelihood, rel.success_rate, 0.8)) as path_confidence
        WHERE path_confidence >= $min_confidence
        RETURN path, node_ids, rel_types, path_confidence
        ORDER BY path_confidence DESC
        LIMIT 20
        """
        
        result = await session.run(
            query,
            start_id=start_node_id,
            min_confidence=min_confidence
        )
        
        paths = []
        async for record in result:
            path = DiagnosticPath(
                starting_issue=start_node_id,
                nodes=record["node_ids"],
                confidence=record["path_confidence"],
                complexity=len(record["node_ids"])
            )
            
            # Extract relationships
            nodes = record["node_ids"]
            rel_types = record["rel_types"]
            for i in range(len(nodes) - 1):
                path.edges.append((
                    nodes[i],
                    nodes[i + 1],
                    RelationshipType(rel_types[i])
                ))
                
            paths.append(path)
            
        return paths
        
    async def _rank_diagnostic_paths(
        self,
        paths: List[DiagnosticPath],
        query_embedding: np.ndarray,
        user_context: Dict[str, Any]
    ) -> List[DiagnosticPath]:
        """Rank diagnostic paths using hybrid scoring."""
        scored_paths = []
        
        async with self._driver.session() as session:
            for path in paths:
                # Calculate path score
                score = 0.0
                
                # 1. Graph-based score (confidence, complexity)
                graph_score = path.confidence / (1 + 0.1 * path.complexity)
                score += 0.4 * graph_score
                
                # 2. Vector similarity score for path nodes
                node_embeddings = []
                for node_id in path.nodes:
                    node_data = await self._get_node_details(session, node_id)
                    if "embedding" in node_data:
                        node_embeddings.append(np.array(node_data["embedding"]))
                        
                if node_embeddings:
                    # Average similarity of path nodes to query
                    similarities = [
                        self._cosine_similarity(query_embedding, emb)
                        for emb in node_embeddings
                    ]
                    vector_score = np.mean(similarities)
                    score += 0.4 * vector_score
                    
                # 3. Context relevance score
                context_score = self._calculate_context_score(path, user_context)
                score += 0.2 * context_score
                
                scored_paths.append((score, path))
                
        # Sort by score
        scored_paths.sort(key=lambda x: x[0], reverse=True)
        
        return [path for _, path in scored_paths]
        
    async def _get_node_details(self, session: AsyncSession, node_id: str) -> Dict[str, Any]:
        """Get full details of a node."""
        query = """
        MATCH (n {id: $node_id})
        RETURN n, labels(n) as labels
        """
        
        result = await session.run(query, node_id=node_id)
        record = await result.single()
        
        if record:
            node_data = dict(record["n"])
            node_data["type"] = record["labels"][0] if record["labels"] else "Unknown"
            return node_data
            
        return {}
        
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    def _calculate_context_score(self, path: DiagnosticPath, context: Dict[str, Any]) -> float:
        """Calculate how well a path matches the user context."""
        score = 0.5  # Base score
        
        # Boost if path includes previously successful solutions
        if "successful_solutions" in context:
            for node_id in path.nodes:
                if node_id in context["successful_solutions"]:
                    score += 0.1
                    
        # Boost if path avoids previously failed solutions
        if "failed_solutions" in context:
            for node_id in path.nodes:
                if node_id in context["failed_solutions"]:
                    score -= 0.1
                    
        return max(0, min(1, score))
        
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using OpenAI."""
        # Check cache
        if text in self._embedding_cache:
            return self._embedding_cache[text]
            
        # Generate new embedding
        response = await openai.Embedding.acreate(
            input=[text],
            model=self.config.embedding_model
        )
        
        embedding = np.array(response['data'][0]['embedding'])
        
        # Cache it
        if self.config.enable_caching:
            self._embedding_cache[text] = embedding
            
        return embedding
        
    def _node_to_issue(self, node_data: Dict[str, Any]) -> TroubleshootingIssue:
        """Convert node data to TroubleshootingIssue."""
        return TroubleshootingIssue(
            id=node_data["id"],
            title=node_data.get("title", ""),
            description=node_data.get("description", ""),
            symptoms=node_data.get("symptoms", []),
            type=IssueType(node_data.get("type", "unknown")),
            severity=Severity(node_data.get("severity", "medium")),
            affected_components=node_data.get("affected_components", []),
            occurrence_count=node_data.get("occurrence_count", 0),
            resolution_rate=node_data.get("resolution_rate", 0.0),
            avg_resolution_time=node_data.get("avg_resolution_time", 0.0)
        )
        
    def _node_to_cause(self, node_data: Dict[str, Any]) -> RootCause:
        """Convert node data to RootCause."""
        return RootCause(
            id=node_data["id"],
            issue_id=node_data.get("issue_id"),
            title=node_data.get("title", ""),
            description=node_data.get("description", ""),
            likelihood=node_data.get("likelihood", 0.5),
            diagnostic_steps=node_data.get("diagnostic_steps", []),
            verification_commands=node_data.get("verification_commands", []),
            expected_outputs=json.loads(node_data.get("expected_outputs", "{}")),
            evidence_patterns=node_data.get("evidence_patterns", []),
            confidence_score=node_data.get("confidence_score", 0.0)
        )
        
    def _node_to_solution(self, node_data: Dict[str, Any]) -> Solution:
        """Convert node data to Solution."""
        return Solution(
            id=node_data["id"],
            title=node_data.get("title", ""),
            description=node_data.get("description", ""),
            steps=node_data.get("steps", []),
            commands=node_data.get("commands", []),
            code_snippets=json.loads(node_data.get("code_snippets", "{}")),
            prerequisites=node_data.get("prerequisites", []),
            success_rate=node_data.get("success_rate", 0.0),
            avg_implementation_time=node_data.get("avg_implementation_time", 0.0),
            risk_level=node_data.get("risk_level", "low"),
            verification_steps=node_data.get("verification_steps", []),
            rollback_procedure=node_data.get("rollback_procedure"),
            requires_restart=node_data.get("requires_restart", False),
            requires_downtime=node_data.get("requires_downtime", False),
            automation_available=node_data.get("automation_available", False)
        )
        
    async def update_success_metrics(
        self,
        path_id: str,
        success: bool,
        resolution_time: float
    ):
        """Update success metrics after a troubleshooting session."""
        async with self._driver.session() as session:
            # Update path success rate
            # Update solution success rates
            # Update issue resolution rates
            pass  # Implementation for feedback loop


class GraphRAGIndex:
    """High-level interface for GraphRAG operations."""
    
    def __init__(self, config: GraphRAGConfig):
        self.config = config
        self.graph_store = Neo4jGraphStore(config)
        
    async def initialize(self):
        """Initialize the GraphRAG index."""
        await self.graph_store.initialize()
        
    async def close(self):
        """Close the GraphRAG index."""
        await self.graph_store.close()
        
    async def troubleshoot(self, query: str, context: Dict[str, Any] = None) -> GraphRAGResult:
        """
        Main entry point for troubleshooting queries.
        
        Args:
            query: Natural language description of the issue
            context: Optional context about the user's environment
            
        Returns:
            GraphRAGResult with diagnostic paths and solutions
        """
        # Create GraphRAG query
        graph_query = GraphRAGQuery(
            query_text=query,
            user_context=context or {}
        )
        
        # Perform GraphRAG search
        result = await self.graph_store.graph_rag_search(graph_query)
        
        # Add reasoning trace
        result.reasoning_steps = [
            f"Analyzed query: '{query}'",
            f"Found {len(result.identified_issues)} potential issues",
            f"Identified {len(result.root_causes)} possible root causes",
            f"Discovered {len(result.diagnostic_paths)} diagnostic paths",
            f"Recommended {len(result.solutions)} solutions"
        ]
        
        return result
