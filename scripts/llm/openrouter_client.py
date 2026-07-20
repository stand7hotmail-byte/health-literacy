"""OpenRouter LLM client module."""

import json
import re
import time
import requests
from typing import Optional

from ..config import FREE_MODELS, OPENROUTER_BASE_URL, OPENROUTER_API_KEY


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
        import json
        return json.loads(cleaned)
    except Exception as e:
        cleaned = re.sub(r'(?<!\\)\n', '\\n', cleaned)
        cleaned = re.sub(r'(?<!\\)\r', '\\r', cleaned)
        cleaned = re.sub(r'(?<!\\)\t', '\\t', cleaned)
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        try:
            import json
            return json.loads(cleaned)
        except Exception:
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                import json
                return json.loads(match.group(0))
            raise


def call_openrouter(prompt: str, model: str = None) -> str:
    """OpenRouter API 呼び出し（フォールバック付き）"""
    from ..config import FREE_MODELS, OPENROUTER_BASE_URL, OPENROUTER_API_KEY
    
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
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://health-literacy.vercel.app",
                    "X-Title": "Health Literacy Column Generator"
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "あなたは健康情報サイト「健康リテラシー」の編集長です。医学論文を一般読者向けに翻訳し、実践的なアクションを提示するコラムを書きます。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
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