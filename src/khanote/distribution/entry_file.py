"""Append/check context reference line in tool entry files."""
from __future__ import annotations

from pathlib import Path

from khanote.models.tool import TOOL_CONFIG

_REFERENCE_LINE = "\n<!-- khanote context -->\n@.khanote/context.md\n"
_REFERENCE_MARKER = ".khanote/context.md"


class EntryFileUpdater:
    """Append a one-line context reference to a tool's entry file.

    Idempotent: calling add_reference twice will not duplicate content.
    """

    def __init__(self, vault_dir: Path) -> None:
        self.vault_dir = Path(vault_dir)

    def add_reference(self, tool_name: str) -> Path:
        """Append context reference to the tool's entry file.

        Args:
            tool_name: Name of the tool (must be in TOOL_CONFIG).

        Returns:
            Path to the entry file.

        Raises:
            ValueError: If tool_name is not recognized.
        """
        if tool_name not in TOOL_CONFIG:
            available = ", ".join(TOOL_CONFIG.keys())
            raise ValueError(f"Unknown tool '{tool_name}'. Available: {available}")

        cfg = TOOL_CONFIG[tool_name]
        entry_path = self.vault_dir / cfg.entry_file

        # Read existing content or start fresh
        existing = entry_path.read_text(encoding="utf-8") if entry_path.exists() else ""

        # Idempotency check
        if _REFERENCE_MARKER in existing:
            return entry_path

        # Create parent dirs if needed (e.g., .cursor/)
        entry_path.parent.mkdir(parents=True, exist_ok=True)

        # Append reference
        with entry_path.open("a", encoding="utf-8") as f:
            f.write(_REFERENCE_LINE)

        return entry_path
