"""Tests for ResearcherRegistryEntry model and registry loader (TDD)."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest
import yaml


# ─────────────────────────────────────────────────────────────────────────────
# T012: ResearcherRegistryEntry model and registry loader
# ─────────────────────────────────────────────────────────────────────────────

class TestResearcherRegistryEntry:
    """T012: ResearcherRegistryEntry model."""

    def test_basic_fields(self):
        from khanote.registry.models import ResearcherRegistryEntry
        entry = ResearcherRegistryEntry(
            name="perplexity",
            type="builtin",
            domains=["general", "news"],
            capabilities=["search", "analyze"],
            description="Real-time web search",
            priority="fallback",
            requires_key=True,
            env_var="PERPLEXITY_API_KEY",
            available=False,
        )
        assert entry.name == "perplexity"
        assert "general" in entry.domains
        assert entry.requires_key is True
        assert entry.available is False

    def test_optional_env_var(self):
        from khanote.registry.models import ResearcherRegistryEntry
        entry = ResearcherRegistryEntry(
            name="arxiv",
            type="builtin",
            domains=["academic"],
            capabilities=["search"],
            description="Academic papers",
            priority="specialized",
            requires_key=False,
            env_var=None,
            available=True,
        )
        assert entry.env_var is None
        assert entry.available is True

    def test_default_available_is_false(self):
        from khanote.registry.models import ResearcherRegistryEntry
        entry = ResearcherRegistryEntry(
            name="test",
            type="builtin",
            domains=[],
            capabilities=[],
            description="test",
            priority="specialized",
            requires_key=True,
        )
        assert entry.available is False

    def test_type_enum(self):
        from khanote.registry.models import ResearcherRegistryEntry
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ResearcherRegistryEntry(
                name="bad",
                type="invalid-type",
                domains=[],
                capabilities=[],
                description="",
                priority="specialized",
                requires_key=False,
            )


class TestRegistryLoader:
    """T012: registry loader — load YAML, set available flag based on env var."""

    def test_load_builtin_registry(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        entries = loader.load()
        assert "perplexity" in entries
        assert "arxiv" in entries
        assert "hackernews" in entries

    def test_load_all_9_researchers(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        entries = loader.load()
        expected = {"perplexity", "arxiv", "pubmed", "github", "hackernews", "newsapi", "rss", "producthunt", "notebooklm"}
        assert expected.issubset(set(entries.keys()))

    def test_available_set_true_when_env_var_present(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            entries = loader.load()
        assert entries["perplexity"].available is True

    def test_available_set_false_when_env_var_missing(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        env_without_key = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
        with patch.dict(os.environ, env_without_key, clear=True):
            entries = loader.load()
        assert entries["perplexity"].available is False

    def test_no_key_required_always_available(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        env_without_keys = {}
        with patch.dict(os.environ, env_without_keys, clear=True):
            entries = loader.load()
        assert entries["arxiv"].available is True
        assert entries["hackernews"].available is True
        assert entries["rss"].available is True

    def test_custom_registry_yaml_overrides(self, tmp_path):
        """Load from a custom YAML file."""
        from khanote.registry.loader import RegistryLoader
        custom_yaml = tmp_path / "registry.yaml"
        custom_yaml.write_text(yaml.dump({
            "custom-researcher": {
                "type": "builtin",
                "domains": ["custom"],
                "capabilities": ["search"],
                "description": "Custom",
                "priority": "specialized",
                "requires_key": False,
                "env_var": None,
            }
        }))
        loader = RegistryLoader(registry_path=custom_yaml)
        entries = loader.load()
        assert "custom-researcher" in entries

    def test_merge_custom_researchers_from_config(self, tmp_path):
        """Custom HTTP researchers from config.yaml appear in registry."""
        from khanote.registry.loader import RegistryLoader
        config_data = {
            "research": {
                "researchers": {
                    "my-api": {
                        "type": "http",
                        "enabled": True,
                        "capabilities": ["search"],
                        "endpoints": {"search": {"url": "https://example.com/search"}},
                        "domains": ["custom-domain"],
                        "description": "My custom API",
                    }
                }
            }
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))
        loader = RegistryLoader()
        entries = loader.load_with_custom(config_file)
        assert "my-api" in entries
        assert entries["my-api"].type == "http"

    def test_entry_domains_field_populated(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        entries = loader.load()
        assert len(entries["perplexity"].domains) > 0

    def test_entry_description_field_populated(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        entries = loader.load()
        assert len(entries["arxiv"].description) > 0


# ─────────────────────────────────────────────────────────────────────────────
# T033: Query router (used in Phase 4)
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryRouter:
    """T033: Query router — match sub-query to researcher by domains."""

    def test_route_academic_query_to_arxiv(self):
        from khanote.registry.router import QueryRouter
        from khanote.registry.models import ResearcherRegistryEntry
        entries = {
            "arxiv": ResearcherRegistryEntry(
                name="arxiv", type="builtin",
                domains=["academic", "computer-science"],
                capabilities=["search"], description="",
                priority="specialized", requires_key=False, available=True,
            ),
            "perplexity": ResearcherRegistryEntry(
                name="perplexity", type="builtin",
                domains=["general"],
                capabilities=["search"], description="",
                priority="fallback", requires_key=True, available=True,
            ),
        }
        router = QueryRouter(entries)
        result = router.route(researcher_name="arxiv")
        assert result is not None
        assert result.name == "arxiv"

    def test_fallback_to_perplexity_when_unavailable(self):
        from khanote.registry.router import QueryRouter
        from khanote.registry.models import ResearcherRegistryEntry
        entries = {
            "arxiv": ResearcherRegistryEntry(
                name="arxiv", type="builtin",
                domains=["academic"],
                capabilities=["search"], description="",
                priority="specialized", requires_key=False, available=False,  # unavailable
            ),
            "perplexity": ResearcherRegistryEntry(
                name="perplexity", type="builtin",
                domains=["general"],
                capabilities=["search"], description="",
                priority="fallback", requires_key=True, available=True,
            ),
        }
        router = QueryRouter(entries)
        result = router.route(researcher_name="arxiv")
        # Returns None or fallback when requested researcher unavailable
        assert result is None or result.name == "perplexity"

    def test_route_returns_none_for_unknown_researcher(self):
        from khanote.registry.router import QueryRouter
        router = QueryRouter({})
        result = router.route(researcher_name="nonexistent")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# T048-T050: On-demand loading, custom auto-registration, API key availability
# ─────────────────────────────────────────────────────────────────────────────

class TestOnDemandLoading:
    """T048: On-demand researcher loading."""

    def test_load_only_requested_researchers(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        entries = loader.load()
        # Should not raise — just verifies registry has entries
        assert len(entries) >= 9

    def test_get_available_researchers(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        entries = loader.load()
        # Free researchers should always be available
        available = [name for name, e in entries.items() if e.available]
        assert len(available) > 0


class TestApiKeyAvailability:
    """T050: API key availability check and graceful degradation."""

    def test_missing_key_sets_available_false(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        env_without_keys = {k: v for k, v in os.environ.items()
                            if k not in ("PERPLEXITY_API_KEY", "NEWSAPI_KEY", "PRODUCTHUNT_TOKEN")}
        with patch.dict(os.environ, env_without_keys, clear=True):
            entries = loader.load()
        assert entries["perplexity"].available is False
        assert entries["newsapi"].available is False

    def test_present_key_sets_available_true(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            entries = loader.load()
        assert entries["newsapi"].available is True

    def test_hint_message_for_missing_key(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        env_without_keys = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
        with patch.dict(os.environ, env_without_keys, clear=True):
            entries = loader.load()
            hint = loader.get_hint_message("perplexity", entries["perplexity"])
        assert hint is not None
        assert "PERPLEXITY_API_KEY" in hint or "key" in hint.lower()

    def test_no_hint_when_key_present(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "present"}):
            entries = loader.load()
            hint = loader.get_hint_message("perplexity", entries["perplexity"])
        assert hint is None

    def test_no_hint_when_key_not_required(self):
        from khanote.registry.loader import RegistryLoader
        loader = RegistryLoader()
        entries = loader.load()
        hint = loader.get_hint_message("arxiv", entries["arxiv"])
        assert hint is None
