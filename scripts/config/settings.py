import os

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# API Keys
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
CATEGORY_MAP = {
    "heart": {"name": "心臓・血管", "icon": "❤️"},
    "brain": {"name": "脳・認知", "icon": "🧠"},
    "muscle": {"name": "筋肉・骨", "icon": "💪"},
    "sugar": {"name": "血糖・脂質", "icon": "🍚"},
    "check": {"name": "検診・予防", "icon": "🔍"},
    "sleep": {"name": "睡眠", "icon": "😴"},
    "gut": {"name": "腸内フローラ", "icon": "🦠"},
    "eyes": {"name": "目の健康", "icon": "👁️"},
}

# TAG_TO_CAT mapping
TAG_TO_CAT = {
    "hypertension": "heart", "blood pressure": "heart", "sarcopenia": "muscle",
    "muscle": "muscle", "protein": "muscle", "cognitive": "brain", "dementia": "brain",
    "alzheimer": "brain", "diabetes": "sugar", "glucose": "sugar", "insulin": "sugar",
    "osteoporosis": "muscle", "bone": "muscle", "fracture": "muscle", "sleep": "sleep",
    "insomnia": "sleep", "gut microbiome": "gut", "longevity": "gut", "aging": "gut",
    "eye": "eyes", "vision": "eyes"
}

# API endpoints
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Base paths
BASE_DIR = r"C:\Users\stand\Documents\hermes_project\test01"

# COLUMN_PROMPT_TEMPLATE
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
6. **HTMLタグ": h2/h3, table, ul/li, strong, em, a, ruby/rt, mark（ハイライト）のみ使用可
7. **禁止": script, style, iframe, div/class（スタイルはCSS変数使用）

---

論文:
タイトル: {paper_title}
概要: {paper_abstract[:3000]}
"""