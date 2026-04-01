"""Full pipeline orchestrator: start → ingest → analyze → save."""
from __future__ import annotations

from pathlib import Path

from khanote.researchers.base import ResearcherError
from khanote.session.analyze import SessionAnalyzer
from khanote.session.ingest import SourceIngester
from khanote.session.manager import SessionManager
from khanote.session.save import SessionSaver


def _researcher_supports(researcher, capability: str) -> bool:
    """Return True if *researcher* declares support for *capability*.

    For ConfigResearcher (type: http), checks the `capabilities` list.
    For built-in researchers (no proper capabilities list), assumes all capabilities.
    """
    caps = getattr(researcher, "capabilities", None)
    if not isinstance(caps, list):
        return True  # built-in researcher or non-config type — assume all capabilities
    return capability in caps


def _is_sop_dependent(researcher) -> bool:
    """Return True if researcher relies on SOP prompts for analysis.

    A researcher is SOP-dependent if it has an 'analyze' capability backed
    only by an SOP (no endpoint) — meaning it needs a vibe coding tool to
    actually execute the filled prompt.
    """
    config = getattr(researcher, "_config", None)
    if config is None:
        return False
    if "analyze" not in getattr(config, "capabilities", []):
        return False
    has_endpoint = config.endpoints is not None and "analyze" in (config.endpoints or {})
    has_sop = config.sop is not None and "analyze" in (config.sop or {})
    return has_sop and not has_endpoint


SOP_MODE_MESSAGE = (
    "This researcher uses SOP prompt templates for analysis. "
    "For best results, run this workflow as a skill inside your vibe coding tool "
    "(Claude Code, Cursor, Codex, Gemini CLI, or OpenCode). "
    "The skill will process the analysis prompt with your AI assistant. "
    "Tip: run /khanote.research.pipeline inside your vibe coding tool."
)


class PipelineOrchestrator:
    """Chain start → ingest → analyze → save in a single call.

    Respects researcher capability declarations — steps for undeclared
    capabilities are silently skipped (Constitution Principle I).
    """

    def __init__(self, vault_dir: Path, researcher=None, skill_mode: bool = False) -> None:
        self.vault_dir = Path(vault_dir)
        self.researcher = researcher
        self.skill_mode = skill_mode

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
            dict with keys: status, session_dir, research_note, synthesis_note, error, warnings
        """
        result: dict = {
            "status": "failed",
            "session_dir": None,
            "research_note": None,
            "synthesis_note": None,
            "error": None,
            "warnings": [],
        }

        # T026: Detect SOP-dependent researcher in non-skill (standalone CLI) mode
        if self.researcher is not None and _is_sop_dependent(self.researcher) and not self.skill_mode:
            result["warnings"].append(SOP_MODE_MESSAGE)

        # Step 1: Start session
        researcher_name = getattr(self.researcher, "name", None)
        if not isinstance(researcher_name, str) or not researcher_name:
            # Derive from class name as fallback (e.g. PerplexityResearcher → perplexity)
            cls_name = type(self.researcher).__name__.lower()
            researcher_name = cls_name.removesuffix("researcher") or "perplexity"
        mgr = SessionManager(vault_dir=self.vault_dir, researcher=researcher_name)
        session_dir = mgr.create(topic)
        result["session_dir"] = session_dir

        # Step 2: Ingest sources (T025: skip if capability not declared)
        if sources and _researcher_supports(self.researcher, "ingest"):
            ingester = SourceIngester(session_dir=session_dir, researcher=self.researcher)
            try:
                ingester.ingest(sources)
            except ResearcherError as e:
                result["error"] = str(e)
                return result
        elif sources and not _researcher_supports(self.researcher, "ingest"):
            result["warnings"].append(
                "Researcher does not support 'ingest' — skipping source ingestion."
            )

        # Step 3: Analyze (T025: skip if capability not declared)
        if _researcher_supports(self.researcher, "analyze"):
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
        else:
            result["warnings"].append(
                "Researcher does not support 'analyze' — skipping analysis step."
            )

        # Step 4: Save
        saver = SessionSaver(session_dir=session_dir, vault_dir=self.vault_dir)
        try:
            synthesis_note = saver.save()
            result["synthesis_note"] = synthesis_note
        except Exception as e:
            result["error"] = str(e)
            return result

        # Optional: Generate (T025: skip if capability not declared)
        if generate and self.researcher is not None and _researcher_supports(self.researcher, "generate"):
            try:
                self.researcher.generate(type=generate)
            except Exception:
                pass  # Generation failure is non-fatal

        result["status"] = "completed"
        return result
