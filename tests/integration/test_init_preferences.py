"""Integration tests for init → preferences collection → start-my-day cold-start flow."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import yaml


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path


@pytest.fixture
def khanote_dir(vault_dir):
    d = vault_dir / ".khanote"
    d.mkdir()
    return d


# ─────────────────────────────────────────────────────────────────────────────
# T044: Init → start-my-day cold-start flow
# ─────────────────────────────────────────────────────────────────────────────

class TestInitPreferencesFlow:
    """T044: Init with role=developer → starter feeds created → briefing generates."""

    def test_select_starter_feeds_developer_ai(self, khanote_dir):
        """Developer + AI interest → starter feeds selected."""
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(khanote_dir)
        feeds = loader.select_starter_feeds(role="developer", interests=["ai"])
        assert len(feeds) > 0
        assert all("researcher" in f for f in feeds)

    def test_write_starter_feeds_to_config(self, khanote_dir, vault_dir):
        """Starter feeds written to config.yaml correctly."""
        from khanote.preferences.loader import PreferencesLoader

        # Setup minimal config
        config_file = khanote_dir / "config.yaml"
        config_data = {
            "version": "0.1.0",
            "vault_path": str(vault_dir),
            "initialized_tools": ["claude-code"],
            "research": {
                "default": "perplexity",
                "researchers": {"perplexity": {"enabled": True}},
            },
        }
        config_file.write_text(yaml.dump(config_data))

        loader = PreferencesLoader(khanote_dir)
        feeds = loader.select_starter_feeds(role="developer", interests=["ai"])
        loader.write_starter_feeds_to_config(config_file, feeds)

        # Verify feeds were written
        with config_file.open("r") as f:
            updated = yaml.safe_load(f)
        assert "feeds" in updated
        assert len(updated["feeds"]) > 0

    def test_starter_feeds_have_correct_fields(self, khanote_dir, vault_dir):
        """Each starter feed entry has required fields."""
        from khanote.preferences.loader import PreferencesLoader

        config_file = khanote_dir / "config.yaml"
        config_data = {
            "version": "0.1.0",
            "vault_path": str(vault_dir),
            "initialized_tools": ["claude-code"],
            "research": {
                "default": "perplexity",
                "researchers": {"perplexity": {"enabled": True}},
            },
        }
        config_file.write_text(yaml.dump(config_data))

        loader = PreferencesLoader(khanote_dir)
        feeds = loader.select_starter_feeds(role="pm", interests=["saas"])
        loader.write_starter_feeds_to_config(config_file, feeds)

        with config_file.open("r") as f:
            updated = yaml.safe_load(f)

        for name, feed in updated.get("feeds", {}).items():
            assert "researcher" in feed, f"Feed {name} missing researcher"
            assert "query" in feed, f"Feed {name} missing query"
            assert "frequency" in feed, f"Feed {name} missing frequency"

    def test_preferences_yaml_written_after_init(self, khanote_dir):
        """After writing preferences, file exists."""
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import Preferences

        loader = PreferencesLoader(khanote_dir)
        prefs = Preferences(language="en-US", role="developer", interests=["ai"])
        loader.save_preferences(prefs)

        assert (khanote_dir / "preferences.yaml").exists()

    def test_cold_start_briefing_after_init(self, khanote_dir, vault_dir):
        """After init with starter feeds, daily briefing runs without error."""
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import Preferences
        from khanote.briefing.daily import DailyBriefingOrchestrator

        # Write preferences
        prefs_loader = PreferencesLoader(khanote_dir)
        prefs = Preferences(role="developer", interests=["ai"])
        prefs_loader.save_preferences(prefs)

        # Setup config with feeds
        config_file = khanote_dir / "config.yaml"
        config_data = {
            "version": "0.1.0",
            "vault_path": str(vault_dir),
            "initialized_tools": ["claude-code"],
            "research": {
                "default": "mock",
                "researchers": {"mock": {"enabled": True}},
            },
            "feeds": {
                "ai-papers": {
                    "researcher": "mock",
                    "query": "artificial intelligence",
                    "frequency": "daily",
                    "active": True,
                }
            },
        }
        config_file.write_text(yaml.dump(config_data))

        # Run briefing
        mock_researcher = MagicMock()
        mock_researcher.search.return_value = [
            {"id": "r1", "title": "AI Advance", "excerpt": "New AI development", "score": 0.9}
        ]
        mock_researcher.analyze.return_value = {
            "summary": "AI summary",
            "sections": {},
            "raw": None,
        }

        orchestrator = DailyBriefingOrchestrator(config_file)
        with patch("khanote.briefing.daily.FeedRunner") as MockRunner:
            MockRunner.return_value.run_all_feeds.return_value = [
                {
                    "feed_name": "ai-papers",
                    "results": mock_researcher.search.return_value,
                    "analysis": mock_researcher.analyze.return_value,
                }
            ]
            result = orchestrator.run()

        assert result is not None
        path = result.get("path") if isinstance(result, dict) else result
        assert path is not None

    def test_api_key_declined_tracking(self, khanote_dir):
        """Declining API key increments counter in usage_stats."""
        from khanote.preferences.loader import PreferencesLoader

        loader = PreferencesLoader(khanote_dir)
        loader.increment_api_key_declined("newsapi")
        loader.increment_api_key_declined("newsapi")

        stats = loader.load_usage_stats()
        assert stats.api_key_declined.get("newsapi") == 2
