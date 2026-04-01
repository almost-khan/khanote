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

    Uses a URL index for O(1) exact-match lookups before falling back to
    O(n) title similarity checks.

    Args:
        items: List of search result dicts. Expected keys: id, title, excerpt, score.
        similarity_threshold: Title similarity above which items are considered duplicates.

    Returns:
        Deduplicated list, preserving insertion order of the kept item.
    """
    if not items:
        return []

    kept: list[dict] = []
    # O(1) URL lookup: url → index in kept list
    url_index: dict[str, int] = {}

    for item in items:
        title = item.get("title", "")
        url = item.get("url")

        # Phase 1: O(1) URL exact-match check
        duplicate_idx = None
        if url and url in url_index:
            duplicate_idx = url_index[url]

        # Phase 2: O(n) title similarity (only when URL didn't match)
        if duplicate_idx is None:
            for i, k in enumerate(kept):
                k_title = k.get("title", "")
                if title and k_title and _similarity(title, k_title) >= similarity_threshold:
                    duplicate_idx = i
                    break

        if duplicate_idx is None:
            idx = len(kept)
            kept.append(item)
            if url:
                url_index[url] = idx
        else:
            # Merge: keep the richer item
            existing = kept[duplicate_idx]
            if _richness_score(item) > _richness_score(existing):
                merged = dict(item)
                merged["score"] = max(item.get("score", 0.0), existing.get("score", 0.0))
                kept[duplicate_idx] = merged
                # Update URL index for the replacement
                if url:
                    url_index[url] = duplicate_idx
            else:
                existing["score"] = max(existing.get("score", 0.0), item.get("score", 0.0))

    return kept
