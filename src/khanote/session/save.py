"""Structure notes, write to synthesis/, update _session.md status and _index.md."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from khanote.session.utils import extract_sources, update_session_status

_SYNTHESIS_TEMPLATE = """---
session: {session}
created: {created}
status: completed
---

## Summary

{summary}

## Key Findings

{findings}

## Sources

{sources}
"""


class SessionSaver:
    """Finalize a research session by writing synthesis notes."""

    def __init__(self, session_dir: Path, vault_dir: Path | None = None) -> None:
        self.session_dir = Path(session_dir)
        self.vault_dir = vault_dir

    def save(self, summary: str | None = None) -> Path:
        """Write synthesis note and mark session as completed.

        Returns path to the synthesis note.
        """
        summary = summary or self._extract_summary_from_research()
        synthesis_path = self._write_synthesis(summary)
        update_session_status(self.session_dir, "completed")
        self._update_index()
        return synthesis_path

    def _write_synthesis(self, summary: str) -> Path:
        session_rel = str(self.session_dir.name)
        sources = extract_sources(self.session_dir)
        content = _SYNTHESIS_TEMPLATE.format(
            session=session_rel,
            created=date.today().isoformat(),
            summary=summary,
            findings="(Extracted from research notes)",
            sources="\n".join(f"- {s}" for s in sources) if sources else "",
        )
        synthesis_dir = self.session_dir / "synthesis"
        synthesis_dir.mkdir(exist_ok=True)
        path = synthesis_dir / f"synthesis-{date.today().isoformat()}.md"
        path.write_text(content, encoding="utf-8")
        return path

    def _extract_summary_from_research(self) -> str:
        """Try to extract summary from latest research note."""
        research_dir = self.session_dir / "research"
        if not research_dir.exists():
            return "(No analysis available)"
        notes = sorted(research_dir.glob("*.md"))
        if not notes:
            return "(No analysis available)"
        content = notes[-1].read_text(encoding="utf-8")
        match = re.search(r"## Summary\n\n(.+?)(?=\n## |\Z)", content, re.DOTALL)
        return match.group(1).strip() if match else "(Summary not found)"

    def _update_index(self) -> None:
        """Update status in khanote/_index.md for this session."""
        if not self.vault_dir:
            return
        index = self.vault_dir / "khanote" / "_index.md"
        if not index.exists():
            return
        slug = self.session_dir.name
        content = index.read_text(encoding="utf-8")
        content = re.sub(
            rf"(\| .* \[.*{re.escape(slug)}.*\| )\w+(-\w+)*( \|)",
            r"\1completed\3",
            content,
        )
        index.write_text(content, encoding="utf-8")
