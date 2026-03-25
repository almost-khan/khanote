"""Preferences show command — display current user preferences."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console()


def preferences_show() -> None:
    """Display current preferences in a Rich table."""
    from khanote.cli._config_path import find_config_path
    from khanote.preferences.loader import PreferencesLoader
    from khanote.preferences.models import Preferences

    config_path = find_config_path()
    if config_path is None:
        console.print("[red]Error:[/red] No config.yaml found. Run [bold]khanote init[/bold] first.")
        return

    prefs_loader = PreferencesLoader(config_path.parent)
    prefs = prefs_loader.load_preferences()
    defaults = Preferences()

    table = Table(title="khanote Preferences", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")
    table.add_column("Default", style="dim")

    def row(name: str, value, default) -> None:
        v_str = str(value) if value is not None else "(empty)"
        d_str = str(default) if default is not None else "(empty)"
        is_default = value == default
        style = "dim" if is_default else "green"
        table.add_row(name, f"[{style}]{v_str}[/{style}]", d_str)

    row("language", prefs.language, defaults.language)
    row("role", prefs.role, defaults.role)
    row("interests", ", ".join(prefs.interests) if prefs.interests else "(none)", "(none)")
    row("depth", prefs.depth, defaults.depth)
    row("expertise", prefs.expertise, defaults.expertise)
    row("tone", prefs.tone, defaults.tone)
    row("discover.enabled", prefs.discover.enabled, defaults.discover.enabled)
    row("discover.serendipity", prefs.discover.serendipity, defaults.discover.serendipity)
    row("discover.count", prefs.discover.count, defaults.discover.count)

    if prefs.discover.liked_topics:
        row("discover.liked_topics", ", ".join(prefs.discover.liked_topics), "(none)")
    if prefs.discover.disliked_topics:
        row("discover.disliked_topics", ", ".join(prefs.discover.disliked_topics), "(none)")
    if prefs.discover.blocked_domains:
        row("discover.blocked_domains", ", ".join(prefs.discover.blocked_domains), "(none)")

    console.print(table)
    console.print(
        "\n[dim]Edit preferences.yaml directly or re-run [bold]khanote init[/bold] to update.[/dim]"
    )
