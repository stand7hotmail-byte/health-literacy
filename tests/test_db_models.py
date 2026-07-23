"""Tests for database models and schema."""

import pytest
import os
import sys

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, scripts_dir)

from db.models import (
    Paper,
    PaperEmbedding,
    GenerationLog,
    create_tables,
    drop_tables
)


class TestPaperModel:
    """Test Paper model/schema."""
    
    def test_paper_has_required_fields(self):
        """Paper should have all required fields."""
        paper = Paper(
            pmid="12345678",
            title="Test Paper Title",
            abstract="Test abstract content",
            authors=["Author A", "Author B"],
            journal="Test Journal",
            pub_date="2024-01-15",
            doi="10.1234/test.2024",
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            mesh_terms=["hypertension", "blood pressure"],
            category="heart",
            evidence_level="RCT"
        )
        
        assert paper.pmid == "12345678"
        assert paper.title == "Test Paper Title"
        assert paper.abstract == "Test abstract content"
        assert paper.authors == ["Author A", "Author B"]
        assert paper.journal == "Test Journal"
        assert paper.pub_date == "2024-01-15"
        assert paper.doi == "10.1234/test.2024"
        assert paper.url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        assert paper.mesh_terms == ["hypertension", "blood pressure"]
        assert paper.category == "heart"
        assert paper.evidence_level == "RCT"
    
    def test_paper_optional_fields_can_be_none(self):
        """Paper should allow optional fields to be None."""
        paper = Paper(
            pmid="87654321",
            title="Minimal Paper",
            abstract=None,
            authors=[],
            journal="",
            pub_date=None,
            doi=None,
            url="",
            mesh_terms=[],
            category=None,
            evidence_level=None
        )
        
        assert paper.pmid == "87654321"
        assert paper.title == "Minimal Paper"
        assert paper.abstract is None
        assert paper.authors == []


class TestPaperEmbeddingModel:
    """Test PaperEmbedding model/schema."""
    
    def test_embedding_has_required_fields(self):
        """PaperEmbedding should have required fields."""
        import numpy as np
        embedding = PaperEmbedding(
            pmid="12345678",
            embedding=np.random.rand(384).astype(np.float32),
            model="all-MiniLM-L6-v2"
        )
        
        assert embedding.pmid == "12345678"
        assert embedding.model == "all-MiniLM-L6-v2"
        assert embedding.embedding.shape == (384,)
        assert embedding.embedding.dtype == np.float32


class TestGenerationLogModel:
    """Test GenerationLog model/schema."""
    
    def test_generation_log_has_required_fields(self):
        """GenerationLog should have required fields."""
        log = GenerationLog(
            week="2024-W03",
            theme="Test Theme",
            source_pmids=["12345678", "87654321"],
            article_slug="test-article-slug"
        )
        
        assert log.week == "2024-W03"
        assert log.theme == "Test Theme"
        assert log.source_pmids == ["12345678", "87654321"]
        assert log.article_slug == "test-article-slug"


class TestDatabaseSchema:
    """Test database schema creation."""
    
    def test_create_tables_creates_all_tables(self):
        """create_tables should create all required tables."""
        import duckdb
    
        conn = duckdb.connect(":memory:")
        create_tables(conn)
        
        # Check tables exist
        tables = conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'main'
        """).fetchall()
        table_names = {t[0] for t in tables}
        
        assert "papers" in table_names
        assert "paper_embeddings" in table_names
        assert "generation_log" in table_names
        
        conn.close()
    
    def test_drop_tables_removes_all_tables(self):
        """drop_tables should remove all tables."""
        import duckdb
    
        conn = duckdb.connect(":memory:")
        create_tables(conn)
        drop_tables(conn)
        
        tables = conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'main'
        """).fetchall()
        
        assert len(tables) == 0
        
        conn.close()
    
    def test_papers_table_has_correct_columns(self):
        """papers table should have all required columns."""
        import duckdb
    
        conn = duckdb.connect(":memory:")
        create_tables(conn)
        
        columns = conn.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'papers'
        """).fetchall()
        column_names = {c[0] for c in columns}
        
        required_columns = {
            "pmid", "title", "abstract", "authors", "journal",
            "pub_date", "doi", "url", "mesh_terms", "category",
            "evidence_level", "created_at", "updated_at"
        }
        
        assert required_columns.issubset(column_names)
        
        conn.close()
    
    def test_paper_embeddings_table_has_hnsw_index(self):
        """paper_embeddings table should have HNSW index."""
        import duckdb
    
        conn = duckdb.connect(":memory:")
        create_tables(conn)
        
        # Check index exists
        indexes = conn.execute("""
            SELECT index_name FROM duckdb_indexes()
            WHERE table_name = 'paper_embeddings'
        """).fetchall()
        
        # At least one index should exist for embeddings
        assert len(indexes) >= 1
        
        conn.close()


class TestCRUDOperations:
    """Test basic CRUD operations."""
    
    def test_insert_and_select_paper(self):
        """Should be able to insert and select a paper."""
        import duckdb
        import numpy as np
    
        conn = duckdb.connect(":memory:")
        create_tables(conn)
        
        # Insert paper
        conn.execute("""
            INSERT INTO papers (pmid, title, abstract, authors, journal, pub_date, doi, url, mesh_terms, category, evidence_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ["12345678", "Test Title", "Test Abstract", '["Author A"]', "Test Journal", "2024-01-15", "10.1234/test", "https://pubmed.ncbi.nlm.nih.gov/12345678/", '["hypertension"]', "heart", "RCT"])
        
        # Select paper
        result = conn.execute("SELECT * FROM papers WHERE pmid = ?", ["12345678"]).fetchone()
        
        assert result is not None
        assert result[0] == "12345678"  # pmid
        assert result[1] == "Test Title"  # title
        
        conn.close()
    
    def test_duplicate_pmid_raises_error(self):
        """Inserting duplicate PMID should raise error (primary key)."""
        import duckdb
    
        conn = duckdb.connect(":memory:")
        create_tables(conn)
        
        conn.execute("""
            INSERT INTO papers (pmid, title) VALUES (?, ?)
        """, ["12345678", "Title 1"])
        
        # Second insert should fail
        with pytest.raises(Exception):
            conn.execute("""
                INSERT INTO papers (pmid, title) VALUES (?, ?)
            """, ["12345678", "Title 2"])
        
        conn.close()
    
    def test_insert_embedding(self):
        """Should be able to insert embedding."""
        import duckdb
        import numpy as np
    
        conn = duckdb.connect(":memory:")
        create_tables(conn)
        
        # Insert paper first
        conn.execute("INSERT INTO papers (pmid, title) VALUES (?, ?)", ["12345678", "Test"])
        
        # Insert embedding
        embedding = np.random.rand(384).astype(np.float32)
        conn.execute("""
            INSERT INTO paper_embeddings (pmid, embedding, model) VALUES (?, ?, ?)
        """, ["12345678", embedding, "all-MiniLM-L6-v2"])
        
        # Select embedding
        result = conn.execute("SELECT * FROM paper_embeddings WHERE pmid = ?", ["12345678"]).fetchone()
        
        assert result is not None
        assert result[0] == "12345678"
        assert result[2] == "all-MiniLM-L6-v2"
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])