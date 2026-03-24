"""Check command: validate vault, tools, researchers, and API keys."""
from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

console = Console()


def run_check(vault_dir: Path | None = None) -> None:
    """Validate vault, tools, researchers, and API keys."""
    if vault_dir is None:
        from khanote.cli.update import _find_vault
        vault_dir = _find_vault()

    table = Table(title="khanote Status", show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    # Vault
    if vault_dir and vault_dir.exists():
        table.add_row("Vault", "[green]✓[/green]", str(vault_dir))
    else:
        table.add_row("Vault", "[red]✗[/red]", "Not found — run khanote init")
        console.print(table)
        return

    # Config
    config_file = vault_dir / ".khanote" / "config.yaml"
    if config_file.exists():
        table.add_row("Config", "[green]✓[/green]", str(config_file))
        with config_file.open() as f:
            config = yaml.safe_load(f)
    else:
        table.add_row("Config", "[red]✗[/red]", "config.yaml missing")
        console.print(table)
        return

    # Tools
    tools = config.get("initialized_tools", [])
    if tools:
        table.add_row("Tools", "[green]✓[/green]", ", ".join(tools))
    else:
        table.add_row("Tools", "[yellow]![/yellow]", "No tools initialized")

    # Researchers
    research = config.get("research", {})
    researchers = research.get("researchers", {})
    enabled = [n for n, r in researchers.items() if r.get("enabled", True)]
    if enabled:
        table.add_row("Researchers", "[green]✓[/green]", ", ".join(enabled))
    else:
        table.add_row("Researchers", "[red]✗[/red]", "No researchers enabled")

    # API Keys
    import os
    key_checks = {
        "perplexity": "PERPLEXITY_API_KEY",
        "arxiv": None,  # No key needed
        "notebooklm": "GOOGLE_API_KEY",
    }
    for name in enabled:
        env_var = key_checks.get(name)
        if env_var is None:
            table.add_row(f"  {name} key", "[green]✓[/green]", "No key required")
        elif os.environ.get(env_var):
            table.add_row(f"  {name} key", "[green]✓[/green]", f"${env_var} set")
        else:
            cfg = researchers.get(name, {})
            if cfg.get("api_key"):
                table.add_row(f"  {name} key", "[green]✓[/green]", "Set in config")
            else:
                table.add_row(f"  {name} key", "[yellow]![/yellow]", f"${env_var} not set")

    # Feeds (T050: include feed health in status table)
    feeds = config.get("feeds") or {}
    if feeds:
        from khanote.feeds.manager import FeedManager
        manager = FeedManager(config_file)
        orphans = manager.detect_orphans()
        active_feeds = [n for n, f in feeds.items() if f.get("active", True)]
        paused_feeds = [n for n, f in feeds.items() if not f.get("active", True)]
        feed_details = f"{len(active_feeds)} active, {len(paused_feeds)} paused"
        if orphans:
            feed_details += f", {len(orphans)} orphaned"
            table.add_row("Feeds", "[yellow]![/yellow]", f"{feed_details} — orphaned: {', '.join(orphans)}")
        else:
            table.add_row("Feeds", "[green]✓[/green]", feed_details)
    else:
        table.add_row("Feeds", "[dim]—[/dim]", "No feeds. Run /khanote.feed.add to create one.")

    console.print(table)
