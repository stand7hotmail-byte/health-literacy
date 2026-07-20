"""設定・定数管理"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==================== API Keys ====================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL")
GH_TOKEN = os.getenv("GH_TOKEN")

# ==================== API Endpoints ====================
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# ==================== Paths ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTICLE_DIR = os.path.join(BASE_DIR, "article")

# ==================== OpenRouter Models ====================
FREE_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "openai/gpt-oss-20b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
]

# ==================== Target Keywords for Scoring ====================
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

# ==================== Affiliate Products ====================
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

# ==================== Category Mapping ====================
CAT_MAP = {
    "heart": "心臓・血管", "brain": "脳・認知", "muscle": "筋肉・骨", "sugar": "血糖・脂質",
    "check": "検診・予防", "sleep": "睡眠", "gut": "腸内フローラ", "eyes": "目の健康",
    "health": "健康",
}

TAG_TO_CAT = {
    "hypertension": "heart", "blood pressure": "heart", "sarcopenia": "muscle",
    "muscle": "muscle", "protein": "muscle", "cognitive": "brain", "dementia": "brain",
    "alzheimer": "brain", "diabetes": "sugar", "glucose": "sugar", "insulin": "sugar",
    "osteoporosis": "muscle", "bone": "muscle", "fracture": "muscle", "sleep": "sleep",
    "insomnia": "sleep", "gut microbiome": "gut", "longevity": "gut", "aging": "gut",
    "eye": "eyes", "vision": "eyes",
}

# ==================== Site URLs ====================
SITE_URL = "https://health-literacy.vercel.app"
SITE_NAME = "健康リテラシー"

# ==================== PubMed API ====================
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"