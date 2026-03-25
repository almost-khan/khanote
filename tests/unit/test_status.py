"""Unit tests for khanote status command (TDD — fail before implementation)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_config(tmp_path: Path, tools=None, feeds=None) -> Path:
    kdir = tmp_path / ".khanote"
    kdir.mkdir(exist_ok=True)
    cfg = {
        "version": "0.1.0",
        "vault_path": str(tmp_path),
        "initialized_tools": tools or ["claude-code"],
        "research": {"default": "arxiv", "researchers": {"arxiv": {"enabled": True}}},
    }
    if feeds:
        cfg["feeds"] = feeds
    (kdir / "config.yaml").write_text(yaml.dump(cfg))
    return kdir


def _make_prefs(kdir: Path, language="en-US", role="developer", interests=None, depth="summary") -> None:
    prefs = {
        "language": language,
        "role": role,
        "interests": interests or ["ai"],
        "depth": depth,
    }
    (kdir / "preferences.yaml").write_text(yaml.dump(prefs))


# ── StatusReport model ────────────────────────────────────────────────────────

class TestStatusReportModel:
    def test_not_initialized_when_no_config(self, tmp_path):
        from khanote.cli.status import build_status_report
        report = build_status_report(vault_dir=tmp_path)
        assert report.initialized is False

    def test_initialized_when_config_exists(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        assert report.initialized is True

    def test_tool_extracted_from_config(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path, tools=["cursor"])
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        assert report.tool == "cursor"

    def test_output_path_from_config(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        assert report.output_path == tmp_path

    def test_feeds_count_zero_when_none_configured(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        assert report.feeds_count == 0

    def test_feeds_count_from_config(self, tmp_path):
        from khanote.cli.status import build_status_report
        feeds = {
            "ai-papers": {"researcher": "arxiv", "query": "AI agents", "active": True},
            "market": {"researcher": "newsapi", "query": "startup news", "active": True},
        }
        kdir = _make_config(tmp_path, feeds=feeds)
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        assert report.feeds_count == 2

    def test_preferences_loaded(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir, language="zh-CN", role="pm", interests=["ai", "product"], depth="detailed")
        report = build_status_report(vault_dir=tmp_path)
        assert report.preferences is not None
        assert report.preferences.language == "zh-CN"
        assert report.preferences.role == "pm"
        assert "ai" in report.preferences.interests
        assert report.preferences.depth == "detailed"

    def test_missing_preferences_yaml_produces_warning(self, tmp_path):
        from khanote.cli.status import build_status_report
        _make_config(tmp_path)
        # No preferences.yaml written
        report = build_status_report(vault_dir=tmp_path)
        assert any("preferences" in w.lower() for w in report.warnings)

    def test_no_feeds_warning(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        assert any("feed" in w.lower() for w in report.warnings)


# ── ApiKeyStatus masking ──────────────────────────────────────────────────────

class TestApiKeyStatus:
    def test_present_key_is_masked(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "sk-pplx-abc123456789"}):
            report = build_status_report(vault_dir=tmp_path)
        key = next((k for k in report.api_keys if k.name == "PERPLEXITY_API_KEY"), None)
        assert key is not None
        assert key.present is True
        assert "****" in key.display
        assert "sk-pplx-abc123456789" not in key.display

    def test_absent_key_shows_not_set(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        with patch.dict("os.environ", {}, clear=False):
            # Ensure PERPLEXITY_API_KEY is unset
            import os
            os.environ.pop("PERPLEXITY_API_KEY", None)
            report = build_status_report(vault_dir=tmp_path)
        key = next((k for k in report.api_keys if k.name == "PERPLEXITY_API_KEY"), None)
        assert key is not None
        assert key.present is False
        assert key.display == "not set"

    def test_short_key_masked_safely(self, tmp_path):
        from khanote.cli.status import build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "abc"}):
            report = build_status_report(vault_dir=tmp_path)
        key = next((k for k in report.api_keys if k.name == "PERPLEXITY_API_KEY"), None)
        assert key is not None
        assert key.present is True
        assert "****" in key.display


# ── Rendering ─────────────────────────────────────────────────────────────────

class TestStatusRendering:
    def test_render_not_initialized(self, tmp_path):
        from khanote.cli.status import render_status_report, build_status_report
        report = build_status_report(vault_dir=tmp_path)
        output = render_status_report(report)
        assert "not initialized" in output.lower() or "khanote init" in output.lower()

    def test_render_shows_tool(self, tmp_path):
        from khanote.cli.status import render_status_report, build_status_report
        kdir = _make_config(tmp_path, tools=["claude-code"])
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        output = render_status_report(report)
        assert "claude-code" in output.lower() or "claude" in output.lower()

    def test_render_shows_feeds_count(self, tmp_path):
        from khanote.cli.status import render_status_report, build_status_report
        feeds = {"ai-feed": {"researcher": "arxiv", "query": "ai", "active": True}}
        kdir = _make_config(tmp_path, feeds=feeds)
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        output = render_status_report(report)
        assert "1" in output

    def test_render_output_fits_80_chars(self, tmp_path):
        from khanote.cli.status import render_status_report, build_status_report
        kdir = _make_config(tmp_path)
        _make_prefs(kdir)
        report = build_status_report(vault_dir=tmp_path)
        output = render_status_report(report)
        for line in output.splitlines():
            # Strip ANSI codes for length check
            import re
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
            assert len(clean) <= 80, f"Line too long ({len(clean)}): {clean!r}"
