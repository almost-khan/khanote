"""Integration tests for feed add and management flows (T033, T040)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from khanote.models.config import Config


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
        "initialized_tools": [],
        "research": {
            "default": "perplexity",
            "researchers": {
                "perplexity": {"enabled": True, "api_key": "key"},
                "arxiv": {"enabled": True},
            },
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(data))
    return path


class TestFeedAddFlow:
    """T033: Guided flow produces valid feed config."""

    def test_add_feed_writes_to_config(self, config_file):
        from khanote.feeds.manager import FeedManager

        manager = FeedManager(config_file)
        manager.add_feed(
            name="daily-llm",
            researcher="perplexity",
            query="large language models",
            keywords=["llm", "gpt"],
            max_age_days=7,
        )
        config = Config.from_yaml(config_file)
        assert "daily-llm" in config.feeds
        feed = config.feeds["daily-llm"]
        assert feed.researcher == "perplexity"
        assert feed.query == "large language models"
        assert feed.active is True

    def test_add_feed_preserves_existing_feeds(self, config_file):
        from khanote.feeds.manager import FeedManager

        manager = FeedManager(config_file)
        manager.add_feed(name="feed-1", researcher="perplexity", query="AI")
        manager.add_feed(name="feed-2", researcher="arxiv", query="ML")
        config = Config.from_yaml(config_file)
        assert "feed-1" in config.feeds
        assert "feed-2" in config.feeds

    def test_feed_active_by_default(self, config_file):
        from khanote.feeds.manager import FeedManager

        manager = FeedManager(config_file)
        manager.add_feed(name="test-feed", researcher="arxiv", query="test")
        config = Config.from_yaml(config_file)
        assert config.feeds["test-feed"].active is True


class TestFeedManagement:
    """T040: CLI commands for list/pause/resume/remove."""

    def test_pause_and_resume_via_manager(self, config_file):
        from khanote.feeds.manager import FeedManager

        manager = FeedManager(config_file)
        manager.add_feed(name="test-feed", researcher="perplexity", query="AI")
        manager.pause_feed("test-feed")
        assert manager.list_feeds()["test-feed"].active is False
        manager.resume_feed("test-feed")
        assert manager.list_feeds()["test-feed"].active is True

    def test_remove_via_manager(self, config_file):
        from khanote.feeds.manager import FeedManager

        manager = FeedManager(config_file)
        manager.add_feed(name="to-remove", researcher="perplexity", query="test")
        manager.remove_feed("to-remove")
        assert "to-remove" not in manager.list_feeds()

    def test_orphan_detection_reports_missing_researcher(self, config_file):
        from khanote.feeds.manager import FeedManager
        import yaml

        with config_file.open("r") as f:
            data = yaml.safe_load(f)
        data.setdefault("feeds", {})["orphan"] = {
            "researcher": "gone",
            "query": "test",
            "frequency": "daily",
            "active": True,
        }
        config_file.write_text(yaml.dump(data))

        manager = FeedManager(config_file)
        orphans = manager.detect_orphans()
        assert "orphan" in orphans


class TestFeedRunner:
    """T037: Feed runner loads researcher, calls search + analyze."""

    def test_feed_runner_returns_results(self, config_file):
        from khanote.feeds.manager import FeedManager
        from khanote.feeds.runner import FeedRunner

        manager = FeedManager(config_file)
        manager.add_feed(name="test-feed", researcher="perplexity", query="AI agents")

        mock_researcher = MagicMock()
        mock_researcher.search.return_value = [
            {"id": "1", "title": "Paper 1", "excerpt": "About AI", "score": 0.9}
        ]
        mock_researcher.analyze.return_value = {
            "summary": "AI agents are emerging",
            "sections": {},
            "raw": None,
        }

        runner = FeedRunner(config_file)
        result = runner.run_feed("test-feed", researcher_override=mock_researcher)

        assert result["feed_name"] == "test-feed"
        assert isinstance(result["results"], list)
        assert "analysis" in result

    def test_feed_runner_skips_inactive_feeds(self, config_file):
        from khanote.feeds.manager import FeedManager
        from khanote.feeds.runner import FeedRunner

        manager = FeedManager(config_file)
        manager.add_feed(name="paused-feed", researcher="perplexity", query="test")
        manager.pause_feed("paused-feed")

        runner = FeedRunner(config_file)
        result = runner.run_feed("paused-feed")
        assert result is None or result.get("skipped") is True
