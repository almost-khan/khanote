"""Unit tests for init wizard logic."""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestWizardLanguageFirst:
    def test_language_is_first_prompt(self, tmp_path):
        """First interactive prompt must be for language."""
        from khanote.cli.init import WizardState
        state = WizardState()
        assert state.step_order[0] == "language"

    def test_default_language_is_english(self, tmp_path):
        from khanote.cli.init import WizardState
        state = WizardState()
        assert state.defaults["language"] == "en"

    def test_step_order_matches_spec(self, tmp_path):
        from khanote.cli.init import WizardState
        state = WizardState()
        assert state.step_order == ["language", "tool", "role", "interests", "api_keys"]


class TestWizardDefaults:
    def test_all_steps_have_defaults(self, tmp_path):
        from khanote.cli.init import WizardState
        state = WizardState()
        for step in ["language", "tool", "role"]:
            assert step in state.defaults, f"Missing default for step '{step}'"

    def test_default_tool_is_claude_code(self):
        from khanote.cli.init import WizardState
        state = WizardState()
        assert state.defaults["tool"] == "claude-code"

    def test_default_role_is_mixed(self):
        from khanote.cli.init import WizardState
        state = WizardState()
        assert state.defaults["role"] == "mixed"

    def test_no_output_path_in_defaults(self):
        """CWD model: output_path should not be in wizard defaults."""
        from khanote.cli.init import WizardState
        state = WizardState()
        assert "output_path" not in state.defaults


class TestWizardLanguageSwitching:
    def test_subsequent_prompts_use_selected_language(self):
        """After selecting Chinese, prompts should use Chinese messages."""
        from khanote.i18n import get_message
        lang = "zh"
        prompt = get_message("wizard.tool_prompt", lang)
        assert "AI" in prompt or "工具" in prompt

    def test_post_init_panel_uses_selected_language(self):
        from khanote.i18n import get_message
        title = get_message("init.success_title", "zh")
        assert "khanote" in title
        assert "完成" in title or "初始化" in title


class TestCtrlCAtomicity:
    def test_no_files_written_on_interrupt_at_step1(self, tmp_path, monkeypatch):
        """KeyboardInterrupt at language step writes no files."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import run_init_wizard
        with patch("typer.prompt", side_effect=KeyboardInterrupt):
            with pytest.raises((KeyboardInterrupt, SystemExit)):
                run_init_wizard(tool=None, lang=None)
        assert not (tmp_path / ".khanote").exists()

    def test_no_files_written_on_interrupt_at_step3(self, tmp_path, monkeypatch):
        """KeyboardInterrupt at role step writes no files."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import run_init_wizard
        prompts = iter(["en", "claude-code"])
        with patch("typer.prompt", side_effect=lambda *a, **kw: (next(prompts) if "language" in str(a) + str(kw) or "tool" in str(a) + str(kw) else (_ for _ in ()).throw(KeyboardInterrupt()))):
            try:
                run_init_wizard(tool=None, lang=None)
            except (KeyboardInterrupt, SystemExit):
                pass
        assert not (tmp_path / ".khanote" / "config.yaml").exists()

    def test_existing_config_untouched_on_interrupt(self, existing_khanote_dir, monkeypatch):
        """Re-init interrupted by Ctrl+C must not modify existing config."""
        monkeypatch.chdir(existing_khanote_dir)
        config_path = existing_khanote_dir / ".khanote" / "config.yaml"
        original_content = config_path.read_text()

        from khanote.cli.init import run_init_wizard
        with patch("typer.prompt", side_effect=KeyboardInterrupt):
            try:
                run_init_wizard(tool=None, lang=None)
            except (KeyboardInterrupt, SystemExit):
                pass

        assert config_path.read_text() == original_content


class TestReInitDetection:
    def test_reinit_shows_detection_notice(self, existing_khanote_dir, capsys, monkeypatch):
        """Re-running init on existing config must display detection notice."""
        monkeypatch.chdir(existing_khanote_dir)
        from khanote.cli.init import run_init_wizard
        from khanote.i18n import get_message

        responses = iter(["en", "claude-code", "developer", "", ""])
        with patch("typer.prompt", side_effect=lambda *a, **kw: next(responses, "")):
            with patch("khanote.cli.init._write_config_files"):
                try:
                    run_init_wizard(tool="claude-code", lang="en")
                except Exception:
                    pass

        captured = capsys.readouterr()
        notice = get_message("wizard.reinit_notice", "en")
        assert notice in captured.out or "Existing configuration" in captured.out

    def test_reinit_preloads_current_values(self, existing_khanote_dir):
        """Defaults for re-init must come from existing config, not built-in defaults."""
        from khanote.cli.init import load_existing_defaults

        defaults = load_existing_defaults(existing_khanote_dir)
        assert defaults.get("tool") == "claude-code"
        assert defaults.get("role") == "developer"


class TestFlagSkipBehavior:
    def test_no_output_path_prompt(self, tmp_path, monkeypatch):
        """CWD model: wizard must never ask for output path."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import run_init_wizard
        prompted_keys = []

        def capture_prompt(*args, **kwargs):
            prompted_keys.append(str(args) + str(kwargs))
            return "en"

        with patch("typer.prompt", side_effect=capture_prompt):
            with patch("khanote.cli.init._write_config_files"):
                try:
                    run_init_wizard(tool="claude-code", lang="en")
                except Exception:
                    pass

        assert not any("output" in k.lower() or "save" in k.lower() or "path" in k.lower() for k in prompted_keys)

    def test_tool_flag_skips_tool_prompt(self, tmp_path, monkeypatch):
        """--tool flag should prevent asking for tool selection."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import run_init_wizard
        prompted_keys = []

        def capture_prompt(*args, **kwargs):
            prompted_keys.append(str(args[0]) if args else "")
            return "en"

        with patch("typer.prompt", side_effect=capture_prompt):
            with patch("khanote.cli.init._write_config_files"):
                try:
                    run_init_wizard(tool="cursor", lang="en")
                except Exception:
                    pass

        assert not any("tool" in k.lower() or "cursor" in k.lower() for k in prompted_keys)


class TestOutputPathAutoCreation:
    def test_nonexistent_path_is_created(self, tmp_path):
        """If output path doesn't exist, wizard must create it."""
        new_path = tmp_path / "new-research-dir"
        assert not new_path.exists()

        from khanote.cli.init import ensure_output_path
        ensure_output_path(new_path)
        assert new_path.exists()


class TestToolNotInstalledWarning:
    def test_missing_tool_dir_triggers_warning(self, tmp_path, capsys):
        """If tool commands directory doesn't exist, post-init panel must warn."""
        from khanote.cli.init import check_tool_installed
        # cursor not installed in tmp_path
        warning = check_tool_installed("cursor", tmp_path)
        assert warning is not None
        assert "cursor" in warning.lower() or "not found" in warning.lower()

    def test_existing_tool_dir_no_warning(self, tmp_path):
        """If tool directory exists, no warning."""
        from khanote.models.tool import TOOL_CONFIG
        tool_cfg = TOOL_CONFIG["claude-code"]
        (tmp_path / tool_cfg.commands_dir).mkdir(parents=True)

        from khanote.cli.init import check_tool_installed
        warning = check_tool_installed("claude-code", tmp_path)
        assert warning is None
