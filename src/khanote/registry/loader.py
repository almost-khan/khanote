"""Registry loader — load researcher registry and set availability flags."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from khanote.registry.models import ResearcherRegistryEntry

_DEFAULT_REGISTRY_PATH = Path(__file__).parent.parent / "data" / "registry.yaml"


class RegistryLoader:
    """Load the researcher registry from YAML and set availability flags."""

    def __init__(self, registry_path: Path | str | None = None) -> None:
        self._registry_path = Path(registry_path) if registry_path else _DEFAULT_REGISTRY_PATH

    def load(self) -> dict[str, ResearcherRegistryEntry]:
        """Load registry.yaml and set available flag based on env vars.

        Returns:
            dict mapping researcher name → ResearcherRegistryEntry
        """
        if not self._registry_path.exists():
            return {}

        with self._registry_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return {
            name: self._parse_entry(name, entry_data)
            for name, entry_data in data.items()
        }

    def load_with_custom(self, config_path: Path | str) -> dict[str, ResearcherRegistryEntry]:
        """Load built-in registry + merge custom HTTP researchers from config.yaml.

        Args:
            config_path: Path to config.yaml

        Returns:
            Merged dict of all researchers
        """
        entries = self.load()
        config_path = Path(config_path)

        if not config_path.exists():
            return entries

        with config_path.open("r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        researchers = config_data.get("research", {}).get("researchers", {})
        for name, r_data in researchers.items():
            if r_data.get("type") == "http":
                # Custom HTTP researcher — auto-register
                entries[name] = ResearcherRegistryEntry(
                    name=name,
                    type="http",
                    domains=r_data.get("domains", []),
                    capabilities=r_data.get("capabilities", []),
                    description=r_data.get("description", f"Custom researcher: {name}"),
                    priority="specialized",
                    requires_key=bool(r_data.get("api_key")),
                    env_var=None,
                    available=r_data.get("enabled", True),
                )

        return entries

    def get_hint_message(
        self, researcher_name: str, entry: ResearcherRegistryEntry
    ) -> str | None:
        """Return a hint message if a researcher is unavailable due to missing key.

        Returns:
            Hint string if key is missing, None if available or no key required.
        """
        if not entry.requires_key:
            return None
        if entry.available:
            return None
        env_var = entry.env_var or f"{researcher_name.upper()}_API_KEY"
        return (
            f"Tip: Set {env_var} environment variable to enable {researcher_name}. "
            f"It provides: {entry.description}"
        )

    def _parse_entry(self, name: str, data: dict) -> ResearcherRegistryEntry:
        """Parse a single registry entry dict into a ResearcherRegistryEntry."""
        env_var = data.get("env_var")
        requires_key = data.get("requires_key", False)

        # Determine availability
        if not requires_key:
            available = True
        elif env_var:
            available = bool(os.environ.get(env_var))
        else:
            available = False

        return ResearcherRegistryEntry(
            name=name,
            type=data.get("type", "builtin"),
            domains=data.get("domains", []),
            capabilities=data.get("capabilities", []),
            description=data.get("description", ""),
            priority=data.get("priority", "specialized"),
            requires_key=requires_key,
            env_var=env_var if env_var and env_var != "null" else None,
            available=available,
        )


__all__ = ["RegistryLoader"]
