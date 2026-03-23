"""Researcher Protocol definition and ResearcherError."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Researcher(Protocol):
    """Protocol that all researchers must conform to.

    Two ends are fixed (vibe coding tools ↔ Obsidian).
    Researchers are the swappable middle (Constitution Principle I).
    """

    def ingest(self, sources: list[str]) -> dict:
        """Ingest sources into the researcher.

        Returns:
            {"source_count": int, "indexed_ids": list[str]}
        """
        ...

    def analyze(self, query: str | None = None) -> dict:
        """Analyze ingested sources and return structured output.

        Returns:
            {"summary": str, "sections": dict[str, str], "raw": Any}
        """
        ...

    def generate(self, type: str, **kwargs) -> str | bytes:
        """Generate content from ingested/analyzed sources.

        Returns:
            Serialized output (markdown, JSON, or binary for audio/images)
        """
        ...

    def search(self, query: str) -> list[dict]:
        """Search for content related to the query.

        Returns:
            [{"id": str, "title": str, "excerpt": str, "score": float}]
        """
        ...


class ResearcherError(Exception):
    """Raised when a researcher encounters an error."""

    def __init__(self, message: str, researcher: str | None = None) -> None:
        super().__init__(message)
        self.researcher = researcher
