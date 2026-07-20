"""論文スコアリング・フィルタリングモジュール"""

from datetime import datetime
from typing import List
from ..models import Paper
from ..config import TARGET_KEYWORDS


def score_paper(paper) -> float:
    """論文スコアリング（50代以上関連度・エビデンスレベル・新しさ）"""
    score = 0.0
    text = (paper.title + " " + paper.abstract).lower()
    
    # キーワードマッチング
    for kw in TARGET_KEYWORDS["high_priority"]:
        if kw in text:
            score += 10
    for kw in TARGET_KEYWORDS["medium_priority"]:
        if kw in text:
            score += 5
    
    # エビデンスレベル
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
    
    # 新しさ（直近ほど高スコア）
    try:
        pub_date = datetime.strptime(paper.pub_date[:10], "%Y-%m-%d")
        days_old = (datetime.now() - pub_date).days
        score += max(0, 30 - days_old)
    except:
        pass
    
    # 日本人関連
    if "japan" in text_lower or "japanese" in text_lower:
        score += 10
    
    return score


def filter_papers(papers: List, top_n: int = 3) -> List:
    """スコア順でソート・上位N件抽出"""
    for p in papers:
        p.score = score_paper(p)
    
    papers.sort(key=lambda x: x.score, reverse=True)
    return papers[:top_n]