"""Source ingestion: accept URL/file/text, update _session.md, call researcher."""
from __future__ import annotations

import re
import shutil
from pathlib import Path


from khanote.researchers.base import ResearcherError


class SourceIngester:
    """Ingest sources into a research session."""

    def __init__(self, session_dir: Path, researcher=None) -> None:
        self.session_dir = Path(session_dir)
        self.researcher = researcher

    def ingest(self, sources: list[str]) -> dict:
        """Ingest a list of sources (URLs or file paths).

        Returns summary: {"ingested": list, "pending": list, "failed": list}
        """
        ingested: list[str] = []
        pending: list[str] = []

        for source in sources:
            resolved = self._resolve_source(source)
            ingested.append(resolved)

        # Try researcher
        if self.researcher is not None:
            try:
                self.researcher.ingest(sources)
                self._update_session_md(ingested, status="ok")
            except ResearcherError:
                self._update_session_md(ingested, status="pending")
                pending.extend(ingested)
        else:
            self._update_session_md(ingested, status="pending")
            pending.extend(ingested)

        return {"ingested": ingested, "pending": pending}

    def _resolve_source(self, source: str) -> str:
        """If source is a local file, copy it to sources/ and return the path."""
        path = Path(source)
        if path.exists() and path.is_file():
            dest = self.session_dir / "sources" / path.name
            shutil.copy2(path, dest)
            return str(dest.relative_to(self.session_dir))
        return source  # URL or text — return as-is

    def _update_session_md(self, sources: list[str], status: str = "ok") -> None:
        """Append source entries to _session.md and update sources_count."""
        session_file = self.session_dir / "_session.md"
        content = session_file.read_text(encoding="utf-8")

        # Update frontmatter sources_count
        content = self._increment_sources_count(content, len(sources))

        # Append to ## Sources section
        source_lines = "\n".join(
            f"- [{status}] {src}" for src in sources
        )
        if "## Sources" in content:
            content = content.replace(
                "## Sources\n",
                f"## Sources\n\n{source_lines}\n",
                1,
            )
        else:
            content += f"\n## Sources\n\n{source_lines}\n"

        session_file.write_text(content, encoding="utf-8")

    def _increment_sources_count(self, content: str, count: int) -> str:
        """Update the sources_count field in frontmatter."""
        match = re.search(r"sources_count:\s*(\d+)", content)
        if match:
            current = int(match.group(1))
            new_count = current + count
            content = content[:match.start()] + f"sources_count: {new_count}" + content[match.end():]
        return content
