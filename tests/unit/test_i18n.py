"""Tests for i18n message loader."""
from __future__ import annotations


from khanote.i18n import get_message


class TestGetMessage:
    def test_exact_language_match(self):
        assert get_message("wizard.language_prompt", "en") == "Select your language"

    def test_exact_chinese_match(self):
        result = get_message("wizard.language_prompt", "zh")
        assert result == "选择你的语言"

    def test_bcp47_prefix_fallback(self):
        # zh-CN should fall back to zh
        result = get_message("wizard.language_prompt", "zh-CN")
        assert result == "选择你的语言"

    def test_underscore_prefix_fallback(self):
        # zh_CN should fall back to zh
        result = get_message("wizard.language_prompt", "zh_CN")
        assert result == "选择你的语言"

    def test_english_fallback_for_unknown_language(self):
        result = get_message("wizard.language_prompt", "xx")
        assert result == "Select your language"

    def test_english_fallback_for_unsupported_bcp47(self):
        result = get_message("wizard.language_prompt", "de-DE")
        assert result == "Select your language"

    def test_missing_key_returns_key(self):
        result = get_message("nonexistent.key", "en")
        assert result == "nonexistent.key"

    def test_default_lang_is_english(self):
        result = get_message("wizard.language_prompt")
        assert result == "Select your language"

    def test_japanese_message(self):
        result = get_message("wizard.language_prompt", "ja")
        assert "言語" in result

    def test_korean_message(self):
        result = get_message("wizard.language_prompt", "ko")
        assert result != "Select your language"

    def test_french_message(self):
        result = get_message("wizard.language_prompt", "fr")
        assert result != "Select your language"

    def test_all_wizard_keys_have_english(self):
        from khanote.i18n.messages import MESSAGES
        for key, translations in MESSAGES.items():
            assert "en" in translations, f"Key '{key}' missing English translation"

    def test_tool_option_keys(self):
        result = get_message("wizard.tool_prompt", "en")
        assert result  # non-empty

    def test_post_init_panel_key(self):
        result = get_message("init.success_title", "en")
        assert result

    def test_restart_claude_code_english(self):
        result = get_message("restart.claude-code", "en")
        assert "Claude Code" in result

    def test_restart_cursor_english(self):
        result = get_message("restart.cursor", "en")
        assert "Cursor" in result or "Reload" in result

    def test_restart_keys_all_5_tools(self):
        for tool in ("claude-code", "cursor", "codex", "gemini-cli", "opencode"):
            result = get_message(f"restart.{tool}", "en")
            assert result and result != f"restart.{tool}", f"Missing restart message for {tool}"
