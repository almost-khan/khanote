"""Tests for LocalFileResearcher (TDD — US3).

Write these tests first, ensure they FAIL before implementation.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# T038: Protocol compliance
# ─────────────────────────────────────────────────────────────────────────────

class TestLocalFileResearcherProtocol:
    """T038: LocalFileResearcher must implement the Researcher Protocol."""

    def test_implements_researcher_protocol(self):
        from khanote.researchers.local_file import LocalFileResearcher
        from khanote.researchers.base import Researcher
        r = LocalFileResearcher()
        assert isinstance(r, Researcher)

    def test_has_ingest_method(self):
        from khanote.researchers.local_file import LocalFileResearcher
        r = LocalFileResearcher()
        assert callable(getattr(r, "ingest", None))

    def test_has_search_method(self):
        from khanote.researchers.local_file import LocalFileResearcher
        r = LocalFileResearcher()
        assert callable(getattr(r, "search", None))

    def test_has_analyze_method(self):
        from khanote.researchers.local_file import LocalFileResearcher
        r = LocalFileResearcher()
        assert callable(getattr(r, "analyze", None))

    def test_has_generate_method(self):
        from khanote.researchers.local_file import LocalFileResearcher
        r = LocalFileResearcher()
        assert callable(getattr(r, "generate", None))


# ─────────────────────────────────────────────────────────────────────────────
# T039: Ingest — Markdown files
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestMarkdownFiles:
    """T039: ingest() reads Markdown files and stores content."""

    def test_ingest_single_md_file(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        md_file = tmp_path / "note.md"
        md_file.write_text("# My Note\n\nThis is my research on AI agents.", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(md_file)])

        assert result["source_count"] == 1
        assert len(result["indexed_ids"]) == 1

    def test_ingest_md_stores_content(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        md_file = tmp_path / "note.md"
        md_file.write_text("# Research\n\nContent about transformers.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(md_file)])

        assert any("transformer" in v.lower() for v in r._indexed_content.values())

    def test_ingest_strips_yaml_frontmatter(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        md_file = tmp_path / "note.md"
        md_file.write_text(
            "---\ntitle: My Note\ndate: 2026-01-01\n---\n\n# Body\n\nActual content here.",
            encoding="utf-8",
        )
        r = LocalFileResearcher()
        r.ingest([str(md_file)])

        content = list(r._indexed_content.values())[0]
        assert "title: My Note" not in content
        assert "Actual content here" in content

    def test_ingest_multiple_md_files(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        for i in range(3):
            (tmp_path / f"note{i}.md").write_text(f"# Note {i}\n\nContent {i}.", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path / f"note{i}.md") for i in range(3)])

        assert result["source_count"] == 3
        assert len(result["indexed_ids"]) == 3


# ─────────────────────────────────────────────────────────────────────────────
# T040: Ingest — TXT files
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestTxtFiles:
    """T040: ingest() reads .txt files."""

    def test_ingest_txt_file(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("Plain text research notes about LLMs.", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(txt_file)])

        assert result["source_count"] == 1
        assert any("llm" in v.lower() for v in r._indexed_content.values())


# ─────────────────────────────────────────────────────────────────────────────
# T041: Ingest — PDF files
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestPdfFiles:
    """T041: ingest() reads PDF files via text extraction."""

    def test_ingest_pdf_file_with_extractable_text(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")  # not a real PDF

        r = LocalFileResearcher()
        # Mock pdfplumber to return text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Abstract: This paper studies attention mechanisms."
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = r.ingest([str(pdf_file)])

        assert result["source_count"] == 1
        assert any("attention" in v.lower() for v in r._indexed_content.values())

    def test_ingest_image_only_pdf_is_skipped_with_warning(self, tmp_path, capsys):
        from khanote.researchers.local_file import LocalFileResearcher
        pdf_file = tmp_path / "scan.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        r = LocalFileResearcher()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None  # image-only PDF
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = r.ingest([str(pdf_file)])

        # Should be skipped (no content extracted)
        assert result["source_count"] == 0 or not r._indexed_content


# ─────────────────────────────────────────────────────────────────────────────
# T042: Ingest — skips unsupported file types
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestUnsupportedTypes:
    """T042: ingest() skips unsupported file types with a warning."""

    def test_unsupported_type_skipped(self, tmp_path, capsys):
        from khanote.researchers.local_file import LocalFileResearcher
        img_file = tmp_path / "photo.png"
        img_file.write_bytes(b"\x89PNG\r\n")

        r = LocalFileResearcher()
        result = r.ingest([str(img_file)])

        assert result["source_count"] == 0

    def test_unsupported_type_does_not_crash(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        for ext in [".jpg", ".mp3", ".docx", ".zip"]:
            f = tmp_path / f"file{ext}"
            f.write_bytes(b"fake content")

        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path / f"file{ext}") for ext in [".jpg", ".mp3", ".docx", ".zip"]])
        # Should not raise
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# T043: Ingest — skips files exceeding 10 MB
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestFileSizeLimit:
    """T043: ingest() skips files exceeding 10 MB with a warning."""

    def test_large_file_skipped(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        large_file = tmp_path / "large.md"
        # Write just over 10 MB of content
        large_file.write_text("x" * (10 * 1024 * 1024 + 1), encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(large_file)])

        assert result["source_count"] == 0
        assert str(large_file) not in r._indexed_content

    def test_small_file_not_skipped(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        small_file = tmp_path / "small.md"
        small_file.write_text("# Small\n\nThis is fine.", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(small_file)])

        assert result["source_count"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# T044: Ingest — skips non-UTF-8 files
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestEncodingError:
    """T044: ingest() skips non-UTF-8 files with a warning."""

    def test_non_utf8_file_skipped(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        bad_file = tmp_path / "latin.md"
        bad_file.write_bytes(b"\xff\xfe# Bad encoding\nContent in Latin-1: \xe9\xe0\xf9")

        r = LocalFileResearcher()
        result = r.ingest([str(bad_file)])

        # Either skipped or content decoded with errors='replace'
        assert isinstance(result, dict)
        # Should not crash


# ─────────────────────────────────────────────────────────────────────────────
# T045: Directory scanning — recursive with exclusions
# ─────────────────────────────────────────────────────────────────────────────

class TestDirectoryScanning:
    """T045: Directory scanning is recursive and excludes system directories."""

    def test_scans_subdirectories_recursively(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "subdir").mkdir()
        (tmp_path / "note.md").write_text("Root note.", encoding="utf-8")
        (tmp_path / "subdir" / "deep.md").write_text("Deep note.", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path)])

        assert result["source_count"] == 2

    def test_excludes_obsidian_dir(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / ".obsidian").mkdir()
        (tmp_path / ".obsidian" / "config.md").write_text("Obsidian config.", encoding="utf-8")
        (tmp_path / "note.md").write_text("My note.", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path)])

        assert result["source_count"] == 1
        assert not any(".obsidian" in k for k in r._indexed_content)

    def test_excludes_git_dir(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
        (tmp_path / "README.md").write_text("# Project", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path)])

        assert result["source_count"] == 1
        assert not any(".git" in k for k in r._indexed_content)

    def test_excludes_node_modules(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
        (tmp_path / "node_modules" / "pkg" / "readme.md").write_text("pkg docs", encoding="utf-8")
        (tmp_path / "index.md").write_text("My content", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path)])

        assert result["source_count"] == 1

    def test_excludes_trash_dir(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / ".trash").mkdir()
        (tmp_path / ".trash" / "old.md").write_text("Old note", encoding="utf-8")
        (tmp_path / "current.md").write_text("Current note", encoding="utf-8")

        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path)])

        assert result["source_count"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# T046: search() — keyword matching with scores
# ─────────────────────────────────────────────────────────────────────────────

class TestSearchKeywordMatching:
    """T046: search() returns keyword-matched results with scores, paths, and excerpts."""

    def test_search_returns_matching_files(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "ai.md").write_text("# AI Agents\n\nMulti-agent systems are transformative.", encoding="utf-8")
        (tmp_path / "cooking.md").write_text("# Recipes\n\nHow to bake a sourdough loaf.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        results = r.search("agent")

        assert len(results) >= 1
        assert any("agent" in r["title"].lower() or "agent" in r["excerpt"].lower() for r in results)

    def test_search_result_has_required_fields(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "note.md").write_text("# Transformers\n\nAttention is all you need.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        results = r.search("transformer")

        assert len(results) > 0
        result = results[0]
        assert "id" in result
        assert "title" in result
        assert "excerpt" in result
        assert "score" in result

    def test_search_excludes_non_matching_files(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "unrelated.md").write_text("# Cooking\n\nRecipes and food.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        results = r.search("quantum physics")

        assert len(results) == 0 or results[0]["score"] < 0.5

    def test_search_scores_are_floats_between_0_and_1(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "note.md").write_text("# AI\n\nDeep learning advances.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        results = r.search("deep learning")

        for result in results:
            assert 0.0 <= result["score"] <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# T047: analyze() — structured content for LLM synthesis
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyzeContent:
    """T047: analyze() returns structured content summary for LLM synthesis."""

    def test_analyze_returns_dict(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "note.md").write_text("# Research\n\nKey findings here.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        result = r.analyze()

        assert isinstance(result, dict)
        assert "summary" in result
        assert "sections" in result
        assert "raw" in result

    def test_analyze_summary_is_non_empty(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "note.md").write_text("# Deep Learning\n\nNeural networks power modern AI.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        result = r.analyze()

        assert len(result["summary"]) > 0

    def test_analyze_sections_contains_file_content(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "note.md").write_text("# Agent Research\n\nFindings on autonomous agents.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        result = r.analyze()

        sections_text = str(result["sections"]).lower()
        assert "agent" in sections_text or "autonomous" in sections_text

    def test_analyze_with_query_filters_content(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        (tmp_path / "ai.md").write_text("# AI\n\nMachine learning is amazing.", encoding="utf-8")
        (tmp_path / "cooking.md").write_text("# Food\n\nBread recipes.", encoding="utf-8")

        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        result = r.analyze(query="machine learning")

        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# T048: Empty directory — returns empty result set, not error
# ─────────────────────────────────────────────────────────────────────────────

class TestEmptyDirectory:
    """T048: Empty directory returns empty result set (not error)."""

    def test_empty_directory_ingest_returns_zero(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        r = LocalFileResearcher()
        result = r.ingest([str(tmp_path)])

        assert result["source_count"] == 0
        assert result["indexed_ids"] == []

    def test_empty_directory_search_returns_empty_list(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        results = r.search("anything")

        assert results == []

    def test_empty_directory_analyze_returns_valid_dict(self, tmp_path):
        from khanote.researchers.local_file import LocalFileResearcher
        r = LocalFileResearcher()
        r.ingest([str(tmp_path)])
        result = r.analyze()

        assert isinstance(result, dict)
        assert "summary" in result
