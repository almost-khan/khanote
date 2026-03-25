"""Integration tests for khanote update flow (TDD)."""
from __future__ import annotations


import pytest
from typer.testing import CliRunner

from khanote.cli.app import app

runner = CliRunner()


@pytest.fixture
def initialized_vault(tmp_path, monkeypatch):
    """Vault that has been through khanote init with claude-code."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["init", "--tool", "claude-code"],
        input="\n\n\n\n\n\n\n",
    )
    assert result.exit_code == 0, result.output
    return tmp_path


class TestUpdateFlow:
    def test_update_redistributes_to_all_initialized_tools(self, initialized_vault):
        """After init claude-code + cursor, update should refresh both."""
        # Also init cursor
        runner.invoke(
            app,
            ["init", "--tool", "cursor"],
            input="\n\n\n\n\n\n\n",
        )
        from khanote.cli.update import run_update
        run_update(vault_dir=initialized_vault)
        # Both tool directories should still have skills
        assert list((initialized_vault / ".claude" / "commands").glob("*.md"))
        assert list((initialized_vault / ".cursor" / "rules").glob("*.md"))

    def test_update_refreshes_ssot(self, initialized_vault):
        """SSOT skills should be updated during update."""
        ssot = initialized_vault / ".khanote" / "skills"
        # Corrupt one skill
        skill_file = next(ssot.glob("**/*.md"))
        skill_file.write_text("corrupted content")

        from khanote.cli.update import run_update
        run_update(vault_dir=initialized_vault)

        # After update, SSOT should be fresh
        content = skill_file.read_text()
        assert "corrupted content" not in content
