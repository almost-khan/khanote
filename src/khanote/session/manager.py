"""Session manager: create and manage research sessions in vault."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from khanote.models.session import Session, SessionStatus

_PACKAGE_DIR = Path(__file__).parent.parent
_SESSION_TEMPLATE = _PACKAGE_DIR / "templates" / "_session.md"
_INDEX_TEMPLATE = _PACKAGE_DIR / "templates" / "_index.md"

_INDEX_ROW = "| {date} | [{topic}]({slug}/_session.md) | {researcher} | {status} |\n"


class SessionManager:
    """Create and manage research sessions under vault/khanote/."""

    def __init__(self, vault_dir: Path, researcher: str = "perplexity") -> None:
        self.vault_dir = Path(vault_dir)
        self.researcher = researcher

    def create(self, topic: str) -> Path:
        """Create a new session folder in khanote/.

        Returns the path to the created session directory.
        """
        session = Session(date=date.today(), topic=topic, researcher=self.researcher)
        slug = session.slug

        khanote_base = self.vault_dir / "khanote"
        khanote_base.mkdir(exist_ok=True)

        # Conflict resolution: if slug exists, append numeric suffix
        session_dir = khanote_base / slug
        if session_dir.exists():
            counter = 2
            while True:
                candidate = khanote_base / f"{slug}-{counter}"
                if not candidate.exists():
                    session_dir = candidate
                    break
                counter += 1

        # Create session structure
        session_dir.mkdir(parents=True)
        for subdir in ("sources", "research", "synthesis", "artifacts"):
            (session_dir / subdir).mkdir()

        # Write _session.md
        self._write_session_md(session_dir, session)

        # Update current_session pointer
        self._update_current_session_pointer(session_dir)

        # Update khanote/_index.md
        self._update_index(session, session_dir)

        return session_dir

    def _write_session_md(self, session_dir: Path, session: Session) -> None:
        template = _SESSION_TEMPLATE.read_text(encoding="utf-8")
        content = template.format(
            date=session.date.isoformat(),
            topic=session.topic,
            researcher=session.researcher,
        )
        (session_dir / "_session.md").write_text(content, encoding="utf-8")

    def _update_current_session_pointer(self, session_dir: Path) -> None:
        """Write relative path of active session to .khanote/current_session."""
        khanote_dir = self.vault_dir / ".khanote"
        if not khanote_dir.exists():
            return  # Skip if not initialized yet
        pointer = khanote_dir / "current_session"
        relative = session_dir.relative_to(self.vault_dir)
        pointer.write_text(str(relative), encoding="utf-8")

    def _update_index(self, session: Session, session_dir: Path) -> None:
        """Append session row to khanote/_index.md."""
        index_path = self.vault_dir / "khanote" / "_index.md"
        slug = session_dir.relative_to(self.vault_dir / "khanote").as_posix()

        if not index_path.exists():
            template = _INDEX_TEMPLATE.read_text(encoding="utf-8")
            index_path.write_text(template, encoding="utf-8")

        row = _INDEX_ROW.format(
            date=session.date.isoformat(),
            topic=session.topic,
            slug=slug,
            researcher=session.researcher,
            status=session.status.value,
        )

        existing = index_path.read_text(encoding="utf-8")
        index_path.write_text(existing + row, encoding="utf-8")

    def resolve_current(self) -> Path | None:
        """Return the current session directory, or None if not set."""
        pointer = self.vault_dir / ".khanote" / "current_session"
        if not pointer.exists():
            return None
        relative = pointer.read_text(encoding="utf-8").strip()
        path = self.vault_dir / relative
        return path if path.exists() else None
