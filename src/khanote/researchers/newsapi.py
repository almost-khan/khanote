"""NewsAPI researcher — newsapi.org /everything endpoint."""
from __future__ import annotations

import os

import httpx

from khanote.researchers.base import ResearcherError

_EVERYTHING_URL = "https://newsapi.org/v2/everything"
_MAX_RESULTS = 15
_TIMEOUT = 15.0


class NewsAPIResearcher:
    """Search news articles using newsapi.org.

    Requires NEWSAPI_KEY environment variable or api_key parameter.
    Free tier: 100 requests/day.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("NEWSAPI_KEY")
        self._results_cache: list[dict] = []

    def search(self, query: str) -> list[dict]:
        """Search news articles matching the query.

        Args:
            query: Search query string.

        Returns:
            List of dicts with id, title, excerpt, score fields.

        Raises:
            ResearcherError: If API key missing or request fails.
        """
        if not self._api_key:
            raise ResearcherError(
                "NewsAPI requires an API key. Set NEWSAPI_KEY environment variable.",
                researcher="newsapi",
            )

        params = {
            "q": query or "technology",
            "apiKey": self._api_key,
            "pageSize": _MAX_RESULTS,
            "language": "en",
            "sortBy": "relevancy",
        }

        try:
            resp = httpx.get(_EVERYTHING_URL, params=params, timeout=_TIMEOUT)
            data = resp.json()

            if data.get("status") == "error":
                raise ResearcherError(
                    f"NewsAPI error: {data.get('message', 'unknown error')}",
                    researcher="newsapi",
                )

            articles = data.get("articles", [])
            results = [self._parse_article(a) for a in articles]
            self._results_cache = results
            return results
        except ResearcherError:
            raise
        except Exception as e:
            raise ResearcherError(f"NewsAPI search failed: {e}", researcher="newsapi") from e

    def analyze(self, query: str | None = None, **kwargs) -> dict:
        """Analyze cached NewsAPI results."""
        results = self._results_cache
        if not results:
            return {"summary": "No news articles to analyze.", "sections": {}, "raw": None}

        sources = list({r.get("source_name", "Unknown") for r in results[:10]})
        summary = f"Found {len(results)} articles from {len(sources)} sources: {', '.join(sources[:3])}."
        return {
            "summary": summary,
            "sections": {"Headlines": "\n".join(f"- {r['title']}" for r in results[:5])},
            "raw": results,
        }

    def generate(self, type: str, **kwargs) -> str:
        """Generate content from NewsAPI results."""
        if not self._results_cache:
            return "No news articles available."
        lines = ["## News Articles\n"]
        for r in self._results_cache[:5]:
            lines.append(f"- **{r['title']}** — {r.get('source_name', 'Unknown')}")
            if r.get("url"):
                lines.append(f"  [{r['url']}]({r['url']})")
        return "\n".join(lines)

    def ingest(self, sources: list[str]) -> dict:
        """Ingest article URLs."""
        return {"source_count": len(sources), "indexed_ids": sources}

    def _parse_article(self, article: dict) -> dict:
        """Parse a NewsAPI article response into a SearchResult-like dict."""
        title = article.get("title") or "Untitled"
        description = article.get("description") or article.get("content") or ""
        url = article.get("url", "")
        source_name = (article.get("source") or {}).get("name", "Unknown")
        published = article.get("publishedAt", "")

        excerpt = f"{description[:300]}" if description else f"From {source_name}"
        if published:
            excerpt = f"[{published[:10]}] {excerpt}"

        # Simple content-based score
        score = 0.6
        if description and len(description) > 100:
            score = 0.8

        return {
            "id": f"newsapi:{url}",
            "title": title[:200],
            "excerpt": excerpt[:400],
            "score": score,
            "url": url,
            "source_name": source_name,
            "published_at": published,
            "source": "newsapi",
        }
