"""Cross-feed deduplication — identify and merge duplicate stories."""
from __future__ import annotations


def _similarity(a: str, b: str) -> float:
    """Simple character n-gram similarity between two strings (0.0-1.0).

    Uses a fast overlap measure: intersection / union of character trigrams.
    """
    a = a.lower().strip()
    b = b.lower().strip()
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    def ngrams(s: str, n: int = 3) -> set[str]:
        return {s[i:i + n] for i in range(len(s) - n + 1)} if len(s) >= n else {s}

    a_grams = ngrams(a)
    b_grams = ngrams(b)
    intersection = len(a_grams & b_grams)
    union = len(a_grams | b_grams)
    return intersection / union if union > 0 else 0.0


def _richness_score(item: dict) -> int:
    """Score how information-rich an item is for preferring one duplicate over another."""
    score = 0
    if item.get("url"):
        score += 10
    score += len(item.get("excerpt", ""))
    return score


def deduplicate(items: list[dict], similarity_threshold: float = 0.85) -> list[dict]:
    """Deduplicate a list of search results from multiple feeds.

    Two items are considered duplicates if:
    - They share the same URL (exact match), OR
    - Their titles have >= similarity_threshold trigram similarity

    When deduplicating, the item with the richest metadata is kept:
    - Prefer items with URLs
    - Prefer longer excerpts
    - Prefer higher scores on tie

    Args:
        items: List of search result dicts. Expected keys: id, title, excerpt, score.
        similarity_threshold: Title similarity above which items are considered duplicates.

    Returns:
        Deduplicated list, preserving insertion order of the kept item.
    """
    if not items:
        return []

    kept: list[dict] = []
    # Track (title, url) for dedup
    for item in items:
        title = item.get("title", "")
        url = item.get("url")

        # Check against already-kept items
        duplicate_idx = None
        for i, k in enumerate(kept):
            k_title = k.get("title", "")
            k_url = k.get("url")

            # URL match is definitive
            if url and k_url and url == k_url:
                duplicate_idx = i
                break

            # Title similarity
            if title and k_title and _similarity(title, k_title) >= similarity_threshold:
                duplicate_idx = i
                break

        if duplicate_idx is None:
            kept.append(item)
        else:
            # Merge: keep the richer item
            existing = kept[duplicate_idx]
            if _richness_score(item) > _richness_score(existing):
                # Replace but keep the higher score
                merged = dict(item)
                merged["score"] = max(item.get("score", 0.0), existing.get("score", 0.0))
                kept[duplicate_idx] = merged
            else:
                # Keep existing, but update score if new item had higher
                existing["score"] = max(existing.get("score", 0.0), item.get("score", 0.0))

    return kept
