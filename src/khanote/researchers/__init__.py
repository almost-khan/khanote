"""Researcher registry and factory."""
from __future__ import annotations

from typing import TYPE_CHECKING

from khanote.researchers.base import Researcher, ResearcherError

if TYPE_CHECKING:
    pass

# Registry: maps researcher name → lazy import path
# Each entry: "module.path:ClassName"
RESEARCHER_REGISTRY: dict[str, str] = {
    "perplexity": "khanote.researchers.perplexity:PerplexityResearcher",
    "arxiv": "khanote.researchers.arxiv:ArxivResearcher",
    "notebooklm": "khanote.researchers.notebooklm:NotebookLMResearcher",
}


class ResearcherFactory:
    """Instantiate researchers by name from the registry."""

    @staticmethod
    def create(name: str, **kwargs) -> Researcher:
        """Create and return a researcher instance by name.

        Args:
            name: Researcher name (must be in RESEARCHER_REGISTRY).
            **kwargs: Passed to the researcher's __init__.

        Raises:
            ResearcherError: If name not found or import fails.
        """
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
    def available() -> list[str]:
        """Return list of registered researcher names."""
        return list(RESEARCHER_REGISTRY.keys())


__all__ = ["Researcher", "ResearcherError", "RESEARCHER_REGISTRY", "ResearcherFactory"]
