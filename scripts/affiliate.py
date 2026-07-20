"""Affiliate HTML generator module."""

from typing import List
from config import AFFILIATE_PRODUCTS


def generate_affiliate_html(keywords: List[str]) -> str:
    """キーワードに基づくアフィリエイトHTML生成"""
    html_parts = []
    used = set()
    
    for kw in keywords:
        kw_lower = kw.lower()
        for key, products in AFFILIATE_PRODUCTS.items():
            if key in kw_lower and key not in used:
                for prod in products[:1]:
                    html_parts.append(f'''
        <div class="aff-box" style="margin-top:16px;padding:16px;display:flex;gap:12px;align-items:flex-start;border:1px solid var(--border);border-radius:var(--radius);background:var(--paper);">
          <span style="font-size:1.5rem;flex-shrink:0;">🛒</span>
          <div style="flex:1;">
            <div style="font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">おすすめ商品</div>
            <div style="font-weight:600;margin-bottom:8px;"><a href="{prod['url']}?tag={prod['tag']}" target="_blank" rel="nofollow" style="color:var(--ink);text-decoration:none;">{prod['name']}</a></div>
            <a href="{prod['url']}?tag={prod['tag']}" target="_blank" rel="nofollow" style="display:inline-block;padding:8px 16px;background:var(--primary);color:#fff;border-radius:var(--radius);font-size:.8rem;font-weight:600;text-decoration:none;">Amazonで見る →</a>
          </div>
        </div>
        <p style="font-size:.7rem;color:var(--muted);margin-top:8px;">※ アフィリエイトリンクを含みます</p>
        ''')
                    used.add(key)
                    break
    
    return "\n".join(html_parts)