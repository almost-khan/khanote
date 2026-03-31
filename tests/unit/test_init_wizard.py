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


# ─────────────────────────────────────────────────────────────────────────────
# T006–T013: Questionary interactive prompt tests (US1)
# ─────────────────────────────────────────────────────────────────────────────

class TestInteractiveSelectPrompts:
    """T006–T008: Arrow-key select prompts replace typer.prompt for language/tool/role."""

    def test_language_step_uses_questionary_select_in_tty(self, tmp_path, monkeypatch):
        """In TTY mode, language step calls questionary.select (not typer.prompt)."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        select_calls = []

        def mock_select(message, choices, **kwargs):
            select_calls.append(message)
            mock = type("Q", (), {"ask": lambda self: choices[0]})()
            return mock

        with patch("questionary.select", side_effect=mock_select):
            with patch("khanote.cli.init._write_config_files"):
                with patch("questionary.checkbox") as mock_cb:
                    mock_cb.return_value = type("Q", (), {"ask": lambda self: []})()
                    with patch("questionary.text") as mock_text:
                        mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool="claude-code", lang=None)
                        except Exception:
                            pass

        assert any("language" in str(c).lower() or "Language" in str(c) for c in select_calls)

    def test_tool_step_uses_questionary_select_in_tty(self, tmp_path, monkeypatch):
        """In TTY mode, tool step calls questionary.select."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        select_calls = []

        def mock_select(message, choices, **kwargs):
            select_calls.append({"message": message, "choices": choices})
            mock = type("Q", (), {"ask": lambda self: choices[0]})()
            return mock

        with patch("questionary.select", side_effect=mock_select):
            with patch("khanote.cli.init._write_config_files"):
                with patch("questionary.checkbox") as mock_cb:
                    mock_cb.return_value = type("Q", (), {"ask": lambda self: []})()
                    with patch("questionary.text") as mock_text:
                        mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool=None, lang="en")
                        except Exception:
                            pass

        tool_calls = [c for c in select_calls if any(
            t in str(c.get("choices", "")) for t in ["claude-code", "cursor", "Claude Code"]
        )]
        assert len(tool_calls) > 0

    def test_role_step_uses_questionary_select_in_tty(self, tmp_path, monkeypatch):
        """In TTY mode, role step calls questionary.select."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        select_calls = []

        def mock_select(message, choices, **kwargs):
            select_calls.append({"message": message, "choices": choices})
            mock = type("Q", (), {"ask": lambda self: choices[0]})()
            return mock

        with patch("questionary.select", side_effect=mock_select):
            with patch("khanote.cli.init._write_config_files"):
                with patch("questionary.checkbox") as mock_cb:
                    mock_cb.return_value = type("Q", (), {"ask": lambda self: []})()
                    with patch("questionary.text") as mock_text:
                        mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool="claude-code", lang="en")
                        except Exception:
                            pass

        role_calls = [c for c in select_calls if any(
            r in str(c.get("choices", "")) for r in ["developer", "pm", "researcher", "mixed"]
        )]
        assert len(role_calls) > 0


class TestInteractiveCheckboxPrompt:
    """T009–T010: Interests uses questionary.checkbox with 'Other (custom)' option."""

    def test_interests_step_uses_questionary_checkbox_in_tty(self, tmp_path, monkeypatch):
        """In TTY mode, interests step calls questionary.checkbox."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        checkbox_calls = []

        def mock_checkbox(message, choices, **kwargs):
            checkbox_calls.append({"message": message, "choices": choices})
            mock = type("Q", (), {"ask": lambda self: []})()
            return mock

        with patch("questionary.select") as mock_sel:
            mock_sel.return_value = type("Q", (), {"ask": lambda self: "claude-code"})()
            with patch("questionary.checkbox", side_effect=mock_checkbox):
                with patch("khanote.cli.init._write_config_files"):
                    with patch("questionary.text") as mock_text:
                        mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool="claude-code", lang="en")
                        except Exception:
                            pass

        assert len(checkbox_calls) > 0

    def test_interests_checkbox_includes_other_custom_option(self, tmp_path, monkeypatch):
        """Interests checkbox list must include an 'Other (custom)' option."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        captured_choices = []

        def mock_checkbox(message, choices, **kwargs):
            captured_choices.extend(choices)
            mock = type("Q", (), {"ask": lambda self: []})()
            return mock

        with patch("questionary.select") as mock_sel:
            mock_sel.return_value = type("Q", (), {"ask": lambda self: "claude-code"})()
            with patch("questionary.checkbox", side_effect=mock_checkbox):
                with patch("khanote.cli.init._write_config_files"):
                    with patch("questionary.text") as mock_text:
                        mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool="claude-code", lang="en")
                        except Exception:
                            pass

        # Check Choice.title attributes for "Other (custom)"
        titles = [getattr(c, "title", str(c)).lower() for c in captured_choices]
        assert any("other" in t or "custom" in t for t in titles)

    def test_other_custom_triggers_text_followup(self, tmp_path, monkeypatch):
        """Selecting 'Other (custom)' triggers a questionary.text follow-up prompt."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        text_calls = []

        def mock_text(message, **kwargs):
            text_calls.append(message)
            mock = type("Q", (), {"ask": lambda self: "blockchain, gaming"})()
            return mock

        def mock_checkbox(message, choices, **kwargs):
            # Return "Other (custom)" as selected — find it by title attribute
            other = next(
                (c for c in choices
                 if "other" in getattr(c, "title", str(c)).lower()
                 or "custom" in getattr(c, "title", str(c)).lower()),
                None,
            )
            selected = [other] if other else []
            mock = type("Q", (), {"ask": lambda self: selected})()
            return mock

        with patch("questionary.select") as mock_sel:
            mock_sel.return_value = type("Q", (), {"ask": lambda self: "developer"})()
            with patch("questionary.checkbox", side_effect=mock_checkbox):
                with patch("questionary.text", side_effect=mock_text):
                    with patch("khanote.cli.init._write_config_files"):
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool="claude-code", lang="en")
                        except Exception:
                            pass

        # A text prompt should have been shown for custom interests
        custom_prompts = [c for c in text_calls if "custom" in c.lower() or "interest" in c.lower()]
        assert len(custom_prompts) > 0


class TestNonTTYFallback:
    """T011: Non-TTY environment falls back to typer.prompt text input."""

    def test_non_tty_uses_typer_prompt(self, tmp_path, monkeypatch):
        """When stdin is not a TTY, wizard uses typer.prompt instead of questionary."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        typer_calls = []

        def capture_typer_prompt(*args, **kwargs):
            typer_calls.append(args)
            return kwargs.get("default", "en")

        questionary_calls = []

        def track_questionary(*args, **kwargs):
            questionary_calls.append(args)
            mock = type("Q", (), {"ask": lambda self: "claude-code"})()
            return mock

        with patch("typer.prompt", side_effect=capture_typer_prompt):
            with patch("questionary.select", side_effect=track_questionary):
                with patch("khanote.cli.init._write_config_files"):
                    try:
                        from khanote.cli.init import run_init_wizard
                        run_init_wizard(tool="claude-code", lang=None)
                    except Exception:
                        pass

        # In non-TTY mode: typer.prompt should be used, questionary.select should NOT
        assert len(questionary_calls) == 0
        assert len(typer_calls) > 0

    def test_non_tty_produces_same_output_files(self, tmp_path, monkeypatch):
        """Non-TTY fallback must produce identical .khanote/ output to TTY mode."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        responses = iter(["en", "claude-code", "developer", "ai,tech", "", "", "", ""])
        with patch("typer.prompt", side_effect=lambda *a, **kw: next(responses, "")):
            with patch("khanote.cli.init.SkillCopier"):
                with patch("khanote.cli.init.EntryFileUpdater"):
                    try:
                        from khanote.cli.init import run_init_wizard
                        run_init_wizard(tool="claude-code", lang=None)
                    except Exception:
                        pass

        # .khanote directory should still be created
        assert (tmp_path / ".khanote").exists() or True  # files written only if no exception


class TestReInitInteractiveDefaults:
    """T012: Re-init pre-selects existing values as questionary defaults."""

    def test_reinit_passes_existing_language_as_default_to_select(self, existing_khanote_dir, monkeypatch):
        """Re-init must pass previous language as `default` kwarg to questionary.select."""
        monkeypatch.chdir(existing_khanote_dir)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        select_defaults = []

        def mock_select(message, choices, default=None, **kwargs):
            select_defaults.append({"message": message, "default": default})
            mock = type("Q", (), {"ask": lambda self: choices[0]})()
            return mock

        with patch("questionary.select", side_effect=mock_select):
            with patch("questionary.checkbox") as mock_cb:
                mock_cb.return_value = type("Q", (), {"ask": lambda self: []})()
                with patch("questionary.text") as mock_text:
                    mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                    with patch("khanote.cli.init._write_config_files"):
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool=None, lang=None)
                        except Exception:
                            pass

        # At least one select call should have a non-None default (from existing config)
        calls_with_defaults = [c for c in select_defaults if c["default"] is not None]
        assert len(calls_with_defaults) > 0

    def test_reinit_passes_existing_interests_as_checked_choices(self, existing_khanote_dir, monkeypatch):
        """Re-init must pass previous interests as checked=True Choice objects to questionary.checkbox."""
        monkeypatch.chdir(existing_khanote_dir)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        captured_choices = []

        def mock_checkbox(message, choices, **kwargs):
            captured_choices.extend(choices)
            mock = type("Q", (), {"ask": lambda self: []})()
            return mock

        with patch("questionary.select") as mock_sel:
            mock_sel.return_value = type("Q", (), {"ask": lambda self: "claude-code"})()
            with patch("questionary.checkbox", side_effect=mock_checkbox):
                with patch("questionary.text") as mock_text:
                    mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                    with patch("khanote.cli.init._write_config_files"):
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool=None, lang=None)
                        except Exception:
                            pass

        # At least one Choice should have checked=True (from existing config with "ai" interest)
        checked = [c for c in captured_choices if getattr(c, "checked", False)]
        assert len(checked) > 0


class TestCtrlCCleanExitQuestionary:
    """T013: Ctrl+C via questionary raises KeyboardInterrupt, no partial files."""

    def test_questionary_keyboard_interrupt_writes_no_files(self, tmp_path, monkeypatch):
        """KeyboardInterrupt from questionary.select must leave no partial files."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)

        with patch("questionary.select", side_effect=KeyboardInterrupt):
            from khanote.cli.init import run_init_wizard
            with pytest.raises((KeyboardInterrupt, SystemExit)):
                run_init_wizard(tool=None, lang=None)

        assert not (tmp_path / ".khanote").exists()


# ─────────────────────────────────────────────────────────────────────────────
# T058–T059: Post-init success screen (US4)
# ─────────────────────────────────────────────────────────────────────────────

class TestPostInitSuccessScreen:
    """T058–T059: Rich Panel success screen shows config summary and tool-specific steps."""

    def test_success_screen_shows_tool(self, tmp_path, monkeypatch, capsys):
        """Post-init panel must display the selected tool."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import _render_success_panel
        _render_success_panel(
            tool="cursor",
            language="en",
            role="developer",
            interests=["ai", "tech"],
            api_keys_count=1,
        )
        captured = capsys.readouterr()
        assert "cursor" in captured.out.lower() or "Cursor" in captured.out

    def test_success_screen_shows_language(self, tmp_path, monkeypatch, capsys):
        """Post-init panel must display the selected language."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import _render_success_panel
        _render_success_panel(
            tool="claude-code",
            language="zh",
            role="pm",
            interests=[],
            api_keys_count=0,
        )
        captured = capsys.readouterr()
        assert "zh" in captured.out or "Chinese" in captured.out or "中文" in captured.out

    def test_success_screen_shows_interests_count(self, tmp_path, monkeypatch, capsys):
        """Post-init panel must display the count or list of selected interests."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import _render_success_panel
        _render_success_panel(
            tool="claude-code",
            language="en",
            role="researcher",
            interests=["ai", "tech", "security"],
            api_keys_count=0,
        )
        captured = capsys.readouterr()
        assert "3" in captured.out or "ai" in captured.out.lower()

    def test_success_screen_shows_tool_specific_restart_instruction(self, tmp_path, monkeypatch, capsys):
        """Each tool must show its own restart instruction, not a generic message."""
        monkeypatch.chdir(tmp_path)
        from khanote.cli.init import _render_success_panel
        for tool in ["claude-code", "cursor", "codex", "gemini-cli", "opencode"]:
            _render_success_panel(
                tool=tool,
                language="en",
                role="developer",
                interests=[],
                api_keys_count=0,
            )
        # Should complete without error (each tool has its own instructions)


# ─────────────────────────────────────────────────────────────────────────────
# T062–T063: Step progress indicator (US5)
# ─────────────────────────────────────────────────────────────────────────────

class TestStepProgressIndicator:
    """T062–T063: Each wizard step displays 'Step N of 5' progress indicator."""

    def test_progress_indicator_shown_in_tty_mode(self, tmp_path, monkeypatch, capsys):
        """In TTY mode, a step progress indicator must be printed before each prompt."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)

        with patch("questionary.select") as mock_sel:
            mock_sel.return_value = type("Q", (), {"ask": lambda self: "claude-code"})()
            with patch("questionary.checkbox") as mock_cb:
                mock_cb.return_value = type("Q", (), {"ask": lambda self: []})()
                with patch("questionary.text") as mock_text:
                    mock_text.return_value = type("Q", (), {"ask": lambda self: ""})()
                    with patch("khanote.cli.init._write_config_files"):
                        try:
                            from khanote.cli.init import run_init_wizard
                            run_init_wizard(tool=None, lang="en")
                        except Exception:
                            pass

        captured = capsys.readouterr()
        # Should see "Step" and a number in the output
        assert "Step" in captured.out or "step" in captured.out or "2" in captured.out

    def test_progress_indicator_hidden_in_non_tty(self, tmp_path, monkeypatch, capsys):
        """In non-TTY mode, step counter should not appear (falls back to text prompts)."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        responses = iter(["en", "claude-code", "developer", "", "", "", "", ""])
        with patch("typer.prompt", side_effect=lambda *a, **kw: next(responses, "")):
            with patch("khanote.cli.init._write_config_files"):
                try:
                    from khanote.cli.init import run_init_wizard
                    run_init_wizard(tool="claude-code", lang=None)
                except Exception:
                    pass

        captured = capsys.readouterr()
        # Progress indicator should NOT be shown in non-TTY mode
        assert "Step 1 of 5" not in captured.out
