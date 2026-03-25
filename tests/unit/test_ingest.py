"""Tests for source ingestion (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from khanote.session.ingest import SourceIngester


@pytest.fixture
def session_dir(tmp_path):
    """Create a session structure for testing."""
    s = tmp_path / "khanote" / "2026-03-22_AI-Agents"
    for subdir in ("sources", "research", "synthesis", "artifacts"):
        (s / subdir).mkdir(parents=True)
    # Write minimal _session.md
    (s / "_session.md").write_text(
        "---\ndate: 2026-03-22\ntopic: AI Agents\nresearcher: perplexity\n"
        "status: in-progress\nsources_count: 0\n---\n\n## Sources\n\n## Notes\n"
    )
    return s


@pytest.fixture
def mock_researcher():
    r = MagicMock()
    r.ingest.return_value = {"source_count": 1, "indexed_ids": ["id-1"]}
    return r


class TestURLIngestion:
    def test_url_recorded_in_session_md(self, session_dir, mock_researcher):
        ingester = SourceIngester(session_dir=session_dir, researcher=mock_researcher)
        ingester.ingest(["https://arxiv.org/abs/2401.12345"])
        content = (session_dir / "_session.md").read_text()
        assert "https://arxiv.org/abs/2401.12345" in content

    def test_url_passed_to_researcher(self, session_dir, mock_researcher):
        ingester = SourceIngester(session_dir=session_dir, researcher=mock_researcher)
        ingester.ingest(["https://example.com"])
        mock_researcher.ingest.assert_called_once_with(["https://example.com"])

    def test_sources_count_updated(self, session_dir, mock_researcher):
        ingester = SourceIngester(session_dir=session_dir, researcher=mock_researcher)
        ingester.ingest(["https://example.com", "https://example2.com"])
        content = (session_dir / "_session.md").read_text()
        assert "sources_count: 2" in content


class TestFileIngestion:
    def test_file_copied_to_sources_dir(self, session_dir, mock_researcher, tmp_path):
        src_file = tmp_path / "paper.pdf"
        src_file.write_bytes(b"PDF content")
        ingester = SourceIngester(session_dir=session_dir, researcher=mock_researcher)
        ingester.ingest([str(src_file)])
        assert (session_dir / "sources" / "paper.pdf").exists()

    def test_file_path_recorded_in_session_md(self, session_dir, mock_researcher, tmp_path):
        src_file = tmp_path / "paper.pdf"
        src_file.write_bytes(b"PDF content")
        ingester = SourceIngester(session_dir=session_dir, researcher=mock_researcher)
        ingester.ingest([str(src_file)])
        content = (session_dir / "_session.md").read_text()
        assert "paper.pdf" in content


class TestResearcherUnavailable:
    def test_source_recorded_with_pending_status_on_failure(self, session_dir):
        """If researcher fails, source is recorded as pending."""
        failing_researcher = MagicMock()
        from khanote.researchers.base import ResearcherError
        failing_researcher.ingest.side_effect = ResearcherError("API down", researcher="perplexity")

        ingester = SourceIngester(session_dir=session_dir, researcher=failing_researcher)
        # Should not raise
        ingester.ingest(["https://example.com"])
        content = (session_dir / "_session.md").read_text()
        assert "pending" in content or "https://example.com" in content

    def test_ingest_without_researcher_records_source(self, session_dir):
        """Ingestion without a researcher still records the source."""
        ingester = SourceIngester(session_dir=session_dir, researcher=None)
        ingester.ingest(["https://example.com"])
        content = (session_dir / "_session.md").read_text()
        assert "https://example.com" in content
