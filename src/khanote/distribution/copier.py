"""Copy skills from SSOT to tool-native directories."""
from __future__ import annotations

from pathlib import Path

from khanote.models.tool import TOOL_CONFIG, ToolConfig


class SkillCopier:
    """Copy SKILL.md files from SSOT to a tool's native directory.

    The SSOT is the `skills/` directory (bundled with the package).
    Each skill is a subdirectory with a SKILL.md file.
    """

    def __init__(self, ssot_dir: Path, vault_dir: Path) -> None:
        self.ssot_dir = Path(ssot_dir)
        self.vault_dir = Path(vault_dir)

    def copy_all(self, tool_name: str) -> list[Path]:
        """Copy all skills to the tool's directory.

        Args:
            tool_name: Name of the tool (must be in TOOL_CONFIG).

        Returns:
            List of destination paths written.

        Raises:
            ValueError: If tool_name is not recognized.
        """
        if tool_name not in TOOL_CONFIG:
            available = ", ".join(TOOL_CONFIG.keys())
            raise ValueError(f"Unknown tool '{tool_name}'. Available: {available}")

        cfg = TOOL_CONFIG[tool_name]
        dest_dir = self.vault_dir / cfg.commands_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []
        for skill_dir in sorted(self.ssot_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            src = skill_dir / "SKILL.md"
            if not src.exists():
                continue
            dest = self._destination_path(cfg, dest_dir, skill_dir.name)
            self._write_skill(src, dest, cfg)
            written.append(dest)

        return written

    def _destination_path(self, cfg: ToolConfig, dest_dir: Path, skill_name: str) -> Path:
        """Compute destination path based on tool config."""
        if cfg.extension == "/SKILL.md":
            # Codex: preserve SKILL.md directory structure
            return dest_dir / skill_name / "SKILL.md"
        else:
            return dest_dir / f"{skill_name}{cfg.extension}"

    def _write_skill(self, src: Path, dest: Path, cfg: ToolConfig) -> None:
        """Read source, convert placeholders, write to destination."""
        content = src.read_text(encoding="utf-8")

        # Convert $ARGUMENTS placeholder to tool's native format
        if cfg.placeholder != "$ARGUMENTS":
            content = content.replace("$ARGUMENTS", cfg.placeholder)

        dest.parent.mkdir(parents=True, exist_ok=True)

        # Check idempotency: only write if content differs
        if dest.exists() and dest.read_text(encoding="utf-8") == content:
            return

        dest.write_text(content, encoding="utf-8")
