"""Feed subcommands — add, list, pause, resume, remove.

NOTE: All operations use guided conversational prompts — no CLI flags.
The actual guided flows are driven by the SKILL.md files in skills/.
These CLI commands are the underlying invocation points.
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from khanote.feeds.manager import FeedManager, FeedValidationError

console = Console()


def _get_config_path() -> Path:
    """Find config.yaml in .khanote/ relative to cwd, or raise."""
    candidates = [
        Path.cwd() / ".khanote" / "config.yaml",
        Path.home() / ".khanote" / "config.yaml",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise typer.BadParameter(
        "config.yaml not found. Run 'khanote init' first.",
    )


def feed_add(
    name: str | None = None,
    researcher: str | None = None,
    query: str | None = None,
) -> None:
    """Add a feed via guided flow (use /khanote.feed.add skill for full experience)."""
    console.print(
        "[yellow]Tip:[/yellow] For the best experience, run [bold]/khanote.feed.add[/bold] "
        "inside your vibe coding tool. The guided flow will prompt you interactively."
    )
    if not (name and researcher and query):
        console.print("[dim]No feed parameters provided — use the skill command for guided flow.[/dim]")
        raise typer.Exit(0)

    config_path = _get_config_path()
    manager = FeedManager(config_path)
    try:
        feed = manager.add_feed(name=name, researcher=researcher, query=query)
        console.print(f"[green]✓[/green] Feed '[bold]{feed.name}[/bold]' added.")
    except FeedValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def feed_list() -> None:
    """List all configured feeds in a Rich table."""
    try:
        config_path = _get_config_path()
    except typer.BadParameter as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    manager = FeedManager(config_path)
    feeds = manager.list_feeds()

    if not feeds:
        console.print("[dim]No feeds configured. Run /khanote.feed.add to create one.[/dim]")
        return

    orphans = set(manager.detect_orphans())
    table = Table(title="Configured Feeds")
    table.add_column("Feed", style="bold")
    table.add_column("Researcher")
    table.add_column("Query")
    table.add_column("Frequency")
    table.add_column("Active")
    table.add_column("Status")

    for name, feed in feeds.items():
        active_mark = "[green]✓[/green]" if feed.active else "[red]✗[/red]"
        status = "[red]orphaned[/red]" if name in orphans else ""
        query_display = feed.query[:30] + "…" if len(feed.query) > 30 else feed.query
        table.add_row(name, feed.researcher, query_display, feed.frequency, active_mark, status)

    console.print(table)


def feed_pause(name: str | None = None) -> None:
    """Pause a feed (sets active=false)."""
    if not name:
        console.print(
            "[yellow]Tip:[/yellow] Run [bold]/khanote.feed.pause[/bold] in your vibe coding tool "
            "for an interactive guided selection."
        )
        raise typer.Exit(0)
    config_path = _get_config_path()
    manager = FeedManager(config_path)
    try:
        manager.pause_feed(name)
        console.print(f"[green]✓[/green] Feed '[bold]{name}[/bold]' paused.")
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def feed_resume(name: str | None = None) -> None:
    """Resume a paused feed (sets active=true)."""
    if not name:
        console.print(
            "[yellow]Tip:[/yellow] Run [bold]/khanote.feed.resume[/bold] in your vibe coding tool."
        )
        raise typer.Exit(0)
    config_path = _get_config_path()
    manager = FeedManager(config_path)
    try:
        manager.resume_feed(name)
        console.print(f"[green]✓[/green] Feed '[bold]{name}[/bold]' resumed.")
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def feed_remove(name: str | None = None) -> None:
    """Remove a feed from config.yaml."""
    if not name:
        console.print(
            "[yellow]Tip:[/yellow] Run [bold]/khanote.feed.remove[/bold] in your vibe coding tool."
        )
        raise typer.Exit(0)
    config_path = _get_config_path()
    manager = FeedManager(config_path)
    try:
        manager.remove_feed(name)
        console.print(f"[green]✓[/green] Feed '[bold]{name}[/bold]' removed.")
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
