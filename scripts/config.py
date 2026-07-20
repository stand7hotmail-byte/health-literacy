"""Configuration constants and shared data."""

import os

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

# カテゴリマッピング
CAT_MAP = {
    "heart": {"name": "心臓・血管", "icon": "❤️"},
    "brain": {"name": "脳・認知", "icon": "🧠"},
    "muscle": {"name": "筋肉・骨", "icon": "💪"},
    "sugar": {"name": "血糖・脂質", "icon": "🍚"},
    "check": {"name": "検診・予防", "icon": "🔍"},
    "sleep": {"name": "睡眠", "icon": "😴"},
    "gut": {"name": "腸内フローラ", "icon": "🦠"},
    "eyes": {"name": "目の健康", "icon": "👁️"},
}

# HTML Template (imported from templates.py)
# CSS_TEMPLATE and JS_TEMPLATE will be imported from templates.py