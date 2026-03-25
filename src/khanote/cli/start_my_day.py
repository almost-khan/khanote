"""start-my-day CLI command — daily briefing or ad-hoc research."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def run_start_my_day(query: Optional[str] = None) -> None:
    """Execute start-my-day command.

    No-argument mode: execute due feeds and generate daily briefing.
    With-argument mode: decompose query, route to researchers, synthesize report.

    Args:
        query: Optional research query. If None, runs daily briefing mode.
    """
    from khanote.cli._config_path import find_config_path

    config_path = find_config_path()
    if config_path is None:
        console.print(
            "[red]Error:[/red] No config.yaml found. Run [bold]khanote init[/bold] first."
        )
        raise typer.Exit(1)

    if query:
        _run_adhoc(query, config_path)
    else:
        _run_daily(config_path)


def _run_daily(config_path: Path) -> None:
    """Run daily briefing mode."""
    from khanote.briefing.daily import DailyBriefingOrchestrator

    console.print("[bold blue]📋 Generating daily briefing...[/bold blue]")

    try:
        orchestrator = DailyBriefingOrchestrator(config_path)
        result = orchestrator.run()

        path = result.get("path") if isinstance(result, dict) else result
        console.print(f"[green]✓[/green] Daily briefing saved to: [bold]{path}[/bold]")

        # Show summary stats
        content = result.get("content", "") if isinstance(result, dict) else ""
        if content:
            lines = content.split("\n")
            section_count = sum(1 for line in lines if line.startswith("## "))
            console.print(f"[dim]  {section_count} sections generated[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] Daily briefing failed: {e}")
        raise typer.Exit(1)


def _run_adhoc(query: str, config_path: Path) -> None:
    """Run ad-hoc research mode."""
    from khanote.briefing.adhoc import AdhocOrchestrator

    console.print(f"[bold blue]🔍 Researching:[/bold blue] {query}")

    try:
        orchestrator = AdhocOrchestrator(config_path)
        result = orchestrator.run(query=query)

        path = result.get("path") if isinstance(result, dict) else result
        console.print(f"[green]✓[/green] Research report saved to: [bold]{path}[/bold]")

    except Exception as e:
        console.print(f"[red]Error:[/red] Ad-hoc research failed: {e}")
        raise typer.Exit(1)
