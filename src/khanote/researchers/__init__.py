"""Researcher registry and factory."""
from __future__ import annotations

from typing import TYPE_CHECKING

from khanote.researchers.base import Researcher, ResearcherError

if TYPE_CHECKING:
    from khanote.models.config import ResearcherConfig
    from khanote.registry.models import ResearcherRegistryEntry

# Registry: maps researcher name → lazy import path
# Each entry: "module.path:ClassName"
RESEARCHER_REGISTRY: dict[str, str] = {
    "perplexity": "khanote.researchers.perplexity:PerplexityResearcher",
    "arxiv": "khanote.researchers.arxiv:ArxivResearcher",
    "notebooklm": "khanote.researchers.notebooklm:NotebookLMResearcher",
    "pubmed": "khanote.researchers.pubmed:PubMedResearcher",
    "github": "khanote.researchers.github_researcher:GitHubResearcher",
    "hackernews": "khanote.researchers.hackernews:HackerNewsResearcher",
    "newsapi": "khanote.researchers.newsapi:NewsAPIResearcher",
    "rss": "khanote.researchers.rss:RSSResearcher",
    "producthunt": "khanote.researchers.producthunt:ProductHuntResearcher",
    "local": "khanote.researchers.local_file:LocalFileResearcher",
}


class ResearcherFactory:
    """Instantiate researchers by name from the registry or config."""

    @staticmethod
    def create(name: str, config: "ResearcherConfig | None" = None, **kwargs) -> Researcher:
        """Create and return a researcher instance.

        If config.type == 'http', creates a ConfigResearcher. Otherwise
        falls back to the static registry lookup.

        Args:
            name: Researcher name.
            config: Optional ResearcherConfig. Required for type=http.
            **kwargs: Passed to the researcher's __init__ (built-in only).

        Raises:
            ResearcherError: If name not found or import fails.
        """
        if config is not None and config.type == "http":
            from khanote.researchers.config_researcher import ConfigResearcher
            return ConfigResearcher(name, config)

        if name not in RESEARCHER_REGISTRY:
            available = ", ".join(RESEARCHER_REGISTRY.keys())
            raise ResearcherError(
                f"Unknown researcher '{name}'. Available: {available}",
                researcher=name,
            )
        import importlib

        module_path, class_name = RESEARCHER_REGISTRY[name].rsplit(":", 1)
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return cls(**kwargs)
        except (ImportError, AttributeError) as e:
            raise ResearcherError(
                f"Failed to load researcher '{name}': {e}",
                researcher=name,
            ) from e

    @staticmethod
    def from_registry_entry(entry: "ResearcherRegistryEntry", **kwargs) -> "Researcher":
        """Create a researcher from a ResearcherRegistryEntry.

        Args:
            entry: Registry entry describing the researcher.
            **kwargs: Additional kwargs passed to the researcher constructor.

        Returns:
            Researcher instance.

        Raises:
            ResearcherError: If the researcher cannot be created or is unavailable.
        """
        if not entry.available:
            raise ResearcherError(
                f"Researcher '{entry.name}' is not available (missing API key or disabled).",
                researcher=entry.name,
            )
        return ResearcherFactory.create(entry.name, **kwargs)

    @staticmethod
    def available() -> list[str]:
        """Return list of registered researcher names."""
        return list(RESEARCHER_REGISTRY.keys())


__all__ = ["Researcher", "ResearcherError", "RESEARCHER_REGISTRY", "ResearcherFactory"]
