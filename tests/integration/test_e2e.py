"""End-to-end integration test: init → start → ingest → analyze → save → verify vault output."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from khanote.cli.app import app
from khanote.session.manager import SessionManager
from khanote.session.ingest import SourceIngester
from khanote.session.analyze import SessionAnalyzer
from khanote.session.save import SessionSaver

runner = CliRunner()


@pytest.fixture
def vault(tmp_path):
    return tmp_path


@pytest.fixture
def mock_researcher():
    r = MagicMock()
    r.ingest.return_value = {"source_count": 1, "indexed_ids": ["id-1"]}
    r.analyze.return_value = {
        "summary": "AI agents are autonomous systems that perceive and act.",
        "sections": {"Key Concepts": "Agents, tools, memory, planning."},
        "raw": None,
    }
    r.generate.return_value = "Generated summary content"
    r.search.return_value = []
    return r


class TestEndToEnd:
    def test_full_workflow(self, vault, mock_researcher):
        # Step 1: Init
        result = runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert (vault / ".khanote").exists()
        assert (vault / ".khanote" / "config.yaml").exists()

        # Step 2: Start session
        (vault / ".khanote").mkdir(exist_ok=True)
        mgr = SessionManager(vault_dir=vault, researcher="perplexity")
        session_dir = mgr.create("AI Agents Overview")
        assert session_dir.exists()
        assert (session_dir / "_session.md").exists()
        assert (vault / "khanote" / "_index.md").exists()

        # Step 3: Ingest sources
        ingester = SourceIngester(session_dir=session_dir, researcher=mock_researcher)
        ingested = ingester.ingest(["https://arxiv.org/abs/2401.12345"])
        assert ingested["ingested"]
        mock_researcher.ingest.assert_called_once()

        # Step 4: Analyze
        analyzer = SessionAnalyzer(session_dir=session_dir, researcher=mock_researcher, vault_dir=vault)
        research_note = analyzer.run(query="What are AI agents?")
        assert research_note.exists()
        content = research_note.read_text()
        assert "AI agents are autonomous" in content

        # Step 5: Save
        saver = SessionSaver(session_dir=session_dir, vault_dir=vault)
        synthesis = saver.save()
        assert synthesis.exists()
        assert "completed" in (session_dir / "_session.md").read_text()

        # Verify vault output structure
        assert (session_dir / "research").exists()
        assert (session_dir / "synthesis").exists()
        assert any((session_dir / "research").glob("*.md"))
        assert any((session_dir / "synthesis").glob("*.md"))
