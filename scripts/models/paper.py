"""Paper data model."""

from dataclasses import dataclass
from typing import List


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