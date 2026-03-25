"""Tests for skill copier and entry file updater (TDD)."""
from __future__ import annotations


import pytest

from khanote.distribution.copier import SkillCopier
from khanote.distribution.entry_file import EntryFileUpdater


@pytest.fixture
def ssot_dir(tmp_path):
    """SSOT skills directory with a sample skill."""
    skills_dir = tmp_path / "skills"
    skill = skills_dir / "khanote.research.start"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "# khanote.research.start\n\nStart a research session with $ARGUMENTS"
    )
    return skills_dir


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path


class TestSkillCopier:
    def test_copies_skill_to_tool_directory(self, ssot_dir, vault_dir):
        copier = SkillCopier(ssot_dir=ssot_dir, vault_dir=vault_dir)
        copier.copy_all(tool_name="claude-code")
        dest = vault_dir / ".claude" / "commands" / "khanote.research.start.md"
        assert dest.exists()

    def test_copied_content_matches_source(self, ssot_dir, vault_dir):
        copier = SkillCopier(ssot_dir=ssot_dir, vault_dir=vault_dir)
        copier.copy_all(tool_name="claude-code")
        dest = vault_dir / ".claude" / "commands" / "khanote.research.start.md"
        content = dest.read_text()
        assert "khanote.research.start" in content

    def test_placeholder_converted_for_gemini(self, ssot_dir, vault_dir):
        """Gemini uses {{args}} instead of $ARGUMENTS, and .toml extension."""
        copier = SkillCopier(ssot_dir=ssot_dir, vault_dir=vault_dir)
        copier.copy_all(tool_name="gemini-cli")
        dest = vault_dir / ".gemini" / "commands" / "khanote.research.start.toml"
        content = dest.read_text()
        assert "{{args}}" in content
        assert "$ARGUMENTS" not in content

    def test_idempotent_copy(self, ssot_dir, vault_dir):
        """Running copy twice should not error or duplicate content."""
        copier = SkillCopier(ssot_dir=ssot_dir, vault_dir=vault_dir)
        copier.copy_all(tool_name="claude-code")
        copier.copy_all(tool_name="claude-code")
        dest = vault_dir / ".claude" / "commands" / "khanote.research.start.md"
        assert dest.exists()
        content = dest.read_text()
        # Content should not be doubled
        assert content.count("khanote.research.start") == 1

    def test_creates_destination_directory(self, ssot_dir, vault_dir):
        copier = SkillCopier(ssot_dir=ssot_dir, vault_dir=vault_dir)
        copier.copy_all(tool_name="cursor")
        dest_dir = vault_dir / ".cursor" / "rules"
        assert dest_dir.exists()

    def test_unknown_tool_raises(self, ssot_dir, vault_dir):
        copier = SkillCopier(ssot_dir=ssot_dir, vault_dir=vault_dir)
        with pytest.raises(ValueError):
            copier.copy_all(tool_name="unknown-tool")

    def test_codex_uses_skill_md_extension(self, ssot_dir, vault_dir):
        """Codex preserves SKILL.md directory structure."""
        copier = SkillCopier(ssot_dir=ssot_dir, vault_dir=vault_dir)
        copier.copy_all(tool_name="codex")
        dest = vault_dir / ".agents" / "skills" / "khanote.research.start" / "SKILL.md"
        assert dest.exists()


class TestEntryFileUpdater:
    def test_appends_reference_line_to_existing_file(self, vault_dir):
        entry = vault_dir / "CLAUDE.md"
        entry.write_text("# My Claude Config\n\nExisting content.\n")
        updater = EntryFileUpdater(vault_dir=vault_dir)
        updater.add_reference("claude-code")
        content = entry.read_text()
        assert ".khanote/context.md" in content

    def test_creates_file_if_missing(self, vault_dir):
        updater = EntryFileUpdater(vault_dir=vault_dir)
        updater.add_reference("claude-code")
        entry = vault_dir / "CLAUDE.md"
        assert entry.exists()
        assert ".khanote/context.md" in entry.read_text()

    def test_idempotent_no_duplicates(self, vault_dir):
        """Calling add_reference twice should not add duplicate lines."""
        updater = EntryFileUpdater(vault_dir=vault_dir)
        updater.add_reference("claude-code")
        updater.add_reference("claude-code")
        entry = vault_dir / "CLAUDE.md"
        content = entry.read_text()
        assert content.count(".khanote/context.md") == 1

    def test_creates_correct_entry_file_for_cursor(self, vault_dir):
        updater = EntryFileUpdater(vault_dir=vault_dir)
        updater.add_reference("cursor")
        entry = vault_dir / ".cursorrules"
        assert entry.exists()

    def test_unknown_tool_raises(self, vault_dir):
        updater = EntryFileUpdater(vault_dir=vault_dir)
        with pytest.raises(ValueError):
            updater.add_reference("unknown-tool")
