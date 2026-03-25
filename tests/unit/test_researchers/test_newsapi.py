"""Tests for NewsAPI researcher (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestNewsAPIResearcher:
    """T082: NewsAPI researcher tests."""

    def test_implements_researcher_protocol(self):
        from khanote.researchers.newsapi import NewsAPIResearcher
        from khanote.researchers.base import Researcher
        r = NewsAPIResearcher(api_key="test-key")
        assert isinstance(r, Researcher)

    def test_search_returns_list(self):
        from khanote.researchers.newsapi import NewsAPIResearcher
        r = NewsAPIResearcher(api_key="test-key")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "AI News Today",
                    "description": "Latest AI developments",
                    "url": "https://example.com/ai-news",
                    "source": {"name": "Tech News"},
                    "publishedAt": "2026-03-24T10:00:00Z",
                }
            ]
        }
        with patch("httpx.get", return_value=mock_response):
            results = r.search("artificial intelligence")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_result_has_required_fields(self):
        from khanote.researchers.newsapi import NewsAPIResearcher
        r = NewsAPIResearcher(api_key="test-key")
        article = {
            "title": "Tech Update",
            "description": "Technology news",
            "url": "https://example.com",
            "source": {"name": "Test Source"},
            "publishedAt": "2026-03-24T10:00:00Z",
        }
        result = r._parse_article(article)
        assert "id" in result
        assert "title" in result
        assert "excerpt" in result
        assert "score" in result

    def test_analyze_returns_dict(self):
        from khanote.researchers.newsapi import NewsAPIResearcher
        r = NewsAPIResearcher(api_key="test-key")
        result = r.analyze(query="technology")
        assert isinstance(result, dict)
        assert "summary" in result

    def test_missing_api_key_raises(self):
        from khanote.researchers.newsapi import NewsAPIResearcher
        from khanote.researchers.base import ResearcherError
        r = NewsAPIResearcher(api_key=None)
        with pytest.raises((ResearcherError, Exception)):
            with patch("httpx.get") as mock_get:
                mock_get.return_value.json.return_value = {"status": "error", "message": "apiKey is required"}
                mock_get.return_value.status_code = 401
                r.search("test")

    def test_ingest_returns_structure(self):
        from khanote.researchers.newsapi import NewsAPIResearcher
        r = NewsAPIResearcher(api_key="test-key")
        result = r.ingest(["https://example.com/article"])
        assert "source_count" in result
