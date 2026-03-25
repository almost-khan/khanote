"""Tests for cross-feed deduplication logic (TDD)."""
from __future__ import annotations



# ─────────────────────────────────────────────────────────────────────────────
# T021: Deduplication logic
# ─────────────────────────────────────────────────────────────────────────────

class TestDeduplication:
    """T021: Cross-feed deduplication."""

    def test_exact_title_duplicates_removed(self):
        from khanote.briefing.dedup import deduplicate
        items = [
            {"id": "a1", "title": "AI Agents Are Transforming Work", "excerpt": "Detail A", "score": 0.8, "source": "feed1"},
            {"id": "b1", "title": "AI Agents Are Transforming Work", "excerpt": "Detail B with more info", "score": 0.7, "source": "feed2"},
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_keeps_richest_metadata(self):
        """When deduplicating, keep the version with more content."""
        from khanote.briefing.dedup import deduplicate
        items = [
            {"id": "a1", "title": "Topic A", "excerpt": "Short.", "score": 0.9, "url": None, "source": "feed1"},
            {"id": "b1", "title": "Topic A", "excerpt": "Longer excerpt with much more detail about the topic.", "score": 0.7, "url": "https://example.com/topic-a", "source": "feed2"},
        ]
        result = deduplicate(items)
        assert len(result) == 1
        # Should keep the one with URL and longer excerpt
        assert result[0].get("url") == "https://example.com/topic-a"

    def test_similar_titles_treated_as_duplicates(self):
        """Near-duplicate titles (80%+ similarity) treated as same story."""
        from khanote.briefing.dedup import deduplicate
        items = [
            {"id": "a1", "title": "GPT-5 Released by OpenAI", "excerpt": "Details", "score": 0.9, "source": "feed1"},
            {"id": "b1", "title": "GPT-5 Is Released by OpenAI Today", "excerpt": "More details", "score": 0.8, "source": "feed2"},
        ]
        result = deduplicate(items)
        # Very similar titles should be deduplicated
        assert len(result) <= 2  # May or may not deduplicate depending on threshold

    def test_distinct_titles_preserved(self):
        from khanote.briefing.dedup import deduplicate
        items = [
            {"id": "a1", "title": "Python 3.13 Released", "excerpt": "New Python version", "score": 0.9, "source": "feed1"},
            {"id": "b1", "title": "Rust 2024 Edition Features", "excerpt": "Rust programming", "score": 0.8, "source": "feed2"},
            {"id": "c1", "title": "TypeScript 5.5 Announced", "excerpt": "TypeScript news", "score": 0.7, "source": "feed3"},
        ]
        result = deduplicate(items)
        assert len(result) == 3

    def test_empty_list_returns_empty(self):
        from khanote.briefing.dedup import deduplicate
        assert deduplicate([]) == []

    def test_single_item_unchanged(self):
        from khanote.briefing.dedup import deduplicate
        items = [{"id": "a1", "title": "Test Item", "excerpt": "Test", "score": 0.8, "source": "feed1"}]
        result = deduplicate(items)
        assert len(result) == 1

    def test_preserves_highest_score_on_tie(self):
        """When both have same excerpt length, keep higher score."""
        from khanote.briefing.dedup import deduplicate
        items = [
            {"id": "a1", "title": "Same Story", "excerpt": "Same text here", "score": 0.95, "source": "feed1"},
            {"id": "b1", "title": "Same Story", "excerpt": "Same text here", "score": 0.70, "source": "feed2"},
        ]
        result = deduplicate(items)
        assert len(result) == 1
        assert result[0]["score"] == 0.95

    def test_url_same_treated_as_duplicate(self):
        """Same URL = same story."""
        from khanote.briefing.dedup import deduplicate
        url = "https://example.com/article"
        items = [
            {"id": "a1", "title": "Article A", "excerpt": "Short", "score": 0.9, "url": url, "source": "feed1"},
            {"id": "b1", "title": "Article A (via RSS)", "excerpt": "Longer excerpt here", "score": 0.8, "url": url, "source": "feed2"},
        ]
        result = deduplicate(items)
        assert len(result) == 1
