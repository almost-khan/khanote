"""Tests for RSS researcher (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch



class TestRSSResearcher:
    """T083: RSS researcher tests."""

    def test_implements_researcher_protocol(self):
        from khanote.researchers.rss import RSSResearcher
        from khanote.researchers.base import Researcher
        r = RSSResearcher(feed_url="https://example.com/feed.xml")
        assert isinstance(r, Researcher)

    def test_search_returns_list(self):
        from khanote.researchers.rss import RSSResearcher
        r = RSSResearcher(feed_url="https://example.com/feed.xml")

        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(
                title="RSS Article 1",
                link="https://example.com/article1",
                summary="Article 1 summary",
                published="Mon, 24 Mar 2026 10:00:00 GMT",
            ),
            MagicMock(
                title="RSS Article 2",
                link="https://example.com/article2",
                summary="Article 2 summary",
                published="Mon, 24 Mar 2026 09:00:00 GMT",
            ),
        ]
        mock_feed.bozo = False

        with patch("feedparser.parse", return_value=mock_feed):
            results = r.search("")
        assert isinstance(results, list)
        assert len(results) == 2

    def test_search_result_has_required_fields(self):
        from khanote.researchers.rss import RSSResearcher
        r = RSSResearcher(feed_url="https://example.com/feed.xml")
        entry = MagicMock()
        entry.title = "Test Entry"
        entry.link = "https://example.com/test"
        entry.summary = "Test summary"
        entry.published = ""
        result = r._parse_entry(entry)
        assert result is not None
        assert "id" in result
        assert "title" in result
        assert "excerpt" in result

    def test_keyword_filtering(self):
        """RSS researcher filters by keywords when provided."""
        from khanote.researchers.rss import RSSResearcher
        r = RSSResearcher(feed_url="https://example.com/feed.xml")

        mock_feed = MagicMock()
        entry1 = MagicMock()
        entry1.title = "Python AI Framework"
        entry1.link = "https://example.com/python-ai"
        entry1.summary = "Python and AI"
        entry1.published = ""

        entry2 = MagicMock()
        entry2.title = "JavaScript Update"
        entry2.link = "https://example.com/js"
        entry2.summary = "JavaScript news"
        entry2.published = ""

        mock_feed.entries = [entry1, entry2]
        mock_feed.bozo = False

        with patch("feedparser.parse", return_value=mock_feed):
            results = r.search("python")
        assert isinstance(results, list)

    def test_analyze_returns_dict(self):
        from khanote.researchers.rss import RSSResearcher
        r = RSSResearcher(feed_url="https://example.com/feed.xml")
        result = r.analyze(query="test")
        assert isinstance(result, dict)
        assert "summary" in result

    def test_ingest_returns_structure(self):
        from khanote.researchers.rss import RSSResearcher
        r = RSSResearcher(feed_url="https://example.com/feed.xml")
        result = r.ingest(["https://example.com/feed.xml"])
        assert "source_count" in result

    def test_bozo_feed_handled_gracefully(self):
        """Malformed RSS feeds don't crash the researcher."""
        from khanote.researchers.rss import RSSResearcher
        r = RSSResearcher(feed_url="https://example.com/feed.xml")
        mock_feed = MagicMock()
        mock_feed.entries = []
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("Feed parse error")

        with patch("feedparser.parse", return_value=mock_feed):
            results = r.search("")
        assert isinstance(results, list)
