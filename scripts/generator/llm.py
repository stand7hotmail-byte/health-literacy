"""LLM呼び出し・コラム生成モジュール"""

import json
import re
import time
import requests
from typing import Optional, List
from datetime import datetime

from ..config import AFFILIATE_PRODUCTS


# プロンプトテンプレート（JSONの波括弧は {{ }} でエスケープ）
COLUMN_PROMPT_TEMPLATE = """以下の医学論文を、**50-60代の一般読者向け健康コラム（連載第{{episode}}回）**として執筆してください。

## 論文情報
- タイトル: {{paper_title}}
- 概要: {{paper_abstract}}
- 雑誌: {{paper_journal}}
- 公開日: {{paper_date}}
- DOI: {{paper_doi}}
- URL: {{paper_url}}
- キーワード: {{paper_tags}}

## 出力形式（JSONのみ、マークダウン不要）

```json
{{
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
}}
```

## 執筆ルール（厳守）

1. **トーン**: 丁寧だが堅すぎない、友人に語りかけるような「わかる語り口」
2. **構成": リード→背景（なぜ今）→ エビデンス（表で比較）→ メカニズム→ 実践（3アクション）→ 専門家一言→ 免責
3. **専門用語": 初出時は平易な日本語で解説（<ruby>ルビ</ruby>や（括弧書き）活用）
4. **数値": パーセント・N数・信頼区間を可能な限り明記
5. **アクション": 具体的・即実行・ハードル低め・金銭的負担少なめの3つ
6. **アフィリエイト": 本文内に自然に組み込み、文末に「※アフィリエイトリンクについて」注記
7. **免責": 本文末尾に必須
8. **HTMLタグ": h2/h3, table, ul/li, strong, em, a, ruby/rt, mark（ハイライト）のみ使用可
9. **禁止": script, style, iframe, div/class（スタイルはCSS変数使用）

---

論文:
タイトル: {{paper_title}}
概要: {{paper_abstract[:3000]}}
"""


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


def call_openrouter(prompt: str, model: str = None):
    """OpenRouter API 呼び出し（フォールバック付き）"""
    from ..config import OPENROUTER_API_KEY, FREE_MODELS
    
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
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"Model used: {model_name}")
                return content
            elif response.status_code == 429:
                print(f"Rate limited on {model_name}, trying next...")
                time.sleep(2)
                continue
            else:
                print(f"Model {model_name} error: {response.status_code} - {response.text[:200]}")
                continue
                
        except Exception as e:
            print(f"Model {model_name} exception: {e}")
            continue
    
    raise RuntimeError("All OpenRouter models failed")


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


def call_openrouter(prompt: str, model: str = None):
    """OpenRouter API 呼び出し（フォールバック付き）"""
    from ..config import OPENROUTER_API_KEY, FREE_MODELS
    import requests
    import time
    
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
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"Model used: {model_name}")
                return content
            elif response.status_code == 429:
                print(f"Rate limited on {model_name}, trying next...")
                time.sleep(2)
                continue
            else:
                print(f"Model {model_name} error: {response.status_code} - {response.text[:200]}")
                continue
                
        except Exception as e:
            print(f"Model {model_name} exception: {e}")
            continue
    
    raise RuntimeError("All OpenRouter models failed")


def generate_column(paper) -> dict:
    """単一論文からコラム生成"""
    from ..config import FREE_MODELS
    from datetime import datetime
    
    prompt = COLUMN_PROMPT_TEMPLATE.format(
        paper_title=paper.title,
        paper_abstract=paper.abstract[:3000],
        paper_journal=paper.journal,
        paper_date=paper.pub_date,
        paper_doi=paper.doi,
        paper_url=paper.url,
        paper_tags=", ".join(paper.tags),
        episode=datetime.now().isocalendar()[1]
    )
    
    response = call_openrouter(prompt)
    
    if not response:
        raise RuntimeError("All OpenRouter models failed")
    
    column_data = safe_json_loads(response)
    
    # アフィリエイトHTML生成
    affiliate_keywords = column_data.get("affiliate_keywords", [])
    column_data["affiliate_html"] = generate_affiliate_html(affiliate_keywords)
    
    return column_data


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


def call_openrouter(prompt: str, model: str = None):
    """OpenRouter API 呼び出し（フォールバック付き）"""
    from ..config import OPENROUTER_API_KEY, FREE_MODELS
    import requests
    import time
    
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
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"Model used: {model_name}")
                return content
            elif response.status_code == 429:
                print(f"Rate limited on {model_name}, trying next...")
                time.sleep(2)
                continue
            else:
                print(f"Model {model_name} error: {response.status_code} - {response.text[:200]}")
                continue
                
        except Exception as e:
            print(f"Model {model_name} exception: {e}")
            continue
    
    raise RuntimeError("All OpenRouter models failed")


def generate_column(paper) -> dict:
    """単一論文からコラム生成"""
    from ..config import FREE_MODELS
    from datetime import datetime
    
    prompt = COLUMN_PROMPT_TEMPLATE.format(
        paper_title=paper.title,
        paper_abstract=paper.abstract[:3000],
        paper_journal=paper.journal,
        paper_date=paper.pub_date,
        paper_doi=paper.doi,
        paper_url=paper.url,
        paper_tags=", ".join(paper.tags),
        episode=datetime.now().isocalendar()[1]
    )
    
    response = call_openrouter(prompt)
    
    if not response:
        raise RuntimeError("All OpenRouter models failed")
    
    column_data = safe_json_loads(response)
    
    # アフィリエイトHTML生成
    affiliate_keywords = column_data.get("affiliate_keywords", [])
    column_data["affiliate_html"] = generate_affiliate_html(affiliate_keywords)
    
    return column_data


def generate_affiliate_html(keywords: List[str]) -> str:
    """キーワードに基づくアフィリエイトHTML生成"""
    from ..config import AFFILIATE_PRODUCTS
    
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