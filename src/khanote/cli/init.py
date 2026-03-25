"""Init command: create .khanote/, distribute skills, update entry files, write config.yaml."""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel

from khanote.distribution.copier import SkillCopier
from khanote.distribution.entry_file import EntryFileUpdater

console = Console()

# Path to bundled skills (relative to this file: src/khanote/cli/ → skills/)
_PACKAGE_DIR = Path(__file__).parent.parent
_BUNDLED_SKILLS = _PACKAGE_DIR.parent.parent / "skills"  # repo root skills/
# Fallback: installed package data
_INSTALLED_SKILLS = _PACKAGE_DIR / "skills"


def _get_skills_dir() -> Path:
    """Return path to skills SSOT directory."""
    if _BUNDLED_SKILLS.exists():
        return _BUNDLED_SKILLS
    if _INSTALLED_SKILLS.exists():
        return _INSTALLED_SKILLS
    raise FileNotFoundError(
        "Skills directory not found. Ensure khanote is installed correctly."
    )


def run_init(
    vault_path: Path,
    tool_name: str,
    researcher_name: str,
) -> None:
    """Execute the init flow.

    1. Create .khanote/ structure
    2. Copy skills SSOT to .khanote/skills/
    3. Distribute skills to tool directory
    4. Update tool entry file
    5. Write config.yaml
    """
    vault_path = vault_path.resolve()
    khanote_dir = vault_path / ".khanote"
    khanote_dir.mkdir(exist_ok=True)

    skills_ssot = khanote_dir / "skills"

    # Step 1: Copy bundled skills to SSOT in vault
    bundled = _get_skills_dir()
    if bundled != skills_ssot:
        if skills_ssot.exists():
            shutil.rmtree(skills_ssot)
        shutil.copytree(bundled, skills_ssot)
    console.print("[green]✓[/green] Skills SSOT copied to .khanote/skills/")

    # Step 2: Copy context.md template to .khanote/
    context_src = _PACKAGE_DIR / "templates" / "context.md"
    context_dst = khanote_dir / "context.md"
    if context_src.exists():
        shutil.copy2(context_src, context_dst)

    # Step 3: Distribute skills to tool directory
    copier = SkillCopier(ssot_dir=skills_ssot, vault_dir=vault_path)
    written = copier.copy_all(tool_name)
    console.print(f"[green]✓[/green] {len(written)} skill(s) distributed to {tool_name}")

    # Step 4: Update tool entry file
    updater = EntryFileUpdater(vault_dir=vault_path)
    entry = updater.add_reference(tool_name)
    console.print(f"[green]✓[/green] Entry file updated: {entry.name}")

    # Step 5: Read existing config or create new one
    config_file = khanote_dir / "config.yaml"
    if config_file.exists():
        with config_file.open("r") as f:
            existing = yaml.safe_load(f) or {}
        initialized_tools = existing.get("initialized_tools", [])
        if tool_name not in initialized_tools:
            initialized_tools.append(tool_name)
        existing["initialized_tools"] = initialized_tools
        config_data = existing
    else:
        config_data = {
            "version": "0.1.0",
            "vault_path": str(vault_path),
            "initialized_tools": [tool_name],
            "research": {
                "default": researcher_name,
                "researchers": {
                    researcher_name: {"enabled": True},
                },
            },
        }

    with config_file.open("w") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    console.print("[green]✓[/green] config.yaml written")

    # Step 6: Collect preferences (language, role, interests) — new in spec-003
    _collect_preferences(khanote_dir, config_file)

    console.print(
        Panel(
            f"[bold green]khanote initialized![/bold green]\n\n"
            f"Vault: {vault_path}\n"
            f"Tool: {tool_name}\n"
            f"Researcher: {researcher_name}\n\n"
            f"Run [bold]khanote start-my-day[/bold] for your daily briefing.\n"
            f"Run [bold]/khanote.start-my-day[/bold] inside your vibe coding tool.\n\n"
            f"[dim]Tip: Edit preferences.yaml to customize language, depth, and tone.[/dim]",
            title="khanote init",
        )
    )


def _collect_preferences(khanote_dir: Path, config_file: Path) -> None:
    """Collect user preferences interactively and write preferences.yaml + starter feeds.

    This function is called after config.yaml is written. It:
    1. Prompts for language, role, and interests
    2. Writes preferences.yaml
    3. Selects and writes starter feeds to config.yaml
    4. API key prompts are optional and skippable
    """
    import typer
    from khanote.preferences.loader import PreferencesLoader
    from khanote.preferences.models import Preferences

    console.print("\n[bold cyan]Setting up your preferences...[/bold cyan]")
    console.print("[dim](Press Enter to accept defaults, Ctrl+C to skip)[/dim]\n")

    try:
        # Language
        language = typer.prompt("Output language (BCP 47 tag)", default="en-US")

        # Role
        console.print("Available roles: developer, pm, researcher, mixed")
        role = typer.prompt("Your role", default="mixed")
        if role not in ("developer", "pm", "researcher", "mixed"):
            console.print(f"[yellow]Unknown role '{role}', using 'mixed'[/yellow]")
            role = "mixed"

        # Interests (comma-separated)
        console.print("Interests help select starter feeds.")
        console.print("Examples: ai, web, devops, security, medical, climate, fintech, saas")
        interests_str = typer.prompt("Your interests (comma-separated, or Enter to skip)", default="")
        interests = [i.strip() for i in interests_str.split(",") if i.strip()] if interests_str else []

        # Write preferences.yaml
        prefs_loader = PreferencesLoader(khanote_dir)
        try:
            prefs = Preferences(language=language, role=role, interests=interests)
        except Exception:
            prefs = Preferences(role=role, interests=interests)
        prefs_loader.save_preferences(prefs)
        console.print("[green]✓[/green] preferences.yaml written")

        # Write starter feeds if interests provided
        if interests or role != "mixed":
            feeds = prefs_loader.select_starter_feeds(role=role, interests=interests or ["general"])
            if feeds:
                prefs_loader.write_starter_feeds_to_config(config_file, feeds)
                console.print(f"[green]✓[/green] {len(feeds)} starter feed(s) added to config.yaml")
            else:
                console.print("[dim]No starter feeds matched your profile — add feeds with khanote feed add[/dim]")

    except (KeyboardInterrupt, Exception):
        console.print("\n[dim]Preferences setup skipped. Edit preferences.yaml manually later.[/dim]")
