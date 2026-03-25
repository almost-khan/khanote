"""Init command: language-first interactive wizard for khanote setup."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import yaml
import typer
from rich.console import Console
from rich.panel import Panel

from khanote.distribution.copier import SkillCopier
from khanote.distribution.entry_file import EntryFileUpdater
from khanote.i18n import get_message

console = Console()

# Path to bundled skills (relative to this file: src/khanote/cli/ → skills/)
_PACKAGE_DIR = Path(__file__).parent.parent
_BUNDLED_SKILLS = _PACKAGE_DIR.parent.parent / "skills"  # repo root skills/
_INSTALLED_SKILLS = _PACKAGE_DIR / "skills"

_TOOL_NAMES = ["claude-code", "cursor", "codex", "gemini-cli", "opencode"]
_ROLE_NAMES = ["developer", "pm", "researcher", "operations", "mixed"]
_INTEREST_OPTIONS = [
    "ai", "product", "market", "tech", "medical",
    "finance", "sports", "climate", "security", "devops", "web", "saas",
]
_SUPPORTED_LANGUAGES = {"en", "zh", "ja", "ko", "fr"}

# Language code → BCP-47 tag stored in preferences
_LANG_TO_BCP47 = {
    "en": "en-US", "zh": "zh-CN", "ja": "ja-JP", "ko": "ko-KR", "fr": "fr-FR",
    "1": "en-US", "2": "zh-CN", "3": "ja-JP", "4": "ko-KR", "5": "fr-FR",
}


class WizardState:
    """Holds wizard step order and built-in defaults."""

    step_order = ["language", "tool", "role", "interests", "api_keys"]

    defaults = {
        "language": "en",
        "tool": "claude-code",
        "role": "mixed",
        "interests": "",
    }


def _get_skills_dir() -> Path:
    if _BUNDLED_SKILLS.exists():
        return _BUNDLED_SKILLS
    if _INSTALLED_SKILLS.exists():
        return _INSTALLED_SKILLS
    raise FileNotFoundError("Skills directory not found. Ensure khanote is installed correctly.")


def ensure_output_path(path: Path) -> None:
    """Create output path if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] {get_message('wizard.path_created', 'en').format(path=path)}")


def check_tool_installed(tool: str, base_dir: Path) -> Optional[str]:
    """Return warning string if tool's commands dir is missing, else None."""
    from khanote.models.tool import TOOL_CONFIG
    cfg = TOOL_CONFIG.get(tool)
    if cfg is None:
        return None
    expected = base_dir / cfg.commands_dir
    if not expected.exists():
        return get_message("wizard.tool_not_found", "en").format(tool=tool)
    return None


def load_existing_defaults(base_dir: Path) -> dict:
    """Load current config/preferences as wizard defaults for re-init."""
    defaults = dict(WizardState.defaults)
    kdir = base_dir / ".khanote"

    config_path = kdir / "config.yaml"
    if config_path.exists():
        try:
            data = yaml.safe_load(config_path.read_text()) or {}
            tools = data.get("initialized_tools", [])
            if tools:
                defaults["tool"] = tools[-1]
            defaults["output_path"] = str(base_dir)
        except Exception:
            pass

    prefs_path = kdir / "preferences.yaml"
    if prefs_path.exists():
        try:
            prefs = yaml.safe_load(prefs_path.read_text()) or {}
            if prefs.get("language"):
                lang_tag = prefs["language"]
                # Convert BCP-47 back to short code for wizard default
                prefix = lang_tag.split("-")[0].split("_")[0].lower()
                defaults["language"] = prefix if prefix in _SUPPORTED_LANGUAGES else "en"
            if prefs.get("role"):
                defaults["role"] = prefs["role"]
            if prefs.get("interests"):
                defaults["interests"] = ",".join(prefs["interests"])
        except Exception:
            pass

    return defaults


def _write_config_files(
    output_path: Path,
    tool: str,
    language: str,
    role: str,
    interests: list[str],
    api_keys: dict[str, str],
    existing_config: dict,
) -> None:
    """Write config.yaml, preferences.yaml, copy skills, update entry file.

    Called only after ALL wizard inputs collected — atomic from caller's perspective.
    """
    kdir = output_path / ".khanote"
    kdir.mkdir(exist_ok=True)

    # Copy bundled skills to SSOT
    bundled = _get_skills_dir()
    skills_ssot = kdir / "skills"
    if bundled != skills_ssot:
        if skills_ssot.exists():
            shutil.rmtree(skills_ssot)
        shutil.copytree(bundled, skills_ssot)

    # Copy context.md template
    context_src = _PACKAGE_DIR / "templates" / "context.md"
    context_dst = kdir / "context.md"
    if context_src.exists():
        shutil.copy2(context_src, context_dst)

    # Distribute skills to tool directory
    copier = SkillCopier(ssot_dir=skills_ssot, vault_dir=output_path)
    copier.copy_all(tool)

    # Update tool entry file
    updater = EntryFileUpdater(vault_dir=output_path)
    updater.add_reference(tool)

    # Build config.yaml — preserve existing feeds/researchers
    config_data = dict(existing_config) if existing_config else {}
    initialized_tools = config_data.get("initialized_tools", [])
    if tool not in initialized_tools:
        initialized_tools.append(tool)
    config_data["version"] = config_data.get("version", "0.1.0")
    config_data["vault_path"] = str(output_path)
    config_data["initialized_tools"] = initialized_tools
    if "research" not in config_data:
        config_data["research"] = {"default": "arxiv", "researchers": {"arxiv": {"enabled": True}}}

    # Add API keys to config
    for researcher, key_val in api_keys.items():
        if key_val:
            config_data["research"].setdefault("researchers", {})[researcher] = {
                "enabled": True,
                "api_key": key_val,
            }
            if researcher == "perplexity":
                config_data["research"]["default"] = "perplexity"

    config_file = kdir / "config.yaml"
    config_file.write_text(yaml.dump(config_data, default_flow_style=False, allow_unicode=True))

    # Write preferences.yaml
    from khanote.preferences.loader import PreferencesLoader
    from khanote.preferences.models import Preferences

    lang_bcp47 = _LANG_TO_BCP47.get(language, language)
    try:
        prefs = Preferences(language=lang_bcp47, role=role, interests=interests)
    except Exception:
        prefs = Preferences(role=role, interests=interests)

    prefs_loader = PreferencesLoader(kdir)
    prefs_loader.save_preferences(prefs)

    # Starter feeds
    if interests or role != "mixed":
        feeds = prefs_loader.select_starter_feeds(role=role, interests=interests or ["general"])
        if feeds:
            prefs_loader.write_starter_feeds_to_config(config_file, feeds)


def run_init_wizard(
    tool: Optional[str] = None,
    lang: Optional[str] = None,
) -> None:
    """Execute the language-first init wizard.

    Installs in the current working directory (like speckit).
    Collects all inputs before writing any files (Ctrl+C atomicity).
    """
    # Output is always the current working directory
    resolved_output = Path.cwd().resolve()

    # Detect re-init
    existing_config: dict = {}
    is_reinit = False
    kdir = resolved_output / ".khanote"
    if kdir.exists() and (kdir / "config.yaml").exists():
        is_reinit = True
        try:
            existing_config = yaml.safe_load((kdir / "config.yaml").read_text()) or {}
        except Exception:
            existing_config = {}

    # Load defaults (from existing config for re-init, or built-in)
    if is_reinit:
        defaults = load_existing_defaults(resolved_output)
    else:
        defaults = dict(WizardState.defaults)

    # ── Step 1: Language (always shown; shown in ALL languages simultaneously) ──
    if lang:
        selected_lang = lang.split("-")[0].split("_")[0].lower()
    else:
        console.print(
            "\n[bold]khanote setup[/bold]\n"
            + get_message("wizard.language_prompt", "en") + " / "
            + get_message("wizard.language_prompt", "zh") + " / "
            + get_message("wizard.language_prompt", "ja") + "\n"
            + get_message("wizard.language_choices", "en")
        )
        lang_input = typer.prompt(
            get_message("wizard.language_prompt", "en"),
            default=defaults.get("language", "en"),
        ).strip().lower()
        # Map numeric choices to codes
        code_map = {"1": "en", "2": "zh", "3": "ja", "4": "ko", "5": "fr"}
        selected_lang = code_map.get(lang_input, lang_input.split("-")[0].split("_")[0])

    # Effective language for subsequent prompts (fallback to en if unsupported)
    eff_lang = selected_lang if selected_lang in _SUPPORTED_LANGUAGES else "en"

    # ── Re-init notice ─────────────────────────────────────────────────────────
    if is_reinit:
        console.print(f"\n[yellow]{get_message('wizard.reinit_notice', eff_lang)}[/yellow]")

    # ── Step 2: Tool ───────────────────────────────────────────────────────────
    if tool:
        selected_tool = tool
    else:
        console.print(f"\n{get_message('wizard.tool_choices', eff_lang)}")
        tool_input = typer.prompt(
            get_message("wizard.tool_prompt", eff_lang),
            default=defaults.get("tool", "claude-code"),
        ).strip().lower()
        tool_map = {"1": "claude-code", "2": "cursor", "3": "codex", "4": "gemini-cli", "5": "opencode"}
        selected_tool = tool_map.get(tool_input, tool_input)
        if selected_tool not in _TOOL_NAMES:
            selected_tool = "claude-code"

    # ── Step 3: Role ───────────────────────────────────────────────────────────
    console.print(f"\n{get_message('wizard.role_choices', eff_lang)}")
    role_input = typer.prompt(
        get_message("wizard.role_prompt", eff_lang),
        default=defaults.get("role", "mixed"),
    ).strip().lower()
    role_map = {"1": "developer", "2": "pm", "3": "researcher", "4": "operations", "5": "mixed"}
    selected_role = role_map.get(role_input, role_input)
    if selected_role not in _ROLE_NAMES:
        selected_role = "mixed"

    # ── Step 4: Interests ──────────────────────────────────────────────────────
    console.print(f"\n[dim]{get_message('wizard.interests_hint', eff_lang)}[/dim]")
    interests_str = typer.prompt(
        get_message("wizard.interests_prompt", eff_lang),
        default=defaults.get("interests", ""),
    ).strip()
    selected_interests = [i.strip().lower() for i in interests_str.split(",") if i.strip()] if interests_str else []

    # ── Step 5: API Keys ───────────────────────────────────────────────────────
    console.print(f"\n{get_message('wizard.apikey_prompt', eff_lang)}")
    api_keys: dict[str, str] = {}

    api_key_fields = [
        ("perplexity", "PERPLEXITY_API_KEY"),
        ("newsapi", "NEWSAPI_KEY"),
        ("producthunt", "PRODUCTHUNT_TOKEN"),
        ("notebooklm", "GOOGLE_API_KEY"),
    ]
    for researcher, env_var in api_key_fields:
        key_val = typer.prompt(f"  {env_var}", default="", show_default=False).strip()
        if key_val:
            # Validate
            console.print(f"  [dim]{get_message('wizard.apikey_validating', eff_lang)}[/dim]", end=" ")
            from khanote.validation.api_keys import validate_api_key
            result = validate_api_key(researcher, key_val)
            if result.valid is True:
                console.print(f"[green]{get_message('wizard.apikey_valid', eff_lang)}[/green]")
            elif result.valid is False:
                console.print(f"[yellow]{get_message('wizard.apikey_invalid', eff_lang)}[/yellow]")
            else:
                console.print(f"[dim]{get_message('wizard.apikey_skipped', eff_lang)}[/dim]")
            api_keys[researcher] = key_val
        else:
            console.print(f"  [dim]{get_message('wizard.apikey_skipped', eff_lang)}[/dim]")

    # ── All inputs collected — now write files ─────────────────────────────────
    ensure_output_path(resolved_output)
    _write_config_files(
        output_path=resolved_output,
        tool=selected_tool,
        language=selected_lang,
        role=selected_role,
        interests=selected_interests,
        api_keys=api_keys,
        existing_config=existing_config,
    )

    # ── Post-init panel ────────────────────────────────────────────────────────
    from khanote.models.tool import TOOL_CONFIG
    tool_cfg = TOOL_CONFIG.get(selected_tool)
    restart_msg = get_message(tool_cfg.restart_instruction if tool_cfg else "restart.claude-code", eff_lang)

    # Check if tool is installed
    tool_warning = check_tool_installed(selected_tool, resolved_output)

    panel_lines = [
        f"[bold green]{get_message('init.success_title', eff_lang)}[/bold green]\n",
        f"[bold]{get_message('init.next_steps_header', eff_lang)}[/bold]\n",
        f"{get_message('init.step1_restart', eff_lang)}\n   {restart_msg}\n",
        f"{get_message('init.step2_run_skill', eff_lang)}\n   [bold cyan]/khanote.start-my-day[/bold cyan]\n",
        f"[dim]{get_message('init.tip_status', eff_lang)}[/dim]",
    ]
    if tool_warning:
        panel_lines.insert(2, f"[yellow]{tool_warning}[/yellow]\n")

    console.print(Panel("\n".join(panel_lines), title="khanote init"))

    console.print(f"[green]✓[/green] Output: {resolved_output}")
    console.print(f"[green]✓[/green] Tool: {selected_tool}")
