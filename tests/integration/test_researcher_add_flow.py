"""Integration tests for researcher add flow (T015, T028)."""
from __future__ import annotations


import pytest
import yaml

from khanote.models.config import Config, ResearcherConfig


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path


@pytest.fixture
def config_file(vault_dir, tmp_path):
    data = {
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
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(data), encoding="utf-8")
    return path


class TestAdHocPromotion:
    """T028: Ad-hoc → promote → persistent in config.yaml; decline → cleanup."""

    def test_promote_session_researcher_to_config(self, config_file, tmp_path):
        from khanote.cli.researcher_add import add_researcher_to_session, promote_session_researcher

        researcher = ResearcherConfig(
            enabled=True,
            type="http",
            api_key="exa-key",
            capabilities=["search"],
            sop={"search": "Search for: {query}"},
        )
        session_dir = tmp_path / "sessions" / "ai-agents"
        add_researcher_to_session(session_dir, "exa-session", researcher)
        promote_session_researcher(session_dir, config_file)

        config = Config.from_yaml(config_file)
        assert "exa-session" in config.research.researchers

    def test_promote_removes_session_file(self, config_file, tmp_path):
        from khanote.cli.researcher_add import add_researcher_to_session, promote_session_researcher

        researcher = ResearcherConfig(
            enabled=True,
            type="http",
            capabilities=["analyze"],
            sop={"analyze": "Analyze: {results}"},
        )
        session_dir = tmp_path / "sessions" / "test"
        add_researcher_to_session(session_dir, "temp", researcher)
        promote_session_researcher(session_dir, config_file)
        assert not (session_dir / "researcher.yaml").exists()

    def test_decline_cleans_up_session_file(self, tmp_path):
        from khanote.cli.researcher_add import add_researcher_to_session, discard_session_researcher

        researcher = ResearcherConfig(
            enabled=True,
            type="http",
            capabilities=["search"],
            sop={"search": "Search: {query}"},
        )
        session_dir = tmp_path / "sessions" / "declined"
        add_researcher_to_session(session_dir, "discarded", researcher)
        discard_session_researcher(session_dir)
        assert not (session_dir / "researcher.yaml").exists()


class TestResearcherAddFlow:
    """T015: Researcher add guided flow produces valid config entry."""

    def test_add_researcher_writes_to_config(self, config_file):
        from khanote.cli.researcher_add import add_researcher_to_config

        new_researcher = ResearcherConfig(
            enabled=True,
            type="http",
            api_key="exa-key",
            capabilities=["search"],
            endpoints={
                "search": {
                    "url": "https://api.exa.ai/search",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer {api_key}"},
                    "body_template": '{"query": "{query}"}',
                    "response_mapping": {"results": "$.results"},
                }
            },
        )
        add_researcher_to_config(
            config_path=config_file,
            name="exa",
            researcher_config=new_researcher,
        )
        config = Config.from_yaml(config_file)
        assert "exa" in config.research.researchers
        assert config.research.researchers["exa"].type == "http"
        assert config.research.researchers["exa"].capabilities == ["search"]

    def test_add_researcher_preserves_existing(self, config_file):
        from khanote.cli.researcher_add import add_researcher_to_config

        new_researcher = ResearcherConfig(
            enabled=True,
            type="http",
            capabilities=["search"],
            sop={"search": "Search for: {query}"},
        )
        add_researcher_to_config(config_file, "new_r", new_researcher)
        config = Config.from_yaml(config_file)
        assert "perplexity" in config.research.researchers
        assert "new_r" in config.research.researchers
