"""Tests for Config Pydantic model (TDD — written before implementation)."""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from khanote.models.config import (
    Config,
    ResearchConfig,
    ResearcherConfig,
    DomainConfig,
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
