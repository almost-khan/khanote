"""Trigger researcher analysis and write results to research/ directory."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from khanote.session.utils import extract_sources, update_session_status

_PACKAGE_DIR = Path(__file__).parent.parent
_RESEARCH_NOTE_TEMPLATE = _PACKAGE_DIR / "templates" / "research-note.md"


class SessionAnalyzer:
    """Trigger researcher.analyze() and write output to research/."""

    def __init__(self, session_dir: Path, researcher, vault_dir: Path | None = None) -> None:
        self.session_dir = Path(session_dir)
        self.researcher = researcher
        self.vault_dir = vault_dir

    def run(self, query: str | None = None) -> Path:
        """Analyze the session and write a research note.

        Returns path to the written research note.
        """
        result = self.researcher.analyze(query=query)
        note_path = self._write_research_note(result)
        update_session_status(self.session_dir, "analyzed")
        return note_path

    def _write_research_note(self, result: dict) -> Path:
        template = _RESEARCH_NOTE_TEMPLATE.read_text(encoding="utf-8")

        # Build sources string from session _session.md
        sources = extract_sources(self.session_dir)
        session_rel = str(self.session_dir.name)
        if self.vault_dir:
            try:
                session_rel = "khanote/" + str(self.session_dir.relative_to(
                    self.vault_dir / "khanote"
                ))
            except ValueError:
                pass

        content = template.format(
            session=session_rel,
            researcher=getattr(self.researcher, "status", "unknown"),
            source=sources[:1] if sources else "unknown",
            created=date.today().isoformat(),
            summary=result.get("summary", ""),
            sources="\n".join(f"- {s}" for s in sources) if sources else "",
        )

        # Add free-layer sections from researcher
        for section_name, section_body in result.get("sections", {}).items():
            if section_name not in ("Analysis",):
                content += f"\n## {section_name}\n\n{section_body}\n"

        research_dir = self.session_dir / "research"
        research_dir.mkdir(exist_ok=True)
        note_path = research_dir / f"analysis-{date.today().isoformat()}.md"
        note_path.write_text(content, encoding="utf-8")
        return note_path
