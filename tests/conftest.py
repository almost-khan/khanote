"""Shared pytest fixtures for khanote tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import yaml


@pytest.fixture
def vault_dir(tmp_path):
    """Temporary directory acting as an Obsidian vault."""
    return tmp_path


@pytest.fixture
def khanote_dir(vault_dir):
    """Temporary .khanote/ config directory inside vault."""
    d = vault_dir / ".khanote"
    d.mkdir()
    return d


@pytest.fixture
def config_yaml_data(vault_dir):
    """Minimal valid config.yaml dict with perplexity enabled."""
    return {
        "version": "0.1.0",
        "vault_path": str(vault_dir),
        "initialized_tools": ["claude-code"],
        "research": {
            "default": "perplexity",
            "researchers": {
                "perplexity": {"enabled": True, "api_key": "test-perplexity-key"},
            },
        },
    }


@pytest.fixture
def config_yaml_file(khanote_dir, config_yaml_data):
    """Write config.yaml to temp .khanote/ directory, return its Path."""
    config_file = khanote_dir / "config.yaml"
    config_file.write_text(yaml.dump(config_yaml_data))
    return config_file


@pytest.fixture
def mock_researcher():
    """Mock researcher conforming to the Researcher Protocol."""
    researcher = MagicMock()
    researcher.ingest.return_value = {"source_count": 1, "indexed_ids": ["id-1"]}
    researcher.analyze.return_value = {
        "summary": "Mock analysis summary.",
        "sections": {"Key Findings": "Finding 1\nFinding 2"},
        "raw": None,
    }
    researcher.generate.return_value = "Generated mock content"
    researcher.search.return_value = [
        {"id": "r1", "title": "Mock Result", "excerpt": "Excerpt text", "score": 0.95}
    ]
    return researcher


@pytest.fixture
def session_dir(vault_dir):
    """Create a valid session directory structure in vault."""
    session_path = vault_dir / "khanote" / "2026-03-22_AI-Agents-Overview"
    for subdir in ("sources", "research", "synthesis", "artifacts"):
        (session_path / subdir).mkdir(parents=True)
    return session_path


# ── Wizard / i18n fixtures ────────────────────────────────────────────────────

@pytest.fixture
def wizard_config_dir(tmp_path):
    """Temporary directory to use as khanote output/vault for wizard tests."""
    d = tmp_path / "khanote-research"
    d.mkdir()
    return d


@pytest.fixture
def clean_khanote_dir(tmp_path):
    """A tmp_path with NO existing .khanote/ — simulates clean install."""
    return tmp_path


@pytest.fixture
def existing_khanote_dir(tmp_path):
    """A tmp_path with an existing .khanote/config.yaml — simulates re-init."""
    kdir = tmp_path / ".khanote"
    kdir.mkdir()
    config = {
        "version": "0.1.0",
        "vault_path": str(tmp_path),
        "initialized_tools": ["claude-code"],
        "research": {"default": "arxiv", "researchers": {"arxiv": {"enabled": True}}},
    }
    (kdir / "config.yaml").write_text(yaml.dump(config))
    prefs = {"language": "en-US", "role": "developer", "interests": ["ai"]}
    (kdir / "preferences.yaml").write_text(yaml.dump(prefs))
    return tmp_path


@pytest.fixture
def mock_api_validation_success():
    """Patch validate_api_key to always return valid=True."""
    from khanote.validation.api_keys import ApiKeyValidationResult
    with patch(
        "khanote.validation.api_keys.validate_api_key",
        return_value=ApiKeyValidationResult("perplexity", "PERPLEXITY_API_KEY", valid=True),
    ) as mock:
        yield mock


@pytest.fixture
def mock_api_validation_failure():
    """Patch validate_api_key to always return valid=False."""
    from khanote.validation.api_keys import ApiKeyValidationResult
    with patch(
        "khanote.validation.api_keys.validate_api_key",
        return_value=ApiKeyValidationResult("perplexity", "PERPLEXITY_API_KEY", valid=False, error="401"),
    ) as mock:
        yield mock


@pytest.fixture
def sample_preferences_yaml(tmp_path):
    """Write a minimal preferences.yaml and return its path."""
    kdir = tmp_path / ".khanote"
    kdir.mkdir(exist_ok=True)
    prefs = {
        "language": "en-US",
        "role": "developer",
        "interests": ["ai", "web"],
        "depth": "summary",
        "expertise": "intermediate",
        "tone": "professional_briefing",
    }
    p = kdir / "preferences.yaml"
    p.write_text(yaml.dump(prefs))
    return p
