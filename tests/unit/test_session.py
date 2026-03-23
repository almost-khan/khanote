"""Tests for Session model and SessionManager (TDD — written before implementation)."""
from datetime import date

import pytest

from khanote.models.session import Session, SessionStatus


class TestSessionModel:
    def test_create_session_with_required_fields(self):
        session = Session(
            date=date(2026, 3, 22),
            topic="AI Agents Overview",
            researcher="perplexity",
        )
        assert session.topic == "AI Agents Overview"
        assert session.status == SessionStatus.IN_PROGRESS

    def test_default_status_is_in_progress(self):
        session = Session(date=date.today(), topic="Test", researcher="arxiv")
        assert session.status == SessionStatus.IN_PROGRESS

    def test_status_transition_to_completed(self):
        session = Session(date=date.today(), topic="Test", researcher="arxiv")
        session.status = SessionStatus.COMPLETED
        assert session.status == SessionStatus.COMPLETED

    def test_status_transition_to_failed(self):
        session = Session(date=date.today(), topic="Test", researcher="arxiv")
        session.status = SessionStatus.FAILED
        assert session.status == SessionStatus.FAILED

    def test_sources_count_defaults_to_zero(self):
        session = Session(date=date.today(), topic="Test", researcher="perplexity")
        assert session.sources_count == 0

    def test_sources_count_can_be_set(self):
        session = Session(date=date.today(), topic="Test", researcher="perplexity", sources_count=3)
        assert session.sources_count == 3

    def test_frontmatter_output(self):
        session = Session(
            date=date(2026, 3, 22),
            topic="AI Agents Overview",
            researcher="perplexity",
            status=SessionStatus.IN_PROGRESS,
            sources_count=2,
        )
        fm = session.to_frontmatter()
        assert "date: 2026-03-22" in fm
        assert "topic: AI Agents Overview" in fm
        assert "researcher: perplexity" in fm
        assert "status: in-progress" in fm
        assert "sources_count: 2" in fm

    def test_from_frontmatter_string(self):
        frontmatter = """date: 2026-03-22
topic: AI Agents Overview
researcher: perplexity
status: completed
sources_count: 3"""
        session = Session.from_frontmatter(frontmatter)
        assert session.topic == "AI Agents Overview"
        assert session.status == SessionStatus.COMPLETED
        assert session.sources_count == 3

    def test_slug_generation(self):
        session = Session(date=date(2026, 3, 22), topic="AI Agents Overview", researcher="perplexity")
        assert session.slug == "2026-03-22_AI-Agents-Overview"

    def test_slug_special_characters_replaced(self):
        session = Session(date=date(2026, 3, 22), topic="MCP: Server & Tools!", researcher="arxiv")
        slug = session.slug
        assert "/" not in slug
        assert ":" not in slug
        assert "&" not in slug


# ============================================================
# SessionManager tests (T033)
# ============================================================
from khanote.session.manager import SessionManager


class TestSessionManager:
    def test_create_session_creates_dated_folder(self, tmp_path):
        mgr = SessionManager(vault_dir=tmp_path)
        session_dir = mgr.create("AI Agents Overview")
        assert session_dir.exists()
        assert session_dir.parent.name == "khanote"
        assert "AI-Agents-Overview" in session_dir.name

    def test_create_session_includes_date_prefix(self, tmp_path):
        from datetime import date
        mgr = SessionManager(vault_dir=tmp_path)
        session_dir = mgr.create("Test Topic")
        today = date.today().isoformat()
        assert session_dir.name.startswith(today)

    def test_create_session_creates_subdirectories(self, tmp_path):
        mgr = SessionManager(vault_dir=tmp_path)
        session_dir = mgr.create("AI Agents")
        for subdir in ("sources", "research", "synthesis", "artifacts"):
            assert (session_dir / subdir).exists()

    def test_create_session_generates_session_md(self, tmp_path):
        mgr = SessionManager(vault_dir=tmp_path)
        session_dir = mgr.create("AI Agents")
        session_md = session_dir / "_session.md"
        assert session_md.exists()
        content = session_md.read_text()
        assert "---" in content
        assert "AI Agents" in content

    def test_create_session_conflict_resolution(self, tmp_path):
        """If a session with same slug exists, append numeric suffix."""
        mgr = SessionManager(vault_dir=tmp_path)
        first = mgr.create("AI Agents")
        second = mgr.create("AI Agents")
        assert first != second
        assert second.exists()

    def test_create_session_updates_current_session_pointer(self, tmp_path):
        mgr = SessionManager(vault_dir=tmp_path)
        khanote_dir = tmp_path / ".khanote"
        khanote_dir.mkdir()
        session_dir = mgr.create("AI Agents")
        pointer = khanote_dir / "current_session"
        assert pointer.exists()
        assert "AI-Agents" in pointer.read_text()

    def test_create_session_updates_index(self, tmp_path):
        mgr = SessionManager(vault_dir=tmp_path)
        mgr.create("First Topic")
        index = tmp_path / "khanote" / "_index.md"
        assert index.exists()
        assert "First Topic" in index.read_text()

    def test_topic_slugification(self, tmp_path):
        mgr = SessionManager(vault_dir=tmp_path)
        session_dir = mgr.create("MCP: Servers & Tools!")
        # Special chars removed, spaces become dashes
        assert "/" not in session_dir.name
        assert "&" not in session_dir.name
