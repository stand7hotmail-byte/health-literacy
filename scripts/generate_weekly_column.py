#!/usr/bin/env python3
"""
Weekly Health Column Generator
使用: OpenRouter無料モデル (google/gemma-4-26b-a4b-it:free 等)
"""

import os
import json
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from jinja2 import Template
import time

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==================== 設定 ====================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL")

# OpenRouter 無料モデル (優先順位順) - 2026/7 時点動作確認済み
FREE_MODELS = [
    "google/gemma-4-26b-a4b-it:free",         # Gemma 4 (高品質)
    "nvidia/nemotron-3-ultra-550b-a55b:free", # Nemotron 3 Ultra (高品質)
    "meta-llama/llama-3.3-70b-instruct:free", # Llama 3.3 70B (高品質)
    "nousresearch/hermes-3-llama-3.1-405b:free", # Hermes 3 405B (最高品質)
    "nvidia/nemotron-3-super-120b-a12b:free", # Nemotron 3 Super
    "qwen/qwen3-next-80b-a3b-instruct:free",  # Qwen3 Next
    "openai/gpt-oss-20b:free",                # GPT-OSS 20B
    "meta-llama/llama-3.2-3b-instruct:free",  # Llama 3.2 3B (軽量)
    "nvidia/nemotron-nano-9b-v2:free",        # Nemotron Nano
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free", # Dolphin
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# 50代以上向けキーワード（スコアリング用）
TARGET_KEYWORDS = {
    "high_priority": [
        "hypertension", "blood pressure", "sarcopenia", "muscle", "protein",
        "cognitive", "dementia", "alzheimer", "diabetes", "glucose", "insulin",
        "osteoporosis", "bone density", "fracture", "fall", "sleep", "insomnia",
        "gut microbiome", "longevity", "aging", "elderly", "older adults",
        "frailty", "polypharmacy", "deprescribing"
    ],
    "medium_priority": [
        "exercise", "physical activity", "nutrition", "diet", "supplement",
        "vitamin", "mineral", "omega-3", "coenzyme", "coq10",
        "blood pressure monitor", "wearable", "cgm", "continuous glucose"
    ]
}

# アフィリエイト商品マッピング（キーワード→商品）
AFFILIATE_PRODUCTS = {
    "blood pressure": [
        {"name": "Omron 上腕式血圧計 HCR-7106", "url": "https://amzn.to/3XyZ123", "tag": "healthlitera2-22"},
    ],
    "salt reduction": [
        {"name": "ヤマキ 減塩だしの素", "url": "https://amzn.to/4AbC789", "tag": "healthlitera2-22"},
    ],
    "potassium": [
        {"name": "ネイチャーメイド カリウム", "url": "https://amzn.to/5DeF012", "tag": "healthlitera2-22"},
    ],
    "smart watch": [
        {"name": "Xiaomi Smart Band 8", "url": "https://amzn.to/6GhI345", "tag": "healthlitera2-22"},
    ],
    "blood glucose": [
        {"name": "血糖値測定器セット", "url": "https://amzn.to/7JkL901", "tag": "healthlitera2-22"},
    ],
    "protein": [
        {"name": "COCOLAB HMB EX", "url": "https://amzn.to/8MnO234", "tag": "healthlitera2-22"},
    ],
}

# ==================== データクラス ====================

@dataclass
class Paper:
    title: str
    abstract: str
    authors: List[str]
    journal: str
    pub_date: str
    doi: str
    url: str
    tags: List[str]
    score: float = 0.0

# ==================== 論文収集 ====================

def fetch_pubmed_papers(days_back: int = 7, max_results: int = 50) -> List[Paper]:
    """PubMed API から最新論文取得"""
    keywords = [
        "hypertension", "blood pressure", "sarcopenia", "cognitive decline", "dementia",
        "type 2 diabetes", "osteoporosis", "frailty", "sleep", "insomnia",
        "gut microbiome", "aging", "older adults", "exercise",
        "protein", "blood pressure", "glucose", "osteoporosis"
    ]
    
    query = " OR ".join([f'"{k}"' for k in keywords])
    query += f' AND ("last {days_back} days"[dp])'
    query += " AND (humans[MeSH Terms])"
    query += " AND (clinical trial[pt] OR meta-analysis[pt] OR guideline[pt] OR review[pt])"
    
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "email": PUBMED_EMAIL,
        "sort": "relevance"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        ids = response.json().get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            return []
        
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "email": PUBMED_EMAIL
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=60)
        fetch_response.raise_for_status()
        
        return parse_pubmed_xml(fetch_response.text)
        
    except Exception as e:
        print("PubMed fetch error: " + str(e))
        return []

def parse_pubmed_xml(xml_text: str) -> List[Paper]:
    """PubMed XML パース"""
    from xml.etree import ElementTree as ET
    
    root = ET.fromstring(xml_text)
    papers = []
    
    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID")
            title = article.findtext(".//ArticleTitle", "")
            abstract = article.findtext(".//Abstract/AbstractText", "")
            
            journal_elem = article.find(".//Journal")
            journal = journal_elem.findtext("Title", "") if journal_elem is not None else ""
            
            pub_date_elem = article.find(".//PubDate")
            if pub_date_elem is not None:
                year = pub_date_elem.findtext("Year", "")
                month = pub_date_elem.findtext("Month", "")
                day = pub_date_elem.findtext("Day", "")
                pub_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}" if year else ""
            else:
                pub_date = ""
            
            doi = ""
            for id_elem in article.findall(".//ArticleId"):
                if id_elem.get("IdType") == "doi":
                    doi = id_elem.text
                    break
            
            mesh_terms = []
            for mesh in article.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text.lower())
            
            papers.append(Paper(
                title=title,
                abstract=abstract,
                authors=[],
                journal=journal,
                pub_date=pub_date,
                doi=doi,
                url="https://pubmed.ncbi.nlm.nih.gov/{pmid}/".format(pmid=pmid),
                tags=mesh_terms
            ))
        except Exception as e:
            print("Parse error: " + str(e))
            continue
    
    return papers

# ==================== スコアリング・フィルタリング ====================

def score_paper(paper: Paper) -> float:
    """論文スコアリング（50代以上関連度・エビデンスレベル・新しさ）"""
    score = 0.0
    text = (paper.title + " " + paper.abstract).lower()
    
    for kw in TARGET_KEYWORDS["high_priority"]:
        if kw in text:
            score += 10
    for kw in TARGET_KEYWORDS["medium_priority"]:
        if kw in text:
            score += 5
    
    text_lower = (paper.title + " " + paper.abstract).lower()
    if "meta-analysis" in text_lower or "systematic review" in text_lower:
        score += 20
    elif "randomized" in text_lower and "controlled" in text_lower:
        score += 15
    elif "guideline" in text_lower:
        score += 15
    elif "clinical trial" in text_lower:
        score += 10
    elif "review" in text_lower:
        score += 5
    
    try:
        pub_date = datetime.strptime(paper.pub_date[:10], "%Y-%m-%d")
        days_old = (datetime.now() - pub_date).days
        score += max(0, 30 - days_old)
    except:
        pass
    
    if "japan" in text_lower or "japanese" in text_lower:
        score += 10
    
    return score

def filter_papers(papers: List[Paper], top_n: int = 3) -> List[Paper]:
    """スコア順でソート・上位N件抽出"""
    for p in papers:
        p.score = score_paper(p)
    
    papers.sort(key=lambda x: x.score, reverse=True)
    return papers[:top_n]

# ==================== LLM呼び出し ====================

def clean_json_response(text: str) -> str:
    """LLM応答からJSON抽出"""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text

def safe_json_loads(text: str) -> dict:
    """Safely parse JSON with cleaning"""
    cleaned = clean_json_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        cleaned = re.sub(r'(?<!\\)\n', '\\n', cleaned)
        cleaned = re.sub(r'(?<!\\)\r', '\\r', cleaned)
        cleaned = re.sub(r'(?<!\\)\t', '\\t', cleaned)
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

def call_openrouter(prompt: str, model: str = None) -> str:
    """OpenRouter API 呼び出し（フォールバック付き）"""
    if model is None:
        model = FREE_MODELS[0]
    
    models_to_try = [model] + [m for m in FREE_MODELS if m != model]
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://health-literacy.vercel.app",
        "X-Title": "Health Literacy Column Generator"
    }
    
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "あなたは健康情報サイト「健康リテラシー」の編集長です。医学論文を一般読者向けに翻訳し、実践的なアクションを提示するコラムを書きます。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                OPENROUTER_BASE_URL,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    print("Model used: " + model_name)
                    return content
                except Exception as e:
                    print("JSON parse error for " + model_name + ": " + str(e))
                    print("Response text: " + response.text[:500])
                    continue
            elif response.status_code == 429:
                print("Rate limited on " + model_name + ", trying next...")
                time.sleep(2)
                continue
            else:
                print("Model " + model_name + " error: " + str(response.status_code))
                print("Response: " + response.text[:500])
                continue
                
        except Exception as e:
            print("Model " + model_name + " exception: " + str(e))
            continue
    
    raise RuntimeError("All OpenRouter models failed")

# ==================== コラム生成 ====================

COLUMN_PROMPT_TEMPLATE = """以下の医学論文を、**50-60代の一般読者向け健康コラム（連載第{episode}回）**として執筆してください。

## 論文情報
- タイトル: {paper_title}
- 概要: {paper_abstract}
- 雑誌: {paper_journal}
- 公開日: {paper_date}
- DOI: {paper_doi}
- URL: {paper_url}
- キーワード: {paper_tags}

## 出力形式（JSONのみ、マークダウン不要）

```json
{
  "title": "読者を引くタイトル（30文字以内、数字・問いかけ推奨）",
  "lead": "リード文（120字以内、結論ファースト・読者を『自分ごと』化）",
  "body_html": "本文HTML（h2/h3見出し、表<table>、箇条書き<ul><li>、強調<strong>含む。専門用語は<ruby>でルビ振るか括弧書きで解説）",
  "action_items": [
    "具体的・即実行・ハードル低めのアクション1",
    "具体的・即実行・ハードル低めのアクション2",
    "具体的・即実行・ハードル低めのアクション3"
  ],
  "source_citation": "雑誌名・年・DOI",
  "disclaimer": "本記事は一般的な健康情報の提供を目的としており、医師の診断・治療に代わるものではありません。健康に関する判断は必ず専門医にご相談ください。",
  "affiliate_keywords": ["関連する商品キーワード1", "関連する商品キーワード2", "関連する商品キーワード3"]
}
```

## 執筆ルール（厳守）

1. **トーン**: 丁寧だが堅すぎない、友人に語りかけるような「わかる語り口」
2. **構成**: リード→背景（なぜ今）→ エビデンス（表で比較）→ メカニズム→ 実践（3アクション）→ 専門家一言→ 免責
3. **専門用語**: 初出時は平易な日本語で解説（<ruby>ルビ</ruby>や（括弧書き）活用）
4. **数値**: パーセント・N数・信頼区間を可能な限り明記
5. **アクション**: 具体的・即実行・ハードル低め・金銭的負担少なめの3つ
6. **アフィリエイト**: 本文内に自然に組み込み、文末に「※アフィリエイトリンクについて」注記
7. **免責**: 本文末尾に必須
8. **HTMLタグ**: h2/h3, table, ul/li, strong, em, a, ruby/rt, mark（ハイライト）のみ使用可
9. **禁止**: script, style, iframe, div/class（スタイルはCSS変数使用）

---

論文:
タイトル: {paper_title}
概要: {paper_abstract[:3000]}
"""

# ==================== HTMLテンプレート ====================

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

# ==================== ユーティリティ ====================

def generate_affiliate_html(keywords: List[str]) -> str:
    """キーワードに基づくアフィリエイトHTML生成"""
    html_parts = []
    used = set()
    
    for kw in keywords:
        kw_lower = kw.lower()
        for key, products in AFFILIATE_PRODUCTS.items():
            if key in kw_lower and key not in used:
                for prod in products[:1]:
                    html_parts.append("""
        <div class="aff-box" style="margin-top:16px;padding:16px;display:flex;gap:12px;align-items:flex-start;border:1px solid var(--border);border-radius:var(--radius);background:var(--paper);">
          <span style="font-size:1.5rem;flex-shrink:0;">🛒</span>
          <div style="flex:1;">
            <div style="font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">おすすめ商品</div>
            <div style="font-weight:600;margin-bottom:8px;"><a href="{url}?tag={tag}" target="_blank" rel="nofollow" style="color:var(--ink);text-decoration:none;">{name}</a></div>
            <a href="{url}?tag={tag}" target="_blank" rel="nofollow" style="display:inline-block;padding:8px 16px;background:var(--primary);color:#fff;border-radius:var(--radius);font-size:.8rem;font-weight:600;text-decoration:none;">Amazonで見る →</a>
          </div>
        </div>
        <p style="font-size:.7rem;color:var(--muted);margin-top:8px;">※ アフィリエイトリンクを含みます</p>
        """.format(url=prod["url"], tag=prod["tag"], name=prod["name"]))
                    used.add(key)
                    break
    
    return "\n".join(html_parts)

# ==================== メイン処理 ====================

def generate_column(paper: Paper) -> Dict:
    """LLMでコラム生成"""
    prompt = COLUMN_PROMPT_TEMPLATE.replace("{paper_title}", paper.title)\
                                   .replace("{paper_abstract[:3000]}", paper.abstract[:3000])\
                                   .replace("{paper_journal}", paper.journal)\
                                   .replace("{paper_date}", paper.pub_date)\
                                   .replace("{paper_doi}", paper.doi)\
                                   .replace("{paper_url}", paper.url)\
                                   .replace("{paper_tags}", ", ".join(paper.tags))\
                                   .replace("{episode}", str(datetime.now().isocalendar()[1]))
    
    response = call_openrouter(prompt)
    
    if not response:
        raise RuntimeError("All OpenRouter models failed")
    
    column_data = safe_json_loads(response)
    
    # アフィリエイトHTML生成
    affiliate_keywords = column_data.get("affiliate_keywords", [])
    column_data["affiliate_html"] = generate_affiliate_html(affiliate_keywords)
    
    return column_data

def main():
    print("🚀 Weekly Health Column Generator 起動")
    
    # 1. 論文収集
    print("📚 論文収集中...")
    papers = fetch_pubmed_papers(days_back=7, max_results=50)
    print("  取得: " + str(len(papers)) + " 件")
    
    if not papers:
        print("❌ 論文が取得できませんでした")
        return
    
    # 2. スコアリング・フィルタリング
    print("🔍 スコアリング・フィルタリング...")
    candidates = filter_papers(papers, top_n=3)
    
    for i, p in enumerate(candidates):
        print("  #" + str(i+1) + " (Score: " + str(p.score)[:4] + ") " + p.title[:60] + "...")
    
    if not candidates:
        print("❌ 適切な論文が見つかりませんでした")
        return
    
    # トップ1本でコラム生成
    best_paper = candidates[0]
    print("\n✍️ コラム生成中: " + best_paper.title[:60] + "...")
    
    try:
        column_data = generate_column(best_paper)
        print("✅ コラム生成完了")
    except Exception as e:
        print("❌ コラム生成失敗: " + str(e))
        import traceback
        traceback.print_exc()
        return
    
    # 保存
    base_dir = r"C:\Users\stand\Documents\hermes_project\test01"
    slug = re.sub(r'[^a-z0-9-]+', '-', best_paper.title.lower())[:60].strip('-')
    article_dir = os.path.join(base_dir, "article", slug)
    os.makedirs(article_dir, exist_ok=True)
    
    # アフィリエイトHTML生成
    affiliate_keywords = column_data.get("affiliate_keywords", [])
    affiliate_html = generate_affiliate_html(affiliate_keywords)
    
    # 記事ページ生成
    read_time = str(max(1, len(column_data['body_html']) // 500)) + "分"
    
    cat_map = {
        "heart": "心臓・血管", "brain": "脳・認知", "muscle": "筋肉・骨", "sugar": "血糖・脂質",
        "check": "検診・予防", "sleep": "睡眠", "gut": "腸内フローラ", "eyes": "目の健康"
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
    for tag in best_paper.tags:
        tag_lower = tag.lower()
        for key, cat in tag_to_cat.items():
            if key in tag_lower:
                category = cat
                break
        if category != "health":
            break
    
    cat_name = cat_map.get(category, "健康")
    
    html = HTML_TEMPLATE.format(
        column_title=column_data["title"],
        column_lead=column_data["lead"],
        column_body_html=column_data["body_html"],
        slug=slug,
        date=best_paper.pub_date,
        episode=datetime.now().isocalendar()[1],
        category_name=cat_name,
        cat_name=cat_name,
        read_time=read_time,
        source_url=best_paper.url,
        affiliate_html=affiliate_html,
        css=CSS_TEMPLATE,
        js=JS_TEMPLATE
    )
    
    with open(os.path.join(article_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    
    print("\n✅ 完了！")
    print("📝 記事: https://health-literacy.vercel.app/article/" + slug + "/")

if __name__ == "__main__":
    main()