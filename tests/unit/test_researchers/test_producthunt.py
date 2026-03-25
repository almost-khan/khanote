"""Tests for Product Hunt researcher (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestProductHuntResearcher:
    """T084: Product Hunt researcher tests."""

    def test_implements_researcher_protocol(self):
        from khanote.researchers.producthunt import ProductHuntResearcher
        from khanote.researchers.base import Researcher
        r = ProductHuntResearcher(token="test-token")
        assert isinstance(r, Researcher)

    def test_search_returns_list(self):
        from khanote.researchers.producthunt import ProductHuntResearcher
        r = ProductHuntResearcher(token="test-token")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "posts": {
                    "edges": [
                        {
                            "node": {
                                "id": "ph-1",
                                "name": "AwesomeAI Tool",
                                "tagline": "AI-powered productivity",
                                "url": "https://www.producthunt.com/posts/awesomeai",
                                "votesCount": 500,
                                "description": "Best AI tool",
                            }
                        }
                    ]
                }
            }
        }
        with patch("httpx.post", return_value=mock_response):
            results = r.search("AI tools")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_result_has_required_fields(self):
        from khanote.researchers.producthunt import ProductHuntResearcher
        r = ProductHuntResearcher(token="test-token")
        node = {
            "id": "ph-test",
            "name": "Test Product",
            "tagline": "Test tagline",
            "url": "https://www.producthunt.com/posts/test",
            "votesCount": 100,
            "description": "Test description",
        }
        result = r._parse_post(node)
        assert "id" in result
        assert "title" in result
        assert "excerpt" in result
        assert "score" in result

    def test_analyze_returns_dict(self):
        from khanote.researchers.producthunt import ProductHuntResearcher
        r = ProductHuntResearcher(token="test-token")
        result = r.analyze(query="productivity tools")
        assert isinstance(result, dict)
        assert "summary" in result

    def test_missing_token_raises_on_search(self):
        from khanote.researchers.producthunt import ProductHuntResearcher
        from khanote.researchers.base import ResearcherError
        r = ProductHuntResearcher(token=None)
        with pytest.raises((ResearcherError, Exception)):
            r.search("test")

    def test_ingest_returns_structure(self):
        from khanote.researchers.producthunt import ProductHuntResearcher
        r = ProductHuntResearcher(token="test-token")
        result = r.ingest(["https://www.producthunt.com/posts/test"])
        assert "source_count" in result
