"""Discover like/dislike CLI commands."""
from __future__ import annotations

from rich.console import Console

console = Console()


def discover_like(item: str) -> None:
    """Mark a topic/item as liked in discover preferences."""
    from khanote.cli._config_path import find_config_path
    from khanote.preferences.loader import PreferencesLoader

    config_path = find_config_path()
    if config_path is None:
        console.print("[red]Error:[/red] No config.yaml found. Run [bold]khanote init[/bold] first.")
        return

    prefs_loader = PreferencesLoader(config_path.parent)
    prefs = prefs_loader.load_preferences()

    if item not in prefs.discover.liked_topics:
        prefs.discover.liked_topics.append(item)
    if item in prefs.discover.disliked_topics:
        prefs.discover.disliked_topics.remove(item)

    prefs_loader.save_preferences(prefs)
    console.print(f"[green]✓[/green] Added '{item}' to liked topics.")


def discover_dislike(item: str) -> None:
    """Mark a topic/item as disliked in discover preferences."""
    from khanote.cli._config_path import find_config_path
    from khanote.preferences.loader import PreferencesLoader

    config_path = find_config_path()
    if config_path is None:
        console.print("[red]Error:[/red] No config.yaml found. Run [bold]khanote init[/bold] first.")
        return

    prefs_loader = PreferencesLoader(config_path.parent)
    prefs = prefs_loader.load_preferences()

    if item not in prefs.discover.disliked_topics:
        prefs.discover.disliked_topics.append(item)
    if item in prefs.discover.liked_topics:
        prefs.discover.liked_topics.remove(item)

    prefs_loader.save_preferences(prefs)
    console.print(f"[green]✓[/green] Added '{item}' to disliked topics.")
