"""Tests for arXiv researcher (TDD — mocked HTTP)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from khanote.researchers.arxiv import ArxivResearcher


@pytest.fixture
def researcher():
    return ArxivResearcher()


_ARXIV_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <title>AI Agents: A Survey</title>
    <summary>We survey AI agent architectures...</summary>
    <author><name>Jane Doe</name></author>
    <published>2024-01-15T00:00:00Z</published>
  </entry>
</feed>"""


class TestArxivSearch:
    def test_search_returns_list(self, researcher):
        mock_response = MagicMock()
        mock_response.text = _ARXIV_RESPONSE
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "get", return_value=mock_response):
            results = researcher.search("AI agents")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_result_has_required_fields(self, researcher):
        mock_response = MagicMock()
        mock_response.text = _ARXIV_RESPONSE
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "get", return_value=mock_response):
            results = researcher.search("AI agents")
        for r in results:
            assert "id" in r
            assert "title" in r
            assert "excerpt" in r
            assert "score" in r

    def test_search_result_title_matches(self, researcher):
        mock_response = MagicMock()
        mock_response.text = _ARXIV_RESPONSE
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "get", return_value=mock_response):
            results = researcher.search("AI agents")
        assert results[0]["title"] == "AI Agents: A Survey"


class TestArxivIngest:
    def test_ingest_returns_source_count(self, researcher):
        result = researcher.ingest(["https://arxiv.org/abs/2401.12345"])
        assert "source_count" in result
        assert result["source_count"] == 1

    def test_ingest_multiple_sources(self, researcher):
        result = researcher.ingest(["url1", "url2"])
        assert result["source_count"] == 2


class TestArxivAnalyze:
    def test_analyze_returns_structured_output(self, researcher):
        mock_response = MagicMock()
        mock_response.text = _ARXIV_RESPONSE
        mock_response.raise_for_status = MagicMock()
        with patch.object(researcher._client, "get", return_value=mock_response):
            result = researcher.analyze(query="AI agents")
        assert "summary" in result
        assert "sections" in result
        assert "raw" in result


class TestArxivGenerate:
    def test_generate_returns_str_or_bytes(self, researcher):
        result = researcher.generate("summary")
        assert isinstance(result, (str, bytes))
