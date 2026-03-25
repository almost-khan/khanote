"""Integration tests for khanote status command (TDD)."""
from __future__ import annotations

import yaml
from typer.testing import CliRunner

from khanote.cli.app import app

runner = CliRunner()

_WIZARD_INPUT = "\n\n\n\n\n\n\n"


class TestStatusAfterInit:
    def test_status_exits_zero(self, tmp_path, monkeypatch):
        """khanote status always exits 0."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0

    def test_status_shows_tool_after_init(self, tmp_path, monkeypatch):
        """Status output should mention the initialized tool."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        result = runner.invoke(app, ["status"])
        assert "claude" in result.output.lower()

    def test_status_shows_feeds_count_after_init(self, tmp_path, monkeypatch):
        """Status output should show a feeds count."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        result = runner.invoke(app, ["status"])
        assert "feed" in result.output.lower()

    def test_status_shows_language_after_init(self, tmp_path, monkeypatch):
        """Status should show the language from preferences."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        result = runner.invoke(app, ["status"])
        assert "en" in result.output.lower()


class TestStatusMissingPreferences:
    def test_status_warns_when_preferences_missing(self, tmp_path, monkeypatch):
        """If preferences.yaml is missing, status should warn."""
        monkeypatch.chdir(tmp_path)
        kdir = tmp_path / ".khanote"
        kdir.mkdir()
        cfg = {
            "version": "0.1.0",
            "vault_path": str(tmp_path),
            "initialized_tools": ["claude-code"],
            "research": {"default": "arxiv", "researchers": {}},
        }
        (kdir / "config.yaml").write_text(yaml.dump(cfg))

        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "warn" in result.output.lower() or "missing" in result.output.lower() or "preferences" in result.output.lower()


class TestStatusNotInitialized:
    def test_status_no_config_shows_init_instruction(self, tmp_path, monkeypatch):
        """If no config, status must tell user to run khanote init."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "init" in result.output.lower()

    def test_status_always_exits_zero(self, tmp_path, monkeypatch):
        """Status must exit 0 even when not initialized."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
