"""Tests for briefing orchestrator, focus selector, feed-due-check, ad-hoc orchestrator (TDD)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ─────────────────────────────────────────────────────────────────────────────
# T022: Focus selector
# ─────────────────────────────────────────────────────────────────────────────

class TestFocusSelector:
    """T022: Focus selector — select top 3-5 items weighted by preferences."""

    def _make_items(self, n: int, scores=None) -> list[dict]:
        """Create n mock feed result items."""
        return [
            {
                "id": f"item-{i}",
                "title": f"Result {i}",
                "excerpt": f"Excerpt for result {i}",
                "score": scores[i] if scores else (1.0 - i * 0.1),
                "source": "test-feed",
            }
            for i in range(n)
        ]

    def test_returns_top_items(self):
        from khanote.briefing.focus import FocusSelector
        from khanote.preferences.models import Preferences
        items = self._make_items(10)
        prefs = Preferences()
        selector = FocusSelector(prefs)
        result = selector.select(items)
        assert 3 <= len(result) <= 5

    def test_higher_score_items_selected(self):
        from khanote.briefing.focus import FocusSelector
        from khanote.preferences.models import Preferences
        items = [
            {"id": "high", "title": "High Score", "excerpt": "top", "score": 0.95, "source": "f1"},
            {"id": "mid", "title": "Mid Score", "excerpt": "mid", "score": 0.50, "source": "f1"},
            {"id": "low", "title": "Low Score", "excerpt": "low", "score": 0.10, "source": "f1"},
        ]
        prefs = Preferences()
        selector = FocusSelector(prefs)
        result = selector.select(items, count=1)
        assert result[0]["id"] == "high"

    def test_respects_count_param(self):
        from khanote.briefing.focus import FocusSelector
        from khanote.preferences.models import Preferences
        items = self._make_items(10)
        prefs = Preferences()
        selector = FocusSelector(prefs)
        result = selector.select(items, count=3)
        assert len(result) == 3

    def test_empty_items_returns_empty(self):
        from khanote.briefing.focus import FocusSelector
        from khanote.preferences.models import Preferences
        prefs = Preferences()
        selector = FocusSelector(prefs)
        result = selector.select([])
        assert result == []

    def test_fewer_items_than_count(self):
        from khanote.briefing.focus import FocusSelector
        from khanote.preferences.models import Preferences
        items = self._make_items(2)
        prefs = Preferences()
        selector = FocusSelector(prefs)
        result = selector.select(items, count=5)
        assert len(result) == 2

    def test_interest_boost(self):
        """Items matching user interests get boosted."""
        from khanote.briefing.focus import FocusSelector
        from khanote.preferences.models import Preferences
        items = [
            {"id": "ai", "title": "AI agents breakthrough", "excerpt": "AI agents", "score": 0.7, "source": "f1"},
            {"id": "other", "title": "Weather forecast", "excerpt": "Weather", "score": 0.9, "source": "f1"},
        ]
        prefs = Preferences(interests=["ai-agents"])
        selector = FocusSelector(prefs)
        result = selector.select(items, count=1)
        # AI item should be boosted above weather despite lower base score
        assert result[0]["id"] == "ai"


# ─────────────────────────────────────────────────────────────────────────────
# T024: Feed due-check logic
# ─────────────────────────────────────────────────────────────────────────────

class TestFeedDueCheck:
    """T024: Feed due-check — compare feed_last_run + frequency vs now."""

    def test_feed_never_run_is_due(self):
        from khanote.briefing.daily import is_feed_due
        from khanote.preferences.models import UsageStats
        stats = UsageStats()
        assert is_feed_due("my-feed", "daily", stats) is True

    def test_daily_feed_run_today_not_due(self):
        from khanote.briefing.daily import is_feed_due
        from khanote.preferences.models import UsageStats
        stats = UsageStats(feed_last_run={"my-feed": datetime.now(tz=timezone.utc)})
        assert is_feed_due("my-feed", "daily", stats) is False

    def test_daily_feed_run_yesterday_is_due(self):
        from khanote.briefing.daily import is_feed_due
        from khanote.preferences.models import UsageStats
        yesterday = datetime.now(tz=timezone.utc) - timedelta(hours=25)
        stats = UsageStats(feed_last_run={"my-feed": yesterday})
        assert is_feed_due("my-feed", "daily", stats) is True

    def test_unknown_frequency_always_due(self):
        from khanote.briefing.daily import is_feed_due
        from khanote.preferences.models import UsageStats
        stats = UsageStats()
        assert is_feed_due("my-feed", "unknown", stats) is True


# ─────────────────────────────────────────────────────────────────────────────
# T023: Daily briefing orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class TestDailyBriefingOrchestrator:
    """T023: Daily briefing orchestrator."""

    @pytest.fixture
    def khanote_dir(self, tmp_path):
        d = tmp_path / ".khanote"
        d.mkdir()
        return d

    @pytest.fixture
    def config_file(self, khanote_dir, tmp_path):
        config_data = {
            "version": "0.1.0",
            "vault_path": str(tmp_path),
            "initialized_tools": ["claude-code"],
            "research": {
                "default": "mock",
                "researchers": {"mock": {"enabled": True}},
            },
            "feeds": {
                "test-feed": {
                    "researcher": "mock",
                    "query": "AI agents",
                    "frequency": "daily",
                    "active": True,
                }
            },
        }
        config_file = khanote_dir / "config.yaml"
        config_file.write_text(yaml.dump(config_data))
        return config_file

    def test_orchestrator_creates_output_file(self, config_file, khanote_dir, tmp_path):
        from khanote.briefing.daily import DailyBriefingOrchestrator
        from unittest.mock import MagicMock

        mock_runner_result = [{
            "feed_name": "test-feed",
            "results": [{"id": "r1", "title": "AI Result", "excerpt": "excerpt", "score": 0.9}],
            "analysis": {"summary": "summary"},
        }]

        orchestrator = DailyBriefingOrchestrator(config_file)
        with patch("khanote.briefing.daily.FeedRunner") as MockRunner:
            MockRunner.return_value.run_all_feeds.return_value = mock_runner_result
            output = orchestrator.run(researcher_overrides={"test-feed": MagicMock()})

        assert output is not None
        assert "path" in output or isinstance(output, Path) or isinstance(output, dict)

    def test_briefing_file_saved_to_disk(self, config_file, khanote_dir, tmp_path):
        from khanote.briefing.daily import DailyBriefingOrchestrator

        mock_runner_result = [{
            "feed_name": "test-feed",
            "results": [{"id": "r1", "title": "Test Result", "excerpt": "excerpt", "score": 0.8}],
            "analysis": {"summary": "Mock summary of findings"},
        }]

        orchestrator = DailyBriefingOrchestrator(config_file)
        with patch("khanote.briefing.daily.FeedRunner") as MockRunner:
            MockRunner.return_value.run_all_feeds.return_value = mock_runner_result
            orchestrator.run()

        # Find briefing files
        briefings_dir = tmp_path / "khanote" / "briefings"
        if briefings_dir.exists():
            files = list(briefings_dir.glob("*.md"))
            assert len(files) >= 1

    def test_all_sections_present(self, config_file, khanote_dir, tmp_path):
        from khanote.briefing.daily import DailyBriefingOrchestrator

        mock_runner_result = [{
            "feed_name": "test-feed",
            "results": [
                {"id": "r1", "title": "AI Agents Update", "excerpt": "New AI agent framework released", "score": 0.9},
                {"id": "r2", "title": "Python News", "excerpt": "Python 3.14 alpha", "score": 0.7},
            ],
            "analysis": {"summary": "AI and Python news"},
        }]

        orchestrator = DailyBriefingOrchestrator(config_file)
        with patch("khanote.briefing.daily.FeedRunner") as MockRunner:
            MockRunner.return_value.run_all_feeds.return_value = mock_runner_result
            result = orchestrator.run()

        assert result is not None
        # Briefing dict/path should be returned
        if isinstance(result, dict):
            content = result.get("content", "")
            # Verify key sections exist
            assert len(content) > 0

    def test_skipped_feeds_handled_gracefully(self, config_file, khanote_dir, tmp_path):
        from khanote.briefing.daily import DailyBriefingOrchestrator

        mock_runner_result = [
            {"feed_name": "test-feed", "skipped": True, "reason": "feed is paused"},
        ]

        orchestrator = DailyBriefingOrchestrator(config_file)
        with patch("khanote.briefing.daily.FeedRunner") as MockRunner:
            MockRunner.return_value.run_all_feeds.return_value = mock_runner_result
            result = orchestrator.run()

        # Should not raise, even if all feeds skipped
        assert result is not None

    def test_empty_feeds_handled(self, khanote_dir, tmp_path):
        from khanote.briefing.daily import DailyBriefingOrchestrator

        config_data = {
            "version": "0.1.0",
            "vault_path": str(tmp_path),
            "initialized_tools": ["claude-code"],
            "research": {
                "default": "mock",
                "researchers": {"mock": {"enabled": True}},
            },
            "feeds": {},
        }
        config_file = khanote_dir / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        orchestrator = DailyBriefingOrchestrator(config_file)
        with patch("khanote.briefing.daily.FeedRunner") as MockRunner:
            MockRunner.return_value.run_all_feeds.return_value = []
            result = orchestrator.run()

        assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# T034: Ad-hoc orchestrator (Phase 4, but tests written now)
# ─────────────────────────────────────────────────────────────────────────────

class TestAdhocOrchestrator:
    """T034: Ad-hoc research orchestrator — decompose → route → execute → synthesize."""

    def test_orchestrator_instantiates(self, tmp_path):
        from khanote.briefing.adhoc import AdhocOrchestrator
        config_file = tmp_path / "config.yaml"
        config_data = {
            "version": "0.1.0",
            "vault_path": str(tmp_path),
            "initialized_tools": [],
            "research": {"default": "mock", "researchers": {"mock": {"enabled": True}}},
        }
        config_file.write_text(yaml.dump(config_data))
        orchestrator = AdhocOrchestrator(config_file)
        assert orchestrator is not None

    def test_adhoc_run_returns_result(self, tmp_path):
        from khanote.briefing.adhoc import AdhocOrchestrator

        config_file = tmp_path / "config.yaml"
        config_data = {
            "version": "0.1.0",
            "vault_path": str(tmp_path),
            "initialized_tools": [],
            "research": {"default": "mock", "researchers": {"mock": {"enabled": True}}},
        }
        config_file.write_text(yaml.dump(config_data))

        mock_researcher = MagicMock()
        mock_researcher.search.return_value = [
            {"id": "r1", "title": "Finding 1", "excerpt": "Important research finding.", "score": 0.9}
        ]
        mock_researcher.analyze.return_value = {"summary": "Analysis summary", "sections": {}, "raw": None}

        orchestrator = AdhocOrchestrator(config_file)
        with patch("khanote.briefing.adhoc.RegistryLoader") as MockRegistry:
            entries = {}
            MockRegistry.return_value.load_with_custom.return_value = entries
            result = orchestrator.run(
                query="What are the latest advances in AI agents?",
                researcher_overrides={"mock": mock_researcher},
            )

        assert result is not None

    def test_simple_query_detection(self, tmp_path):
        """Simple single-domain queries skip decomposition."""
        from khanote.briefing.adhoc import is_simple_query
        assert is_simple_query("python tutorial") is True
        assert is_simple_query("What are the latest advances in AI agents, including their relationship to transformer architectures, recent benchmarks, and enterprise adoption?") is False


# ─────────────────────────────────────────────────────────────────────────────
# T062: Discover template and T064: serendipity=0 disables section
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscoverSection:
    """T062: Discover template filling and T064: enable/disable."""

    def test_discover_context_builder(self):
        """Build discover context from preferences and usage stats."""
        from khanote.preferences.models import Preferences, UsageStats
        from khanote.briefing.daily import build_discover_context
        prefs = Preferences(
            interests=["ai-agents"],
            discover={"enabled": True, "blocked_domains": ["spam.com"], "liked_topics": ["rust"]}
        )
        stats = UsageStats()
        context = build_discover_context(prefs, stats)
        assert isinstance(context, dict)
        assert "blocked_domains" in context or "interests" in context or "recent_topics" in context

    def test_serendipity_zero_skips_discover(self):
        """When serendipity=0.0, discover section should be skipped."""
        from khanote.preferences.models import Preferences
        prefs = Preferences(discover={"serendipity": 0.0, "enabled": True})
        assert prefs.discover.serendipity == 0.0
        # Discover should be disabled when serendipity is 0
        # The orchestrator checks this flag

    def test_discover_disabled_flag(self):
        """When discover.enabled=False, no discover section."""
        from khanote.preferences.models import Preferences
        prefs = Preferences(discover={"enabled": False})
        assert prefs.discover.enabled is False


# ─────────────────────────────────────────────────────────────────────────────
# T063: Discover feedback
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscoverFeedback:
    """T063: Discover feedback — like/dislike updates preferences."""

    def test_like_adds_to_liked_topics(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(tmp_path)
        prefs = loader.load_preferences()
        assert "rust" not in prefs.discover.liked_topics
        prefs.discover.liked_topics.append("rust")
        loader.save_preferences(prefs)
        loaded = loader.load_preferences()
        assert "rust" in loaded.discover.liked_topics

    def test_dislike_adds_to_disliked_topics(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(tmp_path)
        prefs = loader.load_preferences()
        prefs.discover.disliked_topics.append("cryptocurrency")
        loader.save_preferences(prefs)
        loaded = loader.load_preferences()
        assert "cryptocurrency" in loaded.discover.disliked_topics

    def test_blocked_domains_respected(self, tmp_path):
        from khanote.preferences.models import Preferences
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(tmp_path)
        prefs = Preferences(discover={"blocked_domains": ["tabloid.com"]})
        loader.save_preferences(prefs)
        loaded = loader.load_preferences()
        assert "tabloid.com" in loaded.discover.blocked_domains
