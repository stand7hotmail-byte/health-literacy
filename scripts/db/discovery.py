"""Discovery module for finding relationships between papers."""

import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import logging

from .models import Paper, PaperEmbedding, create_tables
from .ingest import PaperIngestor
from .embeddings import cosine_similarity, search_similar_papers

logger = logging.getLogger(__name__)


class PaperClusterer:
    """Cluster papers using their embeddings."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def cluster_papers(self, n_clusters: int = 5, min_cluster_size: int = 2) -> List[List[str]]:
        """Cluster papers using K-means on embeddings.
        
        Returns list of clusters, each containing PMIDs.
        """
        from sklearn.cluster import KMeans
        
        # Get all embeddings
        rows = self.conn.execute("""
            SELECT pmid, embedding FROM paper_embeddings
        """).fetchall()
        
        if not rows:
            return []
        
        pmids = [r[0] for r in rows]
        embeddings = np.array([np.array(r[1], dtype=np.float32) for r in rows])
        
        # Run K-means
        n_clusters = min(n_clusters, len(pmids))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # Group by cluster
        clusters = defaultdict(list)
        for pmid, label in zip(pmids, labels):
            clusters[label].append(pmid)
        
        # Filter by min size
        result = [cluster for cluster in clusters.values() if len(cluster) >= min_cluster_size]
        
        return result
    
    def get_cluster_summary(self, clusters: List[List[str]]) -> List[Dict]:
        """Get summary info for each cluster."""
        summaries = []
        
        for i, cluster in enumerate(clusters):
            if not cluster:
                continue
            
            # Get categories for papers in cluster
            placeholders = ','.join(['?'] * len(cluster))
            rows = self.conn.execute(f"""
                SELECT pmid, category, title FROM papers WHERE pmid IN ({placeholders})
            """, cluster).fetchall()
            
            categories = [r[1] for r in rows if r[1]]
            cat_counts = defaultdict(int)
            for c in categories:
                cat_counts[c] += 1
            
            top_categories = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            summaries.append({
                "cluster_id": i,
                "size": len(cluster),
                "top_categories": top_categories,
                "representative_pmids": cluster[:3],
                "titles": [r[2] for r in rows[:3]]
            })
        
        return summaries


class TrendAnalyzer:
    """Analyze trends in paper publications over time."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def get_keyword_trends(self, keyword: str, months: int = 12) -> Dict:
        """Get monthly publication counts for a keyword."""
        cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
        
        rows = self.conn.execute("""
            SELECT 
                strftime('%Y-%m', pub_date) as month,
                COUNT(*) as count
            FROM papers
            WHERE pub_date >= ? 
            AND (LOWER(title) LIKE ? OR LOWER(abstract) LIKE ? OR LOWER(mesh_terms) LIKE ?)
            GROUP BY month
            ORDER BY month
        """, [cutoff, f'%{keyword.lower()}%', f'%{keyword.lower()}%', f'%{keyword.lower()}%']).fetchall()
        
        monthly_counts = [{"month": r[0], "count": r[1]} for r in rows]
        
        return {
            "keyword": keyword,
            "months_analyzed": months,
            "monthly_counts": monthly_counts,
            "total": sum(r[1] for r in rows)
        }
    
    def detect_trending_topics(self, months: int = 6, min_papers: int = 2) -> List[Dict]:
        """Detect keywords with increasing publication rate."""
        cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
        
        # Get all mesh terms with monthly counts
        rows = self.conn.execute("""
            SELECT mesh_terms, pub_date
            FROM papers
            WHERE pub_date >= ? AND mesh_terms IS NOT NULL
        """, [cutoff]).fetchall()
        
        # Parse and count by month
        keyword_monthly = defaultdict(lambda: defaultdict(int))
        for mesh_json, pub_date in rows:
            try:
                terms = json.loads(mesh_json)
                month = pub_date[:7]  # YYYY-MM
                for term in terms:
                    keyword_monthly[term.lower()][month] += 1
            except:
                continue
        
        # Calculate growth rate
        trending = []
        for keyword, months_data in keyword_monthly.items():
            total = sum(months_data.values())
            if total < min_papers:
                continue
            
            sorted_months = sorted(months_data.keys())
            if len(sorted_months) < 2:
                continue
            
            first_month_count = months_data[sorted_months[0]]
            last_month_count = months_data[sorted_months[-1]]
            
            if first_month_count > 0:
                growth = (last_month_count - first_month_count) / first_month_count
            else:
                growth = float('inf') if last_month_count > 0 else 0
            
            trending.append({
                "keyword": keyword,
                "total_papers": total,
                "growth_rate": growth,
                "monthly_counts": dict(months_data)
            })
        
        trending.sort(key=lambda x: x["growth_rate"], reverse=True)
        return trending[:20]
    
    def get_category_trends(self, months: int = 6) -> Dict[str, List[Dict]]:
        """Get publication trends by category."""
        cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
        
        rows = self.conn.execute("""
            SELECT category, strftime('%Y-%m', pub_date) as month, COUNT(*) as count
            FROM papers
            WHERE pub_date >= ? AND category IS NOT NULL
            GROUP BY category, month
            ORDER BY category, month
        """, [cutoff]).fetchall()
        
        trends = defaultdict(list)
        for cat, month, count in rows:
            trends[cat].append({"month": month, "count": count})
        
        return dict(trends)


class ContradictionDetector:
    """Detect potentially contradictory papers on the same topic."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def find_contradiction_pairs(self, min_similarity: float = 0.5) -> List[Dict]:
        """Find paper pairs on same topic with potentially contradictory conclusions."""
        
        # Get papers with embeddings, grouped by category
        rows = self.conn.execute("""
            SELECT p.pmid, p.title, p.abstract, p.category, p.mesh_terms, p.evidence_level, e.embedding
            FROM papers p
            JOIN paper_embeddings e ON p.pmid = e.pmid
            WHERE p.category IS NOT NULL
        """).fetchall()
        
        if len(rows) < 2:
            return []
        
        # Group by category
        by_category = defaultdict(list)
        for r in rows:
            by_category[r[3]].append({
                "pmid": r[0],
                "title": r[1],
                "abstract": r[2],
                "category": r[3],
                "mesh_terms": json.loads(r[4]) if r[4] else [],
                "evidence_level": r[5],
                "embedding": np.array(r[6], dtype=np.float32) if r[6] is not None else None
            })
        
        pairs = []
        
        for category, papers in by_category.items():
            if len(papers) < 2:
                continue
            
            # Compare all pairs within category
            for i in range(len(papers)):
                for j in range(i + 1, len(papers)):
                    p1, p2 = papers[i], papers[j]
                    
                    # Check if they share mesh terms (same topic)
                    terms1 = set(p1["mesh_terms"])
                    terms2 = set(p2["mesh_terms"])
                    shared = terms1 & terms2
                    
                    if not shared:
                        continue
                    
                    # Check embedding similarity
                    if p1["embedding"] is not None and p2["embedding"] is not None:
                        sim = cosine_similarity(p1["embedding"], p2["embedding"])
                        if sim < min_similarity:
                            continue
                    else:
                        continue
                    
                    # Check for contradictory language
                    contradiction_score = self._check_contradiction(p1, p2)
                    
                    if contradiction_score > 0.3:
                        pairs.append({
                            "pmid1": p1["pmid"],
                            "pmid2": p2["pmid"],
                            "title1": p1["title"][:80],
                            "title2": p2["title"][:80],
                            "category": category,
                            "shared_terms": list(shared),
                            "similarity": sim,
                            "contradiction_score": contradiction_score,
                            "evidence_levels": [p1["evidence_level"], p2["evidence_level"]]
                        })
        
        # Sort by contradiction score
        pairs.sort(key=lambda x: x["contradiction_score"], reverse=True)
        return pairs[:20]
    
    def _check_contradiction(self, p1: Dict, p2: Dict) -> float:
        """Simple heuristic for contradiction detection."""
        positive_keywords = {"benefit", "improve", "reduce", "prevent", "effective", "protect", "decrease", "lower", "positive", "reduces", "improves", "prevents"}
        negative_keywords = {"harm", "increase", "risk", "worsen", "ineffective", "no effect", "no benefit", "raise", "elevate", "negative", "increases", "worsens", "fails"}
        
        text1 = (p1["title"] + " " + (p1["abstract"] or "")).lower()
        text2 = (p2["title"] + " " + (p2["abstract"] or "")).lower()
        
        pos1 = sum(1 for k in positive_keywords if k in text1)
        neg1 = sum(1 for k in negative_keywords if k in text1)
        pos2 = sum(1 for k in positive_keywords if k in text2)
        neg2 = sum(1 for k in negative_keywords if k in text2)
        
        score = 0
        if pos1 > 0 and neg2 > 0:
            score += 0.5
        if neg1 > 0 and pos2 > 0:
            score += 0.5
        if pos1 > 0 and pos2 > 0 and neg1 == 0 and neg2 == 0:
            score -= 0.2
        
        return max(0, score)


class JapanFocusDetector:
    """Detect papers with Japanese population or Japanese origin."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def find_japan_papers(self, category: Optional[str] = None) -> List[Paper]:
        """Find papers related to Japan."""
        from .models import row_to_paper
        
        query = """
            SELECT * FROM papers 
            WHERE LOWER(title) LIKE '%japan%' 
               OR LOWER(abstract) LIKE '%japan%' 
               OR LOWER(mesh_terms) LIKE '%japan%'
               OR LOWER(mesh_terms) LIKE '%japanese%'
        """
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        rows = self.conn.execute(query, params).fetchall()
        return [row_to_paper(r) for r in rows]
    
    def get_japan_paper_ratio(self, category: Optional[str] = None) -> float:
        """Get ratio of Japan-related papers."""
        
        if category:
            total_query = "SELECT COUNT(*) FROM papers WHERE category = ?"
            japan_query = """
                SELECT COUNT(*) FROM papers
                WHERE category = ?
                AND (LOWER(title) LIKE '%japan%' 
                     OR LOWER(abstract) LIKE '%japan%' 
                     OR LOWER(mesh_terms) LIKE '%japan%'
                     OR LOWER(mesh_terms) LIKE '%japanese%')
            """
            total = self.conn.execute(total_query, [category]).fetchone()[0]
            japan = self.conn.execute(japan_query, [category]).fetchone()[0]
        else:
            total_query = "SELECT COUNT(*) FROM papers"
            japan_query = """
                SELECT COUNT(*) FROM papers
                WHERE LOWER(title) LIKE '%japan%' 
                   OR LOWER(abstract) LIKE '%japan%' 
                   OR LOWER(mesh_terms) LIKE '%japan%'
                   OR LOWER(mesh_terms) LIKE '%japanese%'
            """
            total = self.conn.execute(total_query).fetchone()[0]
            japan = self.conn.execute(japan_query).fetchone()[0]
        
        return japan / total if total > 0 else 0.0


class ThemePicker:
    """Pick weekly column theme from recent high-quality papers."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def pick_theme(self, exclude_recent_weeks: int = 4) -> Optional[Dict]:
        """Pick a theme with source papers, excluding recently used ones."""
        
        # Get recently used PMIDs from generation_log (by date, not week string)
        recent_cutoff = datetime.now() - timedelta(weeks=exclude_recent_weeks)
        cutoff_str = recent_cutoff.strftime("%Y-%m-%d")
        
        recent_rows = self.conn.execute("""
            SELECT source_pmids FROM generation_log 
            WHERE created_at >= ?
        """, [cutoff_str]).fetchall()
        
        used_pmids = set()
        for row in recent_rows:
            try:
                used_pmids.update(json.loads(row[0]))
            except:
                pass
        
        # Find candidate papers: recent, high evidence level, not used
        if used_pmids:
            placeholders = ','.join(['?'] * len(used_pmids))
            candidates = self.conn.execute(f"""
                SELECT p.pmid, p.title, p.abstract, p.category, p.mesh_terms, p.evidence_level, 
                       p.pub_date, e.embedding
                FROM papers p
                JOIN paper_embeddings e ON p.pmid = e.pmid
                WHERE p.pub_date >= ?
                AND p.evidence_level IN ('RCT', 'meta-analysis', 'guideline')
                AND p.pmid NOT IN ({placeholders})
                ORDER BY 
                    CASE p.evidence_level 
                        WHEN 'meta-analysis' THEN 3
                        WHEN 'guideline' THEN 2
                        WHEN 'RCT' THEN 1
                        ELSE 0
                    END DESC,
                    p.pub_date DESC
                LIMIT 20
            """, [(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")] + list(used_pmids)).fetchall()
        else:
            candidates = self.conn.execute("""
                SELECT p.pmid, p.title, p.abstract, p.category, p.mesh_terms, p.evidence_level, 
                       p.pub_date, e.embedding
                FROM papers p
                JOIN paper_embeddings e ON p.pmid = e.pmid
                WHERE p.pub_date >= ?
                AND p.evidence_level IN ('RCT', 'meta-analysis', 'guideline')
                ORDER BY 
                    CASE p.evidence_level 
                        WHEN 'meta-analysis' THEN 3
                        WHEN 'guideline' THEN 2
                        WHEN 'RCT' THEN 1
                        ELSE 0
                    END DESC,
                    p.pub_date DESC
                LIMIT 20
            """, [(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")]).fetchall()
        
        if not candidates:
            # Fallback: any recent papers
            if used_pmids:
                placeholders = ','.join(['?'] * len(used_pmids))
                candidates = self.conn.execute(f"""
                    SELECT p.pmid, p.title, p.abstract, p.category, p.mesh_terms, p.evidence_level, 
                           p.pub_date, e.embedding
                    FROM papers p
                    JOIN paper_embeddings e ON p.pmid = e.pmid
                    WHERE p.pub_date >= ?
                    AND p.pmid NOT IN ({placeholders})
                    ORDER BY p.pub_date DESC
                    LIMIT 10
                """, [(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")] + list(used_pmids)).fetchall()
            else:
                candidates = self.conn.execute("""
                    SELECT p.pmid, p.title, p.abstract, p.category, p.mesh_terms, p.evidence_level, 
                           p.pub_date, e.embedding
                    FROM papers p
                    JOIN paper_embeddings e ON p.pmid = e.pmid
                    WHERE p.pub_date >= ?
                    ORDER BY p.pub_date DESC
                    LIMIT 10
                """, [(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")]).fetchall()
        
        if not candidates:
            return None
        
        # Pick best candidate (first one not in used_pmids)
        best = None
        for c in candidates:
            if c[0] not in used_pmids:
                best = c
                break
        
        if best is None:
            # All candidates were used, pick first anyway
            best = candidates[0]
        
        # Find related papers (same category, similar embedding)
        source_pmids = [best[0]]
        best_emb = np.array(best[7], dtype=np.float32) if best[7] else None
        
        if best_emb is not None:
            for c in candidates[1:6]:
                c_emb = np.array(c[7], dtype=np.float32) if c[7] else None
                if c_emb is not None:
                    sim = cosine_similarity(best_emb, c_emb)
                    if sim > 0.6:
                        source_pmids.append(c[0])
        
        # Generate theme reasoning
        mesh_terms = json.loads(best[4]) if best[4] else []
        theme_topic = f"{best[3] or '健康'}: {mesh_terms[0] if mesh_terms else best[1][:30]}"
        
        return {
            "topic": theme_topic,
            "source_pmids": source_pmids,
            "primary_pmid": best[0],
            "reasoning": f"最新の{best[5] or 'RCT'}研究「{best[1][:50]}...」に基づき、{best[3] or '関連分野'}のエビデンスを解説",
            "category": best[3],
            "evidence_level": best[5]
        }


# Convenience functions
def find_related_papers(conn, pmid: str, top_k: int = 5) -> List[Tuple[str, float]]:
    """Find papers similar to given PMID."""
    # Get query embedding
    row = conn.execute("SELECT embedding FROM paper_embeddings WHERE pmid = ?", [pmid]).fetchone()
    if not row or row[0] is None:
        return []
    
    query_emb = np.array(row[0], dtype=np.float32)
    
    # Search all embeddings
    rows = conn.execute("SELECT pmid, embedding FROM paper_embeddings WHERE pmid != ?", [pmid]).fetchall()
    
    embeddings = [(r[0], np.array(r[1], dtype=np.float32)) for r in rows if r[1] is not None]
    results = search_similar_papers(query_emb, [e for _, e in embeddings], top_k=top_k)
    
    return [(embeddings[i][0], score) for i, score in results]


def get_paper_recommendations(conn, pmid: str, top_k: int = 5) -> List[Dict]:
    """Get formatted paper recommendations."""
    related = find_related_papers(conn, pmid, top_k)
    
    if not related:
        return []
    
    pmids = [r[0] for r in related]
    placeholders = ','.join(['?'] * len(pmids))
    
    rows = conn.execute(f"""
        SELECT pmid, title, category, pub_date FROM papers WHERE pmid IN ({placeholders})
    """, pmids).fetchall()
    
    paper_info = {r[0]: {"title": r[1], "category": r[2], "pub_date": r[3]} for r in rows}
    
    recommendations = []
    for r_pmid, similarity in related:
        info = paper_info.get(r_pmid, {})
        recommendations.append({
            "pmid": r_pmid,
            "title": info.get("title", ""),
            "category": info.get("category", ""),
            "pub_date": info.get("pub_date", ""),
            "similarity": similarity
        })
    
    return recommendations