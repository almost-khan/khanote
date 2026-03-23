"""Integration tests for khanote init flow (TDD)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from khanote.cli.app import app


runner = CliRunner()


@pytest.fixture
def vault(tmp_path):
    return tmp_path


class TestInitFlow:
    def test_init_creates_khanote_directory(self, vault):
        result = runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        assert result.exit_code == 0, result.output
        assert (vault / ".khanote").exists()

    def test_init_creates_config_yaml(self, vault):
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        config_file = vault / ".khanote" / "config.yaml"
        assert config_file.exists()
        data = yaml.safe_load(config_file.read_text())
        assert data["vault_path"] == str(vault)
        assert "claude-code" in data["initialized_tools"]

    def test_init_copies_skills_to_tool_directory(self, vault):
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        commands_dir = vault / ".claude" / "commands"
        assert commands_dir.exists()
        # At least some .md files should be present
        md_files = list(commands_dir.glob("*.md"))
        assert len(md_files) > 0

    def test_init_updates_entry_file(self, vault):
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        entry = vault / "CLAUDE.md"
        assert entry.exists()
        assert ".khanote/context.md" in entry.read_text()

    def test_init_is_idempotent(self, vault):
        """Running init twice should not error."""
        for _ in range(2):
            result = runner.invoke(
                app,
                ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
                input="y\n",
            )
        assert result.exit_code == 0


class TestMultiToolInit:
    def test_init_two_tools_both_in_initialized_tools(self, vault):
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "cursor", "--researcher", "perplexity"],
            input="y\n",
        )
        config = yaml.safe_load((vault / ".khanote" / "config.yaml").read_text())
        assert "claude-code" in config["initialized_tools"]
        assert "cursor" in config["initialized_tools"]

    def test_init_second_tool_preserves_first_tool_skills(self, vault):
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "cursor", "--researcher", "perplexity"],
            input="y\n",
        )
        assert (vault / ".claude" / "commands").exists()
        assert (vault / ".cursor" / "rules").exists()

    def test_ssot_preserved_after_multi_init(self, vault):
        """SSOT .khanote/skills/ should be single source of truth."""
        runner.invoke(
            app,
            ["init", "--vault", str(vault), "--tool", "claude-code", "--researcher", "perplexity"],
            input="y\n",
        )
        ssot_dir = vault / ".khanote" / "skills"
        assert ssot_dir.exists()
