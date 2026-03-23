"""Tests for Perplexity researcher (TDD — mocked HTTP)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from khanote.researchers.perplexity import PerplexityResearcher
from khanote.researchers.base import ResearcherError


@pytest.fixture
def researcher():
    return PerplexityResearcher(api_key="test-key")


class TestPerplexityIngest:
    def test_ingest_returns_source_count(self, researcher):
        result = researcher.ingest(["https://example.com"])
        assert "source_count" in result
        assert "indexed_ids" in result
        assert result["source_count"] == 1

    def test_ingest_multiple_sources(self, researcher):
        result = researcher.ingest(["url1", "url2", "url3"])
        assert result["source_count"] == 3


class TestPerplexityAnalyze:
    def test_analyze_calls_sonar_api(self, researcher):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis result"}}]
        }
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "post", return_value=mock_response):
            result = researcher.analyze(query="What are AI agents?")
        assert "summary" in result
        assert "sections" in result

    def test_analyze_without_query(self, researcher):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generic analysis"}}]
        }
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "post", return_value=mock_response):
            result = researcher.analyze()
        assert isinstance(result, dict)

    def test_analyze_raises_researcher_error_on_api_failure(self, researcher):
        import httpx
        with patch.object(researcher._client, "post", side_effect=httpx.HTTPError("API down")):
            with pytest.raises(ResearcherError):
                researcher.analyze()


class TestPerplexitySearch:
    def test_search_returns_list_of_dicts(self, researcher):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Result 1\nResult 2"}}]
        }
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "post", return_value=mock_response):
            results = researcher.search("AI agents")
        assert isinstance(results, list)

    def test_search_result_has_required_fields(self, researcher):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Some result"}}]
        }
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "post", return_value=mock_response):
            results = researcher.search("test")
        for r in results:
            assert "id" in r
            assert "title" in r
            assert "excerpt" in r
            assert "score" in r


class TestPerplexityGenerate:
    def test_generate_returns_string(self, researcher):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated content"}}]
        }
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "post", return_value=mock_response):
            result = researcher.generate("summary")
        assert isinstance(result, (str, bytes))
