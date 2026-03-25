"""Query router — route queries to researchers based on registry entries."""
from __future__ import annotations

from khanote.registry.models import ResearcherRegistryEntry


class QueryRouter:
    """Route queries/sub-queries to appropriate researchers based on registry metadata."""

    def __init__(self, entries: dict[str, ResearcherRegistryEntry]) -> None:
        self._entries = entries

    def route(self, researcher_name: str) -> ResearcherRegistryEntry | None:
        """Return the registry entry for the requested researcher if available.

        Args:
            researcher_name: Name of the researcher to route to.

        Returns:
            ResearcherRegistryEntry if researcher exists and is available, else None.
        """
        entry = self._entries.get(researcher_name)
        if entry is None:
            return None
        if entry.available:
            return entry
        # Researcher exists but unavailable — no automatic fallback at this level
        return None

    def route_with_fallback(
        self, researcher_name: str, fallback_name: str = "perplexity"
    ) -> ResearcherRegistryEntry | None:
        """Route to researcher, falling back to fallback_name if unavailable.

        Args:
            researcher_name: Preferred researcher name.
            fallback_name: Fallback researcher name (default: perplexity).

        Returns:
            Entry for researcher or fallback, or None if neither available.
        """
        entry = self.route(researcher_name)
        if entry is not None:
            return entry
        return self.route(fallback_name)

    def get_available(self) -> list[ResearcherRegistryEntry]:
        """Return all available researchers."""
        return [e for e in self._entries.values() if e.available]

    def get_fallback(self) -> ResearcherRegistryEntry | None:
        """Return the fallback researcher (priority=fallback and available)."""
        for entry in self._entries.values():
            if entry.priority == "fallback" and entry.available:
                return entry
        return None

    def format_registry_description(self) -> str:
        """Format all entries as a readable context block for LLM decompose templates."""
        lines = []
        for name, entry in self._entries.items():
            status = "available" if entry.available else "unavailable"
            domains = ", ".join(entry.domains) if entry.domains else "general"
            lines.append(
                f"- {name} ({status}): {entry.description} [domains: {domains}]"
            )
        return "\n".join(lines)


__all__ = ["QueryRouter"]
