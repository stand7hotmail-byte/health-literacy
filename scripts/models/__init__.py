"""データモデル定義"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Paper:
    """論文データ"""
    title: str
    abstract: str
    authors: List[str]
    journal: str
    pub_date: str
    doi: str
    url: str
    tags: List[str]
    score: float = 0.0


@dataclass
class ColumnData:
    """生成されたコラムデータ"""
    title: str
    lead: str
    body_html: str
    action_items: List[str]
    source_citation: str
    disclaimer: str
    affiliate_keywords: List[str]
    affiliate_html: str = ""
    
    # Metadata
    slug: str = ""
    pub_date: str = ""
    category: str = ""
    cat_name: str = ""
    read_time: str = ""
    source_url: str = ""


@dataclass
class Article:
    """記事ページデータ（パブリッシュ用）"""
    slug: str
    title: str
    lead: str
    body_html: str
    pub_date: str
    category: str
    cat_name: str
    read_time: str
    source_url: str
    affiliate_html: str
    related_articles: List[dict] = field(default_factory=list)
    json_ld: str = ""
    og_tags: dict = field(default_factory=dict)