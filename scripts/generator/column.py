"""LLM column generation module."""

import re
import json
import requests
from datetime import datetime
from typing import Dict, Optional

from config import FREE_MODELS, OPENROUTER_API_KEY


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
3. **数値**: パーセント・N数・信頼区間を可能な限り明記
4. **アクション**: 具体的・即実行・ハードル低め・金銭的負担少なめの3つ
4. **アフィリエイト**: 本文内に自然に組み込み、文末に「※アフィリエイトリンクについて」注記
5. **免責**: 本文末尾に必須
6. **HTMLタグ**: h2/h3, table, ul/li, strong, em, a, ruby/rt, mark（ハイライト）のみ使用可
7. **禁止**: script, style, iframe, div/class（スタイルはCSS変数使用）

---

論文:
タイトル: {paper_title}
概要: {paper_abstract[:3000]}
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
    import json
    cleaned = clean_json_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Try to fix common issues
        # Fix unescaped newlines, tabs, etc.
        text = re.sub(r'(?<!\\)\n', '\\n', text)
        text = re.sub(r'(?<!\\)\r', '\\r', text)
        text = re.sub(r'(?<!\\)\t', '\\t', text)
        # Fix trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        # Try to fix unescaped quotes inside strings
        # Try to find and fix incomplete strings
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Last resort: try to extract the largest valid JSON object
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            # Last resort: return a minimal valid structure
            return {
                "title": "生成エラー",
                "lead": "記事の生成に失敗しました",
                "body_html": "<p>記事の生成に失敗しました。後でもう一度お試しください。</p>",
                "action_items": ["後でもう一度お試しください"],
                "source_citation": "",
                "disclaimer": "本記事は一般的な健康情報の提供を目的としており、医師の診断・治療に代わるものではありません。健康に関する判断は必ず専門医にご相談ください。",
                "affiliate_keywords": []
            }


def call_openrouter(prompt: str, model: str = None) -> str:
    """OpenRouter API 呼び出し（フォールバック付き）"""
    import os
    from config import FREE_MODELS, OPENROUTER_API_KEY
    
    if model is None:
        model = FREE_MODELS[0]
    
    models_to_try = [model] + [m for m in FREE_MODELS if m != model]
    
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://health-literacy.vercel.app",
        "X-Title": "Health Literacy Column Generator"
    }
    
    for model_name in FREE_MODELS:
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
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://health-literacy.vercel.app",
                    "X-Title": "Health Literacy Column Generator"
                },
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    print(f"Model used: {model_name}")
                    return content
                except Exception as e:
                    print(f"JSON parse error for {model_name}: {e}")
                    print(f"Response text: {response.text[:500]}")
                    continue
            elif response.status_code == 429:
                print(f"Rate limited on {model_name}, trying next...")
                import time
                time.sleep(2)
                continue
            else:
                print(f"Model {model_name} error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                continue
                
        except Exception as e:
            print(f"Model {model_name} exception: {e}")
            continue
    
    raise RuntimeError("All OpenRouter models failed")


def generate_column(paper) -> dict:
    """LLMでコラム生成"""
    from datetime import datetime
    
    # Manual string replacement to avoid format() issues
    prompt = COLUMN_PROMPT_TEMPLATE
    replacements = {
        "{paper_title}": paper.title,
        "{paper_abstract[:3000]}": paper.abstract[:3000],
        "{paper_journal}": paper.journal,
        "{paper_date}": paper.pub_date,
        "{paper_doi}": paper.doi,
        "{paper_url}": paper.url,
        "{paper_tags}": ", ".join(paper.tags),
        "{episode}": str(datetime.now().isocalendar()[1])
    }
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)
    
    response = call_openrouter(prompt)
    
    if not response:
        raise RuntimeError("All OpenRouter models failed")
    
    column_data = safe_json_loads(response)
    
    # アフィリエイトHTML生成
    from affiliate import generate_affiliate_html
    affiliate_keywords = column_data.get("affiliate_keywords", [])
    column_data["affiliate_html"] = generate_affiliate_html(affiliate_keywords)
    
    return column_data