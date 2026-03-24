"""Tests for ConfigResearcher (TDD — T013, T014, T022, T027)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from khanote.models.config import EndpointConfig, ResearcherConfig
from khanote.researchers.config_researcher import ConfigResearcher
from khanote.researchers.base import ResearcherError


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def search_endpoint():
    return EndpointConfig(
        url="https://api.example.com/search",
        method="POST",
        headers={"Authorization": "Bearer {api_key}"},
        body_template='{"query": "{query}"}',
        response_mapping={
            "results": "$.results",
            "title": "$.title",
            "excerpt": "$.text",
            "score": "$.score",
        },
    )


@pytest.fixture
def search_only_config(search_endpoint):
    return ResearcherConfig(
        enabled=True,
        type="http",
        api_key="test-key-123",
        capabilities=["search"],
        endpoints={"search": search_endpoint},
    )


@pytest.fixture
def sop_only_config():
    return ResearcherConfig(
        enabled=True,
        type="http",
        capabilities=["analyze"],
        sop={"analyze": "Analyze the following results: {results}"},
    )


@pytest.fixture
def search_with_sop_analyze(search_endpoint):
    return ResearcherConfig(
        enabled=True,
        type="http",
        api_key="key",
        capabilities=["search", "analyze"],
        endpoints={"search": search_endpoint},
        sop={"analyze": "Analyze: {results}"},
    )


# ── T013: ConfigResearcher basic HTTP endpoint calling ────────────────────────

class TestConfigResearcherSearch:
    def test_search_calls_http_endpoint(self, search_only_config):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"title": "Paper 1", "text": "Abstract 1", "score": 0.9},
                {"title": "Paper 2", "text": "Abstract 2", "score": 0.8},
            ]
        }
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client.request.return_value = mock_response

            researcher = ConfigResearcher("exa", search_only_config)
            results = researcher.search("large language models")

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["title"] == "Paper 1"

    def test_search_returns_expected_schema(self, search_only_config):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [{"title": "T", "text": "E", "score": 0.7}]
        }
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client.request.return_value = mock_response

            researcher = ConfigResearcher("exa", search_only_config)
            results = researcher.search("test")

        for r in results:
            assert "id" in r
            assert "title" in r
            assert "excerpt" in r
            assert "score" in r

    def test_search_raises_on_http_error(self, search_only_config):
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client.request.return_value = mock_response

            researcher = ConfigResearcher("exa", search_only_config)
            with pytest.raises(ResearcherError):
                researcher.search("test")


class TestConfigResearcherCapabilityChecks:
    def test_undeclared_capability_search_returns_noop(self, sop_only_config):
        """search not declared — returns empty list without calling HTTP."""
        researcher = ConfigResearcher("sop_only", sop_only_config)
        results = researcher.search("test")
        assert results == []

    def test_undeclared_capability_ingest_returns_noop(self, sop_only_config):
        researcher = ConfigResearcher("sop_only", sop_only_config)
        result = researcher.ingest(["url1"])
        assert result["source_count"] == 0

    def test_undeclared_capability_generate_returns_noop(self, sop_only_config):
        researcher = ConfigResearcher("sop_only", sop_only_config)
        result = researcher.generate("summary")
        assert result == ""

    def test_declared_capabilities_list(self, search_only_config):
        researcher = ConfigResearcher("exa", search_only_config)
        assert researcher.capabilities == ["search"]


class TestConfigResearcherSopAnalyze:
    def test_analyze_via_sop_when_no_endpoint(self, sop_only_config):
        researcher = ConfigResearcher("sop_only", sop_only_config)
        result = researcher.analyze(query="test", results="paper1\npaper2")
        assert "summary" in result
        assert "paper1" in result["summary"] or "paper1" in str(result["sections"])

    def test_analyze_via_sop_returns_protocol_shape(self, sop_only_config):
        researcher = ConfigResearcher("sop_only", sop_only_config)
        result = researcher.analyze()
        assert "summary" in result
        assert "sections" in result
        assert "raw" in result

    def test_analyze_sop_fills_placeholders(self, sop_only_config):
        researcher = ConfigResearcher("sop_only", sop_only_config)
        result = researcher.analyze(results="important findings here")
        assert "important findings here" in result["summary"] or "important findings here" in str(result["sections"])


# ── T027: US2 — Ad-hoc researcher session storage ────────────────────────────

class TestAdHocResearcherStorage:
    """T027: Write/load/cleanup session-scoped researchers."""

    def test_write_session_researcher(self, tmp_path, search_only_config):
        from khanote.cli.researcher_add import add_researcher_to_session

        session_dir = tmp_path / "sessions" / "ai-agents"
        path = add_researcher_to_session(session_dir, "exa", search_only_config)
        assert path.exists()
        assert path.name == "researcher.yaml"

    def test_load_session_researcher(self, tmp_path, search_only_config):
        from khanote.cli.researcher_add import add_researcher_to_session, load_session_researcher

        session_dir = tmp_path / "sessions" / "test-session"
        add_researcher_to_session(session_dir, "exa", search_only_config)
        result = load_session_researcher(session_dir)
        assert result is not None
        name, loaded = result
        assert name == "exa"
        assert loaded.type == "http"
        assert "search" in loaded.capabilities

    def test_load_session_researcher_missing_returns_none(self, tmp_path):
        from khanote.cli.researcher_add import load_session_researcher

        result = load_session_researcher(tmp_path / "nonexistent")
        assert result is None

    def test_cleanup_on_decline(self, tmp_path, search_only_config):
        from khanote.cli.researcher_add import add_researcher_to_session, discard_session_researcher

        session_dir = tmp_path / "sessions" / "declined"
        add_researcher_to_session(session_dir, "exa", search_only_config)
        assert (session_dir / "researcher.yaml").exists()
        discard_session_researcher(session_dir)
        assert not (session_dir / "researcher.yaml").exists()


# ── T022: US6 — SOP-backed capability execution ──────────────────────────────

class TestDefaultSopFallback:
    """T022: Default SOP applied when researcher has no custom SOP configured."""

    def test_analyze_capability_without_endpoint_or_sop_rejected(self):
        """Config validation rejects a capability declared without endpoint or SOP."""
        with pytest.raises(Exception):
            ResearcherConfig(
                enabled=True,
                type="http",
                capabilities=["analyze"],
                # No sop field and no endpoints — invalid
            )

    def test_config_researcher_with_explicit_default_sop(self):
        """When custom SOP is provided, it is used over the default template."""
        custom_sop = "Custom analysis: {results}"
        config = ResearcherConfig(
            enabled=True,
            type="http",
            capabilities=["analyze"],
            sop={"analyze": custom_sop},
        )
        researcher = ConfigResearcher("custom", config)
        result = researcher.analyze(results="test paper")
        assert "Custom analysis" in result["summary"] or "Custom analysis" in str(result["sections"])

    def test_generate_via_sop(self):
        config = ResearcherConfig(
            enabled=True,
            type="http",
            capabilities=["generate"],
            sop={"generate": "Generate a report about: {query}"},
        )
        researcher = ConfigResearcher("gen", config)
        result = researcher.generate("summary", query="AI agents")
        assert "AI agents" in result


# ── T014: Connectivity test ───────────────────────────────────────────────────

class TestConnectivityTest:
    def test_connectivity_ok(self, search_only_config):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client.request.return_value = mock_response

            researcher = ConfigResearcher("exa", search_only_config)
            report = researcher.test_connectivity()

        assert report["status"] == "ok"
        assert "latency_ms" in report
        assert isinstance(report["latency_ms"], int)

    def test_connectivity_failed(self, search_only_config):
        import httpx

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_client.request.side_effect = httpx.ConnectError("Connection refused")

            researcher = ConfigResearcher("exa", search_only_config)
            report = researcher.test_connectivity()

        assert report["status"] == "failed"
        assert "message" in report

    def test_connectivity_no_endpoints_returns_sop_ok(self, sop_only_config):
        """No endpoints to test — report ok with note about SOP mode."""
        researcher = ConfigResearcher("sop_only", sop_only_config)
        report = researcher.test_connectivity()
        assert report["status"] == "ok"
        assert "sop" in report["message"].lower()
