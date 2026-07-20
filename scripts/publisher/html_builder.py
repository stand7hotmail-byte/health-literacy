"""HTML template generation module."""

from datetime import datetime

HTML_TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{column_title} — 健康リテラシー</title>
<meta name="description" content="{column_lead}">
<link rel="canonical" href="https://health-literacy.vercel.app/article/{slug}/">
<meta property="og:title" content="{column_title} — 健康リテラシー">
<meta property="og:description" content="{column_lead}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://health-literacy.vercel.app/article/{slug}/">
<meta property="article:published_time" content="{date}T00:00:00+09:00">
<meta property="article:section" content="{category_name}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{column_title}",
  "description": "{column_lead}",
  "datePublished": "{date}T00:00:00+09:00",
  "dateModified": "{date}T00:00:00+09:00",
  "author": {{"@type": "Organization", "name": "健康リテラシー編集部"}},
  "publisher": {{"@type": "Organization", "name": "健康リテラシー"}},
  "mainEntityOfPage": {{"@type": "WebPage", "@id": "https://health-literacy.vercel.app/article/{slug}/"}}
}}
</script>
{{ css }}
</head>
<body>
<a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>

<header class="masthead" role="banner">
  <div class="container">
    <p class="masthead-date">{date} 📝 健康リテラシー・コラム 第{episode}回</p>
    <h1 class="masthead-title">健康リテラシー</h1>
    <p class="masthead-subtitle">50歳すぎたらここを見る</p>
    <div class="masthead-rule" aria-hidden="true"></div>
  </div>
</header>

<div class="daily-corner">
  <div class="container">
    <div class="daily-corner-inner">
      <span class="dc-label">今日のひとこと</span>
      <p class="dc-text">今日は <strong>夕食前に血圧を測ってメモする</strong> からはじめてみましょう。1日2回の記録が、大きな病気を防ぐ最初の一歩です。</p>
    </div>
  </div>
</div>

<nav class="tab-nav" aria-label="カテゴリで絞り込み">
  <div class="tab-nav-inner">
    <a href="/" class="active">すべて</a>
    <a href="/article/category/heart/">❤️ 心臓・血管</a>
    <a href="/article/category/brain/">🧠 脳・認知</a>
    <a href="/article/category/muscle/">💪 筋肉・骨</a>
    <a href="/article/category/sugar/">🍚 血糖・脂質</a>
    <a href="/article/category/check/">🔍 検診・予防</a>
    <a href="/article/category/sleep/">😴 睡眠</a>
    <a href="/article/category/gut/">🦠 腸内フローラ</a>
    <a href="/article/category/eyes/">👁️ 目の健康</a>
    <a href="/search/" style="background:var(--accent);color:#fff;border-radius:var(--radius);padding:0 16px;font-weight:600;">🔍 検索</a>
  </div>
</nav>

<main id="main-content" class="article-page">
  <div class="container">
    <article>
      <header class="article-header">
        <div class="article-meta">
          <span class="cat-badge">{cat_name}</span>
          <span>・{date}</span>
          <span>・読了{read_time}</span>
        </div>
        <h1>{column_title}</h1>
        <p class="article-lead">{column_lead}</p>
      </header>
      
      <div class="article-content" itemprop="articleBody">
{column_body_html}
      </div>
      
      <footer class="article-footer">
        <div class="source-link-wrap">
          <a href="{source_url}" class="source-link" target="_blank" rel="noopener noreferrer">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            原文を読む
          </a>
        </div>
        
        {affiliate_html}
        
        <p style="font-size:.7rem;color:var(--muted);margin-top:8px;">※ アフィリエイトリンクを含みます</p>
      </footer>
      
      <nav class="related-articles" style="margin-top:32px;padding-top:24px;border-top:1px solid var(--border);" aria-labelledby="related-heading">
        <h3 id="related-heading" style="font-size:.9rem;font-weight:700;margin:0 0 16px;color:var(--ink);">この記事を読んだ人はこちらも</h3>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a href="/article/dual-task-cognitive-improvement/" class="related-card" style="flex:1;min-width:140px;background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:12px;text-decoration:none;color:inherit;transition:all .2s;" onmouseover="this.style.borderColor='var(--primary)';this.style.boxShadow='var(--shadow-md)'" onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow='none'">
            <span style="display:inline-block;font-size:.65rem;font-weight:700;color:var(--primary);background:var(--primary-light);padding:2px 8px;border-radius:4px;margin-bottom:6px;">脳・認知</span>
            <span style="font-size:.8rem;font-weight:600;line-height:1.5;">週3回の「ながら運動」で認知機能が改善</span>
          </a>
          <a href="/article/postprandial-walking-glucose-control/" class="related-card" style="flex:1;min-width:140px;background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:12px;text-decoration:none;color:inherit;transition:all .2s;" onmouseover="this.style.borderColor='var(--primary)';this.style.boxShadow='var(--shadow-md)'" onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow='none'">
            <span style="display:inline-block;font-size:.65rem;font-weight:700;color:var(--primary);background:var(--primary-light);padding:2px 8px;border-radius:4px;margin-bottom:6px;">血糖・脂質</span>
            <span style="font-size:.8rem;font-weight:600;line-height:1.5;">食後15分のウォーキングが糖を変える</span>
          </a>
          <a href="/article/protein-timing-muscle-maintenance/" class="related-card" style="flex:1;min-width:140px;background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:12px;text-decoration:none;color:inherit;transition:all .2s;" onmouseover="this.style.borderColor='var(--primary)';this.style.boxShadow='var(--shadow-md)'" onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow='none'">
            <span style="display:inline-block;font-size:.65rem;font-weight:700;color:var(--primary);background:var(--primary-light);padding:2px 8px;border-radius:4px;margin-bottom:6px;">筋肉・骨</span>
            <span style="font-size:.8rem;font-weight:600;line-height:1.5;">「たんぱく質は朝と夜に分ける」が新しい常識</span>
          </a>
        </div>
      </nav>
    </article>
  </div>
</main>

<footer class="footer" role="contentinfo">
  <div class="footer-inner">
    <div class="footer-col">
      <h4>健康リテラシー</h4>
      <p>最新の学術論文を、わかりやすくお届けします。医療専門家向けではなく、50歳以上のあなたの「今日の行動」につなげる情報サイト。</p>
    </div>
    <div class="footer-col">
      <h4>カテゴリ</h4>
      <ul>
        <li><a href="/article/category/heart/">心臓・血管</a></li>
        <li><a href="/article/category/brain/">脳・認知</a></li>
        <li><a href="/article/category/muscle/">筋肉・骨</a></li>
        <li><a href="/article/category/sugar/">血糖・脂質</a></li>
        <li><a href="/article/category/check/">検診・予防</a></li>
        <li><a href="/article/category/sleep/">睡眠</a></li>
        <li><a href="/article/category/gut/">腸内フローラ</a></li>
        <li><a href="/article/category/eyes/">目の健康</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>このサイトについて</h4>
      <ul>
        <li><a href="/privacy.html#about">運営者情報</a></li>
        <li><a href="/privacy.html#privacy">プライバシー</a></li>
        <li><a href="/privacy.html#disclaimer">免責事項</a></li>
        <li><a href="/privacy.html#revision">改訂履歴</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <p>※ 本サイトの情報は医療行為の代わりになるものではありません。診断・治療については必ず医療専門家にご相談ください。</p>
    <p>&copy; 2026 健康リテラシー. All rights reserved.</p>
  </div>
</footer>

{{ js }}
</body>
</html>"""

# CSS and JS templates (using existing site's)
CSS_TEMPLATE = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{--ink:#1a1a1a;--muted:#6b6b6b;--paper:#ffffff;--border:#e0e0e0;--primary:#1e5f3a;--primary-light:#e8f4ef;--accent:#c9a96e;--accent-dark:#b8860b;--radius:8px;--shadow-sm:0 1px 3px rgba(0,0,0,.08);--shadow-md:0 4px 12px rgba(0,0,0,.1);--shadow-lg:0 8px 24px rgba(0,0,0,.12);--container:800px}
*{box-sizing:border-box}html{font-size:17px}body{font-family:'Noto Sans JP',sans-serif;color:var(--ink);background:var(--paper);line-height:1.8;margin:0}.skip-link{position:absolute;top:-100%;left:50%;transform:translateX(-50%);padding:12px 24px;background:var(--primary);color:#fff;border-radius:var(--radius);z-index:1000;text-decoration:none;font-weight:600}.skip-link:focus{top:10px}.container{max-width:var(--container);margin:0 auto;padding:0 20px}.masthead{background:linear-gradient(135deg,#0f1419 0%,#1a1f2a 100%);color:#fff;padding:32px 0;margin-bottom:24px}.masthead-date{font-size:.8rem;opacity:.7;margin:0 0 8px}.masthead-title{font-family:'Noto Serif JP',serif;font-size:2.5rem;font-weight:700;margin:0 0 4px}.masthead-subtitle{font-size:1rem;opacity:.8;margin:0}.masthead-rule{height:2px;background:linear-gradient(90deg,var(--primary),var(--accent));width:60px;margin-top:16px;border-radius:1px}.daily-corner{background:#f8faf8;border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:16px 0;margin-bottom:24px}.daily-corner-inner{display:flex;align-items:center;gap:12px}.dc-label{font-size:.7rem;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:.5em}.dc-text{margin:0;font-size:.9rem}.tab-nav{overflow-x:auto;white-space:nowrap;margin-bottom:24px;-webkit-overflow-scrolling:touch}.tab-nav-inner{display:flex;gap:8px}.tab-nav a{display:inline-block;padding:10px 16px;background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);font-size:.85rem;font-weight:600;color:var(--ink);text-decoration:none;transition:all .2s;white-space:nowrap}.tab-nav a:hover,.tab-nav a.active{background:var(--primary);color:#fff;border-color:var(--primary)}.article-page{margin-top:8px}.article-header{margin-bottom:24px}.article-meta{display:flex;gap:12px;font-size:.8rem;color:var(--muted);margin-bottom:12px}.cat-badge{display:inline-block;padding:2px 10px;background:var(--primary-light);color:var(--primary);border-radius:20px;font-size:.7rem;font-weight:700}.article-title{font-family:'Noto Serif JP',serif;font-size:1.8rem;font-weight:700;line-height:1.3;margin:0 0 16px}.article-lead{font-size:1.05rem;line-height:1.7;color:var(--muted);padding:16px;background:var(--primary-light);border-radius:var(--radius);border-left:4px solid var(--primary);margin:0}.article-content h2{font-family:'Noto Serif JP',serif;font-size:1.4rem;font-weight:700;margin:32px 0 16px;padding-bottom:8px;border-bottom:2px solid var(--primary)}.article-content h3{font-size:1.1rem;font-weight:600;margin:24px 0 12px;color:var(--ink)}.article-content p{margin:16px 0}.article-content ul{margin:16px 0;padding-left:24px}.article-content li{margin:8px 0}.article-content table{width:100%;border-collapse:collapse;margin:24px 0;font-size:.9rem}.article-content th,.article-content td{padding:12px;border:1px solid var(--border);text-align:left}.article-content th{background:var(--primary-light);font-weight:700;color:var(--primary)}.article-content tr:nth-child(even) td{background:#fafafa}.article-content strong{color:var(--ink)}.article-content mark{background:#fff9c4;padding:2px 4px;border-radius:3px}.article-content .aff-box{margin-top:16px;padding:16px;display:flex;gap:12px;align-items:flex-start;border:1px solid var(--border);border-radius:var(--radius);background:var(--paper)}.article-content .aff-box span:first-child{font-size:1.5rem;flex-shrink:0}.article-content .aff-box div{flex:1}.article-content .aff-box div:first-child{font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}.article-content .aff-box a{color:var(--ink);text-decoration:none;font-weight:600}.article-content .aff-box a[href*="amzn"]{display:inline-block;padding:8px 16px;background:var(--primary);color:#fff;border-radius:var(--radius);font-size:.8rem;font-weight:600;text-decoration:none;margin-top:8px}.article-footer{margin-top:32px;padding-top:24px;border-top:1px solid var(--border)}.source-link-wrap{margin-bottom:16px}.source-link{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);font-size:.9rem;font-weight:600;color:var(--ink);text-decoration:none;transition:all .2s}.source-link:hover{background:var(--primary);color:#fff;border-color:var(--primary)}.related-articles h3{font-size:.9rem;font-weight:700;margin:0 0 16px;color:var(--ink)}.related-card{flex:1;min-width:140px;background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:12px;text-decoration:none;color:inherit;transition:all .2s}.related-card:hover{border-color:var(--primary);box-shadow:var(--shadow-md)}.related-card span:first-child{display:inline-block;font-size:.65rem;font-weight:700;color:var(--primary);background:var(--primary-light);padding:2px 8px;border-radius:4px;margin-bottom:6px}.related-card span:last-child{font-size:.8rem;font-weight:600;line-height:1.5}.footer{background:#0f1419;color:#fff;padding:48px 0 24px;margin-top:48px}.footer-inner{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;max-width:var(--container);margin:0 auto;padding:0 20px}.footer-col h4{font-size:.9rem;font-weight:700;margin:0 0 16px;color:var(--accent)}.footer-col ul{list-style:none;padding:0;margin:0}.footer-col li{margin:8px 0}.footer-col a{color:#ccc;text-decoration:none;transition:color .2s}.footer-col a:hover{color:var(--accent)}.footer-bottom{border-top:1px solid #2a2f3a;margin-top:32px;padding-top:24px;text-align:center;font-size:.8rem;color:#888}@media(max-width:768px){.footer-inner{grid-template-columns:1fr}.masthead-title{font-size:2rem}.article-title{font-size:1.5rem}.tab-nav a{padding:8px 12px;font-size:.8rem}}
</style>"""

JS_TEMPLATE = """<script>
document.addEventListener('DOMContentLoaded',function(){const links=document.querySelectorAll('.tab-nav a');links.forEach(l=>{l.addEventListener('click',function(e){if(this.classList.contains('active'))return;links.forEach(x=>x.classList.remove('active'));this.classList.add('active');});});});
</script>"""


def build_article_html(column_data: dict, paper, slug: str, affiliate_html: str) -> str:
    """記事詳細ページ生成"""
    cat_map = {
        "heart": {"name": "心臓・血管", "icon": "❤️"},
        "brain": {"name": "脳・認知", "icon": "🧠"},
        "muscle": {"name": "筋肉・骨", "icon": "💪"},
        "sugar": {"name": "血糖・脂質", "icon": "🍚"},
        "check": {"name": "検診・予防", "icon": "🔍"},
        "sleep": {"name": "睡眠", "icon": "😴"},
        "gut": {"name": "腸内フローラ", "icon": "🦠"},
        "eyes": {"name": "目の健康", "icon": "👁️"},
    }
    
    # Determine category from paper tags
    tag_to_cat = {
        "hypertension": "heart", "blood pressure": "heart", "sarcopenia": "muscle",
        "muscle": "muscle", "protein": "muscle", "cognitive": "brain", "dementia": "brain",
        "alzheimer": "brain", "diabetes": "sugar", "glucose": "sugar", "insulin": "sugar",
        "osteoporosis": "muscle", "bone": "muscle", "fracture": "muscle", "sleep": "sleep",
        "insomnia": "sleep", "gut microbiome": "gut", "longevity": "gut", "aging": "gut",
        "eye": "eyes", "vision": "eyes"
    }
    category = "health"
    for tag in paper.tags:
        tag_lower = tag.lower()
        for key, cat in tag_to_cat.items():
            if key in tag_lower:
                category = cat
                break
        if category != "health":
            break
    
    cat = cat_map.get(category, {"name": "健康", "icon": "📝"})
    
    return HTML_TEMPLATE.format(
        column_title=column_data["title"],
        column_lead=column_data["lead"],
        column_body_html=column_data["body_html"],
        slug=slug,
        date=paper.pub_date,
        episode=datetime.now().isocalendar()[1],
        category_name=cat["name"],
        cat_name=cat["name"],
        read_time="5分",
        source_url=paper.url,
        affiliate_html=affiliate_html,
        css=CSS_TEMPLATE,
        js=JS_TEMPLATE
    )