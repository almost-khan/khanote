"""Integration tests for pipeline capability skip (T023 — US6)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from khanote.models.config import ResearcherConfig
from khanote.researchers.config_researcher import ConfigResearcher
from khanote.session.pipeline import PipelineOrchestrator


@pytest.fixture
def vault_dir(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def search_only_researcher():
    """A researcher that only supports search — no ingest, analyze, generate."""
    config = ResearcherConfig(
        enabled=True,
        type="http",
        capabilities=["search"],
        sop={"search": "Search for: {query}"},
    )
    return ConfigResearcher("search-only", config)


@pytest.fixture
def analyze_only_researcher():
    """A researcher that only supports analyze via SOP."""
    config = ResearcherConfig(
        enabled=True,
        type="http",
        capabilities=["analyze"],
        sop={"analyze": "Analyze: {results}"},
    )
    return ConfigResearcher("analyze-only", config)


class TestPipelineCapabilitySkip:
    """T023: Pipeline skips undeclared capabilities silently."""

    def test_search_on_undeclared_returns_empty(self, search_only_researcher):
        """Calling search on search-only researcher works."""
        results = search_only_researcher.search("test query")
        assert isinstance(results, list)

    def test_ingest_on_search_only_returns_noop(self, search_only_researcher):
        """ingest not declared — returns noop without error."""
        result = search_only_researcher.ingest(["url1", "url2"])
        assert result["source_count"] == 0

    def test_analyze_on_search_only_returns_noop(self, search_only_researcher):
        """analyze not declared — returns noop without error."""
        result = search_only_researcher.analyze()
        assert result["summary"] == ""

    def test_generate_on_search_only_returns_noop(self, search_only_researcher):
        """generate not declared — returns empty string without error."""
        result = search_only_researcher.generate("podcast")
        assert result == ""

    def test_pipeline_runs_with_search_only_researcher(self, vault_dir, search_only_researcher):
        """Pipeline completes (no crash) with a search-only researcher."""
        orchestrator = PipelineOrchestrator(
            vault_dir=vault_dir,
            researcher=search_only_researcher,
        )
        result = orchestrator.run(topic="ai-agents")
        # Pipeline should not crash even though ingest is not supported
        assert result["status"] in ("completed", "failed")
        # If failed, the error should NOT be about missing capability
        if result["status"] == "failed":
            assert "capability" not in (result.get("error") or "").lower()

    def test_sop_only_researcher_produces_valid_analyze_output(self, analyze_only_researcher):
        """SOP-only researcher returns valid analyze output shape."""
        result = analyze_only_researcher.analyze(results="paper about AI agents")
        assert "summary" in result
        assert "sections" in result
        assert "raw" in result
        assert result["summary"] != ""

    def test_capabilities_list_accurate(self, search_only_researcher):
        assert search_only_researcher.capabilities == ["search"]


class TestCliModeDetection:
    """T026: CLI-mode detection for SOP-dependent researchers."""

    def test_sop_analyze_outside_skill_mode_returns_prompt(self, analyze_only_researcher):
        """SOP analyze returns the filled prompt — caller must handle skill vs CLI mode."""
        result = analyze_only_researcher.analyze(results="test data")
        # The result contains the SOP prompt — it is the caller's (skill/CLI) responsibility
        # to process it with an LLM. The content itself is a prompt string.
        assert "Analyze:" in result["summary"] or len(result["summary"]) > 0
