"""
Semantic service — placeholder for future semantic search capabilities.
Currently provides basic keyword frequency scoring.
"""

from collections import Counter
import re


def compute_keyword_relevance(text: str, query: str) -> float:
    """
    Compute a simple keyword frequency relevance score.
    Returns a value between 0.0 and 1.0.
    """
    if not text or not query:
        return 0.0

    text_lower = text.lower()
    query_terms = re.findall(r"\w+", query.lower())

    if not query_terms:
        return 0.0

    words = re.findall(r"\w+", text_lower)
    word_count = len(words) if words else 1
    word_freq = Counter(words)

    total_freq = sum(word_freq.get(term, 0) for term in query_terms)
    # Normalize: frequency per 1000 words, capped at 1.0
    score = min(1.0, (total_freq / word_count) * 100)

    return round(score, 4)
