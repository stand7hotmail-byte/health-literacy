"""Paper scoring and filtering module."""

from typing import List
from models import Paper
from config import TARGET_KEYWORDS
from datetime import datetime


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
    
    if "japan" in (paper.title + " " + paper.abstract).lower() or "japanese" in (paper.title + " " + paper.abstract).lower():
        score += 10
    
    return score


def filter_papers(papers: List[Paper], top_n: int = 3) -> List[Paper]:
    """スコア順でソート・上位N件抽出"""
    for p in papers:
        p.score = score_paper(p)
    
    papers.sort(key=lambda x: x.score, reverse=True)
    return papers[:top_n]