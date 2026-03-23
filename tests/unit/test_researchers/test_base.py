"""Tests for Researcher Protocol conformance (TDD)."""
import pytest

from khanote.researchers.base import Researcher, ResearcherError


class ConcreteResearcher:
    """Minimal conforming researcher implementation."""

    def ingest(self, sources: list[str]) -> dict:
        return {"source_count": len(sources), "indexed_ids": sources}

    def analyze(self, query: str | None = None) -> dict:
        return {"summary": "Test summary", "sections": {}, "raw": None}

    def generate(self, type: str, **kwargs) -> str | bytes:
        return "Generated content"

    def search(self, query: str) -> list[dict]:
        return [{"id": "1", "title": "Result", "excerpt": "...", "score": 0.9}]


class IncompleteResearcher:
    """Missing the search method."""

    def ingest(self, sources: list[str]) -> dict:
        return {}

    def analyze(self, query: str | None = None) -> dict:
        return {}

    def generate(self, type: str, **kwargs) -> str | bytes:
        return ""


class TestResearcherProtocol:
    def test_concrete_researcher_is_instance_of_protocol(self):
        researcher = ConcreteResearcher()
        assert isinstance(researcher, Researcher)

    def test_incomplete_researcher_fails_protocol_check(self):
        researcher = IncompleteResearcher()
        assert not isinstance(researcher, Researcher)

    def test_ingest_returns_dict_with_source_count(self):
        researcher = ConcreteResearcher()
        result = researcher.ingest(["url1", "url2"])
        assert "source_count" in result
        assert "indexed_ids" in result
        assert result["source_count"] == 2

    def test_analyze_returns_dict_with_summary(self):
        researcher = ConcreteResearcher()
        result = researcher.analyze()
        assert "summary" in result
        assert "sections" in result
        assert "raw" in result

    def test_analyze_accepts_optional_query(self):
        researcher = ConcreteResearcher()
        result = researcher.analyze(query="What are AI agents?")
        assert isinstance(result, dict)

    def test_generate_returns_str_or_bytes(self):
        researcher = ConcreteResearcher()
        result = researcher.generate("audio")
        assert isinstance(result, (str, bytes))

    def test_search_returns_list_of_dicts(self):
        researcher = ConcreteResearcher()
        results = researcher.search("AI agents")
        assert isinstance(results, list)
        for item in results:
            assert "id" in item
            assert "title" in item
            assert "excerpt" in item
            assert "score" in item


class TestResearcherError:
    def test_researcher_error_is_exception(self):
        with pytest.raises(ResearcherError):
            raise ResearcherError("Something went wrong")

    def test_researcher_error_has_message(self):
        err = ResearcherError("API rate limit exceeded")
        assert "API rate limit exceeded" in str(err)

    def test_researcher_error_has_researcher_name(self):
        err = ResearcherError("Timeout", researcher="perplexity")
        assert err.researcher == "perplexity"

    def test_researcher_error_is_subclass_of_exception(self):
        assert issubclass(ResearcherError, Exception)
