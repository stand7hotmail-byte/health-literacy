"""Database ingestion module for paper knowledge base."""

import duckdb
import numpy as np
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging

from .models import (
    Paper,
    PaperEmbedding,
    GenerationLog,
    create_tables,
    paper_to_row,
    row_to_paper,
    embedding_to_row,
    row_to_embedding
)

logger = logging.getLogger(__name__)


class PaperIngestor:
    """Handles paper ingestion into the database."""
    
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
    
    def insert_paper(self, paper: Paper) -> None:
        """Insert or update a paper in the database."""
        # Check if paper exists
        existing = self.conn.execute("SELECT pmid FROM papers WHERE pmid = ?", [paper.pmid]).fetchone()
        
        if existing:
            # Update existing paper
            paper.updated_at = datetime.now()
            self.conn.execute("""
                UPDATE papers SET
                    title = ?, abstract = ?, authors = ?, journal = ?,
                    pub_date = ?, doi = ?, url = ?, mesh_terms = ?,
                    category = ?, evidence_level = ?, updated_at = ?
                WHERE pmid = ?
            """, [
                paper.title, paper.abstract, json.dumps(paper.authors, ensure_ascii=False),
                paper.journal, paper.pub_date, paper.doi, paper.url,
                json.dumps(paper.mesh_terms, ensure_ascii=False),
                paper.category, paper.evidence_level, paper.updated_at, paper.pmid
            ])
            logger.debug(f"Updated paper: {paper.pmid}")
        else:
            # Insert new paper
            self.conn.execute("""
                INSERT INTO papers (
                    pmid, title, abstract, authors, journal, pub_date,
                    doi, url, mesh_terms, category, evidence_level,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, paper_to_row(paper))
            logger.debug(f"Inserted paper: {paper.pmid}")
    
    def insert_embedding(self, embedding: PaperEmbedding) -> None:
        """Insert or update paper embedding."""
        self.conn.execute("""
            INSERT INTO paper_embeddings (pmid, embedding, model, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (pmid) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                model = EXCLUDED.model,
                created_at = EXCLUDED.created_at
        """, embedding_to_row(embedding))
        logger.debug(f"Inserted embedding for: {embedding.pmid}")
    
    def get_paper_by_pmid(self, pmid: str) -> Optional[Paper]:
        """Retrieve a paper by PMID."""
        row = self.conn.execute("SELECT * FROM papers WHERE pmid = ?", [pmid]).fetchone()
        if row:
            return row_to_paper(row)
        return None
    
    def get_papers_by_category(self, category: str, limit: int = 100) -> List[Paper]:
        """Retrieve papers by category."""
        rows = self.conn.execute(
            "SELECT * FROM papers WHERE category = ? ORDER BY pub_date DESC LIMIT ?",
            [category, limit]
        ).fetchall()
        return [row_to_paper(row) for row in rows]
    
    def get_recent_papers(self, days: int = 7, limit: int = 100) -> List[Paper]:
        """Retrieve papers published within the last N days."""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self.conn.execute(
            "SELECT * FROM papers WHERE pub_date >= ? ORDER BY pub_date DESC LIMIT ?",
            [cutoff_date, limit]
        ).fetchall()
        return [row_to_paper(row) for row in rows]
    
    def log_generation(
        self,
        week: str,
        theme: str,
        source_pmids: List[str],
        article_slug: str
    ) -> int:
        """Log a weekly column generation."""
        import json
        # Get next ID
        next_id = self.conn.execute("SELECT nextval('generation_log_seq')").fetchone()[0]
        
        self.conn.execute("""
            INSERT INTO generation_log (id, week, theme, source_pmids, article_slug, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            next_id, week, theme,
            json.dumps(source_pmids, ensure_ascii=False),
            article_slug, datetime.now()
        ])
        return next_id
    
    def is_paper_processed(self, pmid: str) -> bool:
        """Check if paper has been used in a generation."""
        result = self.conn.execute(
            "SELECT 1 FROM generation_log WHERE source_pmids LIKE ?",
            [f'%"{pmid}"%']
        ).fetchone()
        return result is not None
    
    def get_generation_log(self, week: str) -> Optional[dict]:
        """Get generation log for a specific week."""
        row = self.conn.execute(
            "SELECT * FROM generation_log WHERE week = ?", [week]
        ).fetchone()
        if row:
            import json
            return {
                "id": row[0],
                "week": row[1],
                "theme": row[2],
                "source_pmids": json.loads(row[3]) if row[3] else [],
                "article_slug": row[4],
                "created_at": row[5]
            }
        return None


def ingest_pubmed_papers(
    papers: List[Paper],
    conn: duckdb.DuckDBPyConnection
) -> int:
    """Ingest a list of PubMed papers into the database.
    
    Returns the number of papers inserted/updated.
    """
    ingestor = PaperIngestor(conn)
    count = 0
    for paper in papers:
        ingestor.insert_paper(paper)
        count += 1
    return count


def get_paper_by_pmid(pmid: str, conn: duckdb.DuckDBPyConnection) -> Optional[Paper]:
    """Get a paper by PMID."""
    ingestor = PaperIngestor(conn)
    return ingestor.get_paper_by_pmid(pmid)


def get_papers_by_category(category: str, conn: duckdb.DuckDBPyConnection, limit: int = 100) -> List[Paper]:
    """Get papers by category."""
    ingestor = PaperIngestor(conn)
    return ingestor.get_papers_by_category(category, limit)


def get_recent_papers(days: int = 7, conn: duckdb.DuckDBPyConnection = None, limit: int = 100) -> List[Paper]:
    """Get recent papers."""
    if conn is None:
        # Create temporary connection
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
        conn = duckdb.connect(temp_db)
        create_tables(conn)
    ingestor = PaperIngestor(conn)
    return ingestor.get_recent_papers(days, limit)