#!/usr/bin/env python3
"""
Weekly Health Column Generator - メインエントリーポイント
使用: OpenRouter無料モデル (google/gemma-4-26b-a4b-it:free 等)
"""

import os
import sys
import re

# パス追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import BASE_DIR, CAT_MAP, TAG_TO_CAT, AFFILIATE_PRODUCTS
from scripts.fetcher.pubmed import fetch_pubmed_papers
from scripts.fetcher.scorer import filter_papers as score_and_filter
from scripts.generator.llm import generate_column
from scripts.publisher.article import (
    save_article, update_search_index, generate_affiliate_html, 
    determine_category, build_article_page_direct
)


def determine_category_from_paper(paper) -> str:
    """論文タグからカテゴリ決定"""
    for tag in paper.tags:
        tag_lower = tag.lower()
        for key, cat in TAG_TO_CAT.items():
            if key in tag_lower:
                return cat
    return "health"


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
    from scripts.fetcher.scorer import filter_papers
    candidates = score_and_filter(papers, top_n=3)
    
    for i, p in enumerate(candidates):
        print(f"  #{i+1} (Score: {p.score:.1f}) {p.title[:60]}...")
    
    if not candidates:
        print("❌ 適切な論文が見つかりませんでした")
        return
    
    # トップ1本でコラム生成
    best_paper = candidates[0]
    print(f"\n✍️ コラム生成中: {best_paper.title[:60]}...")
    
    try:
        column_data = generate_column(best_paper)
        print("✅ コラム生成完了")
    except Exception as e:
        print(f"❌ コラム生成失敗: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 保存
    slug = re.sub(r'[^a-z0-9-]+', '-', best_paper.title.lower())[:60].strip('-')
    article_dir = os.path.join(BASE_DIR, "article", slug)
    os.makedirs(article_dir, exist_ok=True)
    
    # アフィリエイトHTML生成
    from scripts.publisher.article import generate_affiliate_html, determine_category, build_article_page_direct
    
    affiliate_keywords = column_data.get("affiliate_keywords", [])
    affiliate_html = generate_affiliate_html(affiliate_keywords)
    
    # カテゴリ決定
    cat = determine_category(best_paper)
    cat_name = CAT_MAP.get(cat, "健康")
    
    # 記事ページ生成
    read_time = f"{max(1, len(column_data['body_html']) // 500)}分"
    
    # 関連記事（固定3件）
    related_articles = [
        {"slug": "dual-task-cognitive-improvement", "cat": "brain", "title": "週3回の「ながら運動」で認知機能が改善", "cat_name": "脳・認知"},
        {"slug": "postprandial-walking-glucose-control", "cat": "sugar", "title": "食後15分のウォーキングが糖を変える", "cat_name": "血糖・脂質"},
        {"slug": "protein-timing-muscle-maintenance", "cat": "muscle", "title": "「たんぱく質は朝と夜に分ける」が新しい常識", "cat_name": "筋肉・骨"},
    ]
    
    # 関連記事用のカテゴリ名追加
    for r in related_articles:
        r["cat_name"] = CAT_MAP.get(r["cat"], "健康")
    
    # アフィリエイトHTML
    affiliate_html = generate_affiliate_html(column_data.get("affiliate_keywords", []))
    
    # HTMLテンプレートを直接構築
    html = build_article_page_direct(
        column_data=column_data,
        slug=slug,
        date=best_paper.pub_date,
        cat_name=CAT_MAP.get(determine_category(best_paper), "健康"),
        read_time=f"{max(1, len(column_data['body_html']) // 500)}分",
        source_url=best_paper.url,
        affiliate_html=generate_affiliate_html(column_data.get("affiliate_keywords", [])),
        related_articles=related_articles
    )
    
    # 保存
    article_dir = os.path.join(BASE_DIR, "article", slug)
    os.makedirs(article_dir, exist_ok=True)
    
    filepath = os.path.join(article_dir, "index.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ 完了！")
    print(f"📝 記事: https://health-literacy.vercel.app/article/{slug}/")
    
    # 検索インデックス更新
    update_search_index(column_data, slug, best_paper)
    print(f"🔍 検索インデックス更新済み")


if __name__ == "__main__":
    main()