"""Update command: update SSOT skills and re-distribute to all initialized tools."""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from rich.console import Console

console = Console()


def run_update(vault_dir: Path | None = None) -> None:
    """Update SSOT skills and re-distribute to all initialized tools."""
    from khanote.cli.init import _get_skills_dir

    if vault_dir is None:
        vault_dir = _find_vault()

    if vault_dir is None:
        console.print("[red]Error:[/red] Could not find vault. Run [bold]khanote init[/bold] first.")
        return

    config_file = vault_dir / ".khanote" / "config.yaml"
    if not config_file.exists():
        console.print("[red]Error:[/red] config.yaml not found. Run [bold]khanote init[/bold] first.")
        return

    with config_file.open() as f:
        config = yaml.safe_load(f)

    initialized_tools = config.get("initialized_tools", [])
    if not initialized_tools:
        console.print("[yellow]No initialized tools found.[/yellow]")
        return

    # Update SSOT
    bundled = _get_skills_dir()
    ssot = vault_dir / ".khanote" / "skills"
    if bundled != ssot:
        shutil.rmtree(ssot, ignore_errors=True)
        shutil.copytree(bundled, ssot)
        console.print("[green]✓[/green] SSOT skills updated")

    # Re-distribute to all tools
    from khanote.distribution.copier import SkillCopier
    copier = SkillCopier(ssot_dir=ssot, vault_dir=vault_dir)
    for tool in initialized_tools:
        try:
            written = copier.copy_all(tool)
            console.print(f"[green]✓[/green] {tool}: {len(written)} skill(s) updated")
        except ValueError as e:
            console.print(f"[yellow]Warning:[/yellow] {e}")

    console.print("[bold green]Update complete.[/bold green]")


def _find_vault() -> Path | None:
    """Walk up from cwd looking for a .khanote/ directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".khanote").exists():
            return parent
    return None
