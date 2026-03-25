"""Content verification tests for SKILL.md files (TDD — fail before rewrite)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"
_SKILL_NAMES = [
    "khanote.start-my-day",
    "khanote.research.start",
    "khanote.research.ingest",
    "khanote.research.analyze",
    "khanote.research.save",
    "khanote.research.pipeline",
    "khanote.feed.add",
    "khanote.feed.list",
    "khanote.feed.pause",
    "khanote.feed.resume",
    "khanote.feed.remove",
    "khanote.discover.feedback",
    "khanote.researcher.add",
    "khanote.update",
]

# Terminal command pattern: "khanote start-my-day" as a CLI invocation
_TERMINAL_CMD_RE = re.compile(r"^\s*```\s*\n.*\bkhanote start-my-day\b", re.MULTILINE)
# Inline code block with the CLI command
_INLINE_TERMINAL_CMD_RE = re.compile(r"`khanote start-my-day`")


def _read_skill(name: str) -> str:
    path = _SKILLS_DIR / name / "SKILL.md"
    assert path.exists(), f"SKILL.md missing for {name}"
    return path.read_text()


@pytest.mark.parametrize("name", _SKILL_NAMES)
class TestSkillContent:
    def test_skill_file_exists(self, name: str) -> None:
        """Every skill must have a SKILL.md file."""
        assert (_SKILLS_DIR / name / "SKILL.md").exists()

    def test_skill_has_instructions_section(self, name: str) -> None:
        """Every SKILL.md must contain an Instructions section."""
        content = _read_skill(name)
        assert re.search(r"^#{1,3}\s+Instructions", content, re.MULTILINE), (
            f"{name}/SKILL.md missing '## Instructions' section"
        )

    def test_skill_not_terminal_command_doc(self, name: str) -> None:
        """No SKILL.md may document 'khanote start-my-day' as a terminal command."""
        content = _read_skill(name)
        assert not _TERMINAL_CMD_RE.search(content), (
            f"{name}/SKILL.md references 'khanote start-my-day' as a terminal command"
        )
        assert not _INLINE_TERMINAL_CMD_RE.search(content), (
            f"{name}/SKILL.md has inline `khanote start-my-day` terminal reference"
        )

    def test_skill_addressed_to_llm(self, name: str) -> None:
        """SKILL.md must use imperative mood addressed to the LLM (You/your)."""
        content = _read_skill(name)
        # Check for imperative language directed at the LLM
        has_imperative = bool(
            re.search(r"\bYou\b", content)
            or re.search(r"\byour\b", content, re.IGNORECASE)
            or re.search(r"^(Read|Write|Create|Load|Fetch|Save|Run|Check|Ask|Tell|Use|Find)\b", content, re.MULTILINE)
        )
        assert has_imperative, (
            f"{name}/SKILL.md does not appear to be addressed to the LLM (missing imperative verbs/pronouns)"
        )
