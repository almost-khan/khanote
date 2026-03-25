"""Tests for Hacker News researcher (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch



class TestHackerNewsResearcher:
    """T081: Hacker News researcher tests."""

    def test_implements_researcher_protocol(self):
        from khanote.researchers.hackernews import HackerNewsResearcher
        from khanote.researchers.base import Researcher
        r = HackerNewsResearcher()
        assert isinstance(r, Researcher)

    def test_search_returns_list(self):
        from khanote.researchers.hackernews import HackerNewsResearcher
        r = HackerNewsResearcher()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": [
                {
                    "objectID": "12345",
                    "title": "Ask HN: What's new in AI?",
                    "url": "https://example.com/ai",
                    "points": 150,
                    "num_comments": 42,
                    "author": "user123",
                    "created_at": "2026-03-24T10:00:00.000Z",
                }
            ]
        }
        with patch("httpx.get", return_value=mock_response):
            results = r.search("AI machine learning")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_result_has_required_fields(self):
        from khanote.researchers.hackernews import HackerNewsResearcher
        r = HackerNewsResearcher()
        hit = {
            "objectID": "99999",
            "title": "New Python Framework Released",
            "url": "https://example.com",
            "points": 200,
            "num_comments": 50,
            "author": "dev",
            "created_at": "2026-03-24T12:00:00.000Z",
        }
        result = r._parse_hit(hit)
        assert "id" in result
        assert "title" in result
        assert "excerpt" in result
        assert "score" in result

    def test_analyze_returns_dict(self):
        from khanote.researchers.hackernews import HackerNewsResearcher
        r = HackerNewsResearcher()
        result = r.analyze(query="AI")
        assert isinstance(result, dict)
        assert "summary" in result

    def test_ingest_returns_structure(self):
        from khanote.researchers.hackernews import HackerNewsResearcher
        r = HackerNewsResearcher()
        result = r.ingest(["https://news.ycombinator.com/item?id=12345"])
        assert "source_count" in result

    def test_empty_search_returns_list(self):
        from khanote.researchers.hackernews import HackerNewsResearcher
        r = HackerNewsResearcher()
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": []}
        with patch("httpx.get", return_value=mock_response):
            results = r.search("")
        assert isinstance(results, list)
