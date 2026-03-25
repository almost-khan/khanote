"""Tool config model and TOOL_CONFIG registry."""
from __future__ import annotations

from pydantic import BaseModel


class ToolConfig(BaseModel, frozen=True):
    """Configuration for a single vibe coding tool."""

    commands_dir: str
    entry_file: str
    format: str
    placeholder: str
    extension: str
    skills_dir: str | None = None  # Optional second target (e.g., claude-code)
    restart_instruction: str = "restart.claude-code"  # i18n message key


TOOL_CONFIG: dict[str, ToolConfig] = {
    "claude-code": ToolConfig(
        commands_dir=".claude/commands/",
        skills_dir=".claude/skills/",
        entry_file="CLAUDE.md",
        format="markdown",
        placeholder="$ARGUMENTS",
        extension=".md",
        restart_instruction="restart.claude-code",
    ),
    "cursor": ToolConfig(
        commands_dir=".cursor/rules/",
        entry_file=".cursorrules",
        format="markdown",
        placeholder="$ARGUMENTS",
        extension=".md",
        restart_instruction="restart.cursor",
    ),
    "codex": ToolConfig(
        commands_dir=".agents/skills/",
        entry_file="AGENTS.md",
        format="skill",
        placeholder="$ARGUMENTS",
        extension="/SKILL.md",
        restart_instruction="restart.codex",
    ),
    "gemini-cli": ToolConfig(
        commands_dir=".gemini/commands/",
        entry_file="GEMINI.md",
        format="toml",
        placeholder="{{args}}",
        extension=".toml",
        restart_instruction="restart.gemini-cli",
    ),
    "opencode": ToolConfig(
        commands_dir=".opencode/commands/",
        entry_file="OPENCODE.md",
        format="markdown",
        placeholder="$ARGUMENTS",
        extension=".md",
        restart_instruction="restart.opencode",
    ),
}
