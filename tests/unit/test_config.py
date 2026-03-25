"""Tests for Config Pydantic model (TDD — written before implementation)."""
import os
from pathlib import Path

import pytest
import yaml

from khanote.models.config import (
    Config,
    FeedConfig,
    FeedFiltersConfig,
)


@pytest.fixture
def vault_dir(tmp_path):
    """A temporary directory that acts as an Obsidian vault."""
    return tmp_path


@pytest.fixture
def minimal_config_dict(vault_dir):
    """Minimal valid config.yaml dict."""
    return {
        "version": "0.1.0",
        "vault_path": str(vault_dir),
        "initialized_tools": ["claude-code"],
        "research": {
            "default": "perplexity",
            "researchers": {
                "perplexity": {"enabled": True, "api_key": "test-key"},
            },
        },
    }


class TestConfigVaultPath:
    def test_vault_path_must_exist(self, minimal_config_dict):
        minimal_config_dict["vault_path"] = "/nonexistent/path/to/vault"
        with pytest.raises(Exception):
            Config(**minimal_config_dict)

    def test_vault_path_is_expanded(self, vault_dir, minimal_config_dict):
        """Env var and ~ should be expanded."""
        os.environ["TEST_VAULT"] = str(vault_dir)
        minimal_config_dict["vault_path"] = "${TEST_VAULT}"
        config = Config(**minimal_config_dict)
        assert config.vault_path == vault_dir
        del os.environ["TEST_VAULT"]

    def test_vault_path_as_path_object(self, vault_dir, minimal_config_dict):
        config = Config(**minimal_config_dict)
        assert isinstance(config.vault_path, Path)


class TestConfigResearchers:
    def test_at_least_one_researcher_must_be_enabled(self, vault_dir, minimal_config_dict):
        minimal_config_dict["research"]["researchers"] = {
            "perplexity": {"enabled": False},
        }
        with pytest.raises(Exception):
            Config(**minimal_config_dict)

    def test_disabled_researcher_not_counted(self, vault_dir, minimal_config_dict):
        minimal_config_dict["research"]["researchers"] = {
            "perplexity": {"enabled": False},
            "arxiv": {"enabled": True},
        }
        config = Config(**minimal_config_dict)
        assert config.research.researchers["arxiv"].enabled is True

    def test_researcher_api_key_env_expansion(self, vault_dir, minimal_config_dict):
        os.environ["PERPLEXITY_API_KEY"] = "secret-key-123"
        minimal_config_dict["research"]["researchers"]["perplexity"]["api_key"] = "${PERPLEXITY_API_KEY}"
        config = Config(**minimal_config_dict)
        assert config.research.researchers["perplexity"].api_key == "secret-key-123"
        del os.environ["PERPLEXITY_API_KEY"]

    def test_researcher_status_defaults_to_stable(self, vault_dir, minimal_config_dict):
        config = Config(**minimal_config_dict)
        # notebooklm not present — when added, defaults
        minimal_config_dict["research"]["researchers"]["notebooklm"] = {
            "enabled": True,
            "status": "experimental",
        }
        config = Config(**minimal_config_dict)
        assert config.research.researchers["notebooklm"].status == "experimental"


class TestConfigInitializedTools:
    def test_initialized_tools_is_list(self, vault_dir, minimal_config_dict):
        config = Config(**minimal_config_dict)
        assert isinstance(config.initialized_tools, list)

    def test_initialized_tools_can_be_empty_on_first_init(self, vault_dir):
        """Before first init, initialized_tools may be empty."""
        data = {
            "version": "0.1.0",
            "vault_path": str(vault_dir),
            "initialized_tools": [],
            "research": {
                "default": "perplexity",
                "researchers": {"perplexity": {"enabled": True}},
            },
        }
        config = Config(**data)
        assert config.initialized_tools == []

    def test_known_tool_names_accepted(self, vault_dir, minimal_config_dict):
        minimal_config_dict["initialized_tools"] = [
            "claude-code", "cursor", "codex", "gemini-cli", "opencode"
        ]
        config = Config(**minimal_config_dict)
        assert len(config.initialized_tools) == 5


class TestResearcherConfigType:
    """T006: Tests for extended ResearcherConfig with type, capabilities, endpoints, sop."""

    def test_builtin_type_default(self, vault_dir, minimal_config_dict):
        config = Config(**minimal_config_dict)
        assert config.research.researchers["perplexity"].type == "builtin"

    def test_http_type_accepted(self, vault_dir, minimal_config_dict):
        minimal_config_dict["research"]["researchers"]["exa"] = {
            "enabled": True,
            "type": "http",
            "api_key": "test-key",
            "capabilities": ["search"],
            "endpoints": {
                "search": {
                    "url": "https://api.exa.ai/search",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer {api_key}"},
                    "body_template": '{"query": "{query}"}',
                    "response_mapping": {"results": "$.results"},
                }
            },
        }
        config = Config(**minimal_config_dict)
        assert config.research.researchers["exa"].type == "http"

    def test_http_type_requires_capabilities(self, vault_dir, minimal_config_dict):
        minimal_config_dict["research"]["researchers"]["exa"] = {
            "enabled": True,
            "type": "http",
            "api_key": "test-key",
            "capabilities": [],  # empty — invalid
        }
        with pytest.raises(Exception):
            Config(**minimal_config_dict)

    def test_http_type_capabilities_must_have_endpoint_or_sop(self, vault_dir, minimal_config_dict):
        minimal_config_dict["research"]["researchers"]["exa"] = {
            "enabled": True,
            "type": "http",
            "api_key": "test-key",
            "capabilities": ["search"],
            # no endpoints and no sop for "search" — invalid
        }
        with pytest.raises(Exception):
            Config(**minimal_config_dict)

    def test_sop_only_capability_accepted(self, vault_dir, minimal_config_dict):
        minimal_config_dict["research"]["researchers"]["sop_only"] = {
            "enabled": True,
            "type": "http",
            "capabilities": ["analyze"],
            "sop": {"analyze": "Analyze the following: {results}"},
        }
        config = Config(**minimal_config_dict)
        assert config.research.researchers["sop_only"].sop["analyze"] == "Analyze the following: {results}"

    def test_sop_fallback_with_endpoint(self, vault_dir, minimal_config_dict):
        """Both endpoint and SOP for same capability — both stored."""
        minimal_config_dict["research"]["researchers"]["dual"] = {
            "enabled": True,
            "type": "http",
            "capabilities": ["search"],
            "endpoints": {
                "search": {
                    "url": "https://example.com/search",
                    "method": "GET",
                    "headers": {},
                    "body_template": "",
                    "response_mapping": {"results": "$.items"},
                }
            },
            "sop": {"search": "Search for: {query}"},
        }
        config = Config(**minimal_config_dict)
        r = config.research.researchers["dual"]
        assert r.endpoints is not None
        assert r.sop is not None


class TestFeedConfig:
    """T006: Tests for FeedConfig model and Config.feeds section."""

    def test_feed_config_minimal(self):
        feed = FeedConfig(researcher="arxiv", query="large language models")
        assert feed.researcher == "arxiv"
        assert feed.query == "large language models"
        assert feed.frequency == "daily"
        assert feed.active is True

    def test_feed_config_with_filters(self):
        feed = FeedConfig(
            researcher="perplexity",
            query="AI startup funding",
            filters=FeedFiltersConfig(keywords=["startup", "funding"], max_age_days=7),
        )
        assert feed.filters.keywords == ["startup", "funding"]
        assert feed.filters.max_age_days == 7

    def test_feed_config_active_defaults_true(self):
        feed = FeedConfig(researcher="arxiv", query="test")
        assert feed.active is True

    def test_feed_config_frequency_must_be_daily(self):
        with pytest.raises(Exception):
            FeedConfig(researcher="arxiv", query="test", frequency="weekly")

    def test_feed_config_query_must_be_nonempty(self):
        with pytest.raises(Exception):
            FeedConfig(researcher="arxiv", query="")

    def test_config_feeds_section(self, vault_dir, minimal_config_dict):
        minimal_config_dict["feeds"] = {
            "llm-papers": {
                "researcher": "perplexity",
                "query": "large language models",
                "frequency": "daily",
                "active": True,
            }
        }
        config = Config(**minimal_config_dict)
        assert "llm-papers" in config.feeds
        assert config.feeds["llm-papers"].researcher == "perplexity"

    def test_config_feeds_empty_by_default(self, vault_dir, minimal_config_dict):
        config = Config(**minimal_config_dict)
        assert config.feeds == {}


class TestConfigFromYaml:
    def test_load_from_yaml_file(self, vault_dir, minimal_config_dict, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(minimal_config_dict))
        config = Config.from_yaml(config_file)
        assert config.vault_path == vault_dir

    def test_missing_yaml_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Config.from_yaml(tmp_path / "nonexistent.yaml")

    def test_version_field_present(self, vault_dir, minimal_config_dict):
        config = Config(**minimal_config_dict)
        assert config.version == "0.1.0"
