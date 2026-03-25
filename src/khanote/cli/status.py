"""Status command: show khanote configuration at a glance."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()

_API_KEY_NAMES = [
    "PERPLEXITY_API_KEY",
    "NEWSAPI_KEY",
    "PRODUCTHUNT_TOKEN",
    "GOOGLE_API_KEY",
    "GITHUB_TOKEN",
]


@dataclass
class ApiKeyStatus:
    name: str
    present: bool
    display: str


@dataclass
class PreferencesSummary:
    language: str
    role: str
    interests: list[str]
    depth: str


@dataclass
class StatusReport:
    initialized: bool
    tool: Optional[str] = None
    output_path: Optional[Path] = None
    feeds_count: int = 0
    preferences: Optional[PreferencesSummary] = None
    api_keys: list[ApiKeyStatus] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _mask_key(value: str) -> str:
    """Mask an API key, showing only the last 4 chars."""
    if len(value) <= 4:
        return f"****{value}"
    return f"****{value[-4:]}"


def build_status_report(vault_dir: Optional[Path] = None) -> StatusReport:
    """Build a StatusReport from config.yaml + preferences.yaml + env vars."""
    if vault_dir is None:
        from khanote.cli.update import _find_vault
        vault_dir = _find_vault()

    if vault_dir is None:
        return StatusReport(initialized=False)

    kdir = vault_dir / ".khanote"
    config_path = kdir / "config.yaml"

    if not config_path.exists():
        return StatusReport(initialized=False)

    try:
        config = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        return StatusReport(initialized=False)

    # Tool
    tools = config.get("initialized_tools", [])
    tool = tools[-1] if tools else None

    # Output path
    output_path = Path(config.get("vault_path", str(vault_dir)))

    # Feeds count
    feeds = config.get("feeds", {})
    feeds_count = len(feeds) if isinstance(feeds, dict) else 0

    report = StatusReport(
        initialized=True,
        tool=tool,
        output_path=output_path,
        feeds_count=feeds_count,
    )

    # Preferences
    prefs_path = kdir / "preferences.yaml"
    if prefs_path.exists():
        try:
            prefs = yaml.safe_load(prefs_path.read_text()) or {}
            report.preferences = PreferencesSummary(
                language=prefs.get("language", "en-US"),
                role=prefs.get("role", "mixed"),
                interests=prefs.get("interests", []),
                depth=prefs.get("depth", "summary"),
            )
        except Exception:
            report.warnings.append("preferences.yaml could not be read — run: khanote init")
    else:
        report.warnings.append("Missing preferences.yaml — run: khanote init")

    # API keys
    for key_name in _API_KEY_NAMES:
        value = os.environ.get(key_name, "")
        if value:
            report.api_keys.append(ApiKeyStatus(name=key_name, present=True, display=_mask_key(value)))
        else:
            report.api_keys.append(ApiKeyStatus(name=key_name, present=False, display="not set"))

    # Warnings
    if feeds_count == 0:
        report.warnings.append("No feeds configured — run /khanote.feed.add in your vibe coding tool")

    return report


def render_status_report(report: StatusReport) -> str:
    """Render a StatusReport to a plain string (ANSI allowed but no Rich markup in output)."""
    if not report.initialized:
        return "khanote is not initialized.\nRun: khanote init"

    lines = []

    # Header info
    if report.tool:
        lines.append(f"Tool:     {report.tool}")
    if report.output_path:
        path_str = str(report.output_path)
        home = str(Path.home())
        if path_str.startswith(home):
            path_str = "~" + path_str[len(home):]
        # Truncate long paths to fit 80-char panel (10 label chars + 70 for path)
        if len(path_str) > 68:
            path_str = "..." + path_str[-65:]
        lines.append(f"Output:   {path_str}")
    lines.append(f"Feeds:    {report.feeds_count} configured")

    # Preferences
    if report.preferences:
        lines.append(f"Language: {report.preferences.language}")
        lines.append(f"Role:     {report.preferences.role}")
        if report.preferences.interests:
            lines.append(f"Interests:{' ' + ', '.join(report.preferences.interests)}")
        lines.append(f"Depth:    {report.preferences.depth}")

    # API keys (compact — only show if present, list missing at end)
    lines.append("")
    lines.append("API Keys:")
    for key in report.api_keys:
        mark = "✓" if key.present else "✗"
        lines.append(f"  {mark} {key.name:<26} {key.display}")

    # Warnings
    if report.warnings:
        lines.append("")
        for w in report.warnings:
            lines.append(f"⚠ {w}")

    return "\n".join(lines)


def run_status() -> None:
    """Print khanote configuration status."""
    report = build_status_report()
    output = render_status_report(report)

    if not report.initialized:
        console.print(f"[yellow]{output}[/yellow]")
        return

    console.print(Panel(output, title="khanote status", width=80))
