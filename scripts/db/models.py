"""Database models and schema for paper knowledge base."""

import duckdb
import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class Paper:
    """Paper data model."""
    pmid: str
    title: str
    abstract: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    pub_date: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    mesh_terms: Optional[List[str]] = None
    category: Optional[str] = None
    evidence_level: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.mesh_terms is None:
            self.mesh_terms = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_db_tuple(self):
        """Convert to tuple for database insertion."""
        return (
            self.pmid,
            self.title,
            self.abstract,
            json.dumps(self.authors, ensure_ascii=False),
            self.journal,
            self.pub_date,
            self.doi,
            self.url,
            json.dumps(self.mesh_terms, ensure_ascii=False),
            self.category,
            self.evidence_level,
            self.created_at,
            self.updated_at
        )

    @classmethod
    def from_db_row(cls, row):
        """Create Paper from database row."""
        return cls(
            pmid=row[0],
            title=row[1],
            abstract=row[2],
            authors=json.loads(row[3]) if row[3] else [],
            journal=row[4],
            pub_date=row[5],
            doi=row[6],
            url=row[7],
            mesh_terms=json.loads(row[8]) if row[8] else [],
            category=row[9],
            evidence_level=row[10],
            created_at=row[11],
            updated_at=row[12]
        )


@dataclass
class PaperEmbedding:
    """Paper embedding model."""
    pmid: str
    embedding: np.ndarray
    model: str
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class GenerationLog:
    """Generation log model."""
    week: str
    theme: str
    source_pmids: List[str]
    article_slug: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_db_tuple(self):
        return (
            self.id,
            self.week,
            self.theme,
            json.dumps(self.source_pmids, ensure_ascii=False),
            self.article_slug,
            self.created_at
        )


def create_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all database tables."""
    # Main papers table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            pmid VARCHAR PRIMARY KEY,
            title VARCHAR NOT NULL,
            abstract TEXT,
            authors TEXT,           -- JSON array
            journal VARCHAR,
            pub_date DATE,
            doi VARCHAR,
            url VARCHAR,
            mesh_terms TEXT,        -- JSON array
            category VARCHAR,       -- heart/brain/muscle/sugar/check/sleep/gut/eyes
            evidence_level VARCHAR, -- RCT/meta/guideline/obs
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Paper embeddings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_embeddings (
            pmid VARCHAR PRIMARY KEY REFERENCES papers(pmid),
            embedding FLOAT[384],
            model VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Generation log table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS generation_log (
            id INTEGER PRIMARY KEY,
            week VARCHAR NOT NULL,
            theme TEXT,
            source_pmids TEXT,      -- JSON array
            article_slug VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create sequence for generation_log id
    conn.execute("CREATE SEQUENCE IF NOT EXISTS generation_log_seq")

    # Additional indexes for common queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_pub_date ON papers(pub_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_evidence_level ON papers(evidence_level)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_generation_log_week ON generation_log(week)")

    # Try to create HNSW index for vector similarity search (requires VSS extension)
    # This may fail if VSS extension is not available, so we wrap in try/except
    try:
        # Load VSS extension if available
        conn.execute("INSTALL vss;")
        conn.execute("LOAD vss;")
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_paper_embeddings_hnsw
            ON paper_embeddings
            USING HNSW(embedding)
            WITH (metric = 'cosine')
        """)
    except Exception:
        # VSS extension not available, skip HNSW index
        pass


def drop_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Drop all database tables."""
    conn.execute("DROP INDEX IF EXISTS idx_paper_embeddings_hnsw")
    conn.execute("DROP INDEX IF EXISTS idx_papers_category")
    conn.execute("DROP INDEX IF EXISTS idx_papers_pub_date")
    conn.execute("DROP INDEX IF EXISTS idx_papers_evidence_level")
    conn.execute("DROP INDEX IF EXISTS idx_generation_log_week")
    conn.execute("DROP TABLE IF EXISTS generation_log")
    conn.execute("DROP TABLE IF EXISTS paper_embeddings")
    conn.execute("DROP TABLE IF EXISTS papers")
    conn.execute("DROP SEQUENCE IF EXISTS generation_log_seq")


def paper_to_row(paper: Paper) -> tuple:
    """Convert Paper object to database row tuple."""
    return (
        paper.pmid,
        paper.title,
        paper.abstract,
        json.dumps(paper.authors, ensure_ascii=False),
        paper.journal,
        paper.pub_date,
        paper.doi,
        paper.url,
        json.dumps(paper.mesh_terms, ensure_ascii=False),
        paper.category,
        paper.evidence_level,
        paper.created_at,
        paper.updated_at
    )


def row_to_paper(row: tuple) -> Paper:
    """Convert database row to Paper object."""
    return Paper(
        pmid=row[0],
        title=row[1],
        abstract=row[2],
        authors=json.loads(row[3]) if row[3] else [],
        journal=row[4],
        pub_date=row[5],
        doi=row[6],
        url=row[7],
        mesh_terms=json.loads(row[8]) if row[8] else [],
        category=row[9],
        evidence_level=row[10],
        created_at=row[11],
        updated_at=row[12]
    )


def embedding_to_row(embedding: PaperEmbedding) -> tuple:
    """Convert PaperEmbedding object to database row tuple."""
    return (
        embedding.pmid,
        embedding.embedding.tolist() if isinstance(embedding.embedding, np.ndarray) else embedding.embedding,
        embedding.model,
        embedding.created_at
    )


def row_to_embedding(row: tuple) -> PaperEmbedding:
    """Convert database row to PaperEmbedding object."""
    return PaperEmbedding(
        pmid=row[0],
        embedding=np.array(row[1], dtype=np.float32) if row[1] is not None else None,
        model=row[2],
        created_at=row[3]
    )