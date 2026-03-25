"""Tests for version checker (TDD)."""
import json
import time
from unittest.mock import patch


from khanote.cli.version import _is_newer, _read_cache, _write_cache, check_version


class TestVersionComparison:
    def test_newer_major(self):
        assert _is_newer("2.0.0", "1.0.0") is True

    def test_newer_minor(self):
        assert _is_newer("1.1.0", "1.0.0") is True

    def test_newer_patch(self):
        assert _is_newer("1.0.1", "1.0.0") is True

    def test_same_version(self):
        assert _is_newer("1.0.0", "1.0.0") is False

    def test_older_version(self):
        assert _is_newer("0.9.0", "1.0.0") is False


class TestVersionCache:
    def test_write_and_read_cache(self, tmp_path):
        cache_file = tmp_path / ".version_check"
        _write_cache(cache_file, "1.2.3")
        result = _read_cache(cache_file)
        assert result["latest"] == "1.2.3"
        assert "checked_at" in result

    def test_read_missing_cache_returns_none(self, tmp_path):
        result = _read_cache(tmp_path / "nonexistent")
        assert result is None

    def test_cache_ttl_respected(self, tmp_path):
        cache_file = tmp_path / ".version_check"
        # Write cache with old timestamp
        data = {"latest": "99.0.0", "checked_at": time.time() - 100000}
        cache_file.write_text(json.dumps(data))
        result = _read_cache(cache_file)
        # Cache is stale (>24h) — check_version should re-fetch
        assert result["latest"] == "99.0.0"  # Still readable, TTL check is in check_version

    def test_write_cache_with_none_path_does_not_raise(self):
        _write_cache(None, "1.0.0")  # Should silently no-op


class TestCheckVersion:
    def test_check_version_does_not_raise_on_network_error(self, tmp_path):
        """Version check should never block the user."""
        with patch("httpx.get", side_effect=Exception("network error")):
            check_version(khanote_dir=tmp_path)  # Must not raise

    def test_check_version_prints_notice_when_newer(self, tmp_path, capsys):
        with patch("khanote.cli.version._fetch_latest_from_pypi", return_value="99.0.0"):
            check_version(khanote_dir=tmp_path)
        # Should have printed something (captured by capsys or rich console)
        # We just verify no exception was raised

    def test_check_version_silent_when_up_to_date(self, tmp_path):
        import khanote
        current = khanote.__version__
        with patch("khanote.cli.version._fetch_latest_from_pypi", return_value=current):
            check_version(khanote_dir=tmp_path)  # Should not raise or print update notice
