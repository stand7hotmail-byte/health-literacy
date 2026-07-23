"""Embeddings generation for paper similarity search."""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model: Optional[SentenceTransformer] = None
_model_name = "all-MiniLM-L6-v2"  # 384 dimensions, fast, good quality


def get_embedding_model(model_name: str = _model_name) -> SentenceTransformer:
    """Get or create the embedding model instance."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
    return _model


def generate_embedding(text: str, model: Optional[SentenceTransformer] = None) -> np.ndarray:
    """Generate embedding for a single text."""
    if model is None:
        model = get_embedding_model()
    
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.astype(np.float32)


def generate_embeddings_batch(texts: List[str], model: Optional[SentenceTransformer] = None, batch_size: int = 32) -> np.ndarray:
    """Generate embeddings for multiple texts efficiently."""
    if model is None:
        model = get_embedding_model()
    
    embeddings = model.encode(
        texts, 
        convert_to_numpy=True, 
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100
    )
    return embeddings.astype(np.float32)


def paper_to_embedding_text(paper) -> str:
    """Convert paper to text suitable for embedding."""
    parts = []
    
    if paper.title:
        parts.append(f"Title: {paper.title}")
    
    if paper.abstract:
        parts.append(f"Abstract: {paper.abstract}")
    
    if paper.mesh_terms:
        parts.append(f"Keywords: {', '.join(paper.mesh_terms)}")
    
    if paper.category:
        parts.append(f"Category: {paper.category}")
    
    return "\n\n".join(parts)


def generate_paper_embedding(paper, model: Optional[SentenceTransformer] = None) -> np.ndarray:
    """Generate embedding for a paper."""
    text = paper_to_embedding_text(paper)
    return generate_embedding(text, model)


def generate_paper_embeddings_batch(papers: List, model: Optional[SentenceTransformer] = None) -> np.ndarray:
    """Generate embeddings for multiple papers."""
    texts = [paper_to_embedding_text(p) for p in papers]
    return generate_embeddings_batch(texts, model)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def search_similar_papers(
    query_embedding: np.ndarray,
    paper_embeddings: List[np.ndarray],
    top_k: int = 10
) -> List[tuple]:
    """Search for similar papers using cosine similarity.
    
    Returns list of (index, similarity_score) tuples sorted by similarity.
    """
    similarities = []
    for i, emb in enumerate(paper_embeddings):
        if emb is not None:
            sim = cosine_similarity(query_embedding, emb)
            similarities.append((i, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


class EmbeddingManager:
    """Manages paper embeddings generation and storage."""
    
    def __init__(self, model_name: str = _model_name):
        self.model = get_embedding_model(model_name)
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
    
    def embed_papers(self, papers: List) -> List[np.ndarray]:
        """Generate embeddings for a list of papers."""
        texts = [paper_to_embedding_text(p) for p in papers]
        embeddings = generate_embeddings_batch(texts, self.model)
        return [emb for emb in embeddings]
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a search query."""
        return generate_embedding(query, self.model)
    
    def embed_paper(self, paper) -> np.ndarray:
        """Generate embedding for a single paper."""
        text = paper_to_embedding_text(paper)
        return generate_embedding(text, self.model)


# Convenience functions
def get_model() -> SentenceTransformer:
    """Get the default embedding model."""
    return get_embedding_model()


def embed_text(text: str) -> np.ndarray:
    """Generate embedding for text."""
    return generate_embedding(text)


def embed_paper(paper) -> np.ndarray:
    """Generate embedding for paper."""
    return generate_paper_embedding(paper)