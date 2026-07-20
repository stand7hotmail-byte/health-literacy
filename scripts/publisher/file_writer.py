"""File writer module."""

import os
import re
from typing import Dict
from models import Paper


def save_article(article_dir: str, slug: str, html: str) -> str:
    """記事HTMLを保存"""
    os.makedirs(article_dir, exist_ok=True)
    filepath = os.path.join(article_dir, slug, "index.html")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filepath


def update_index_html(index_path: str, new_article: dict, base_dir: str) -> None:
    """index.html に新しい記事カードを追加"""
    # この関数は将来実装
    pass


def update_search_index(search_index_path: str, article: dict, slug: str) -> None:
    """search-index.json を更新"""
    # この関数は将来実装
    pass