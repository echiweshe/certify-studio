"""
Knowledge Graph Builder Module for Domain Extraction Agent.

Builds and manages a knowledge graph representation of extracted concepts
and relationships using Neo4j or NetworkX.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import json

from loguru import logger
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt

from .models import (
    Concept,
    Relationship,
    DomainKnowledge,
    ConceptCluster,
    LearningPath,
    DomainCategory,
    RelationshipType
)


class KnowledgeGraphBuilder:
    """Build and manage knowledge graphs from extracted domain knowledge."""
    
    def __init__(self):
        self.graph = None
        self._concept_positions = {}
        
    async def build_graph(
        self,
        domain_knowledge: DomainKnowledge
    ) -> nx.DiGraph:
        """Build NetworkX graph from domain knowledge."""
        try:
            logger.info(f"Building knowledge graph with {len(domain_knowledge.concepts)} concepts")
            
            # Create directed graph
            self.graph = nx.DiGraph()
            
            # Add concepts as nodes
            for concept in domain_knowledge.concepts:
                self.graph.add_node(
                    concept.id,
                    label=concept.name,
                    type=concept.type.value,
                    category=concept.category.value,
                    importance=concept.importance_score,
                    description=concept.description,
                    examples=concept.examples,
                    exam_weight=concept.exam_weight or 0.0
                )
                
            # Add relationships as edges
            for relationship in domain_knowledge.relationships:
                self.graph.add_edge(
                    relationship.source_concept_id,
                    relationship.target_concept_id,
                    type=relationship.type.value,
                    strength=relationship.strength,
                    evidence=relationship.evidence,
                    bidirectional=relationship.bidirectional
                )
                
                # Add reverse edge if bidirectional
                if relationship.bidirectional:
                    self.graph.add_edge(
                        relationship.target_concept_id,
                        relationship.source_concept_id,
                        type=relationship.type.value,
                        strength=relationship.strength,
                        evidence=relationship.evidence,
                        bidirectional=True
                    )
                    
            # Calculate layout positions
            self._calculate_layout()
            
            logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            return self.graph
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}")
            raise
            
    def _calculate_layout(self):
        """Calculate optimal layout for graph visualization."""
        if not self.graph or self.graph.number_of_nodes() == 0:
            return
            
        # Group nodes by category
        category_nodes = {}
        for node_id, data in self.graph.nodes(data=True):
            category = data.get('category', 'unknown')
            if category not in category_nodes:
                category_nodes[category] = []
            category_nodes[category].append(node_id)
            
        # Use hierarchical layout with categories
        if len(category_nodes) > 1:
            # Create subgraphs for each category
            pos = {}
            y_offset = 0
            
            for category, nodes in category_nodes.items():
                subgraph = self.graph.subgraph(nodes)
                
                # Layout subgraph
                if subgraph.number_of_nodes() > 0:
                    sub_pos = nx.spring_layout(
                        subgraph,
                        k=2,
                        iterations=50,
                        weight='strength'
                    )
                    
                    # Offset positions
                    for node, (x, y) in sub_pos.items():
                        pos[node] = (x, y + y_offset)
                        
                    y_offset += 3
                    
            self._concept_positions = pos
        else:
            # Single category, use spring layout
            self._concept_positions = nx.spring_layout(
                self.graph,
                k=2,
                iterations=50,
                weight='strength'
            )
            
    async def find_learning_paths(
        self,
        start_concepts: List[str],
        target_concepts: List[str],
        max_paths: int = 3
    ) -> List[LearningPath]:
        """Find optimal learning paths between concepts."""
        try:
            learning_paths = []
            
            # Find shortest paths
            for start in start_concepts:
                for target in target_concepts:
                    if start == target:
                        continue
                        
                    try:
                        # Find multiple paths
                        paths = list(nx.all_simple_paths(
                            self.graph,
                            start,
                            target,
                            cutoff=10  # Max path length
                        ))[:max_paths]
                        
                        for path in paths:
                            # Calculate path metrics
                            difficulty = self._calculate_path_difficulty(path)
                            duration = self._estimate_path_duration(path)
                            
                            # Get learning objectives
                            objectives = self._extract_path_objectives(path)
                            
                            learning_path = LearningPath(
                                name=f"Path from {self.graph.nodes[start]['label']} to {self.graph.nodes[target]['label']}",
                                description=f"Learning path covering {len(path)} concepts",
                                concept_sequence=path,
                                estimated_duration_hours=duration,
                                difficulty_level=difficulty,
                                learning_objectives=objectives
                            )
                            learning_paths.append(learning_path)
                            
                    except nx.NetworkXNoPath:
                        continue
                        
            return learning_paths
            
        except Exception as e:
            logger.error(f"Error finding learning paths: {str(e)}")
            return []
            
    def _calculate_path_difficulty(self, path: List[str]) -> str:
        """Calculate difficulty level of learning path."""
        if not path:
            return "beginner"
            
        # Average importance scores
        importance_scores = []
        for node_id in path:
            importance = self.graph.nodes[node_id].get('importance', 0.5)
            importance_scores.append(importance)
            
        avg_importance = sum(importance_scores) / len(importance_scores)
        
        # Consider path length
        length_factor = len(path) / 10  # Normalize by typical path length
        
        # Combined difficulty
        difficulty_score = (avg_importance + length_factor) / 2
        
        if difficulty_score < 0.4:
            return "beginner"
        elif difficulty_score < 0.7:
            return "intermediate"
        else:
            return "advanced"
            
    def _estimate_path_duration(self, path: List[str]) -> float:
        """Estimate time to complete learning path."""
        # Base time per concept (in hours)
        base_time = 0.5
        
        # Adjust based on concept importance
        total_time = 0
        for node_id in path:
            importance = self.graph.nodes[node_id].get('importance', 0.5)
            concept_time = base_time * (1 + importance)
            total_time += concept_time
            
        return round(total_time, 1)
        
    def _extract_path_objectives(self, path: List[str]) -> List[str]:
        """Extract learning objectives for path."""
        objectives = []
        
        for i, node_id in enumerate(path):
            node_data = self.graph.nodes[node_id]
            label = node_data['label']
            
            if i == 0:
                objectives.append(f"Understand the fundamentals of {label}")
            elif i == len(path) - 1:
                objectives.append(f"Master advanced concepts of {label}")
            else:
                objectives.append(f"Learn how {label} works and its applications")
                
        return objectives
        
    async def identify_central_concepts(
        self,
        top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """Identify most central/important concepts in the graph."""
        try:
            # Calculate different centrality measures
            degree_centrality = nx.degree_centrality(self.graph)
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            pagerank = nx.pagerank(self.graph, weight='strength')
            
            # Combine measures
            combined_scores = {}
            for node in self.graph.nodes():
                # Weight different measures
                score = (
                    degree_centrality.get(node, 0) * 0.3 +
                    betweenness_centrality.get(node, 0) * 0.3 +
                    pagerank.get(node, 0) * 0.2 +
                    self.graph.nodes[node].get('importance', 0) * 0.2
                )
                combined_scores[node] = score
                
            # Sort and return top concepts
            sorted_concepts = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
            
            # Return with concept names
            result = []
            for concept_id, score in sorted_concepts:
                concept_name = self.graph.nodes[concept_id]['label']
                result.append((concept_name, score))
                
            return result
            
        except Exception as e:
            logger.error(f"Error identifying central concepts: {str(e)}")
            return []
            
    async def find_concept_clusters(self) -> List[ConceptCluster]:
        """Find clusters of related concepts."""
        try:
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()
            
            # Find communities
            communities = nx.community.louvain_communities(undirected)
            
            clusters = []
            for community in communities:
                if len(community) < 2:
                    continue
                    
                # Analyze cluster
                subgraph = self.graph.subgraph(community)
                
                # Find most central node
                centrality = nx.degree_centrality(subgraph)
                centroid_id = max(centrality.items(), key=lambda x: x[1])[0]
                
                # Determine cluster category
                categories = [
                    self.graph.nodes[node]['category']
                    for node in community
                ]
                most_common_category = max(set(categories), key=categories.count)
                
                # Calculate cohesion
                density = nx.density(subgraph)
                
                # Create cluster
                cluster = ConceptCluster(
                    name=f"{most_common_category} Cluster",
                    category=DomainCategory(most_common_category),
                    concepts=list(community),
                    centroid_concept=centroid_id,
                    cohesion_score=density,
                    description=f"Cluster of {len(community)} related {most_common_category} concepts"
                )
                clusters.append(cluster)
                
            return clusters
            
        except Exception as e:
            logger.error(f"Error finding concept clusters: {str(e)}")
            return []
            
    async def export_graph(
        self,
        format: str = "json",
        include_positions: bool = True
    ) -> Any:
        """Export graph in various formats."""
        try:
            if format == "json":
                # Convert to node-link format
                data = nx.node_link_data(self.graph)
                
                # Add positions if requested
                if include_positions and self._concept_positions:
                    for node in data['nodes']:
                        node_id = node['id']
                        if node_id in self._concept_positions:
                            x, y = self._concept_positions[node_id]
                            node['x'] = float(x)
                            node['y'] = float(y)
                            
                return json.dumps(data, indent=2)
                
            elif format == "gexf":
                # GEXF format for Gephi
                return nx.generate_gexf(self.graph)
                
            elif format == "graphml":
                # GraphML format
                return nx.generate_graphml(self.graph)
                
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting graph: {str(e)}")
            raise
            
    async def visualize_graph(
        self,
        output_path: str,
        highlight_concepts: Optional[List[str]] = None
    ) -> str:
        """Create interactive visualization of the graph."""
        try:
            # Create Pyvis network
            net = Network(
                height="750px",
                width="100%",
                bgcolor="#ffffff",
                font_color="#000000"
            )
            
            # Configure physics
            net.barnes_hut(
                gravity=-80000,
                central_gravity=0.3,
                spring_length=250,
                spring_strength=0.001
            )
            
            # Add nodes
            for node_id, data in self.graph.nodes(data=True):
                # Determine node appearance
                category = data.get('category', 'unknown')
                importance = data.get('importance', 0.5)
                
                # Node color based on category
                color_map = {
                    'fundamentals': '#FF6B6B',
                    'services': '#4ECDC4',
                    'security': '#45B7D1',
                    'architecture': '#96CEB4',
                    'best_practices': '#FFEAA7',
                    'troubleshooting': '#DDA0DD',
                    'cost_optimization': '#98D8C8',
                    'performance': '#F7DC6F',
                    'governance': '#85C1E2',
                    'migration': '#F8B739'
                }
                
                color = color_map.get(category, '#95A5A6')
                
                # Highlight if requested
                if highlight_concepts and data['label'] in highlight_concepts:
                    color = '#E74C3C'
                    
                # Node size based on importance
                size = 20 + (importance * 30)
                
                net.add_node(
                    node_id,
                    label=data['label'],
                    title=f"{data['label']}\n{data.get('description', '')}",
                    color=color,
                    size=size
                )
                
            # Add edges
            for source, target, data in self.graph.edges(data=True):
                edge_type = data.get('type', 'related_to')
                strength = data.get('strength', 0.5)
                
                # Edge appearance based on type
                if edge_type == 'depends_on':
                    edge_color = '#E74C3C'
                    dashes = False
                elif edge_type == 'part_of':
                    edge_color = '#3498DB'
                    dashes = False
                else:
                    edge_color = '#95A5A6'
                    dashes = True
                    
                net.add_edge(
                    source,
                    target,
                    value=strength,
                    color=edge_color,
                    dashes=dashes,
                    title=edge_type
                )
                
            # Set options
            net.set_options("""
            var options = {
                "nodes": {
                    "font": {
                        "size": 14
                    }
                },
                "edges": {
                    "smooth": {
                        "type": "continuous"
                    }
                },
                "physics": {
                    "barnesHut": {
                        "gravitationalConstant": -80000,
                        "centralGravity": 0.3,
                        "springLength": 250,
                        "springConstant": 0.001
                    }
                }
            }
            """)
            
            # Save visualization
            net.save_graph(output_path)
            
            logger.info(f"Graph visualization saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error visualizing graph: {str(e)}")
            raise
            
    async def get_concept_neighborhood(
        self,
        concept_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get neighborhood of a concept up to specified depth."""
        try:
            if concept_id not in self.graph:
                return {}
                
            # Get neighbors at different depths
            neighborhood = {
                'center': concept_id,
                'levels': {}
            }
            
            visited = {concept_id}
            current_level = {concept_id}
            
            for level in range(1, depth + 1):
                next_level = set()
                level_nodes = []
                
                for node in current_level:
                    # Get all neighbors (both in and out edges)
                    neighbors = set(self.graph.successors(node)) | set(self.graph.predecessors(node))
                    
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_level.add(neighbor)
                            
                            # Get relationship info
                            rel_info = {
                                'id': neighbor,
                                'label': self.graph.nodes[neighbor]['label'],
                                'category': self.graph.nodes[neighbor]['category'],
                                'relationships': []
                            }
                            
                            # Check relationship from current to neighbor
                            if self.graph.has_edge(node, neighbor):
                                edge_data = self.graph.edges[node, neighbor]
                                rel_info['relationships'].append({
                                    'from': node,
                                    'type': edge_data['type'],
                                    'direction': 'outgoing'
                                })
                                
                            # Check relationship from neighbor to current
                            if self.graph.has_edge(neighbor, node):
                                edge_data = self.graph.edges[neighbor, node]
                                rel_info['relationships'].append({
                                    'from': node,
                                    'type': edge_data['type'],
                                    'direction': 'incoming'
                                })
                                
                            level_nodes.append(rel_info)
                            
                neighborhood['levels'][f'depth_{level}'] = level_nodes
                current_level = next_level
                
                if not next_level:
                    break
                    
            return neighborhood
            
        except Exception as e:
            logger.error(f"Error getting concept neighborhood: {str(e)}")
            return {}
            
    async def suggest_missing_relationships(
        self,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Suggest potential missing relationships based on graph structure."""
        try:
            suggestions = []
            
            # Find nodes with common neighbors but no direct connection
            for node1 in self.graph.nodes():
                for node2 in self.graph.nodes():
                    if node1 >= node2:  # Avoid duplicates
                        continue
                        
                    if self.graph.has_edge(node1, node2) or self.graph.has_edge(node2, node1):
                        continue
                        
                    # Find common neighbors
                    neighbors1 = set(self.graph.neighbors(node1))
                    neighbors2 = set(self.graph.neighbors(node2))
                    common = neighbors1 & neighbors2
                    
                    if len(common) >= 2:  # At least 2 common neighbors
                        # Calculate suggestion score
                        score = len(common) / (len(neighbors1 | neighbors2) or 1)
                        
                        if score >= threshold:
                            suggestions.append({
                                'source': node1,
                                'target': node2,
                                'source_label': self.graph.nodes[node1]['label'],
                                'target_label': self.graph.nodes[node2]['label'],
                                'score': score,
                                'common_neighbors': len(common),
                                'suggested_type': 'related_to'
                            })
                            
            # Sort by score
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            
            return suggestions[:20]  # Return top 20 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting missing relationships: {str(e)}")
            return []
