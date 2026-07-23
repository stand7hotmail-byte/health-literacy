#!/usr/bin/env python3
"""
Migrate existing articles and health_sources.json to DuckDB database.
"""

import os
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

import duckdb
import sys

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, scripts_dir)

from db.models import create_tables, Paper, PaperEmbedding
from db.ingest import PaperIngestor
from db.embeddings import EmbeddingManager


def extract_article_metadata(html_path: str) -> dict:
    """Extract metadata from article HTML."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract title
    title_elem = soup.find("h1")
    title = title_elem.get_text(strip=True) if title_elem else ""
    
    # Extract category from cat-badge
    cat_elem = soup.find("span", class_="cat-badge")
    category = cat_elem.get_text(strip=True) if cat_elem else "健康"
    
    # Map Japanese category to English
    cat_map = {
        "心臓・血管": "heart",
        "脳・認知": "brain",
        "筋肉・骨": "muscle",
        "血糖・脂質": "sugar",
        "検診・予防": "check",
        "睡眠": "sleep",
        "腸内フローラ": "gut",
        "目の健康": "eyes",
    }
    category_en = cat_map.get(category, "health")
    
    # Extract date from masthead-date or article-meta
    date = None
    date_elem = soup.find("p", class_="masthead-date")
    if not date_elem:
        date_elem = soup.find("div", class_="article-meta")
    if date_elem:
        date_text = date_elem.get_text(strip=True)
        # Try to parse date
        for fmt in ["%Y-%m-%d", "%Y年%m月%d日", "%Y/%m/%d"]:
            try:
                date = datetime.strptime(date_text[:10], fmt).strftime("%Y-%m-%d")
                break
            except:
                pass
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract lead
    lead_elem = soup.find("p", class_="article-lead")
    lead = lead_elem.get_text(strip=True) if lead_elem else ""
    
    # Extract body content
    body_elem = soup.find("div", class_="article-content")
    body_html = str(body_elem) if body_elem else ""
    
    # Extract source URL
    source_link = soup.find("a", class_="source-link")
    source_url = source_link.get("href") if source_link else ""
    
    # Extract DOI from source URL if possible
    doi = ""
    if "doi.org" in source_url:
        doi = source_url.split("doi.org/")[-1]
    elif "pubmed.ncbi.nlm.nih.gov" in source_url:
        pmid = source_url.rstrip("/").split("/")[-1]
        doi = f"PMID:{pmid}"
    
    # Generate slug from filename or title
    slug = os.path.basename(os.path.dirname(html_path))
    
    # Extract MeSH terms from tags
    tags = []
    tag_elements = soup.find_all("a", class_="tag")
    for t in tag_elements:
        tags.append(t.get_text(strip=True))
    
    return {
        "pmid": slug,  # Use slug as PMID substitute
        "title": title,
        "abstract": lead,
        "authors": ["健康リテラシー編集部"],
        "journal": "健康リテラシー",
        "pub_date": date,
        "doi": doi,
        "url": f"https://health-literacy.vercel.app/article/{slug}/",
        "mesh_terms": tags,
        "category": category_en,
        "evidence_level": "article",
        "body_html": body_html,
        "source_url": source_url,
    }


def extract_all_articles(base_dir: str) -> list:
    """Extract metadata from all article HTML files."""
    article_dir = os.path.join(base_dir, "article")
    articles = []
    
    for dirname in sorted(os.listdir(article_dir)):
        path = os.path.join(article_dir, dirname)
        if not os.path.isdir(path) or dirname == "category" or dirname.startswith("-"):
            continue
        
        idx_path = os.path.join(path, "index.html")
        if not os.path.exists(idx_path):
            continue
        
        try:
            metadata = extract_article_metadata(idx_path)
            metadata["slug"] = dirname
            articles.append(metadata)
            print(f"Extracted: {dirname} - {metadata['title'][:50]}...")
        except Exception as e:
            print(f"Error extracting {dirname}: {e}")
    
    return articles


def migrate_health_sources(conn, base_dir: str):
    """Migrate health_sources.json to database."""
    sources_path = os.path.join(base_dir, "health_sources.json")
    
    if not os.path.exists(sources_path):
        print("health_sources.json not found")
        return
    
    with open(sources_path, "r", encoding="utf-8") as f:
        sources = json.load(f)
    
    # Create sources table with auto-increment
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_sources (
            id INTEGER PRIMARY KEY,
            category VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            url VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    
    # Create sequence for auto-increment
    conn.execute("CREATE SEQUENCE IF NOT EXISTS health_sources_seq")
    
    # Clear existing
    conn.execute("DELETE FROM health_sources")
    
    # Insert
    for category, items in sources.items():
        if isinstance(items, dict):
            for name, url in items.items():
                conn.execute(
                    "INSERT INTO health_sources (id, category, name, url) VALUES (nextval('health_sources_seq'), ?, ?, ?)",
                    [category, name, url]
                )
        elif isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    conn.execute(
                        "INSERT INTO health_sources (id, category, name, url) VALUES (nextval('health_sources_seq'), ?, ?, ?)",
                        [category, item.get("name", ""), item.get("url", "")]
                    )
                else:
                    conn.execute(
                        "INSERT INTO health_sources (id, category, name, url) VALUES (nextval('health_sources_seq'), ?, ?, ?)",
                        [category, str(item), ""]
                    )
    
    count = conn.execute("SELECT COUNT(*) FROM health_sources").fetchone()[0]
    print(f"Migrated {count} health sources")


def create_search_index(conn):
    """Create search index table for article search."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_index (
            slug VARCHAR PRIMARY KEY,
            title VARCHAR NOT NULL,
            description VARCHAR,
            category VARCHAR,
            tags VARCHAR,  -- JSON array
            pub_date DATE,
            url VARCHAR
        )
    """
    )
    conn.execute("DELETE FROM search_index")


def main():
    base_dir = r"C:\Users\stand\Documents\hermes_project\test01"
    db_path = os.path.join(base_dir, "health_literacy.db")
    
    print(f"Connecting to database: {db_path}")
    conn = duckdb.connect(db_path)
    conn.execute("INSTALL vss; LOAD vss;")
    
    # Create tables
    create_tables(conn)
    
    # Create search index
    create_search_index(conn)
    
    # Migrate health sources
    print("\n=== Migrating health sources ===")
    migrate_health_sources(conn, base_dir)
    
    # Extract and migrate articles
    print("\n=== Extracting existing articles ===")
    articles = extract_all_articles(base_dir)
    print(f"Found {len(articles)} articles")
    
    # Initialize ingestor and embedding manager
    ingestor = PaperIngestor(conn)
    embedding_manager = EmbeddingManager()
    
    # Migrate articles
    print("\n=== Migrating articles to database ===")
    for article in articles:
        try:
            paper = Paper(
                pmid=article["pmid"],
                title=article["title"],
                abstract=article["abstract"],
                authors=article["authors"],
                journal=article["journal"],
                pub_date=article["pub_date"],
                doi=article["doi"],
                url=article["url"],
                mesh_terms=article["mesh_terms"],
                category=article["category"],
                evidence_level=article["evidence_level"],
            )
            
            # Insert/update paper
            ingestor.insert_paper(paper)
            
            # Generate and store embedding
            embedding = embedding_manager.embed_paper(paper)
            ingestor.insert_embedding(PaperEmbedding(
                pmid=paper.pmid,
                embedding=embedding,
                model="all-MiniLM-L6-v2"
            ))
            
            # Add to search index
            conn.execute("""
                INSERT OR REPLACE INTO search_index 
                (slug, title, description, category, tags, pub_date, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                article["slug"],
                article["title"],
                article["abstract"][:200],
                article["category"],
                json.dumps(article["mesh_terms"], ensure_ascii=False),
                article["pub_date"],
                article["url"]
            ])
            
            print(f"  ✓ {article['title'][:50]}...")
            
        except Exception as e:
            print(f"  ✗ Error migrating {article.get('title', 'unknown')}: {e}")
    
    # Verify
    paper_count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    emb_count = conn.execute("SELECT COUNT(*) FROM paper_embeddings").fetchone()[0]
    search_count = conn.execute("SELECT COUNT(*) FROM search_index").fetchone()[0]
    source_count = conn.execute("SELECT COUNT(*) FROM health_sources").fetchone()[0]
    
    print(f"\n=== Migration Complete ===")
    print(f"Papers: {paper_count}")
    print(f"Embeddings: {emb_count}")
    print(f"Search index entries: {search_count}")
    print(f"Health sources: {source_count}")
    
    conn.close()
    print(f"\nDatabase saved to: {db_path}")


if __name__ == "__main__":
    main()