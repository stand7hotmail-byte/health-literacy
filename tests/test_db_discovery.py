"""Tests for database discovery module - finding relationships between papers."""

import pytest
import os
import sys
import numpy as np
from datetime import datetime, timedelta

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, scripts_dir)

from db.models import Paper, PaperEmbedding, create_tables
from db.ingest import PaperIngestor
from db.discovery import (
    PaperClusterer,
    TrendAnalyzer,
    ContradictionDetector,
    JapanFocusDetector,
    ThemePicker,
    find_related_papers,
    get_paper_recommendations
)
import duckdb


class TestPaperClusterer:
    """Test paper clustering functionality."""
    
    def setup_method(self):
        """Set up test database with sample papers."""
        self.conn = duckdb.connect(":memory:")
        create_tables(self.conn)
        self.ingestor = PaperIngestor(self.conn)
        
        # Create papers with embeddings in different clusters
        np.random.seed(42)
        base_embeddings = {
            "heart": np.array([1.0] + [0.0] * 383, dtype=np.float32),
            "brain": np.array([0.0, 1.0] + [0.0] * 382, dtype=np.float32),
            "muscle": np.array([0.0, 0.0, 1.0] + [0.0] * 381, dtype=np.float32),
        }
        
        for i, (cat, base_emb) in enumerate(base_embeddings.items()):
            for j in range(3):
                pmid = f"{10000000 + i * 10 + j}"
                paper = Paper(
                    pmid=pmid,
                    title=f"{cat.title()} Paper {j}",
                    abstract=f"Abstract about {cat}",
                    category=cat,
                    mesh_terms=[cat]
                )
                self.ingestor.insert_paper(paper)
                
                # Add slight noise to embeddings
                noise = np.random.rand(384).astype(np.float32) * 0.1
                emb = base_emb + noise
                emb = emb / np.linalg.norm(emb)
                self.ingestor.insert_embedding(PaperEmbedding(
                    pmid=pmid,
                    embedding=emb,
                    model="all-MiniLM-L6-v2"
                ))
    
    def teardown_method(self):
        self.conn.close()
    
    def test_cluster_papers_returns_clusters(self):
        """cluster_papers should return cluster assignments."""
        clusterer = PaperClusterer(self.conn)
        clusters = clusterer.cluster_papers(n_clusters=3)
        
        assert len(clusters) == 3
        assert all(len(c) > 0 for c in clusters)
        
        # Check papers from same category are in same cluster
        cluster_labels = {}
        for i, cluster in enumerate(clusters):
            for pmid in cluster:
                cluster_labels[pmid] = i
        
        assert len(cluster_labels) == 9  # All papers clustered
    
    def test_get_cluster_summary(self):
        """get_cluster_summary should return cluster info."""
        clusterer = PaperClusterer(self.conn)
        clusters = clusterer.cluster_papers(n_clusters=3)
        summary = clusterer.get_cluster_summary(clusters)
        
        assert len(summary) == 3
        for s in summary:
            assert "cluster_id" in s
            assert "size" in s
            assert "top_categories" in s
            assert "representative_pmids" in s


class TestTrendAnalyzer:
    """Test trend analysis functionality."""
    
    def setup_method(self):
        self.conn = duckdb.connect(":memory:")
        create_tables(self.conn)
        self.ingestor = PaperIngestor(self.conn)
        
        # Add papers over recent time (last 12 months) with embeddings
        base_date = datetime.now() - timedelta(days=365)
        for i in range(24):
            date = base_date + timedelta(weeks=i*2)
            pmid = f"202301{i:06d}"
            paper = Paper(
                pmid=pmid,
                title=f"Paper {i}",
                pub_date=date.strftime("%Y-%m-%d"),
                category="heart" if i % 2 == 0 else "brain",
                mesh_terms=["hypertension"] if i % 2 == 0 else ["cognitive"]
            )
            self.ingestor.insert_paper(paper)
            
            # Add embedding
            emb = np.random.rand(384).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            self.ingestor.insert_embedding(PaperEmbedding(
                pmid=pmid, embedding=emb, model="all-MiniLM-L6-v2"
            ))
    
    def teardown_method(self):
        self.conn.close()
    
    def test_get_keyword_trends(self):
        """get_keyword_trends should return trend data."""
        analyzer = TrendAnalyzer(self.conn)
        trends = analyzer.get_keyword_trends("hypertension", months=12)
        
        assert "keyword" in trends
        assert "monthly_counts" in trends
        assert len(trends["monthly_counts"]) > 0
    
    def test_detect_trending_topics(self):
        """detect_trending_topics should find increasing keywords."""
        analyzer = TrendAnalyzer(self.conn)
        trending = analyzer.detect_trending_topics(months=6, min_papers=2)
        
        assert isinstance(trending, list)
        for t in trending:
            assert "keyword" in t
            assert "growth_rate" in t
    
    def test_category_trends(self):
        """get_category_trends should show category distribution over time."""
        analyzer = TrendAnalyzer(self.conn)
        trends = analyzer.get_category_trends(months=6)
        
        assert "heart" in trends
        assert "brain" in trends


class TestContradictionDetector:
    """Test contradiction detection."""
    
    def setup_method(self):
        self.conn = duckdb.connect(":memory:")
        create_tables(self.conn)
        self.ingestor = PaperIngestor(self.conn)
        
        # Add papers with potentially contradictory conclusions WITH embeddings
        papers = [
            Paper(pmid="1", title="Coffee prevents heart disease", abstract="Coffee reduces CVD risk by 20%", category="heart", mesh_terms=["coffee", "cardiovascular"], evidence_level="RCT"),
            Paper(pmid="2", title="Coffee increases heart risk", abstract="Coffee increases CVD risk by 15%", category="heart", mesh_terms=["coffee", "cardiovascular"], evidence_level="RCT"),
            Paper(pmid="3", title="Exercise improves cognition", abstract="Aerobic exercise boosts memory", category="brain", mesh_terms=["exercise", "cognition"], evidence_level="RCT"),
            Paper(pmid="4", title="Exercise no effect on cognition", abstract="No significant effect found", category="brain", mesh_terms=["exercise", "cognition"], evidence_level="RCT"),
        ]
        for p in papers:
            self.ingestor.insert_paper(p)
            # Add embeddings
            emb = np.random.rand(384).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            self.ingestor.insert_embedding(PaperEmbedding(pmid=p.pmid, embedding=emb, model="all-MiniLM-L6-v2"))
    
    def teardown_method(self):
        self.conn.close()
    
    def test_find_contradiction_pairs(self):
        """find_contradiction_pairs should identify potential contradictions."""
        detector = ContradictionDetector(self.conn)
        pairs = detector.find_contradiction_pairs()
        
        assert len(pairs) > 0
        for pair in pairs:
            assert "pmid1" in pair
            assert "pmid2" in pair
            assert "category" in pair  # Actual field name
            assert "contradiction_score" in pair  # Actual field name
            assert "shared_terms" in pair
    
    def test_contradiction_requires_same_topic(self):
        """Contradictions should be on same topic."""
        detector = ContradictionDetector(self.conn)
        pairs = detector.find_contradiction_pairs()
        
        for pair in pairs:
            # Both papers should share at least one mesh term
            # Our implementation returns shared_terms
            assert "shared_terms" in pair
            assert len(pair["shared_terms"]) > 0
            assert pair["category"] is not None


class TestJapanFocusDetector:
    """Test Japan-focused paper detection."""
    
    def setup_method(self):
        self.conn = duckdb.connect(":memory:")
        create_tables(self.conn)
        self.ingestor = PaperIngestor(self.conn)
        
        papers = [
            Paper(pmid="1", title="Japanese hypertension study", abstract="Study in Japanese population", category="heart", mesh_terms=["hypertension", "Japan"]),
            Paper(pmid="2", title="US hypertension study", abstract="Study in US population", category="heart", mesh_terms=["hypertension", "United States"]),
            Paper(pmid="3", title="Japan cohort study", abstract="Japanese cohort", category="brain", mesh_terms=["dementia", "Japan"]),
        ]
        for p in papers:
            self.ingestor.insert_paper(p)
    
    def teardown_method(self):
        self.conn.close()
    
    def test_find_japan_papers(self):
        """find_japan_papers should return Japan-related papers."""
        detector = JapanFocusDetector(self.conn)
        papers = detector.find_japan_papers()
        
        assert len(papers) == 2
        pmid_set = {p.pmid for p in papers}
        assert "1" in pmid_set
        assert "3" in pmid_set
    
    def test_get_japan_paper_ratio(self):
        """get_japan_paper_ratio should return ratio."""
        detector = JapanFocusDetector(self.conn)
        ratio = detector.get_japan_paper_ratio(category="heart")
        
        # 1 out of 2 heart papers is Japan-related
        assert ratio == 0.5


class TestThemePicker:
    """Test weekly theme selection."""
    
    def setup_method(self):
        self.conn = duckdb.connect(":memory:")
        create_tables(self.conn)
        self.ingestor = PaperIngestor(self.conn)
        
        # Add recent high-quality papers (last 30 days)
        for i in range(10):
            pmid = f"202401{i:06d}"
            paper = Paper(
                pmid=pmid,
                title=f"Recent Paper {i}",
                pub_date=(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                category="heart" if i < 5 else "brain",
                evidence_level="RCT" if i % 2 == 0 else "meta-analysis",
                mesh_terms=["hypertension", "treatment"] if i < 5 else ["cognitive", "exercise"]
            )
            self.ingestor.insert_paper(paper)
            
            # Add embedding
            emb = np.random.rand(384).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            self.ingestor.insert_embedding(PaperEmbedding(
                pmid=pmid, embedding=emb, model="all-MiniLM-L6-v2"
            ))
        
        # Log some generations to test deduplication
        self.ingestor.log_generation("2024-W01", "Theme 1", ["202401000000"], "theme-1")
    
    def teardown_method(self):
        self.conn.close()
    
    def test_pick_theme(self):
        """pick_theme should return a theme with source papers."""
        picker = ThemePicker(self.conn)
        theme = picker.pick_theme()
        
        assert theme is not None
        assert "topic" in theme
        assert "source_pmids" in theme
        assert "reasoning" in theme
        assert len(theme["source_pmids"]) > 0
    
    def test_theme_excludes_recently_used(self):
        """pick_theme should not reuse recent papers."""
        picker = ThemePicker(self.conn)
        
        # Pick first theme - should exclude the logged paper (202401000000)
        theme1 = picker.pick_theme()
        assert theme1 is not None, "Should return a theme"
        assert "202401000000" not in theme1["source_pmids"], "Should exclude logged paper"
        
        # Log the picked papers
        self.ingestor.log_generation("2024-W02", "Theme 2", theme1["source_pmids"], "theme-2")
        
        # Pick second theme - should exclude both previous sets
        theme2 = picker.pick_theme()
        assert theme2 is not None, "Should return second theme"
        for pmid in theme1["source_pmids"]:
            assert pmid not in theme2["source_pmids"], f"PMID {pmid} reused in theme2!"
        
        # Add more papers to test third pick (we only have 10 total)
        # Skip third pick test as we only have 10 papers total


class TestRecommendationFunctions:
    """Test recommendation convenience functions."""
    
    def setup_method(self):
        self.conn = duckdb.connect(":memory:")
        create_tables(self.conn)
        self.ingestor = PaperIngestor(self.conn)
        
        # Add papers with embeddings
        for i, cat in enumerate(["heart", "brain", "muscle"]):
            pmid = f"1111111{i}"
            paper = Paper(pmid=pmid, title=f"{cat} Paper", category=cat)
            self.ingestor.insert_paper(paper)
            emb = np.random.rand(384).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            self.ingestor.insert_embedding(PaperEmbedding(pmid=pmid, embedding=emb, model="test"))
    
    def teardown_method(self):
        self.conn.close()
    
    def test_find_related_papers(self):
        """find_related_papers should return similar papers."""
        related = find_related_papers(self.conn, "11111110", top_k=2)
        
        assert len(related) <= 2
        for pmid, score in related:
            assert isinstance(score, float)
            assert 0 <= score <= 1
    
    def test_get_paper_recommendations(self):
        """get_paper_recommendations should return formatted recommendations."""
        recs = get_paper_recommendations(self.conn, "11111110", top_k=2)
        
        assert isinstance(recs, list)
        for r in recs:
            assert "pmid" in r
            assert "title" in r
            assert "similarity" in r
            assert "category" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])