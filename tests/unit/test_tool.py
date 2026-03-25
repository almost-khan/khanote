"""Tests for Tool model and TOOL_CONFIG registry (TDD)."""
import pytest

from khanote.models.tool import TOOL_CONFIG


class TestToolConfigRegistry:
    def test_all_supported_tools_present(self):
        expected = {"claude-code", "cursor", "codex", "gemini-cli", "opencode"}
        assert expected.issubset(TOOL_CONFIG.keys())

    def test_each_tool_has_required_fields(self):
        required = {"commands_dir", "entry_file", "format", "placeholder", "extension"}
        for tool_name, config in TOOL_CONFIG.items():
            for field in required:
                assert hasattr(config, field), f"{tool_name} missing field: {field}"

    def test_claude_code_config(self):
        cfg = TOOL_CONFIG["claude-code"]
        assert cfg.commands_dir == ".claude/commands/"
        assert cfg.placeholder == "$ARGUMENTS"
        assert cfg.entry_file == "CLAUDE.md"

    def test_cursor_config(self):
        cfg = TOOL_CONFIG["cursor"]
        assert cfg.commands_dir == ".cursor/rules/"
        assert cfg.entry_file == ".cursorrules"

    def test_codex_config(self):
        cfg = TOOL_CONFIG["codex"]
        assert cfg.commands_dir == ".agents/skills/"
        assert cfg.entry_file == "AGENTS.md"

    def test_gemini_cli_config(self):
        cfg = TOOL_CONFIG["gemini-cli"]
        assert cfg.commands_dir == ".gemini/commands/"
        assert cfg.placeholder == "{{args}}"
        assert cfg.entry_file == "GEMINI.md"

    def test_opencode_config(self):
        cfg = TOOL_CONFIG["opencode"]
        assert cfg.commands_dir == ".opencode/commands/"
        assert cfg.entry_file == "OPENCODE.md"

    def test_placeholder_values_non_empty(self):
        for tool_name, config in TOOL_CONFIG.items():
            assert config.placeholder, f"{tool_name} has empty placeholder"

    def test_extension_values_non_empty(self):
        for tool_name, config in TOOL_CONFIG.items():
            assert config.extension, f"{tool_name} has empty extension"

    def test_get_unknown_tool_raises(self):
        with pytest.raises(KeyError):
            _ = TOOL_CONFIG["unknown-tool"]


class TestToolConfigModel:
    def test_tool_config_is_frozen(self):
        cfg = TOOL_CONFIG["claude-code"]
        with pytest.raises(Exception):
            cfg.commands_dir = "modified"
