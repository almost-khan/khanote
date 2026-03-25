"""Typer app with init/update/check subcommands."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="khanote",
    help="Universal research workflow kit connecting vibe coding tools with Obsidian.",
    no_args_is_help=True,
)

researcher_app = typer.Typer(help="Manage custom researchers.", no_args_is_help=True)
app.add_typer(researcher_app, name="researcher")

feed_app = typer.Typer(help="Manage research feeds.", no_args_is_help=True)
app.add_typer(feed_app, name="feed")

discover_app = typer.Typer(help="Manage discover feedback (like/dislike).", no_args_is_help=True)
app.add_typer(discover_app, name="discover")

preferences_app = typer.Typer(help="Manage user preferences.", no_args_is_help=True)
app.add_typer(preferences_app, name="preferences")

console = Console()


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Run version check before any command."""
    # Lazy import to avoid circular issues
    if ctx.invoked_subcommand not in ("init",):
        try:
            from khanote.cli.version import check_version
            check_version()
        except Exception:
            pass  # Version check is advisory only


@app.command()
def init(
    vault: Optional[Path] = typer.Option(
        None,
        "--vault",
        help="Path to your Obsidian vault.",
        show_default=False,
    ),
    tool: Optional[str] = typer.Option(
        None,
        "--tool",
        help="Vibe coding tool to initialize (claude-code, cursor, codex, gemini-cli, opencode).",
        show_default=False,
    ),
    researcher: Optional[str] = typer.Option(
        None,
        "--researcher",
        help="Default researcher to use (perplexity, arxiv, notebooklm).",
        show_default=False,
    ),
) -> None:
    """Initialize khanote in your Obsidian vault."""
    from khanote.models.tool import TOOL_CONFIG

    # Interactive prompts for missing values
    if vault is None:
        vault_str = typer.prompt("Path to your Obsidian vault")
        vault = Path(vault_str)

    if not vault.exists():
        console.print(f"[red]Error:[/red] Vault path does not exist: {vault}")
        raise typer.Exit(1)

    if tool is None:
        available_tools = list(TOOL_CONFIG.keys())
        console.print(f"Available tools: {', '.join(available_tools)}")
        tool = typer.prompt("Which tool to initialize", default="claude-code")

    if tool not in TOOL_CONFIG:
        console.print(f"[red]Error:[/red] Unknown tool '{tool}'. Available: {', '.join(TOOL_CONFIG.keys())}")
        raise typer.Exit(1)

    if researcher is None:
        researcher = typer.prompt("Default researcher", default="perplexity")

    from khanote.cli.init import run_init
    run_init(vault_path=vault, tool_name=tool, researcher_name=researcher)


@app.command()
def update() -> None:
    """Update khanote skills to the latest version."""
    from khanote.cli.update import run_update
    run_update()


@app.command()
def check() -> None:
    """Validate vault, tools, researchers, and API keys."""
    from khanote.cli.check import run_check
    run_check()


@researcher_app.command("add")
def researcher_add() -> None:
    """Add a custom researcher via guided flow (run as a skill for best experience)."""
    console.print(
        "[yellow]Tip:[/yellow] For the best experience, run [bold]/khanote.researcher.add[/bold] "
        "inside your vibe coding tool (Claude Code, Cursor, etc.).\n"
        "The guided flow will prompt you interactively."
    )


@feed_app.command("add")
def _feed_add() -> None:
    """Add a feed via guided flow."""
    from khanote.cli.feed_commands import feed_add
    feed_add()


@feed_app.command("list")
def _feed_list() -> None:
    """List all configured feeds."""
    from khanote.cli.feed_commands import feed_list
    feed_list()


@feed_app.command("pause")
def _feed_pause(name: str = typer.Argument(None, help="Feed name to pause")) -> None:
    """Pause a feed."""
    from khanote.cli.feed_commands import feed_pause
    feed_pause(name)


@feed_app.command("resume")
def _feed_resume(name: str = typer.Argument(None, help="Feed name to resume")) -> None:
    """Resume a paused feed."""
    from khanote.cli.feed_commands import feed_resume
    feed_resume(name)


@feed_app.command("remove")
def _feed_remove(name: str = typer.Argument(None, help="Feed name to remove")) -> None:
    """Remove a feed."""
    from khanote.cli.feed_commands import feed_remove
    feed_remove(name)


@app.command("start-my-day")
def start_my_day(
    query: Optional[str] = typer.Argument(None, help="Optional research query for ad-hoc research mode."),
) -> None:
    """Run daily briefing (no args) or ad-hoc research (with query)."""
    from khanote.cli.start_my_day import run_start_my_day
    run_start_my_day(query=query)


@discover_app.command("like")
def _discover_like(item: str = typer.Argument(..., help="Topic or item to mark as liked.")) -> None:
    """Mark a discover item as liked."""
    from khanote.cli.discover_commands import discover_like
    discover_like(item)


@discover_app.command("dislike")
def _discover_dislike(item: str = typer.Argument(..., help="Topic or item to mark as disliked.")) -> None:
    """Mark a discover item as disliked."""
    from khanote.cli.discover_commands import discover_dislike
    discover_dislike(item)


@preferences_app.command("show")
def _preferences_show() -> None:
    """Show current preferences in a formatted table."""
    from khanote.cli.preferences_commands import preferences_show
    preferences_show()


if __name__ == "__main__":
    app()
