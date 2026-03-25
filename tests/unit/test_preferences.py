"""Tests for Preferences, UsageStats models, preferences loader, personalization builder (TDD)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# T008: Preferences model
# ─────────────────────────────────────────────────────────────────────────────

class TestPreferencesModel:
    """T008: Preferences Pydantic model validation and defaults."""

    def test_defaults(self):
        from khanote.preferences.models import Preferences
        p = Preferences()
        assert p.language == "en-US"
        assert p.role == "mixed"
        assert p.interests == []
        assert p.depth == "summary"
        assert p.expertise == "intermediate"
        assert p.tone == "professional_briefing"

    def test_discover_defaults(self):
        from khanote.preferences.models import Preferences
        p = Preferences()
        assert p.discover.enabled is True
        assert p.discover.serendipity == 0.15
        assert p.discover.count == 2

    def test_valid_language_bcp47(self):
        from khanote.preferences.models import Preferences
        p = Preferences(language="zh-CN")
        assert p.language == "zh-CN"

    def test_invalid_language_raises(self):
        from khanote.preferences.models import Preferences
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Preferences(language="not-a-valid-bcp47-tag!!!")

    def test_valid_role(self):
        from khanote.preferences.models import Preferences
        for role in ("developer", "pm", "researcher", "mixed"):
            p = Preferences(role=role)
            assert p.role == role

    def test_invalid_role_raises(self):
        from khanote.preferences.models import Preferences
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Preferences(role="unknown_role")

    def test_valid_depth(self):
        from khanote.preferences.models import Preferences
        for depth in ("headlines", "summary", "detailed", "deep_dive"):
            p = Preferences(depth=depth)
            assert p.depth == depth

    def test_invalid_depth_raises(self):
        from khanote.preferences.models import Preferences
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Preferences(depth="ultra")

    def test_valid_expertise(self):
        from khanote.preferences.models import Preferences
        for exp in ("beginner", "intermediate", "expert"):
            p = Preferences(expertise=exp)
            assert p.expertise == exp

    def test_valid_tone(self):
        from khanote.preferences.models import Preferences
        for tone in ("formal_report", "professional_briefing", "casual_notes"):
            p = Preferences(tone=tone)
            assert p.tone == tone

    def test_serendipity_range_valid(self):
        from khanote.preferences.models import Preferences
        p = Preferences(discover={"serendipity": 0.5})
        assert p.discover.serendipity == 0.5

    def test_serendipity_out_of_range_raises(self):
        from khanote.preferences.models import Preferences
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Preferences(discover={"serendipity": 1.5})

    def test_serendipity_zero_disables(self):
        from khanote.preferences.models import Preferences
        p = Preferences(discover={"serendipity": 0.0})
        assert p.discover.serendipity == 0.0

    def test_strategy_weights_sum_to_one(self):
        from khanote.preferences.models import Preferences
        p = Preferences(discover={"strategy_weights": {"adjacent": 0.4, "trending": 0.3, "random": 0.2, "curated": 0.1}})
        total = sum(p.discover.strategy_weights.values())
        assert abs(total - 1.0) < 1e-9

    def test_interests_list(self):
        from khanote.preferences.models import Preferences
        p = Preferences(interests=["ai-agents", "strength-training"])
        assert "ai-agents" in p.interests

    def test_discover_blocked_domains(self):
        from khanote.preferences.models import Preferences
        p = Preferences(discover={"blocked_domains": ["example.com"]})
        assert "example.com" in p.discover.blocked_domains

    def test_liked_disliked_topics(self):
        from khanote.preferences.models import Preferences
        p = Preferences(discover={"liked_topics": ["rust"], "disliked_topics": ["crypto"]})
        assert "rust" in p.discover.liked_topics
        assert "crypto" in p.discover.disliked_topics


# ─────────────────────────────────────────────────────────────────────────────
# T009: UsageStats model
# ─────────────────────────────────────────────────────────────────────────────

class TestUsageStatsModel:
    """T009: UsageStats Pydantic model."""

    def test_empty_defaults(self):
        from khanote.preferences.models import UsageStats
        us = UsageStats()
        assert us.topics == []
        assert us.researchers == []
        assert us.queries == []
        assert us.feed_last_run == {}
        assert us.api_key_declined == {}

    def test_topic_stat_fields(self):
        from khanote.preferences.models import UsageStats, TopicStat
        ts = TopicStat(name="ai", saved=3, skipped=1, last_seen=date.today())
        us = UsageStats(topics=[ts])
        assert us.topics[0].name == "ai"
        assert us.topics[0].saved == 3

    def test_researcher_stat_fields(self):
        from khanote.preferences.models import UsageStats, ResearcherStat
        rs = ResearcherStat(name="perplexity", calls=10, last_used=date.today())
        us = UsageStats(researchers=[rs])
        assert us.researchers[0].calls == 10

    def test_query_record_fields(self):
        from khanote.preferences.models import UsageStats, QueryRecord
        qr = QueryRecord(text="ai agents", date=date.today(), researchers=["arxiv"])
        us = UsageStats(queries=[qr])
        assert us.queries[0].text == "ai agents"
        assert "arxiv" in us.queries[0].researchers

    def test_feed_last_run_dict(self):
        from khanote.preferences.models import UsageStats
        now = datetime.now(tz=timezone.utc)
        us = UsageStats(feed_last_run={"ai-papers": now})
        assert us.feed_last_run["ai-papers"] == now

    def test_api_key_declined_dict(self):
        from khanote.preferences.models import UsageStats
        us = UsageStats(api_key_declined={"newsapi": 2})
        assert us.api_key_declined["newsapi"] == 2

    def test_prune_old_topics(self):
        """90-day pruning: topics older than 90 days removed on prune()."""
        from khanote.preferences.models import UsageStats, TopicStat
        old_date = date.today() - timedelta(days=91)
        recent_date = date.today() - timedelta(days=10)
        us = UsageStats(topics=[
            TopicStat(name="old-topic", saved=1, skipped=0, last_seen=old_date),
            TopicStat(name="new-topic", saved=2, skipped=0, last_seen=recent_date),
        ])
        us.prune()
        assert len(us.topics) == 1
        assert us.topics[0].name == "new-topic"

    def test_prune_old_queries(self):
        """Queries older than 90 days are pruned."""
        from khanote.preferences.models import UsageStats, QueryRecord
        old_date = date.today() - timedelta(days=95)
        recent_date = date.today() - timedelta(days=5)
        us = UsageStats(queries=[
            QueryRecord(text="old query", date=old_date, researchers=[]),
            QueryRecord(text="new query", date=recent_date, researchers=[]),
        ])
        us.prune()
        assert len(us.queries) == 1
        assert us.queries[0].text == "new query"

    def test_prune_preserves_recent(self):
        from khanote.preferences.models import UsageStats, TopicStat
        us = UsageStats(topics=[
            TopicStat(name="topic", saved=1, skipped=0, last_seen=date.today()),
        ])
        us.prune()
        assert len(us.topics) == 1


# ─────────────────────────────────────────────────────────────────────────────
# T010: Preferences loader
# ─────────────────────────────────────────────────────────────────────────────

class TestPreferencesLoader:
    """T010: preferences loader — read/write preferences.yaml and usage_stats.yaml."""

    def test_load_creates_defaults_if_missing(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(tmp_path)
        prefs = loader.load_preferences()
        from khanote.preferences.models import Preferences
        assert isinstance(prefs, Preferences)
        assert prefs.language == "en-US"

    def test_save_and_load_roundtrip(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import Preferences
        loader = PreferencesLoader(tmp_path)
        prefs = Preferences(language="zh-CN", role="developer", interests=["ai"])
        loader.save_preferences(prefs)
        loaded = loader.load_preferences()
        assert loaded.language == "zh-CN"
        assert loaded.role == "developer"
        assert "ai" in loaded.interests

    def test_preferences_yaml_written_to_disk(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import Preferences
        loader = PreferencesLoader(tmp_path)
        loader.save_preferences(Preferences(language="fr-FR"))
        assert (tmp_path / "preferences.yaml").exists()

    def test_load_usage_stats_creates_defaults_if_missing(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import UsageStats
        loader = PreferencesLoader(tmp_path)
        stats = loader.load_usage_stats()
        assert isinstance(stats, UsageStats)
        assert stats.topics == []

    def test_save_and_load_usage_stats_roundtrip(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import UsageStats, TopicStat
        loader = PreferencesLoader(tmp_path)
        stats = UsageStats()
        stats.topics.append(TopicStat(name="ai", saved=1, skipped=0, last_seen=date.today()))
        loader.save_usage_stats(stats)
        loaded = loader.load_usage_stats()
        assert len(loaded.topics) == 1
        assert loaded.topics[0].name == "ai"

    def test_usage_stats_yaml_written_to_disk(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import UsageStats
        loader = PreferencesLoader(tmp_path)
        loader.save_usage_stats(UsageStats())
        assert (tmp_path / "usage_stats.yaml").exists()


# ─────────────────────────────────────────────────────────────────────────────
# T011: Personalization block builder
# ─────────────────────────────────────────────────────────────────────────────

class TestPersonalizationBuilder:
    """T011: personalization block builder."""

    def test_builds_non_empty_block(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences()
        block = build_personalization_block(p)
        assert isinstance(block, str)
        assert len(block) > 0

    def test_depth_headlines_instructions(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences(depth="headlines")
        block = build_personalization_block(p)
        assert "headline" in block.lower() or "brief" in block.lower() or "concise" in block.lower()

    def test_depth_deep_dive_instructions(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences(depth="deep_dive")
        block = build_personalization_block(p)
        assert "deep" in block.lower() or "thorough" in block.lower() or "comprehensive" in block.lower()

    def test_expertise_beginner_instructions(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences(expertise="beginner")
        block = build_personalization_block(p)
        assert "beginner" in block.lower() or "simple" in block.lower() or "jargon" in block.lower()

    def test_expertise_expert_instructions(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences(expertise="expert")
        block = build_personalization_block(p)
        assert "expert" in block.lower() or "technical" in block.lower() or "advanced" in block.lower()

    def test_tone_formal_report_instructions(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences(tone="formal_report")
        block = build_personalization_block(p)
        assert "formal" in block.lower() or "report" in block.lower()

    def test_tone_casual_notes_instructions(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences(tone="casual_notes")
        block = build_personalization_block(p)
        assert "casual" in block.lower() or "conversational" in block.lower()

    def test_language_included(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p = Preferences(language="zh-CN")
        block = build_personalization_block(p)
        assert "zh-CN" in block or "Chinese" in block.lower() or "language" in block.lower()

    def test_different_prefs_produce_different_blocks(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        p1 = Preferences(depth="headlines", expertise="beginner")
        p2 = Preferences(depth="deep_dive", expertise="expert")
        assert build_personalization_block(p1) != build_personalization_block(p2)


# ─────────────────────────────────────────────────────────────────────────────
# T042 / T043: Starter feed loading and init preference collection
# ─────────────────────────────────────────────────────────────────────────────

class TestStarterFeedLoading:
    """T042: Starter feed template loading."""

    def test_load_starter_feeds_yaml_exists(self):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader.__new__(PreferencesLoader)
        feeds = loader._load_starter_feeds_yaml()
        assert "developer" in feeds
        assert "pm" in feeds
        assert "researcher" in feeds
        assert "mixed" in feeds

    def test_developer_ai_feeds(self):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader.__new__(PreferencesLoader)
        feeds = loader._load_starter_feeds_yaml()
        dev_ai = feeds["developer"]["ai"]
        assert len(dev_ai) > 0
        assert any(f["researcher"] == "arxiv" for f in dev_ai)

    def test_feed_has_required_fields(self):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader.__new__(PreferencesLoader)
        feeds = loader._load_starter_feeds_yaml()
        feed = feeds["developer"]["ai"][0]
        for field in ("name", "researcher", "query", "frequency"):
            assert field in feed, f"Missing field: {field}"

    def test_select_feeds_by_role_interests(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(tmp_path)
        selected = loader.select_starter_feeds(role="developer", interests=["ai"])
        assert len(selected) > 0
        assert all("researcher" in f for f in selected)

    def test_select_feeds_mixed_role_multiple_interests(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(tmp_path)
        selected = loader.select_starter_feeds(role="mixed", interests=["ai", "health"])
        assert len(selected) > 0

    def test_select_feeds_unknown_interest_uses_general(self, tmp_path):
        from khanote.preferences.loader import PreferencesLoader
        loader = PreferencesLoader(tmp_path)
        selected = loader.select_starter_feeds(role="developer", interests=["unknown-interest-xyz"])
        # Should fall back to general feeds or return empty gracefully
        assert isinstance(selected, list)
