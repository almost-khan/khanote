"""Integration tests for khanote init flow (TDD)."""
from __future__ import annotations


import pytest
import yaml
from typer.testing import CliRunner

from khanote.cli.app import app


runner = CliRunner()


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# With --tool flag: wizard asks language(1) + role(2) + interests(3) + 4 api keys(4-7)
_WIZARD_INPUT = "\n\n\n\n\n\n\n"  # 7 Enter presses


class TestInitFlow:
    def test_init_creates_khanote_directory(self, vault):
        result = runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        assert result.exit_code == 0, result.output
        assert (vault / ".khanote").exists()

    def test_init_creates_config_yaml(self, vault):
        runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        config_file = vault / ".khanote" / "config.yaml"
        assert config_file.exists()
        data = yaml.safe_load(config_file.read_text())
        assert data["vault_path"] == str(vault)
        assert "claude-code" in data["initialized_tools"]

    def test_init_copies_skills_to_tool_directory(self, vault):
        runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        commands_dir = vault / ".claude" / "commands"
        assert commands_dir.exists()
        # At least some .md files should be present
        md_files = list(commands_dir.glob("*.md"))
        assert len(md_files) > 0

    def test_init_updates_entry_file(self, vault):
        runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        entry = vault / "CLAUDE.md"
        assert entry.exists()
        assert ".khanote/context.md" in entry.read_text()

    def test_init_is_idempotent(self, vault):
        """Running init twice should not error."""
        for _ in range(2):
            result = runner.invoke(
                app,
                ["init", "--tool", "claude-code"],
                input=_WIZARD_INPUT,
            )
        assert result.exit_code == 0


class TestPostInitFeedPrompt:
    """T046: US5 — post-init feed prompt appears."""

    def test_init_mentions_feed_setup(self, vault):
        """After init completes, output should reference the start-my-day skill."""
        result = runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        assert result.exit_code == 0, result.output
        output = result.output.lower()
        assert "khanote.start-my-day" in output or "skill" in output


class TestMultiToolInit:
    def test_init_two_tools_both_in_initialized_tools(self, vault):
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        runner.invoke(app, ["init", "--tool", "cursor"], input=_WIZARD_INPUT)
        config = yaml.safe_load((vault / ".khanote" / "config.yaml").read_text())
        assert "claude-code" in config["initialized_tools"]
        assert "cursor" in config["initialized_tools"]

    def test_init_second_tool_preserves_first_tool_skills(self, vault):
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        runner.invoke(app, ["init", "--tool", "cursor"], input=_WIZARD_INPUT)
        assert (vault / ".claude" / "commands").exists()
        assert (vault / ".cursor" / "rules").exists()

    def test_ssot_preserved_after_multi_init(self, vault):
        """SSOT .khanote/skills/ should be single source of truth."""
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        ssot_dir = vault / ".khanote" / "skills"
        assert ssot_dir.exists()


# ── New wizard-based init tests (spec-004) ────────────────────────────────────

class TestWizardInit:
    """Tests for the language-first interactive wizard (spec-004)."""

    def test_wizard_installs_in_cwd(self, vault):
        """khanote init installs in the current working directory."""
        result = runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        assert result.exit_code == 0, result.output
        assert (vault / ".khanote" / "config.yaml").exists()

    def test_wizard_no_output_flag(self):
        """--output flag must not appear in init help."""
        result = runner.invoke(app, ["init", "--help"])
        assert "--output" not in result.output

    def test_wizard_shows_skill_command_in_completion(self, vault):
        """Post-init output must reference /khanote.start-my-day."""
        result = runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        assert "/khanote.start-my-day" in result.output

    def test_wizard_creates_preferences_yaml(self, vault):
        """Wizard must write preferences.yaml."""
        result = runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input=_WIZARD_INPUT,
        )
        assert result.exit_code == 0, result.output
        assert (vault / ".khanote" / "preferences.yaml").exists()

    def test_wizard_reinit_shows_notice(self, vault):
        """Re-running init on existing config must show detection notice."""
        runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        result = runner.invoke(app, ["init", "--tool", "claude-code"], input=_WIZARD_INPUT)
        assert "Existing configuration" in result.output or "existing" in result.output.lower()

    def test_start_my_day_cli_shows_redirect(self):
        """khanote start-my-day in terminal must show redirect, not run."""
        result = runner.invoke(app, ["start-my-day"])
        assert result.exit_code == 1
        assert "skill" in result.output.lower() or "/khanote.start-my-day" in result.output

    def test_start_my_day_not_in_help(self):
        """start-my-day must not appear in khanote --help."""
        result = runner.invoke(app, ["--help"])
        assert "start-my-day" not in result.output

    def test_unsupported_language_uses_english_wizard(self, vault):
        """Selecting unsupported language (e.g. 'de') falls back to English prompts."""
        result = runner.invoke(
            app,
            ["init", "--tool", "claude-code"],
            input="de\n\n\n\n\n\n\n",
        )
        assert result.exit_code == 0, result.output
        prefs_path = vault / ".khanote" / "preferences.yaml"
        if prefs_path.exists():
            prefs = yaml.safe_load(prefs_path.read_text())
            assert prefs.get("language") in ("de", "en")
