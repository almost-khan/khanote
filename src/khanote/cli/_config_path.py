"""Helper to locate the khanote config.yaml from the current working directory."""
from __future__ import annotations

from pathlib import Path


def find_config_path() -> Path | None:
    """Search for config.yaml starting from cwd upward.

    Looks in:
    1. .khanote/config.yaml in cwd
    2. .khanote/config.yaml in parent directories (up to 5 levels)

    Returns:
        Path to config.yaml if found, else None.
    """
    cwd = Path.cwd()
    candidate = cwd / ".khanote" / "config.yaml"
    if candidate.exists():
        return candidate

    for parent in cwd.parents:
        candidate = parent / ".khanote" / "config.yaml"
        if candidate.exists():
            return candidate

    return None
