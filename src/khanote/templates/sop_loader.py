"""SOP prompt template loader — load and fill SOP templates for ConfigResearcher."""
from __future__ import annotations

import re
import string
from pathlib import Path

_DEFAULT_SOP_DIR = Path(__file__).parent / "sop"


class SopTemplateNotFoundError(Exception):
    """Raised when a requested SOP template does not exist."""


class SopLoader:
    """Load SOP templates from a directory and fill placeholders via str.format_map."""

    def __init__(self, sop_dir: Path | str | None = None) -> None:
        self._dir = Path(sop_dir) if sop_dir is not None else _DEFAULT_SOP_DIR

    def load(self, capability: str) -> str:
        """Load an SOP template by capability name (e.g., 'analyze'), strip frontmatter."""
        path = self._dir / f"{capability}.md"
        if not path.exists():
            raise SopTemplateNotFoundError(
                f"No SOP template found for capability '{capability}' in {self._dir}"
            )
        content = path.read_text(encoding="utf-8")
        return _strip_frontmatter(content)

    def fill(self, capability: str, **kwargs: str) -> str:
        """Load template for *capability* and fill known placeholders."""
        template = self.load(capability)
        return fill_string(template, **kwargs)

    def fill_string(self, template: str, **kwargs: str) -> str:
        """Fill placeholders in an arbitrary template string."""
        return fill_string(template, **kwargs)


def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter (--- ... ---) from beginning of template."""
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return content
    end = stripped.find("---", 3)
    if end == -1:
        return content
    return stripped[end + 3:].lstrip("\n")


def fill_string(template: str, **kwargs: str) -> str:
    """Fill known placeholders in *template* using str.format_map with safe fallback.

    Unknown placeholders (not in kwargs) are left unchanged as literal {name}.
    """
    return template.format_map(_SafeFormatMap(kwargs))


class _SafeFormatMap(dict):
    """dict subclass that returns '{key}' for missing keys instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
