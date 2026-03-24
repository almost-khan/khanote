"""End-to-end integration test: add researcher → add feed → run feed → verify output (T051)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from khanote.models.config import Config, EndpointConfig, ResearcherConfig
from khanote.cli.researcher_add import add_researcher_to_config
from khanote.feeds.manager import FeedManager
from khanote.feeds.runner import FeedRunner


@pytest.fixture
def vault_dir(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def config_file(vault_dir, tmp_path):
    data = {
        "version": "0.1.0",
        "vault_path": str(vault_dir),
        "initialized_tools": ["claude-code"],
        "research": {
            "default": "perplexity",
            "researchers": {
                "perplexity": {"enabled": True, "api_key": "perplexity-key"},
            },
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(data))
    return path


class TestEndToEndResearcherFeed:
    """T051: Full flow: add researcher → add feed → run feed → verify output."""

    def test_full_flow_custom_researcher_to_feed_run(self, config_file):
        # Step 1: Add a custom researcher
        exa_config = ResearcherConfig(
            enabled=True,
            type="http",
            api_key="exa-test-key",
            capabilities=["search", "analyze"],
            endpoints={
                "search": EndpointConfig(
                    url="https://api.exa.ai/search",
                    method="POST",
                    headers={"Authorization": "Bearer {api_key}"},
                    body_template='{"query": "{query}"}',
                    response_mapping={
                        "results": "$.results",
                        "title": "$.title",
                        "excerpt": "$.text",
                        "score": "$.score",
                    },
                )
            },
            sop={"analyze": "Analyze these results: {results}"},
        )
        add_researcher_to_config(config_file, "exa", exa_config)

        # Verify researcher was added
        config = Config.from_yaml(config_file)
        assert "exa" in config.research.researchers
        assert config.research.researchers["exa"].type == "http"

        # Step 2: Add a feed bound to the new researcher
        manager = FeedManager(config_file)
        manager.add_feed(
            name="ai-papers",
            researcher="exa",
            query="AI agent research 2025",
            keywords=["agent", "llm"],
        )

        # Verify feed was added
        feeds = manager.list_feeds()
        assert "ai-papers" in feeds
        assert feeds["ai-papers"].researcher == "exa"

        # Step 3: Run the feed (with mocked HTTP calls)
        mock_researcher = MagicMock()
        mock_researcher.search.return_value = [
            {"id": "1", "title": "AI Agents 2025", "excerpt": "New findings on AI agents", "score": 0.95},
            {"id": "2", "title": "LLM Planning", "excerpt": "Planning with language models", "score": 0.88},
        ]
        mock_researcher.analyze.return_value = {
            "summary": "AI agents are improving rapidly in 2025.",
            "sections": {"Key Findings": "Agents use better planning."},
            "raw": None,
        }

        runner = FeedRunner(config_file)
        result = runner.run_feed("ai-papers", researcher_override=mock_researcher)

        # Verify output
        assert result is not None
        assert result["feed_name"] == "ai-papers"
        assert len(result["results"]) > 0
        assert "summary" in result["analysis"]
        assert "failed" not in result

    def test_orphaned_feed_detected_after_researcher_removal(self, config_file):
        """If researcher is removed, feed becomes orphaned and is detected."""
        # Add researcher and feed
        r_config = ResearcherConfig(
            enabled=True,
            type="http",
            capabilities=["search"],
            sop={"search": "Search: {query}"},
        )
        add_researcher_to_config(config_file, "temp-r", r_config)
        manager = FeedManager(config_file)
        manager.add_feed(name="temp-feed", researcher="temp-r", query="test")

        # Simulate researcher removal by deleting from config
        with config_file.open("r") as f:
            data = yaml.safe_load(f)
        del data["research"]["researchers"]["temp-r"]
        config_file.write_text(yaml.dump(data))

        # Orphan should be detected
        orphans = manager.detect_orphans()
        assert "temp-feed" in orphans
