"""
Vector Store Module for Domain Extraction Agent.

Manages vector storage and retrieval of concepts and documents using ChromaDB,
with support for semantic search and knowledge base operations.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import numpy as np

from loguru import logger
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from .models import (
    Document,
    DocumentChunk,
    Concept,
    SearchQuery,
    SearchResult,
    KnowledgeBaseStats
)
from ....config import settings


class VectorStore:
    """Vector store for domain knowledge."""
    
    def __init__(self, collection_name: str = "domain_knowledge"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedding_function = None
        
    async def initialize(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Initialize ChromaDB client
            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(settings.DATA_DIR / "chroma_db")
            ))
            
            # Initialize embedding function
            self._embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name="text-embedding-ada-002"
            )
            
            # Get or create collection
            try:
                self._collection = self._client.get_collection(
                    name=self.collection_name,
                    embedding_function=self._embedding_function
                )
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except:
                self._collection = self._client.create_collection(
                    name=self.collection_name,
                    embedding_function=self._embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
            
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to vector store."""
        try:
            if not chunks:
                return
                
            # Prepare data for ChromaDB
            ids = [chunk.id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = []
            
            for chunk in chunks:
                metadata = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "concepts": json.dumps(chunk.concepts),
                    "timestamp": datetime.utcnow().isoformat()
                }
                # Add any additional metadata
                if chunk.metadata:
                    metadata.update({
                        k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                        for k, v in chunk.metadata.items()
                    })
                metadatas.append(metadata)
                
            # Add to collection
            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {str(e)}")
            raise
            
    async def add_concepts(self, concepts: List[Concept]) -> None:
        """Add concepts to vector store for retrieval."""
        try:
            if not concepts:
                return
                
            # Create concept documents
            ids = [f"concept_{concept.id}" for concept in concepts]
            documents = []
            metadatas = []
            
            for concept in concepts:
                # Create searchable document from concept
                doc_text = f"{concept.name}: {concept.description}"
                if concept.examples:
                    doc_text += " Examples: " + " ".join(concept.examples[:2])
                documents.append(doc_text)
                
                # Create metadata
                metadata = {
                    "type": "concept",
                    "concept_id": concept.id,
                    "concept_name": concept.name,
                    "concept_type": concept.type.value,
                    "category": concept.category.value,
                    "importance_score": concept.importance_score,
                    "timestamp": datetime.utcnow().isoformat()
                }
                metadatas.append(metadata)
                
            # Add to collection
            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(concepts)} concepts to vector store")
            
        except Exception as e:
            logger.error(f"Error adding concepts to vector store: {str(e)}")
            raise
            
    async def search(
        self,
        query: SearchQuery,
        include_chunks: bool = True,
        include_concepts: bool = True
    ) -> List[SearchResult]:
        """Search for relevant content."""
        try:
            # Build where clause for filtering
            where_clause = {}
            
            if not include_chunks and include_concepts:
                where_clause["type"] = "concept"
            elif include_chunks and not include_concepts:
                where_clause["type"] = {"$ne": "concept"}
                
            if query.domain_filter:
                where_clause["domain"] = query.domain_filter
                
            if query.category_filter:
                where_clause["category"] = {"$in": [c.value for c in query.category_filter]}
                
            # Perform search
            results = self._collection.query(
                query_texts=[query.query],
                n_results=query.max_results,
                where=where_clause if where_clause else None
            )
            
            # Process results
            search_results = []
            
            if results and results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    
                    # Calculate relevance score (convert distance to similarity)
                    relevance_score = 1 - distance
                    
                    if relevance_score >= query.min_relevance_score:
                        # Check if it's a concept or chunk
                        if metadata.get('type') == 'concept':
                            # Create concept result
                            concept = Concept(
                                id=metadata['concept_id'],
                                name=metadata['concept_name'],
                                type=metadata['concept_type'],
                                category=metadata['category'],
                                description=results['documents'][0][i],
                                importance_score=metadata.get('importance_score', 0.5)
                            )
                            
                            result = SearchResult(
                                concept=concept,
                                relevance_score=relevance_score,
                                context_summary=results['documents'][0][i]
                            )
                        else:
                            # Create chunk result
                            # This is simplified - in production, you'd fetch the full concept
                            result = SearchResult(
                                concept=None,  # Would need to fetch
                                relevance_score=relevance_score,
                                context_summary=results['documents'][0][i]
                            )
                            
                        search_results.append(result)
                        
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise
            
    async def get_similar_concepts(
        self,
        concept: Concept,
        max_results: int = 5
    ) -> List[Tuple[Concept, float]]:
        """Find concepts similar to the given concept."""
        try:
            # Create query from concept
            query_text = f"{concept.name}: {concept.description}"
            
            # Search for similar concepts
            results = self._collection.query(
                query_texts=[query_text],
                n_results=max_results + 1,  # +1 because it might include itself
                where={"type": "concept"}
            )
            
            similar_concepts = []
            
            if results and results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    
                    # Skip if it's the same concept
                    if metadata['concept_id'] == concept.id:
                        continue
                        
                    # Create concept (simplified)
                    similar_concept = Concept(
                        id=metadata['concept_id'],
                        name=metadata['concept_name'],
                        type=metadata['concept_type'],
                        category=metadata['category'],
                        description=results['documents'][0][i],
                        importance_score=metadata.get('importance_score', 0.5)
                    )
                    
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    similarity = 1 - distance
                    
                    similar_concepts.append((similar_concept, similarity))
                    
            return similar_concepts[:max_results]
            
        except Exception as e:
            logger.error(f"Error finding similar concepts: {str(e)}")
            return []
            
    async def get_stats(self) -> KnowledgeBaseStats:
        """Get statistics about the knowledge base."""
        try:
            # Get collection count
            count = self._collection.count()
            
            # Query for different types
            concept_results = self._collection.get(
                where={"type": "concept"},
                limit=1000
            )
            
            chunk_results = self._collection.get(
                where={"type": {"$ne": "concept"}},
                limit=1
            )
            
            # Count concepts by type and category
            concepts_by_type = {}
            concepts_by_category = {}
            
            if concept_results and concept_results['metadatas']:
                for metadata in concept_results['metadatas']:
                    concept_type = metadata.get('concept_type', 'unknown')
                    category = metadata.get('category', 'unknown')
                    
                    concepts_by_type[concept_type] = concepts_by_type.get(concept_type, 0) + 1
                    concepts_by_category[category] = concepts_by_category.get(category, 0) + 1
                    
            stats = KnowledgeBaseStats(
                total_chunks=count - len(concept_results['ids']) if concept_results['ids'] else count,
                total_concepts=len(concept_results['ids']) if concept_results['ids'] else 0,
                concepts_by_type=concepts_by_type,
                concepts_by_category=concepts_by_category
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return KnowledgeBaseStats()
            
    async def clear_collection(self) -> None:
        """Clear all data from the collection."""
        try:
            # Delete the collection
            self._client.delete_collection(self.collection_name)
            
            # Recreate it
            self._collection = self._client.create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"Cleared collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise
            
    async def export_knowledge_base(self) -> Dict[str, Any]:
        """Export the entire knowledge base."""
        try:
            # Get all data
            results = self._collection.get()
            
            return {
                "collection_name": self.collection_name,
                "export_date": datetime.utcnow().isoformat(),
                "total_items": len(results['ids']) if results['ids'] else 0,
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Error exporting knowledge base: {str(e)}")
            raise
            
    async def import_knowledge_base(self, data: Dict[str, Any]) -> None:
        """Import knowledge base from export."""
        try:
            if 'data' not in data:
                raise ValueError("Invalid import data format")
                
            kb_data = data['data']
            
            if kb_data.get('ids') and kb_data.get('documents'):
                self._collection.add(
                    ids=kb_data['ids'],
                    documents=kb_data['documents'],
                    metadatas=kb_data.get('metadatas', []),
                    embeddings=kb_data.get('embeddings')
                )
                
                logger.info(f"Imported {len(kb_data['ids'])} items")
                
        except Exception as e:
            logger.error(f"Error importing knowledge base: {str(e)}")
            raise
