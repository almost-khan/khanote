"""Shared session utilities — DRY helpers used by analyze.py and save.py."""
from __future__ import annotations

import re
from pathlib import Path


def extract_sources(session_dir: Path) -> list[str]:
    """Extract source URLs/paths from _session.md.

    Parses the ``## Sources`` section and strips status prefixes like ``[ok]``.

    Args:
        session_dir: Path to the session directory containing ``_session.md``.

    Returns:
        List of source strings (URLs or file paths).
    """
    session_md = session_dir / "_session.md"
    if not session_md.exists():
        return []
    content = session_md.read_text(encoding="utf-8")
    sources: list[str] = []
    in_sources = False
    for line in content.splitlines():
        if line.strip() == "## Sources":
            in_sources = True
            continue
        if line.startswith("## ") and in_sources:
            break
        if in_sources and line.strip().startswith("- "):
            src = line.strip().lstrip("- ")
            if src.startswith("["):
                src = src.split("] ", 1)[-1] if "] " in src else src
            sources.append(src.strip())
    return sources


def update_session_status(session_dir: Path, status: str) -> None:
    """Update the ``status`` field in ``_session.md`` frontmatter.

    Args:
        session_dir: Path to the session directory.
        status: New status value (e.g. ``analyzed``, ``completed``).
    """
    session_md = session_dir / "_session.md"
    if not session_md.exists():
        return
    content = session_md.read_text(encoding="utf-8")
    content = re.sub(r"status:\s*\S+", f"status: {status}", content)
    session_md.write_text(content, encoding="utf-8")
