"""Full pipeline orchestrator: start → ingest → analyze → save."""
from __future__ import annotations

from pathlib import Path

from khanote.researchers.base import ResearcherError
from khanote.session.analyze import SessionAnalyzer
from khanote.session.ingest import SourceIngester
from khanote.session.manager import SessionManager
from khanote.session.save import SessionSaver


class PipelineOrchestrator:
    """Chain start → ingest → analyze → save in a single call."""

    def __init__(self, vault_dir: Path, researcher=None) -> None:
        self.vault_dir = Path(vault_dir)
        self.researcher = researcher

    def run(
        self,
        topic: str,
        sources: list[str] | None = None,
        query: str | None = None,
        generate: str | None = None,
    ) -> dict:
        """Execute the full pipeline.

        Args:
            topic: Research topic name.
            sources: List of URLs or file paths to ingest.
            query: Optional query to guide analysis.
            generate: If set, call researcher.generate(type=generate) after save.

        Returns:
            dict with keys: status, session_dir, research_note, synthesis_note, error
        """
        result: dict = {
            "status": "failed",
            "session_dir": None,
            "research_note": None,
            "synthesis_note": None,
            "error": None,
        }

        # Step 1: Start session
        mgr = SessionManager(vault_dir=self.vault_dir, researcher=getattr(self.researcher, "__class__", object).__name__.lower().replace("researcher", "") or "perplexity")
        session_dir = mgr.create(topic)
        result["session_dir"] = session_dir

        # Step 2: Ingest sources
        if sources:
            ingester = SourceIngester(session_dir=session_dir, researcher=self.researcher)
            try:
                ingester.ingest(sources)
            except ResearcherError as e:
                result["error"] = str(e)
                return result

        # Step 3: Analyze
        analyzer = SessionAnalyzer(
            session_dir=session_dir,
            researcher=self.researcher,
            vault_dir=self.vault_dir,
        )
        try:
            research_note = analyzer.run(query=query)
            result["research_note"] = research_note
        except ResearcherError as e:
            result["error"] = str(e)
            return result

        # Step 4: Save
        saver = SessionSaver(session_dir=session_dir, vault_dir=self.vault_dir)
        try:
            synthesis_note = saver.save()
            result["synthesis_note"] = synthesis_note
        except Exception as e:
            result["error"] = str(e)
            return result

        # Optional: Generate
        if generate and self.researcher is not None:
            try:
                self.researcher.generate(type=generate)
            except Exception:
                pass  # Generation failure is non-fatal

        result["status"] = "completed"
        return result
