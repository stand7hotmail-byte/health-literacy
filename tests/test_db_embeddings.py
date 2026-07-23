"""Tests for embeddings module."""

import pytest
import numpy as np
import sys
import os

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, scripts_dir)

from db.embeddings import (
    generate_embedding,
    generate_embeddings_batch,
    paper_to_embedding_text,
    generate_paper_embedding,
    cosine_similarity,
    search_similar_papers,
    EmbeddingManager
)
from db.models import Paper


class MockPaper:
    """Mock paper for testing."""
    def __init__(self, title="Test Title", abstract="Test abstract content", mesh_terms=None, category="heart"):
        self.title = title
        self.abstract = abstract
        self.mesh_terms = mesh_terms or ["hypertension", "blood pressure"]
        self.category = category


class TestEmbeddingGeneration:
    """Test embedding generation functions."""
    
    def test_generate_embedding_returns_correct_shape(self):
        """generate_embedding should return 384-dimensional vector."""
        embedding = generate_embedding("Test text for embedding")
        
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32
    
    def test_generate_embedding_normalized(self):
        """Generated embeddings should be normalized (unit length)."""
        embedding = generate_embedding("Test text")
        
        # Should be normalized to unit length
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5
    
    def test_generate_embeddings_batch(self):
        """generate_embeddings_batch should return correct shape for multiple texts."""
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = generate_embeddings_batch(texts)
        
        assert embeddings.shape == (3, 384)
        assert embeddings.dtype == np.float32
    
    def test_paper_to_embedding_text(self):
        """paper_to_embedding_text should format paper correctly."""
        paper = MockPaper(
            title="Hypertension Treatment",
            abstract="This study examines...",
            mesh_terms=["hypertension", "treatment"],
            category="heart"
        )
        
        text = paper_to_embedding_text(paper)
        
        assert "Hypertension Treatment" in text
        assert "This study examines" in text
        assert "hypertension" in text
        assert "treatment" in text
        assert "Category: heart" in text
    
    def test_generate_paper_embedding(self):
        """generate_paper_embedding should return normalized vector."""
        paper = MockPaper(title="Test", abstract="Content")
        embedding = generate_paper_embedding(paper)
        
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32
        assert abs(np.linalg.norm(embedding) - 1.0) < 1e-5


class TestCosineSimilarity:
    """Test cosine similarity calculations."""
    
    def test_cosine_similarity_identical_vectors(self):
        """Similarity of identical vectors should be 1.0."""
        a = np.random.rand(384).astype(np.float32)
        a = a / np.linalg.norm(a)
        
        sim = cosine_similarity(a, a)
        
        assert abs(sim - 1.0) < 1e-5
    
    def test_cosine_similarity_orthogonal_vectors(self):
        """Similarity of orthogonal vectors should be 0."""
        a = np.zeros(384, dtype=np.float32)
        a[0] = 1.0
        b = np.zeros(384, dtype=np.float32)
        b[1] = 1.0
        
        sim = cosine_similarity(a, b)
        
        assert abs(sim) < 1e-5
    
    def test_cosine_similarity_opposite_vectors(self):
        """Similarity of opposite vectors should be -1."""
        a = np.zeros(384, dtype=np.float32)
        a[0] = 1.0
        b = np.zeros(384, dtype=np.float32)
        b[0] = -1.0
        
        sim = cosine_similarity(a, b)
        
        assert abs(sim - (-1.0)) < 1e-5


class TestSearchSimilarPapers:
    """Test similar paper search."""
    
    def test_search_returns_top_k(self):
        """search_similar_papers should return top k results."""
        query = np.random.rand(384).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Create embeddings where first one is most similar
        embeddings = []
        for i in range(20):
            emb = np.random.rand(384).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            embeddings.append(emb)
        
        # Make first embedding identical to query
        embeddings[0] = query.copy()
        
        results = search_similar_papers(query, embeddings, top_k=5)
        
        assert len(results) == 5
        assert results[0][0] == 0  # First should be the identical one
        assert results[0][1] > 0.99  # Should be nearly 1.0
    
    def test_search_handles_none_embeddings(self):
        """search_similar_papers should skip None embeddings."""
        query = np.random.rand(384).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        embeddings = [query, None, query / 2, None]
        
        results = search_similar_papers(query, embeddings, top_k=3)
        
        # Should only find valid embeddings
        assert len(results) <= 3
        for idx, score in results:
            assert idx != 1  # Should not include None at index 1
            assert idx != 3  # Should not include None at index 3


class TestEmbeddingManager:
    """Test EmbeddingManager class."""
    
    def test_manager_initialization(self):
        """EmbeddingManager should initialize with model."""
        manager = EmbeddingManager()
        
        assert manager.model is not None
        assert manager.dimension == 384
    
    def test_embed_paper(self):
        """embed_paper should return normalized embedding."""
        manager = EmbeddingManager()
        paper = MockPaper(title="Test", abstract="Content")
        
        embedding = manager.embed_paper(paper)
        
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32
        assert abs(np.linalg.norm(embedding) - 1.0) < 1e-5
    
    def test_embed_query(self):
        """embed_query should return normalized embedding."""
        manager = EmbeddingManager()
        
        embedding = manager.embed_query("hypertension treatment")
        
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32
        assert abs(np.linalg.norm(embedding) - 1.0) < 1e-5
    
    def test_embed_papers_batch(self):
        """embed_papers should return list of embeddings."""
        manager = EmbeddingManager()
        papers = [MockPaper(title=f"Paper {i}") for i in range(5)]
        
        embeddings = manager.embed_papers(papers)
        
        assert len(embeddings) == 5
        for emb in embeddings:
            assert emb.shape == (384,)
            assert abs(np.linalg.norm(emb) - 1.0) < 1e-5


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_model(self):
        """get_model should return model instance."""
        from db.embeddings import get_model
        model = get_model()
        
        assert model is not None
    
    def test_embed_text(self):
        """embed_text should return embedding."""
        from db.embeddings import embed_text
        embedding = embed_text("test text")
        
        assert embedding.shape == (384,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 1e-5
    
    def test_embed_paper(self):
        """embed_paper should work with Paper object."""
        from db.embeddings import embed_paper
        paper = MockPaper()
        embedding = embed_paper(paper)
        
        assert embedding.shape == (384,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 1e-5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])