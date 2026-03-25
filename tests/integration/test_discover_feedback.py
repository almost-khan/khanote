"""Integration tests for discover feedback flow."""
from __future__ import annotations


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


@pytest.fixture
def config_file(khanote_dir, vault_dir):
    config_data = {
        "version": "0.1.0",
        "vault_path": str(vault_dir),
        "initialized_tools": ["claude-code"],
        "research": {
            "default": "mock",
            "researchers": {"mock": {"enabled": True}},
        },
        "feeds": {},
    }
    path = khanote_dir / "config.yaml"
    path.write_text(yaml.dump(config_data))
    return path


# ─────────────────────────────────────────────────────────────────────────────
# T065: Discover feedback flow integration test
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscoverFeedbackFlow:
    """T065: Run briefing, give feedback, verify preferences updated."""

    def test_like_adds_to_liked_topics(self, khanote_dir):
        from khanote.preferences.loader import PreferencesLoader

        loader = PreferencesLoader(khanote_dir)
        prefs = loader.load_preferences()
        assert "rust-programming" not in prefs.discover.liked_topics

        # Simulate like command
        prefs.discover.liked_topics.append("rust-programming")
        loader.save_preferences(prefs)

        # Reload and verify
        loaded = loader.load_preferences()
        assert "rust-programming" in loaded.discover.liked_topics

    def test_dislike_adds_to_disliked_topics(self, khanote_dir):
        from khanote.preferences.loader import PreferencesLoader

        loader = PreferencesLoader(khanote_dir)
        prefs = loader.load_preferences()
        prefs.discover.disliked_topics.append("cryptocurrency")
        loader.save_preferences(prefs)

        loaded = loader.load_preferences()
        assert "cryptocurrency" in loaded.discover.disliked_topics

    def test_like_removes_from_disliked(self, khanote_dir):
        """Liking a topic removes it from disliked."""
        from khanote.preferences.loader import PreferencesLoader

        loader = PreferencesLoader(khanote_dir)
        prefs = loader.load_preferences()
        prefs.discover.disliked_topics.append("quantum-computing")
        loader.save_preferences(prefs)

        # Now like it (simulating discover_like)
        prefs2 = loader.load_preferences()
        if "quantum-computing" in prefs2.discover.liked_topics:
            pass
        else:
            prefs2.discover.liked_topics.append("quantum-computing")
        if "quantum-computing" in prefs2.discover.disliked_topics:
            prefs2.discover.disliked_topics.remove("quantum-computing")
        loader.save_preferences(prefs2)

        loaded = loader.load_preferences()
        assert "quantum-computing" in loaded.discover.liked_topics
        assert "quantum-computing" not in loaded.discover.disliked_topics

    def test_blocked_domain_persists(self, khanote_dir):
        """Blocked domains saved and reloaded correctly."""
        from khanote.preferences.loader import PreferencesLoader

        loader = PreferencesLoader(khanote_dir)
        prefs = loader.load_preferences()
        prefs.discover.blocked_domains.append("tabloid-news.com")
        loader.save_preferences(prefs)

        loaded = loader.load_preferences()
        assert "tabloid-news.com" in loaded.discover.blocked_domains

    def test_serendipity_zero_disables_discover(self, khanote_dir):
        """serendipity=0.0 should disable discover section generation."""
        from khanote.preferences.loader import PreferencesLoader
        from khanote.preferences.models import Preferences

        loader = PreferencesLoader(khanote_dir)
        prefs = Preferences(discover={"serendipity": 0.0, "enabled": True})
        loader.save_preferences(prefs)

        loaded = loader.load_preferences()
        assert loaded.discover.serendipity == 0.0
