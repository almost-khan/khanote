"""Tests for SOP template loading and placeholder filling (TDD)."""
import textwrap

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


# ─────────────────────────────────────────────────────────────────────────────
# T013: Personalization injection into SOP templates
# ─────────────────────────────────────────────────────────────────────────────

class TestPersonalizationInjection:
    """T013: SopLoader personalization injection via {personalization_instructions}."""

    @pytest.fixture
    def sop_dir_with_personalization(self, tmp_path):
        """SOP template with {personalization_instructions} placeholder."""
        tmpl = tmp_path / "analyze.md"
        tmpl.write_text(
            "{personalization_instructions}\n\nYou are a research analyst.\n\nQuery: {query}\n",
            encoding="utf-8",
        )
        return tmp_path

    def test_personalization_placeholder_filled(self, sop_dir_with_personalization):
        loader = SopLoader(sop_dir_with_personalization)
        result = loader.fill(
            "analyze",
            personalization_instructions="- Output in English\n- Use detailed depth",
            query="AI agents",
        )
        assert "Output in English" in result
        assert "AI agents" in result

    def test_personalization_placeholder_left_when_not_provided(self, sop_dir_with_personalization):
        """If personalization_instructions not provided, placeholder remains."""
        loader = SopLoader(sop_dir_with_personalization)
        result = loader.fill("analyze", query="test")
        assert "{personalization_instructions}" in result

    def test_fill_with_preferences(self, sop_dir_with_personalization):
        """SopLoader.fill_with_preferences reads prefs and injects block."""
        from khanote.preferences.models import Preferences
        loader = SopLoader(sop_dir_with_personalization)
        prefs = Preferences(depth="headlines", expertise="beginner", language="en-US")
        result = loader.fill_with_preferences("analyze", prefs, query="AI news")
        assert "{personalization_instructions}" not in result
        assert "AI news" in result

    def test_personalization_injection_end_to_end(self, sop_dir_with_personalization):
        """Preferences → personalization block → injected into template."""
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        loader = SopLoader(sop_dir_with_personalization)
        prefs = Preferences(depth="deep_dive", expertise="expert", tone="formal_report")
        block = build_personalization_block(prefs)
        result = loader.fill("analyze", personalization_instructions=block, query="test")
        assert "{personalization_instructions}" not in result
        assert len(result) > 50


# ─────────────────────────────────────────────────────────────────────────────
# T055: Personalization injection end-to-end
# ─────────────────────────────────────────────────────────────────────────────

class TestPersonalizationEndToEnd:
    """T055: preferences → personalization block → template with correct guidelines."""

    def test_zh_cn_language_in_block(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        prefs = Preferences(language="zh-CN")
        block = build_personalization_block(prefs)
        assert "zh-CN" in block or "Chinese" in block.lower() or "language" in block.lower()

    def test_headlines_depth_block_differs_from_detailed(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        block_h = build_personalization_block(Preferences(depth="headlines"))
        block_d = build_personalization_block(Preferences(depth="detailed"))
        assert block_h != block_d

    def test_all_prefs_reflected(self):
        from khanote.preferences.models import Preferences
        from khanote.preferences.personalization import build_personalization_block
        prefs = Preferences(depth="deep_dive", expertise="expert", tone="formal_report", language="de-DE")
        block = build_personalization_block(prefs)
        # Block should mention each preference dimension
        assert len(block) > 100  # substantial block with multiple guidelines


# ─────────────────────────────────────────────────────────────────────────────
# T071-T074: Upgraded SOP template content tests
# ─────────────────────────────────────────────────────────────────────────────

class TestUpgradedSopTemplates:
    """T071-T074: Verify upgraded template content."""

    def test_analyze_template_has_source_quality_assessment(self):
        loader = SopLoader()
        template = loader.load("analyze")
        assert "source" in template.lower()
        assert "quality" in template.lower() or "assess" in template.lower()

    def test_analyze_template_has_personalization_placeholder(self):
        loader = SopLoader()
        template = loader.load("analyze")
        assert "{personalization_instructions}" in template

    def test_ingest_template_has_personalization_placeholder(self):
        loader = SopLoader()
        template = loader.load("ingest")
        assert "{personalization_instructions}" in template

    def test_search_template_has_personalization_placeholder(self):
        loader = SopLoader()
        template = loader.load("search")
        assert "{personalization_instructions}" in template

    def test_generate_briefing_template_exists(self):
        loader = SopLoader()
        template = loader.load("generate-briefing")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_generate_briefing_has_personalization_placeholder(self):
        loader = SopLoader()
        template = loader.load("generate-briefing")
        assert "{personalization_instructions}" in template

    def test_generate_report_template_exists(self):
        loader = SopLoader()
        template = loader.load("generate-report")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_briefing_template_exists(self):
        loader = SopLoader()
        template = loader.load("briefing")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_decompose_template_exists(self):
        loader = SopLoader()
        template = loader.load("decompose")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_discover_template_exists(self):
        loader = SopLoader()
        template = loader.load("discover")
        assert isinstance(template, str)
        assert len(template) > 0
