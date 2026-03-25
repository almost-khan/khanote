"""Tests for NotebookLM researcher stubs (TDD — experimental status)."""
from __future__ import annotations


from khanote.researchers.notebooklm import NotebookLMResearcher


class TestNotebookLMStatus:
    def test_is_marked_experimental(self):
        researcher = NotebookLMResearcher()
        assert researcher.status == "experimental"

    def test_ingest_returns_source_count(self):
        researcher = NotebookLMResearcher()
        result = researcher.ingest(["https://example.com"])
        assert "source_count" in result
        assert result["source_count"] == 1

    def test_analyze_returns_structured_dict(self):
        researcher = NotebookLMResearcher()
        result = researcher.analyze()
        assert "summary" in result
        assert "sections" in result

    def test_search_returns_list(self):
        researcher = NotebookLMResearcher()
        results = researcher.search("test query")
        assert isinstance(results, list)

    def test_generate_returns_str_or_bytes(self):
        researcher = NotebookLMResearcher()
        result = researcher.generate("summary")
        assert isinstance(result, (str, bytes))
