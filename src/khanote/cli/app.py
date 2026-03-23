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


if __name__ == "__main__":
    app()
