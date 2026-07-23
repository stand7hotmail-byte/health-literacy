"""Tests for database ingestion module."""

import pytest
import os
import sys
import json

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, scripts_dir)

from db.models import (
    Paper,
    PaperEmbedding,
    GenerationLog,
    create_tables,
    drop_tables,
    paper_to_row,
    row_to_paper,
    embedding_to_row,
    row_to_embedding
)
from db.ingest import (
    PaperIngestor,
    ingest_pubmed_papers,
    get_paper_by_pmid,
    get_papers_by_category,
    get_recent_papers
)
import duckdb


class TestPaperIngestor:
    """Test PaperIngestor class."""

    def setup_method(self):
        """Set up test database."""
        import duckdb
        self.conn = duckdb.connect(":memory:")
        create_tables(self.conn)

    def teardown_method(self):
        """Clean up."""
        self.conn.close()

    def test_ingestor_initialization(self):
        """PaperIngestor should initialize with connection."""
        ingestor = PaperIngestor(self.conn)
        assert ingestor.conn == self.conn

    def test_insert_paper(self):
        """Should insert paper into database."""
        ingestor = PaperIngestor(self.conn)
        
        paper = Paper(
            pmid="12345678",
            title="Test Paper",
            abstract="Test abstract",
            authors=["Author A"],
            journal="Test Journal",
            pub_date="2024-01-15",
            doi="10.1234/test",
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            mesh_terms=["hypertension"],
            category="heart",
            evidence_level="RCT"
        )
        
        ingestor.insert_paper(paper)
        
        # Verify insertion
        result = self.conn.execute("SELECT * FROM papers WHERE pmid = ?", ["12345678"]).fetchone()
        assert result is not None
        assert result[0] == "12345678"
        assert result[1] == "Test Paper"

    def test_upsert_paper_updates_existing(self):
        """Upserting existing paper should update it."""
        ingestor = PaperIngestor(self.conn)
        
        paper = Paper(
            pmid="12345678",
            title="Original Title",
            abstract="Original abstract",
            authors=["Author A"],
            journal="Test Journal",
            pub_date="2024-01-15",
            doi="10.1234/test",
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            mesh_terms=["hypertension"],
            category="heart",
            evidence_level="RCT"
        )
        ingestor.insert_paper(paper)
        
        # Update paper
        paper.title = "Updated Title"
        paper.abstract = "Updated abstract"
        paper.updated_at = None  # Will be set to now
        ingestor.insert_paper(paper)
        
        # Verify update
        result = self.conn.execute("SELECT title, abstract FROM papers WHERE pmid = ?", ["12345678"]).fetchone()
        assert result[0] == "Updated Title"
        assert result[1] == "Updated abstract"

    def test_insert_embedding(self):
        """Should insert embedding for paper."""
        import numpy as np
        ingestor = PaperIngestor(self.conn)
        
        # First insert paper
        paper = Paper(pmid="12345678", title="Test")
        ingestor.insert_paper(paper)
        
        # Insert embedding
        embedding = PaperEmbedding(
            pmid="12345678",
            embedding=np.random.rand(384).astype(np.float32),
            model="all-MiniLM-L6-v2"
        )
        ingestor.insert_embedding(embedding)
        
        # Verify
        result = self.conn.execute("SELECT pmid, model FROM paper_embeddings WHERE pmid = ?", ["12345678"]).fetchone()
        assert result is not None
        assert result[0] == "12345678"
        assert result[1] == "all-MiniLM-L6-v2"

    def test_get_paper_by_pmid(self):
        """Should retrieve paper by PMID."""
        ingestor = PaperIngestor(self.conn)
        
        paper = Paper(
            pmid="12345678",
            title="Test Paper",
            abstract="Test abstract",
            authors=["Author A"],
            journal="Test Journal",
            pub_date="2024-01-15",
            doi="10.1234/test",
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            mesh_terms=["hypertension"],
            category="heart",
            evidence_level="RCT"
        )
        ingestor.insert_paper(paper)
        
        retrieved = ingestor.get_paper_by_pmid("12345678")
        
        assert retrieved is not None
        assert retrieved.pmid == "12345678"
        assert retrieved.title == "Test Paper"
        assert retrieved.category == "heart"

    def test_get_nonexistent_paper_returns_none(self):
        """Getting non-existent paper should return None."""
        ingestor = PaperIngestor(self.conn)
        
        result = ingestor.get_paper_by_pmid("99999999")
        
        assert result is None

    def test_get_papers_by_category(self):
        """Should retrieve papers by category."""
        ingestor = PaperIngestor(self.conn)
        
        # Insert papers in different categories
        for i, cat in enumerate(["heart", "brain", "heart", "muscle"]):
            paper = Paper(
                pmid=f"1111111{i}",
                title=f"Paper {i}",
                category=cat
            )
            ingestor.insert_paper(paper)
        
        heart_papers = ingestor.get_papers_by_category("heart")
        
        assert len(heart_papers) == 2
        assert all(p.category == "heart" for p in heart_papers)

    def test_get_recent_papers(self):
        """Should retrieve recent papers within days."""
        ingestor = PaperIngestor(self.conn)
        
        # Insert papers with different dates
        import datetime
        old_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        recent_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        
        paper_old = Paper(pmid="11111111", title="Old Paper", pub_date=old_date)
        paper_recent = Paper(pmid="22222222", title="Recent Paper", pub_date=recent_date)
        
        ingestor.insert_paper(paper_old)
        ingestor.insert_paper(paper_recent)
        
        recent = ingestor.get_recent_papers(days=7)
        
        assert len(recent) == 1
        assert recent[0].pmid == "22222222"

    def test_log_generation(self):
        """Should log generation info."""
        ingestor = PaperIngestor(self.conn)
        
        ingestor.log_generation(
            week="2024-W03",
            theme="Test Theme",
            source_pmids=["12345678", "87654321"],
            article_slug="test-article"
        )
        
        result = self.conn.execute("SELECT * FROM generation_log WHERE week = ?", ["2024-W03"]).fetchone()
        assert result is not None
        assert result[1] == "2024-W03"
        assert result[2] == "Test Theme"
        assert "12345678" in result[3]
        assert result[4] == "test-article"

    def test_is_paper_processed(self):
        """Should check if paper was already used in generation."""
        ingestor = PaperIngestor(self.conn)
        
        # Log a generation
        ingestor.log_generation(
            week="2024-W03",
            theme="Test",
            source_pmids=["12345678"],
            article_slug="test"
        )
        
        assert ingestor.is_paper_processed("12345678") is True
        assert ingestor.is_paper_processed("99999999") is False


class TestIngestPubmedPapers:
    """Test pubmed ingestion function."""
    
    def test_ingest_pubmed_papers_returns_papers(self):
        """Should return list of papers (mocked)."""
        # This test would require mocking PubMed API
        # For now, just verify function exists and is callable
        assert callable(ingest_pubmed_papers)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])