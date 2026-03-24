"""Tests for Feed model (TDD — written before implementation)."""
import pytest

from khanote.models.feed import Feed, FeedStatus


class TestFeedModel:
    """T008: Feed model field validation and defaults."""

    def test_feed_minimal(self):
        feed = Feed(name="llm-papers", researcher="arxiv", query="large language models")
        assert feed.name == "llm-papers"
        assert feed.researcher == "arxiv"
        assert feed.query == "large language models"
        assert feed.frequency == "daily"
        assert feed.active is True

    def test_feed_name_must_be_nonempty(self):
        with pytest.raises(Exception):
            Feed(name="", researcher="arxiv", query="test")

    def test_feed_query_must_be_nonempty(self):
        with pytest.raises(Exception):
            Feed(name="test-feed", researcher="arxiv", query="")

    def test_feed_frequency_must_be_daily(self):
        with pytest.raises(Exception):
            Feed(name="test-feed", researcher="arxiv", query="test", frequency="weekly")

    def test_feed_active_defaults_true(self):
        feed = Feed(name="test-feed", researcher="arxiv", query="test")
        assert feed.active is True

    def test_feed_with_keywords(self):
        feed = Feed(
            name="test-feed",
            researcher="arxiv",
            query="AI agents",
            keywords=["agent", "llm"],
        )
        assert feed.keywords == ["agent", "llm"]

    def test_feed_with_max_age_days(self):
        feed = Feed(name="test-feed", researcher="arxiv", query="test", max_age_days=7)
        assert feed.max_age_days == 7

    def test_feed_name_allows_hyphens(self):
        feed = Feed(name="ai-industry-news", researcher="perplexity", query="AI startups")
        assert feed.name == "ai-industry-news"

    def test_feed_name_rejects_spaces(self):
        with pytest.raises(Exception):
            Feed(name="my feed", researcher="arxiv", query="test")

    def test_feed_name_rejects_special_chars(self):
        with pytest.raises(Exception):
            Feed(name="feed@2024", researcher="arxiv", query="test")


class TestFeedStatus:
    """T008: Feed orphan detection and status."""

    def test_feed_is_not_orphan_when_researcher_present(self):
        feed = Feed(name="test-feed", researcher="arxiv", query="test")
        status = feed.check_orphan(available_researchers=["arxiv", "perplexity"])
        assert status == FeedStatus.ACTIVE

    def test_feed_is_orphan_when_researcher_missing(self):
        feed = Feed(name="test-feed", researcher="deleted-researcher", query="test")
        status = feed.check_orphan(available_researchers=["arxiv", "perplexity"])
        assert status == FeedStatus.ORPHANED

    def test_paused_feed_not_orphan(self):
        feed = Feed(name="test-feed", researcher="arxiv", query="test", active=False)
        status = feed.check_orphan(available_researchers=["arxiv"])
        assert status == FeedStatus.PAUSED

    def test_paused_feed_becomes_orphan_when_researcher_missing(self):
        feed = Feed(name="test-feed", researcher="deleted", query="test", active=False)
        status = feed.check_orphan(available_researchers=["arxiv"])
        assert status == FeedStatus.ORPHANED


class TestFeedManager:
    """T032: Feed manager — add, validate, clone feed in config.yaml."""

    def test_add_feed_to_config(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        manager.add_feed(
            name="llm-papers",
            researcher="perplexity",
            query="large language models",
        )
        feeds = manager.list_feeds()
        assert "llm-papers" in feeds

    def test_add_feed_validates_researcher_exists(self, tmp_path):
        from khanote.feeds.manager import FeedManager, FeedValidationError

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        with pytest.raises(FeedValidationError):
            manager.add_feed(
                name="bad-feed",
                researcher="nonexistent-researcher",
                query="test",
            )

    def test_add_feed_rejects_duplicate_names(self, tmp_path):
        from khanote.feeds.manager import FeedManager, FeedValidationError

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        manager.add_feed(name="llm-papers", researcher="perplexity", query="llms")
        with pytest.raises(FeedValidationError):
            manager.add_feed(name="llm-papers", researcher="perplexity", query="other")

    def test_clone_feed(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        manager.add_feed(
            name="llm-papers",
            researcher="perplexity",
            query="large language models",
            keywords=["llm", "transformer"],
        )
        manager.clone_feed(source_name="llm-papers", new_name="llm-papers-copy")
        feeds = manager.list_feeds()
        assert "llm-papers-copy" in feeds
        assert feeds["llm-papers-copy"].query == "large language models"

    def test_list_feeds_empty_initially(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        assert manager.list_feeds() == {}


def _make_config(tmp_path):
    """Helper: write a minimal config.yaml with perplexity researcher."""
    import yaml

    vault = tmp_path / "vault"
    vault.mkdir()
    data = {
        "version": "0.1.0",
        "vault_path": str(vault),
        "initialized_tools": [],
        "research": {
            "default": "perplexity",
            "researchers": {"perplexity": {"enabled": True, "api_key": "k"}},
        },
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(data))
    return config_file


class TestFeedManagerCRUD:
    """T039: Feed list/pause/resume/remove operations."""

    def test_pause_feed(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        manager.add_feed(name="my-feed", researcher="perplexity", query="test")
        manager.pause_feed("my-feed")
        feeds = manager.list_feeds()
        assert feeds["my-feed"].active is False

    def test_resume_feed(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        manager.add_feed(name="my-feed", researcher="perplexity", query="test")
        manager.pause_feed("my-feed")
        manager.resume_feed("my-feed")
        feeds = manager.list_feeds()
        assert feeds["my-feed"].active is True

    def test_remove_feed(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        manager.add_feed(name="my-feed", researcher="perplexity", query="test")
        manager.remove_feed("my-feed")
        feeds = manager.list_feeds()
        assert "my-feed" not in feeds

    def test_list_returns_all_feeds(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        manager.add_feed(name="feed-1", researcher="perplexity", query="AI")
        manager.add_feed(name="feed-2", researcher="perplexity", query="ML")
        feeds = manager.list_feeds()
        assert len(feeds) == 2
        assert "feed-1" in feeds
        assert "feed-2" in feeds

    def test_pause_nonexistent_feed_raises(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        with pytest.raises(KeyError):
            manager.pause_feed("nonexistent")

    def test_orphan_detection(self, tmp_path):
        from khanote.feeds.manager import FeedManager

        config_file = _make_config(tmp_path)
        manager = FeedManager(config_file)
        # Add a feed with a researcher that doesn't exist
        import yaml
        with config_file.open("r") as f:
            data = yaml.safe_load(f)
        data.setdefault("feeds", {})["orphan-feed"] = {
            "researcher": "deleted-researcher",
            "query": "test",
            "frequency": "daily",
            "active": True,
        }
        config_file.write_text(yaml.dump(data))
        orphans = manager.detect_orphans()
        assert "orphan-feed" in orphans


class TestFeedFromConfig:
    """T008: Feed construction from config dict."""

    def test_from_config_dict(self):
        data = {
            "name": "llm-papers",
            "researcher": "arxiv",
            "query": "large language models",
            "keywords": ["llm", "transformer"],
            "max_age_days": 7,
            "frequency": "daily",
            "active": True,
        }
        feed = Feed(**data)
        assert feed.name == "llm-papers"
        assert feed.keywords == ["llm", "transformer"]
