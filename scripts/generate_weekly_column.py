#!/usr/bin/env python3
"""
Weekly Health Column Generator - Main Entry Point
使用: OpenRouter無料モデル (google/gemma-4-26b-a4b-it:free 等)
"""

import os
import sys
import re

# Add scripts directory to Python path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

# Import modules - using direct module imports (not from scripts.*)
from fetcher import fetch_pubmed_papers
from scoring import filter_papers
from generator import generate_column
from templates import HTML_TEMPLATE, CSS_TEMPLATE, JS_TEMPLATE
from config import CAT_MAP
from publisher import save_article
from affiliate import generate_affiliate_html


def main():
    print("🚀 Weekly Health Column Generator 起動")
    
    # 1. 論文収集
    print("📚 論文収集中...")
    papers = fetch_pubmed_papers(days_back=7, max_results=50)
    print(f"  取得: {len(papers)} 件")
    
    if not papers:
        print("❌ 論文が取得できませんでした")
        return
    
    # 2. スコアリング・フィルタリング
    print("🔍 スコアリング・フィルタリング...")
    candidates = filter_papers(papers, top_n=3)
    
    for i, p in enumerate(candidates):
        print(f"  #{i+1} (Score: {p.score:.1f}) {p.title[:60]}...")
    
    if not candidates:
        print("❌ 適切な論文が見つかりませんでした")
        return
    
    # トップ1本でコラム生成
    best_paper = candidates[0]
    print(f"\n✍️ コラム生成中: {best_paper.title[:60]}...")
    
    try:
        from generator import generate_column
        column_data = generate_column(best_paper)
        print("✅ コラム生成完了")
    except Exception as e:
        print(f"❌ コラム生成失敗: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 保存
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    slug = re.sub(r'[^a-z0-9-]+', '-', best_paper.title.lower())[:60].strip('-')
    article_dir = os.path.join(base_dir, "article", slug)
    os.makedirs(article_dir, exist_ok=True)
    
    # アフィリエイトHTML生成
    from affiliate import generate_affiliate_html
    affiliate_keywords = column_data.get("affiliate_keywords", [])
    affiliate_html = generate_affiliate_html(affiliate_keywords)
    column_data["affiliate_html"] = affiliate_html
    
    # HTML生成
    from publisher.html_builder import build_article_html
    html = build_article_html(column_data, best_paper, slug, affiliate_html)
    
    # 保存
    article_dir = os.path.join(base_dir, "article", slug)
    os.makedirs(article_dir, exist_ok=True)
    
    with open(os.path.join(article_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ 完了！")
    print(f"📝 記事: https://health-literacy.vercel.app/article/{slug}/")


if __name__ == "__main__":
    main()