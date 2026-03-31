"""Tests for Pyramid Principle writing quality in user-facing SOP templates (US2).

TDD: These tests define what the updated templates MUST contain.
Write tests first — they should FAIL before template rewrites, PASS after.
"""
from __future__ import annotations

import pytest

from khanote.templates.sop_loader import SopLoader

# User-facing SOPs: must have writing quality rules
USER_FACING_SOPS = ["briefing", "analyze", "discover", "generate", "generate-briefing", "generate-report"]

# Internal processing SOPs: must NOT have writing quality rules imposed
INTERNAL_SOPS = ["ingest", "search", "decompose"]

# Phrases that must appear in user-facing SOPs to enforce quality
BANNED_PHRASES_MARKER = "banned"          # word indicating a banned phrases section
ACTION_TITLE_MARKER = "action title"      # instruction about action titles
SO_WHAT_MARKER = "so what"               # "so what?" test requirement
CITATION_MARKER = "source"               # source citation requirement
SELF_CHECK_MARKER = "self-check"         # or "verify" / "checklist"
PYRAMID_MARKER = "conclusion"            # conclusion-first / pyramid instruction
FEW_SHOT_MARKER = "example"             # few-shot example present


@pytest.fixture
def loader():
    return SopLoader()


# ─────────────────────────────────────────────────────────────────────────────
# T024: Briefing SOP — banned phrases list
# ─────────────────────────────────────────────────────────────────────────────

class TestBriefingSopBannedPhrases:
    """T024: Daily briefing SOP must include a banned phrases list."""

    def test_briefing_has_banned_phrases_section(self, loader):
        template = loader.load("briefing").lower()
        assert BANNED_PHRASES_MARKER in template, (
            "briefing.md must contain a 'banned' phrases section to prohibit LLM filler"
        )

    def test_briefing_bans_filler_preamble(self, loader):
        template = loader.load("briefing").lower()
        # Should explicitly prohibit common preambles
        assert any(phrase in template for phrase in [
            "in today", "it's important", "let's dive", "rapidly evolving"
        ]), "briefing.md should list specific filler phrases to prohibit"


# ─────────────────────────────────────────────────────────────────────────────
# T025: Briefing SOP — action titles + few-shot example
# ─────────────────────────────────────────────────────────────────────────────

class TestBriefingSopActionTitles:
    """T025: Daily briefing SOP must enforce action titles with a few-shot example."""

    def test_briefing_has_action_title_instruction(self, loader):
        template = loader.load("briefing").lower()
        assert ACTION_TITLE_MARKER in template, (
            "briefing.md must instruct the LLM to use action titles (insight-driven headings)"
        )

    def test_briefing_has_few_shot_example(self, loader):
        template = loader.load("briefing").lower()
        assert FEW_SHOT_MARKER in template, (
            "briefing.md must include a few-shot example of correct action title output"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T026: Briefing SOP — self-check quality checklist
# ─────────────────────────────────────────────────────────────────────────────

class TestBriefingSopSelfCheck:
    """T026: Daily briefing SOP must include a self-check quality checklist."""

    def test_briefing_has_self_check_instruction(self, loader):
        template = loader.load("briefing").lower()
        assert any(marker in template for marker in [
            SELF_CHECK_MARKER, "verify", "checklist", "before finaliz"
        ]), "briefing.md must instruct the LLM to self-check output quality"


# ─────────────────────────────────────────────────────────────────────────────
# T027: Analyze SOP — pyramid principle structure
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyzeSopPyramid:
    """T027: Analyze SOP must contain pyramid principle structure instructions."""

    def test_analyze_has_conclusion_first_instruction(self, loader):
        template = loader.load("analyze").lower()
        assert PYRAMID_MARKER in template, (
            "analyze.md must instruct conclusion-first (pyramid principle) structure"
        )

    def test_analyze_has_action_title_instruction(self, loader):
        template = loader.load("analyze").lower()
        assert ACTION_TITLE_MARKER in template, (
            "analyze.md must instruct the LLM to use action titles"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T028: Generate-report SOP — SCQA framework
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateReportSopSCQA:
    """T028: Generate-report SOP must use the SCQA framework."""

    def test_generate_report_has_scqa_framework(self, loader):
        template = loader.load("generate-report").lower()
        assert "scqa" in template or (
            "situation" in template and "complication" in template
        ), "generate-report.md must include SCQA framework (Situation-Complication-Question-Answer)"


# ─────────────────────────────────────────────────────────────────────────────
# T029: All user-facing SOPs — "so what?" requirement
# ─────────────────────────────────────────────────────────────────────────────

class TestUserFacingSopsSoWhat:
    """T029: All user-facing output SOPs must require a 'so what?' implication."""

    @pytest.mark.parametrize("sop_name", USER_FACING_SOPS)
    def test_sop_requires_so_what(self, loader, sop_name):
        template = loader.load(sop_name).lower()
        assert any(marker in template for marker in [
            "so what", "implication", "actionable", "what this means", "what to do"
        ]), f"{sop_name}.md must require a 'so what?' implication in every section"


# ─────────────────────────────────────────────────────────────────────────────
# T030: All user-facing SOPs — source citation requirement
# ─────────────────────────────────────────────────────────────────────────────

class TestUserFacingSopsSourceCitations:
    """T030: All user-facing output SOPs must require inline source citations."""

    @pytest.mark.parametrize("sop_name", USER_FACING_SOPS)
    def test_sop_requires_source_citation(self, loader, sop_name):
        template = loader.load(sop_name).lower()
        assert CITATION_MARKER in template, (
            f"{sop_name}.md must require source citations for factual claims"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T031: Internal SOPs — must NOT have writing quality rules
# ─────────────────────────────────────────────────────────────────────────────

class TestInternalSopsExempt:
    """T031: Internal processing SOPs (ingest, search, decompose) must NOT have writing rules."""

    @pytest.mark.parametrize("sop_name", INTERNAL_SOPS)
    def test_internal_sop_has_no_banned_phrases_section(self, loader, sop_name):
        template = loader.load(sop_name).lower()
        # Internal SOPs should not have a "banned phrases" enforcement block
        # (they may mention sources but not as a prose writing rule)
        assert "never use" not in template or "banned phrase" not in template, (
            f"{sop_name}.md is an internal SOP and should not have prose writing quality rules"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T031b: Discover SOP — writing quality rules
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscoverSopQuality:
    """T031b: Discover SOP must include writing quality rules (user-facing)."""

    def test_discover_has_action_title_instruction(self, loader):
        template = loader.load("discover").lower()
        assert ACTION_TITLE_MARKER in template or "insight" in template, (
            "discover.md must instruct action titles (user-facing output)"
        )

    def test_discover_has_banned_phrases(self, loader):
        template = loader.load("discover").lower()
        assert BANNED_PHRASES_MARKER in template or "do not" in template, (
            "discover.md must prohibit LLM filler phrases (user-facing output)"
        )

    def test_discover_has_self_check(self, loader):
        template = loader.load("discover").lower()
        assert any(marker in template for marker in [
            SELF_CHECK_MARKER, "verify", "checklist", "before finaliz"
        ]), "discover.md must include a self-check instruction"

    def test_discover_requires_source_citation(self, loader):
        template = loader.load("discover").lower()
        assert CITATION_MARKER in template, (
            "discover.md must require source citations"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T031c: Generate SOP — writing quality rules
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateSopQuality:
    """T031c: Generate SOP must include writing quality rules (user-facing)."""

    def test_generate_has_action_title_instruction(self, loader):
        template = loader.load("generate").lower()
        assert ACTION_TITLE_MARKER in template or "insight" in template, (
            "generate.md must instruct action titles (user-facing output)"
        )

    def test_generate_has_banned_phrases(self, loader):
        template = loader.load("generate").lower()
        assert BANNED_PHRASES_MARKER in template or "do not" in template, (
            "generate.md must prohibit LLM filler phrases (user-facing output)"
        )

    def test_generate_has_pyramid_structure(self, loader):
        template = loader.load("generate").lower()
        assert PYRAMID_MARKER in template, (
            "generate.md must enforce conclusion-first (pyramid principle) structure"
        )

    def test_generate_has_self_check(self, loader):
        template = loader.load("generate").lower()
        assert any(marker in template for marker in [
            SELF_CHECK_MARKER, "verify", "checklist", "before finaliz"
        ]), "generate.md must include a self-check instruction"
