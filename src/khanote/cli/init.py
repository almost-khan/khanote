"""Init command: language-first interactive wizard for khanote setup."""
from __future__ import annotations

import sys
import shutil
from pathlib import Path
from typing import Optional

import yaml
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from khanote.distribution.copier import SkillCopier
from khanote.distribution.entry_file import EntryFileUpdater
from khanote.i18n import get_message

console = Console()

# ── Brand colors ──────────────────────────────────────────────────────────────
_GRADIENT = ["#00e5ff", "#00d4f5", "#00c4eb", "#00b3e0", "#00a3d6", "#0093cc"]
_ACCENT = "#00bcd4"  # Primary cyan
_SUCCESS = "#4caf50"
_DIM = "dim"

# ── ASCII Art Logo (ANSI Shadow style) ────────────────────────────────────────
_LOGO_LINES = [
    r"  ██╗  ██╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ████████╗███████╗",
    r"  ██║ ██╔╝██║  ██║██╔══██╗████╗  ██║██╔═══██╗╚══██╔══╝██╔════╝",
    r"  █████╔╝ ███████║███████║██╔██╗ ██║██║   ██║   ██║   █████╗  ",
    r"  ██╔═██╗ ██╔══██║██╔══██║██║╚██╗██║██║   ██║   ██║   ██╔══╝  ",
    r"  ██║  ██╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝   ██║   ███████╗",
    r"  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝    ╚═╝   ╚══════╝",
]

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

_LANG_DISPLAY = {
    "en": "English",
    "zh": "中文 (Chinese)",
    "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)",
    "fr": "Français (French)",
}

_TOOL_DISPLAY = {
    "claude-code": "Claude Code",
    "cursor": "Cursor",
    "codex": "OpenAI Codex CLI",
    "gemini-cli": "Gemini CLI",
    "opencode": "OpenCode",
}

_ROLE_DISPLAY = {
    "developer": "Developer",
    "pm": "Product Manager",
    "researcher": "Researcher",
    "operations": "Operations",
    "mixed": "Mixed / Other",
}

_OTHER_CUSTOM_LABEL = "Other (custom)"

_TOTAL_STEPS = 5


def _print_banner() -> None:
    """Print the gradient ASCII art banner with tagline."""
    console.print()
    for i, line in enumerate(_LOGO_LINES):
        color = _GRADIENT[i % len(_GRADIENT)]
        console.print(f"[{color}]{line}[/{color}]")
    console.print()
    tagline = Text("  Your AI research workflow companion", style="italic dim")
    from khanote import __version__
    tagline.append(f"  v{__version__}", style=f"bold {_ACCENT}")
    console.print(tagline)
    console.print()


def _fmt_choice(code: str, display: str) -> str:
    """Format a questionary choice as 'Display (code)' for test inspectability."""
    return f"{display} ({code})"


def _parse_code(chosen: str, mapping: dict[str, str]) -> str:
    """Extract code from 'Display (code)' string, falling back to mapping lookup."""
    import re as _re
    m = _re.search(r"\(([^)]+)\)$", chosen)
    return m.group(1) if m else mapping.get(chosen, chosen)


def _is_tty() -> bool:
    return sys.stdin.isatty()


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


def _render_success_panel(
    tool: str,
    language: str,
    role: str,
    interests: list[str],
    api_keys_count: int,
) -> None:
    """Render the post-init Rich Panel with configuration summary."""
    from rich.box import HEAVY
    from khanote.models.tool import TOOL_CONFIG

    eff_lang = language if language in _SUPPORTED_LANGUAGES else "en"
    tool_cfg = TOOL_CONFIG.get(tool)
    restart_msg = get_message(
        tool_cfg.restart_instruction if tool_cfg else "restart.claude-code", eff_lang
    )

    lang_display = _LANG_DISPLAY.get(language, language)
    tool_display = _TOOL_DISPLAY.get(tool, tool)
    interests_display = ", ".join(interests) if interests else "(none)"
    api_display = str(api_keys_count) if api_keys_count else "0"

    # ── Checkmark header ──
    console.print()
    header = Text()
    header.append("  ✔ ", style=f"bold {_SUCCESS}")
    header.append(get_message("init.success_title", eff_lang), style=f"bold {_SUCCESS}")
    console.print(header)
    console.print()

    # ── Config summary table ──
    table = Table(
        show_header=False,
        box=HEAVY,
        border_style=_ACCENT,
        padding=(0, 2),
        title=f"[bold {_ACCENT}]Configuration[/bold {_ACCENT}]",
        title_style=f"bold {_ACCENT}",
    )
    table.add_column(style="dim", min_width=12)
    table.add_column()

    table.add_row("Language", f"[bold]{lang_display}[/bold]  [dim]({language})[/dim]")
    table.add_row("Tool", f"[bold {_ACCENT}]{tool_display}[/bold {_ACCENT}]")
    table.add_row("Role", f"[bold]{role.title()}[/bold]")
    table.add_row("Interests", f"[bold]{interests_display}[/bold]")
    table.add_row("API Keys", f"[bold]{api_display}[/bold] configured")

    console.print(table)

    # ── Next steps ──
    console.print()
    console.print(f"  [bold]{get_message('init.next_steps_header', eff_lang)}[/bold]")
    console.print()
    step1_msg = get_message('init.step1_restart', eff_lang)
    # Strip leading "1. " or "1." if the i18n message already includes numbering
    for prefix in ("1. ", "1.", "2. ", "2."):
        step1_msg = step1_msg.removeprefix(prefix).lstrip()
    step2_msg = get_message('init.step2_run_skill', eff_lang)
    for prefix in ("1. ", "1.", "2. ", "2."):
        step2_msg = step2_msg.removeprefix(prefix).lstrip()

    console.print(f"  [{_ACCENT}]1.[/{_ACCENT}] {step1_msg}")
    console.print(f"     [bold {_ACCENT}]$ {restart_msg}[/bold {_ACCENT}]")
    console.print()
    console.print(f"  [{_ACCENT}]2.[/{_ACCENT}] {step2_msg}")
    console.print(f"     [bold {_ACCENT}]/khanote.start-my-day[/bold {_ACCENT}]")
    console.print()
    console.print(f"  [dim]{get_message('init.tip_status', eff_lang)}[/dim]")
    console.print()


def _print_step(step_num: int, label: str) -> None:
    """Print step header with dot progress indicator."""
    dots = Text()
    for i in range(1, _TOTAL_STEPS + 1):
        if i < step_num:
            dots.append("● ", style=_SUCCESS)
        elif i == step_num:
            dots.append("● ", style=f"bold {_ACCENT}")
        else:
            dots.append("○ ", style="dim")
    step_text = Text(f" Step {step_num} of {_TOTAL_STEPS}", style="dim")
    console.print()
    console.print(dots, step_text)
    console.print(f"  [bold]{label}[/bold]")


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
    Uses questionary (arrow-key navigation) in TTY mode; falls back to
    typer.prompt in non-TTY / piped environments.
    """
    use_interactive = _is_tty()

    # Show branded banner in TTY mode
    if use_interactive:
        _print_banner()

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

    # Parse existing interests for questionary default pre-selection
    existing_interests: list[str] = []
    if defaults.get("interests"):
        existing_interests = [i.strip() for i in defaults["interests"].split(",") if i.strip()]

    # ── Step 1: Language ───────────────────────────────────────────────────────
    if lang:
        selected_lang = lang.split("-")[0].split("_")[0].lower()
    elif use_interactive:
        import questionary

        _print_step(1, "Language / 语言 / 言語")

        lang_choices = [_fmt_choice(k, v) for k, v in _LANG_DISPLAY.items()]
        default_lang_str = _fmt_choice(
            defaults.get("language", "en"),
            _LANG_DISPLAY.get(defaults.get("language", "en"), "English"),
        )
        result = questionary.select(
            "Choose your language:",
            choices=lang_choices,
            default=default_lang_str,
        ).ask()
        selected_lang = _parse_code(result, {v: k for k, v in _LANG_DISPLAY.items()}) if result else defaults.get("language", "en")
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
    elif use_interactive:
        import questionary

        _print_step(2, get_message("wizard.tool_prompt", eff_lang))

        tool_choices = [_fmt_choice(k, v) for k, v in _TOOL_DISPLAY.items()]
        default_tool_str = _fmt_choice(
            defaults.get("tool", "claude-code"),
            _TOOL_DISPLAY.get(defaults.get("tool", "claude-code"), "Claude Code"),
        )
        result = questionary.select(
            get_message("wizard.tool_prompt", eff_lang),
            choices=tool_choices,
            default=default_tool_str,
        ).ask()
        selected_tool = _parse_code(result, {v: k for k, v in _TOOL_DISPLAY.items()}) if result else "claude-code"
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
    if use_interactive:
        import questionary

        _print_step(3, get_message("wizard.role_prompt", eff_lang))

        role_choices = [_fmt_choice(k, v) for k, v in _ROLE_DISPLAY.items()]
        default_role_str = _fmt_choice(
            defaults.get("role", "mixed"),
            _ROLE_DISPLAY.get(defaults.get("role", "mixed"), "Mixed / Other"),
        )
        result = questionary.select(
            get_message("wizard.role_prompt", eff_lang),
            choices=role_choices,
            default=default_role_str,
        ).ask()
        selected_role = _parse_code(result, {v: k for k, v in _ROLE_DISPLAY.items()}) if result else "mixed"
    else:
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
    if use_interactive:
        import questionary

        _print_step(4, get_message("wizard.interests_prompt", eff_lang))

        # Prominent instruction before the checkbox prompt
        if eff_lang == "zh":
            console.print(f"  [{_ACCENT}]提示：按 空格键 选择/取消，选好后按 Enter 确认[/{_ACCENT}]")
        else:
            console.print(f"  [{_ACCENT}]Tip: press Space to select, Enter to confirm[/{_ACCENT}]")

        # Build Choice objects — pre-check items from existing config on re-init
        default_set = set(existing_interests) & set(_INTEREST_OPTIONS)
        interest_choices = [
            questionary.Choice(title=opt, checked=(opt in default_set))
            for opt in _INTEREST_OPTIONS
        ] + [questionary.Choice(title=_OTHER_CUSTOM_LABEL, checked=False)]

        selected_raw: list = questionary.checkbox(
            get_message("wizard.interests_prompt", eff_lang),
            choices=interest_choices,
            instruction="(Space = select, Enter = confirm)",
        ).ask() or []

        def _choice_label(s) -> str:
            """Get display label from a raw checkbox result (str or Choice)."""
            if isinstance(s, str):
                return s
            return getattr(s, "title", None) or getattr(s, "value", None) or str(s)

        selected_interests: list[str] = []
        has_custom = any(
            "other" in _choice_label(s).lower() or "custom" in _choice_label(s).lower()
            for s in selected_raw
        )

        for item in selected_raw:
            label = _choice_label(item)
            if "other" not in label.lower() and "custom" not in label.lower():
                selected_interests.append(label)

        if has_custom:
            custom_raw = questionary.text(
                "Enter custom interests (comma-separated):",
            ).ask() or ""
            custom_list = [i.strip().lower() for i in custom_raw.split(",") if i.strip()]
            selected_interests.extend(custom_list)
    else:
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

    # ── Post-init success screen ───────────────────────────────────────────────
    tool_warning = check_tool_installed(selected_tool, resolved_output)
    if tool_warning:
        console.print(f"\n[yellow]⚠[/yellow] {tool_warning}")

    _render_success_panel(
        tool=selected_tool,
        language=selected_lang,
        role=selected_role,
        interests=selected_interests,
        api_keys_count=len([v for v in api_keys.values() if v]),
    )
