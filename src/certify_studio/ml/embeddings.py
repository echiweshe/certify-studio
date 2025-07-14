"""
Embedding Generator - Multimodal Intelligence Encoding
Part of the AI Agent Orchestration Platform for Educational Excellence

This component creates rich embeddings that capture not just semantic meaning,
but educational value, cognitive load, and learning relationships.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from transformers import (
    AutoTokenizer,
    AutoModel,
    CLIPProcessor,
    CLIPModel
)
import librosa
from PIL import Image

from ..core.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Advanced embedding generator for multimodal educational content.
    
    This isn't just about vector representations - it's about encoding
    the educational essence of content across modalities.
    """
    
    def __init__(self):
        """Initialize embedding models."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Text embedding model - educational content optimized
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_model.to(self.device)
        
        # Multimodal model for vision-text
        try:
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model.to(self.device)
            self.multimodal_available = True
        except Exception as e:
            logger.warning(f"CLIP model not available: {e}")
            self.multimodal_available = False
        
        # Educational concept embedding space
        self.concept_embeddings = {}
        self._initialize_concept_space()
        
        logger.info(f"EmbeddingGenerator initialized on {self.device}")
    
    def _initialize_concept_space(self):
        """Initialize educational concept embedding space."""
        # Core educational concepts with their embeddings
        # In production, these would be learned from data
        core_concepts = [
            "learning", "understanding", "application", "analysis",
            "synthesis", "evaluation", "knowledge", "skill",
            "competency", "mastery", "prerequisite", "foundation"
        ]
        
        for concept in core_concepts:
            self.concept_embeddings[concept] = self.text_model.encode(concept)
    
    async def generate_text_embedding(self, 
                                    text: str,
                                    educational_context: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Generate text embedding with educational awareness.
        
        Args:
            text: Input text
            educational_context: Context about learning objectives, level, etc.
            
        Returns:
            Embedding vector
        """
        # Basic text embedding
        base_embedding = self.text_model.encode(text, convert_to_numpy=True)
        
        if educational_context:
            # Enhance with educational context
            base_embedding = self._enhance_with_education_context(
                base_embedding, text, educational_context
            )
        
        return base_embedding
    
    async def generate_multimodal_embedding(self,
                                          image: Optional[Image.Image] = None,
                                          text: Optional[str] = None,
                                          audio: Optional[np.ndarray] = None,
                                          metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Generate unified embedding from multiple modalities.
        
        Args:
            image: PIL Image
            text: Text content
            audio: Audio array
            metadata: Additional metadata
            
        Returns:
            Unified multimodal embedding
        """
        embeddings = []
        weights = []
        
        # Text embedding
        if text:
            text_emb = await self.generate_text_embedding(text, metadata)
            embeddings.append(text_emb)
            weights.append(0.4)  # Text is primary for education
        
        # Image embedding
        if image and self.multimodal_available:
            image_emb = self._generate_image_embedding(image)
            embeddings.append(image_emb)
            weights.append(0.3)
        
        # Audio embedding
        if audio is not None:
            audio_emb = self._generate_audio_embedding(audio)
            embeddings.append(audio_emb)
            weights.append(0.2)
        
        # Metadata embedding
        if metadata:
            meta_emb = self._generate_metadata_embedding(metadata)
            embeddings.append(meta_emb)
            weights.append(0.1)
        
        if not embeddings:
            return np.zeros(384)  # Default embedding size
        
        # Normalize weights
        weights = np.array(weights) / np.sum(weights)
        
        # Combine embeddings
        # First, ensure all embeddings have the same dimension
        target_dim = embeddings[0].shape[0]
        normalized_embeddings = []
        
        for emb in embeddings:
            if emb.shape[0] != target_dim:
                # Project to target dimension
                emb = self._project_embedding(emb, target_dim)
            normalized_embeddings.append(emb)
        
        # Weighted combination
        combined = np.zeros(target_dim)
        for emb, weight in zip(normalized_embeddings, weights):
            combined += weight * emb
        
        # Normalize
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        
        return combined
    
    def _generate_image_embedding(self, image: Image.Image) -> np.ndarray:
        """Generate embedding for image."""
        if not self.multimodal_available:
            return np.zeros(512)
        
        inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
        
        return image_features.cpu().numpy().flatten()
    
    def _generate_audio_embedding(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """Generate embedding for audio."""
        # Extract audio features
        features = []
        
        # MFCCs
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
        features.extend(np.mean(mfccs, axis=1))
        features.extend(np.std(mfccs, axis=1))
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)
        features.append(np.mean(spectral_centroids))
        features.append(np.std(spectral_centroids))
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)
        features.append(np.mean(zcr))
        features.append(np.std(zcr))
        
        # Tempo
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sample_rate)
        features.append(tempo)
        
        return np.array(features)
    
    def _generate_metadata_embedding(self, metadata: Dict[str, Any]) -> np.ndarray:
        """Generate embedding from metadata."""
        # Convert metadata to text representation
        meta_text = []
        
        if 'type' in metadata:
            meta_text.append(f"type: {metadata['type']}")
        
        if 'cognitive_level' in metadata:
            meta_text.append(f"cognitive level: {metadata['cognitive_level']}")
        
        if 'difficulty' in metadata:
            meta_text.append(f"difficulty: {metadata['difficulty']}")
        
        if 'concepts' in metadata:
            meta_text.append(f"concepts: {', '.join(metadata['concepts'][:5])}")
        
        combined_text = "; ".join(meta_text)
        
        if combined_text:
            return self.text_model.encode(combined_text, convert_to_numpy=True)
        else:
            return np.zeros(384)
    
    def _enhance_with_education_context(self,
                                      base_embedding: np.ndarray,
                                      text: str,
                                      context: Dict[str, Any]) -> np.ndarray:
        """Enhance embedding with educational context."""
        # Extract educational signals
        enhancements = []
        
        # Cognitive level enhancement
        if 'cognitive_level' in context:
            level_text = f"cognitive level {context['cognitive_level']}"
            level_emb = self.text_model.encode(level_text, convert_to_numpy=True)
            enhancements.append(level_emb * 0.1)
        
        # Learning objective alignment
        if 'learning_objectives' in context:
            objectives_text = " ".join(context['learning_objectives'][:3])
            obj_emb = self.text_model.encode(objectives_text, convert_to_numpy=True)
            enhancements.append(obj_emb * 0.15)
        
        # Concept alignment
        if 'concepts' in context:
            # Find concept similarity
            concept_sims = []
            for concept in context['concepts']:
                if concept.lower() in self.concept_embeddings:
                    concept_emb = self.concept_embeddings[concept.lower()]
                    sim = np.dot(base_embedding, concept_emb) / (
                        np.linalg.norm(base_embedding) * np.linalg.norm(concept_emb)
                    )
                    concept_sims.append(sim)
            
            if concept_sims:
                # Boost embedding towards relevant concepts
                avg_sim = np.mean(concept_sims)
                base_embedding = base_embedding * (1 + avg_sim * 0.1)
        
        # Combine enhancements
        enhanced = base_embedding
        for enhancement in enhancements:
            if enhancement.shape == enhanced.shape:
                enhanced = enhanced + enhancement
        
        # Normalize
        norm = np.linalg.norm(enhanced)
        if norm > 0:
            enhanced = enhanced / norm
        
        return enhanced
    
    def _project_embedding(self, embedding: np.ndarray, target_dim: int) -> np.ndarray:
        """Project embedding to target dimension."""
        current_dim = embedding.shape[0]
        
        if current_dim == target_dim:
            return embedding
        
        if current_dim > target_dim:
            # Reduce dimension by taking first components
            return embedding[:target_dim]
        else:
            # Pad with zeros
            padded = np.zeros(target_dim)
            padded[:current_dim] = embedding
            return padded
    
    async def generate_concept_embedding(self,
                                       concept_name: str,
                                       concept_definition: str,
                                       related_concepts: List[str] = None) -> np.ndarray:
        """
        Generate embedding for an educational concept.
        
        Args:
            concept_name: Name of the concept
            concept_definition: Definition/explanation
            related_concepts: Related concept names
            
        Returns:
            Concept embedding
        """
        # Combine concept information
        concept_text = f"{concept_name}: {concept_definition}"
        
        if related_concepts:
            concept_text += f" Related to: {', '.join(related_concepts[:5])}"
        
        # Generate embedding with educational context
        embedding = await self.generate_text_embedding(
            concept_text,
            educational_context={
                'type': 'concept',
                'name': concept_name
            }
        )
        
        # Store for future reference
        self.concept_embeddings[concept_name.lower()] = embedding
        
        return embedding
    
    async def generate_learning_path_embedding(self,
                                             concepts: List[str],
                                             relationships: List[Tuple[str, str, str]]) -> np.ndarray:
        """
        Generate embedding for a learning path.
        
        Args:
            concepts: List of concepts in the path
            relationships: List of (source, relation, target) tuples
            
        Returns:
            Learning path embedding
        """
        # Create text representation of the path
        path_text = f"Learning path: {' -> '.join(concepts)}"
        
        # Add relationship information
        rel_texts = []
        for source, relation, target in relationships[:5]:
            rel_texts.append(f"{source} {relation} {target}")
        
        if rel_texts:
            path_text += f". Relationships: {'; '.join(rel_texts)}"
        
        # Generate embedding
        embedding = await self.generate_text_embedding(
            path_text,
            educational_context={
                'type': 'learning_path',
                'concepts': concepts,
                'num_concepts': len(concepts)
            }
        )
        
        return embedding
    
    async def generate_assessment_embedding(self,
                                          question: str,
                                          correct_answer: str,
                                          difficulty: float,
                                          concepts_tested: List[str]) -> np.ndarray:
        """
        Generate embedding for assessment content.
        
        Args:
            question: The question text
            correct_answer: The correct answer
            difficulty: Difficulty level (0-1)
            concepts_tested: Concepts being assessed
            
        Returns:
            Assessment embedding
        """
        # Combine assessment information
        assessment_text = f"Question: {question} Answer: {correct_answer}"
        
        # Add metadata
        meta_text = f"Difficulty: {difficulty:.2f}, Tests: {', '.join(concepts_tested)}"
        full_text = f"{assessment_text}. {meta_text}"
        
        # Generate embedding
        embedding = await self.generate_text_embedding(
            full_text,
            educational_context={
                'type': 'assessment',
                'difficulty': difficulty,
                'concepts': concepts_tested
            }
        )
        
        return embedding
    
    def compute_educational_similarity(self,
                                     embedding1: np.ndarray,
                                     embedding2: np.ndarray,
                                     similarity_type: str = "cosine") -> float:
        """
        Compute similarity between embeddings with educational awareness.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            similarity_type: Type of similarity metric
            
        Returns:
            Similarity score (0-1)
        """
        if similarity_type == "cosine":
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Scale to 0-1 range
            return (similarity + 1) / 2
        
        elif similarity_type == "euclidean":
            # Euclidean distance converted to similarity
            distance = np.linalg.norm(embedding1 - embedding2)
            # Convert to similarity (assuming embeddings are normalized)
            similarity = 1 / (1 + distance)
            return similarity
        
        else:
            raise ValueError(f"Unknown similarity type: {similarity_type}")
    
    async def find_similar_content(self,
                                 query_embedding: np.ndarray,
                                 content_embeddings: Dict[str, np.ndarray],
                                 top_k: int = 5,
                                 threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Find similar educational content.
        
        Args:
            query_embedding: Query embedding
            content_embeddings: Dictionary of content_id -> embedding
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (content_id, similarity_score) tuples
        """
        similarities = []
        
        for content_id, content_embedding in content_embeddings.items():
            sim = self.compute_educational_similarity(query_embedding, content_embedding)
            
            if sim >= threshold:
                similarities.append((content_id, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    async def generate_audio_embedding(self,
                                     audio_data: np.ndarray,
                                     sample_rate: int,
                                     transcription: Optional[str] = None) -> np.ndarray:
        """
        Generate embedding for audio content.
        
        Args:
            audio_data: Audio signal
            sample_rate: Sample rate
            transcription: Optional transcription text
            
        Returns:
            Audio embedding
        """
        # Audio features
        audio_features = self._generate_audio_embedding(audio_data, sample_rate)
        
        # If transcription available, combine with text embedding
        if transcription:
            text_embedding = await self.generate_text_embedding(transcription)
            
            # Project audio features to text embedding space
            audio_proj = self._project_embedding(audio_features, text_embedding.shape[0])
            
            # Weighted combination (text is more important for education)
            combined = 0.7 * text_embedding + 0.3 * audio_proj
            
            # Normalize
            norm = np.linalg.norm(combined)
            if norm > 0:
                combined = combined / norm
            
            return combined
        else:
            return audio_features
