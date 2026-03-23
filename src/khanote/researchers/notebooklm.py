"""NotebookLM researcher — experimental, wraps notebooklm-py."""
from __future__ import annotations

from khanote.researchers.base import ResearcherError


class NotebookLMResearcher:
    """Experimental researcher using NotebookLM.

    Requires: pip install khanote[notebooklm]
    Status: experimental — API may change without notice.
    """

    status = "experimental"

    def __init__(self, **kwargs) -> None:
        self._ingested: list[str] = []
        self._client = None
        # Lazy import to avoid hard dependency
        try:
            import notebooklm  # type: ignore
            self._client = notebooklm
        except ImportError:
            pass  # Optional dependency — gracefully degrade

    def ingest(self, sources: list[str]) -> dict:
        """Record sources for NotebookLM."""
        self._ingested.extend(sources)
        return {"source_count": len(sources), "indexed_ids": list(range(len(sources)))}

    def analyze(self, query: str | None = None) -> dict:
        """Stub — NotebookLM analysis requires browser automation."""
        return {
            "summary": (
                "[NotebookLM — experimental] Analysis not available via API. "
                "Use NotebookLM web interface for full analysis."
            ),
            "sections": {},
            "raw": None,
        }

    def generate(self, type: str, **kwargs) -> str | bytes:
        """Stub — NotebookLM audio/summary generation."""
        return (
            f"[NotebookLM — experimental] {type} generation requires NotebookLM web interface."
        )

    def search(self, query: str) -> list[dict]:
        """Return empty results — NotebookLM doesn't support direct search."""
        return []
