"""Typer app with init/update/check subcommands."""
from __future__ import annotations

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
    tool: Optional[str] = typer.Option(
        None,
        "--tool",
        help="Vibe coding tool to initialize (claude-code, cursor, codex, gemini-cli, opencode).",
        show_default=False,
    ),
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        help="Language code (en, zh, ja, ko, fr). If omitted, wizard prompts for language.",
        show_default=False,
    ),
) -> None:
    """Set up khanote in the current directory."""
    from khanote.cli.init import run_init_wizard
    run_init_wizard(tool=tool, lang=lang)


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


@app.command("start-my-day", hidden=True)
def start_my_day(
    query: Optional[str] = typer.Argument(None, help="Optional research query."),
) -> None:
    """Redirect: start-my-day is now a skill, not a CLI command."""
    from khanote.i18n import get_message
    console.print(f"[yellow]{get_message('error.start_my_day_removed', 'en')}[/yellow]")
    raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show khanote configuration status."""
    from khanote.cli.status import run_status
    run_status()


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
