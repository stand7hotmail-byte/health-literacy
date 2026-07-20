"""HTML builder module."""

from templates import HTML_TEMPLATE, CSS_TEMPLATE, JS_TEMPLATE
from config import CAT_MAP
from datetime import datetime


def build_article_html(column_data: dict, paper, slug: str, affiliate_html: str) -> str:
    """記事詳細ページ生成"""
    
    cat = CAT_MAP.get(paper.category, {"name": "健康", "icon": "📝"})
    cat_name = cat["name"]
    
    read_time = f"{max(1, len(column_data['body_html']) // 500)}分"
    
    html = HTML_TEMPLATE.format(
        column_title=column_data["title"],
        column_lead=column_data["lead"],
        column_body_html=column_data["body_html"],
        slug=slug,
        date=paper.pub_date,
        episode=datetime.now().isocalendar()[1],
        category_name=cat["name"],
        cat_name=cat["name"],
        read_time=read_time,
        source_url=paper.url,
        affiliate_html=affiliate_html,
        css=CSS_TEMPLATE,
        js=JS_TEMPLATE
    )
    
    return html