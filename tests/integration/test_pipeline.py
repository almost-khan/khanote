"""Integration tests for full pipeline orchestration (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from khanote.session.pipeline import PipelineOrchestrator
from khanote.researchers.base import ResearcherError


@pytest.fixture
def vault(tmp_path):
    (tmp_path / ".khanote").mkdir()
    return tmp_path


@pytest.fixture
def mock_researcher():
    r = MagicMock()
    r.ingest.return_value = {"source_count": 1, "indexed_ids": ["id-1"]}
    r.analyze.return_value = {
        "summary": "Test summary from mock researcher.",
        "sections": {"Key Findings": "Finding A"},
        "raw": None,
    }
    r.generate.return_value = "Generated content"
    r.search.return_value = []
    return r


class TestPipelineFlow:
    def test_pipeline_creates_session_folder(self, vault, mock_researcher):
        pipeline = PipelineOrchestrator(vault_dir=vault, researcher=mock_researcher)
        result = pipeline.run(topic="AI Agents", sources=["https://example.com"])
        assert result["session_dir"].exists()

    def test_pipeline_creates_research_note(self, vault, mock_researcher):
        pipeline = PipelineOrchestrator(vault_dir=vault, researcher=mock_researcher)
        result = pipeline.run(topic="AI Agents", sources=["https://example.com"])
        research_dir = result["session_dir"] / "research"
        assert any(research_dir.glob("*.md"))

    def test_pipeline_creates_synthesis_note(self, vault, mock_researcher):
        pipeline = PipelineOrchestrator(vault_dir=vault, researcher=mock_researcher)
        result = pipeline.run(topic="AI Agents", sources=["https://example.com"])
        synthesis_dir = result["session_dir"] / "synthesis"
        assert any(synthesis_dir.glob("*.md"))

    def test_pipeline_session_status_completed(self, vault, mock_researcher):
        pipeline = PipelineOrchestrator(vault_dir=vault, researcher=mock_researcher)
        result = pipeline.run(topic="AI Agents", sources=["https://example.com"])
        session_md = result["session_dir"] / "_session.md"
        assert "completed" in session_md.read_text()

    def test_pipeline_records_pending_on_ingest_failure(self, vault):
        """Per spec FR-015: ingest failure records source as pending, pipeline continues."""
        failing = MagicMock()
        failing.ingest.side_effect = ResearcherError("Ingest failed", researcher="test")
        failing.analyze.return_value = {"summary": "ok", "sections": {}, "raw": None}
        pipeline = PipelineOrchestrator(vault_dir=vault, researcher=failing)
        result = pipeline.run(topic="AI Agents", sources=["https://example.com"])
        # Session should exist; source recorded as pending; pipeline continues
        assert result["session_dir"].exists()
        session_md = result["session_dir"] / "_session.md"
        assert "pending" in session_md.read_text()

    def test_pipeline_preserves_partial_on_analyze_failure(self, vault):
        partial = MagicMock()
        partial.ingest.return_value = {"source_count": 1, "indexed_ids": ["id-1"]}
        partial.analyze.side_effect = ResearcherError("Analyze failed", researcher="test")
        pipeline = PipelineOrchestrator(vault_dir=vault, researcher=partial)
        result = pipeline.run(topic="AI Agents", sources=["https://example.com"])
        assert result["status"] == "failed"
        assert result["session_dir"].exists()

    def test_pipeline_with_no_sources(self, vault, mock_researcher):
        pipeline = PipelineOrchestrator(vault_dir=vault, researcher=mock_researcher)
        result = pipeline.run(topic="AI Agents Overview", sources=[])
        # Should still succeed — session created, no ingest
        assert result["session_dir"].exists()
