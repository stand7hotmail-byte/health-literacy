"""Data classes for the application."""

from dataclasses import dataclass
from typing import List


@dataclass
class Paper:
    """Medical paper data class."""
    title: str
    abstract: str
    authors: List[str]
    journal: str
    pub_date: str
    doi: str
    url: str
    tags: List[str]
    score: float = 0.0


@dataclass
class Column:
    """Generated column data class."""
    title: str
    lead: str
    body_html: str
    action_items: List[str]
    source_citation: str
    disclaimer: str
    affiliate_keywords: List[str]
    affiliate_html: str = ""