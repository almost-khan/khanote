"""Tests for SOP template loading and placeholder filling (TDD)."""
import textwrap
from pathlib import Path

import pytest

from khanote.templates.sop_loader import SopLoader, SopTemplateNotFoundError


@pytest.fixture
def sop_dir(tmp_path):
    """A temp dir with mock SOP templates."""
    analyze_md = tmp_path / "analyze.md"
    analyze_md.write_text(
        textwrap.dedent("""\
            ---
            template_id: analyze-v1
            type: research
            output_format: markdown
            chain_of_thought: true
            ---

            You are a research analyst.

            ## Input
            {sources_text}

            ## Task
            Analyze the results for query: {query}

            Keywords: {keywords}
        """),
        encoding="utf-8",
    )
    search_md = tmp_path / "search.md"
    search_md.write_text(
        textwrap.dedent("""\
            ---
            template_id: search-v1
            ---

            Search for: {query}
            Results: {results}
        """),
        encoding="utf-8",
    )
    return tmp_path


class TestSopLoaderLoad:
    """T010: Load template by ID."""

    def test_load_existing_template(self, sop_dir):
        loader = SopLoader(sop_dir)
        template = loader.load("analyze")
        assert "{sources_text}" in template
        assert "{query}" in template

    def test_load_missing_template_raises(self, sop_dir):
        loader = SopLoader(sop_dir)
        with pytest.raises(SopTemplateNotFoundError):
            loader.load("nonexistent")

    def test_load_strips_yaml_frontmatter(self, sop_dir):
        loader = SopLoader(sop_dir)
        template = loader.load("analyze")
        assert "template_id:" not in template
        assert "---" not in template

    def test_load_returns_string(self, sop_dir):
        loader = SopLoader(sop_dir)
        template = loader.load("analyze")
        assert isinstance(template, str)

    def test_load_by_default_dir(self):
        """Default SopLoader uses the built-in sop/ directory."""
        loader = SopLoader()
        for cap in ["analyze", "ingest", "search", "generate"]:
            template = loader.load(cap)
            assert isinstance(template, str)
            assert len(template) > 0


class TestSopLoaderFill:
    """T010: Fill placeholders with str.format()."""

    def test_fill_single_placeholder(self, sop_dir):
        loader = SopLoader(sop_dir)
        result = loader.fill("search", query="large language models", results="[r1, r2]")
        assert "large language models" in result
        assert "[r1, r2]" in result

    def test_fill_multiple_placeholders(self, sop_dir):
        loader = SopLoader(sop_dir)
        result = loader.fill(
            "analyze",
            sources_text="paper1\npaper2",
            query="AI agents",
            keywords="agent, llm",
        )
        assert "paper1\npaper2" in result
        assert "AI agents" in result
        assert "agent, llm" in result

    def test_fill_missing_placeholder_leaves_literal(self, sop_dir):
        """Unknown placeholders remain in the string unchanged."""
        loader = SopLoader(sop_dir)
        # analyze.md has {domain_name} — not provided, should survive unfilled
        # Using search.md which has {query} and {results}
        result = loader.fill("search", query="test")
        # {results} not provided — should remain as-is (partial fill)
        assert "{results}" in result

    def test_fill_custom_template_string(self, sop_dir):
        loader = SopLoader(sop_dir)
        custom = "Analyze these results: {results} for domain {domain_name}"
        result = loader.fill_string(custom, results="paper1", domain_name="AI")
        assert "paper1" in result
        assert "AI" in result
