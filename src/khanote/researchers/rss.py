"""RSS researcher — parse RSS/Atom feeds using feedparser."""
from __future__ import annotations

from khanote.researchers.base import ResearcherError

_MAX_RESULTS = 20


class RSSResearcher:
    """Read RSS/Atom feed entries using feedparser.

    No authentication required. Supports RSS 2.0 and Atom feeds.
    """

    def __init__(self, feed_url: str) -> None:
        self._feed_url = feed_url
        self._results_cache: list[dict] = []

    def search(self, query: str) -> list[dict]:
        """Fetch feed entries, optionally filtering by query keywords.

        Args:
            query: Optional keyword filter. Empty string returns all recent entries.

        Returns:
            List of dicts with id, title, excerpt, score fields.
        """
        import feedparser
        try:
            feed = feedparser.parse(self._feed_url)
        except Exception as e:
            raise ResearcherError(f"RSS parse failed for {self._feed_url}: {e}", researcher="rss") from e

        entries = feed.entries[:_MAX_RESULTS]
        results = []

        for entry in entries:
            parsed = self._parse_entry(entry)
            if parsed:
                if query.strip():
                    # Filter by keyword match
                    text = (parsed["title"] + " " + parsed["excerpt"]).lower()
                    if query.lower() in text:
                        results.append(parsed)
                else:
                    results.append(parsed)

        # If keyword filter returned nothing, return all entries
        if query.strip() and not results:
            results = [self._parse_entry(e) for e in entries if self._parse_entry(e)]

        self._results_cache = [r for r in results if r]
        return self._results_cache

    def analyze(self, query: str | None = None, **kwargs) -> dict:
        """Analyze cached RSS feed results."""
        results = self._results_cache
        if not results:
            return {"summary": "No RSS entries to analyze.", "sections": {}, "raw": None}

        summary = f"Found {len(results)} RSS entries from {self._feed_url}. Latest: {results[0]['title']}."
        return {
            "summary": summary,
            "sections": {"Entries": "\n".join(f"- {r['title']}" for r in results[:5])},
            "raw": results,
        }

    def generate(self, type: str, **kwargs) -> str:
        """Generate content from RSS results."""
        if not self._results_cache:
            return "No RSS entries available."
        lines = [f"## RSS Feed: {self._feed_url}\n"]
        for r in self._results_cache[:5]:
            lines.append(f"- **{r['title']}**")
            if r.get("url"):
                lines.append(f"  [{r['url']}]({r['url']})")
            if r.get("excerpt"):
                lines.append(f"  {r['excerpt'][:150]}")
        return "\n".join(lines)

    def ingest(self, sources: list[str]) -> dict:
        """Ingest RSS feed URLs."""
        return {"source_count": len(sources), "indexed_ids": sources}

    def _parse_entry(self, entry) -> dict | None:
        """Parse a feedparser entry into a SearchResult-like dict."""
        try:
            title = getattr(entry, "title", None) or "Untitled"
            link = getattr(entry, "link", None) or ""
            summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
            published = getattr(entry, "published", None) or ""

            # Strip HTML from summary if present
            if summary:
                import re
                summary = re.sub(r"<[^>]+>", "", summary).strip()

            excerpt = summary[:400] if summary else f"From {link}"
            if published and len(published) >= 10:
                excerpt = f"[{published[:10]}] {excerpt}"

            return {
                "id": f"rss:{link or title}",
                "title": title[:200],
                "excerpt": excerpt[:400],
                "score": 0.7,
                "url": link or None,
                "published": published,
                "source": "rss",
            }
        except Exception:
            return None
