"""Hacker News researcher — Algolia HN search API."""
from __future__ import annotations

import httpx

from khanote.researchers.base import ResearcherError

_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"
_MAX_RESULTS = 15
_TIMEOUT = 15.0


class HackerNewsResearcher:
    """Search Hacker News using the Algolia API.

    Free, no API key required, no rate limit documented.
    """

    def __init__(self) -> None:
        self._results_cache: list[dict] = []

    def search(self, query: str) -> list[dict]:
        """Search Hacker News stories and Ask HN posts.

        Args:
            query: Search query. Empty string returns front page results.

        Returns:
            List of dicts with id, title, excerpt, score fields.
        """
        if not query.strip():
            # Front page: search by date for top stories
            params = {
                "tags": "story",
                "hitsPerPage": _MAX_RESULTS,
            }
            url = _SEARCH_BY_DATE_URL
        else:
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": _MAX_RESULTS,
            }
            url = _SEARCH_URL

        try:
            resp = httpx.get(url, params=params, timeout=_TIMEOUT)
            data = resp.json()
            hits = data.get("hits", [])
            results = [self._parse_hit(hit) for hit in hits]
            self._results_cache = results
            return results
        except Exception as e:
            raise ResearcherError(f"HN search failed: {e}", researcher="hackernews") from e

    def analyze(self, query: str | None = None, **kwargs) -> dict:
        """Analyze cached HN results."""
        results = self._results_cache
        if not results:
            return {"summary": "No Hacker News results to analyze.", "sections": {}, "raw": None}

        top = results[:3]
        summary = f"Found {len(results)} HN stories. Top: {', '.join(r['title'] for r in top)}."
        return {
            "summary": summary,
            "sections": {
                "Top Stories": "\n".join(
                    f"- {r['title']} ({r.get('points', 0)} pts)" for r in results[:5]
                )
            },
            "raw": results,
        }

    def generate(self, type: str, **kwargs) -> str:
        """Generate content from HN results."""
        if not self._results_cache:
            return "No Hacker News results available."
        lines = ["## Hacker News Stories\n"]
        for r in self._results_cache[:5]:
            pts = r.get("points", 0)
            comments = r.get("comments", 0)
            lines.append(f"- **{r['title']}** ({pts} pts, {comments} comments)")
            if r.get("url"):
                lines.append(f"  [{r['url']}]({r['url']})")
        return "\n".join(lines)

    def ingest(self, sources: list[str]) -> dict:
        """Ingest HN item URLs."""
        return {"source_count": len(sources), "indexed_ids": sources}

    def _parse_hit(self, hit: dict) -> dict:
        """Parse an Algolia HN search hit into a SearchResult-like dict."""
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        title = hit.get("title") or hit.get("story_title", "No title")
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        author = hit.get("author", "unknown")

        # Score: normalized points (HN items can have 0-thousands)
        import math
        score = min(1.0, math.log10(points + 1) / 4.0) if points > 0 else 0.3

        excerpt = f"{points} points, {comments} comments by {author}"
        if hit.get("url"):
            excerpt += f" — {hit['url']}"

        return {
            "id": f"hn:{hit.get('objectID', 'unknown')}",
            "title": title,
            "excerpt": excerpt[:400],
            "score": round(score, 3),
            "url": url,
            "points": points,
            "comments": comments,
            "author": author,
            "source": "hackernews",
        }
