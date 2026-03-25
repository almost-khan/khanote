"""Product Hunt researcher — GraphQL API v2."""
from __future__ import annotations

import os

import httpx

from khanote.researchers.base import ResearcherError

_GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"
_TIMEOUT = 15.0
_MAX_RESULTS = 10

_SEARCH_QUERY = """
query SearchPosts($query: String!, $first: Int!) {
  posts(first: $first, order: VOTES, search: $query) {
    edges {
      node {
        id
        name
        tagline
        url
        votesCount
        description
      }
    }
  }
}
"""

_FEATURED_QUERY = """
query FeaturedPosts($first: Int!) {
  posts(first: $first, order: VOTES) {
    edges {
      node {
        id
        name
        tagline
        url
        votesCount
        description
      }
    }
  }
}
"""


class ProductHuntResearcher:
    """Search Product Hunt products using GraphQL API v2.

    Requires PRODUCTHUNT_TOKEN environment variable or token parameter.
    Free tier: 500 requests/day.
    """

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ.get("PRODUCTHUNT_TOKEN")
        self._results_cache: list[dict] = []

    def search(self, query: str) -> list[dict]:
        """Search Product Hunt posts matching the query.

        Args:
            query: Search query string.

        Returns:
            List of dicts with id, title, excerpt, score fields.

        Raises:
            ResearcherError: If token missing or request fails.
        """
        if not self._token:
            raise ResearcherError(
                "Product Hunt requires a token. Set PRODUCTHUNT_TOKEN environment variable.",
                researcher="producthunt",
            )

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        if query.strip():
            payload = {
                "query": _SEARCH_QUERY,
                "variables": {"query": query, "first": _MAX_RESULTS},
            }
        else:
            payload = {
                "query": _FEATURED_QUERY,
                "variables": {"first": _MAX_RESULTS},
            }

        try:
            resp = httpx.post(_GRAPHQL_URL, json=payload, headers=headers, timeout=_TIMEOUT)
            data = resp.json()

            if "errors" in data:
                raise ResearcherError(
                    f"Product Hunt API error: {data['errors']}",
                    researcher="producthunt",
                )

            posts = data.get("data", {}).get("posts", {}).get("edges", [])
            results = [self._parse_post(edge["node"]) for edge in posts]
            self._results_cache = results
            return results
        except ResearcherError:
            raise
        except Exception as e:
            raise ResearcherError(f"Product Hunt search failed: {e}", researcher="producthunt") from e

    def analyze(self, query: str | None = None, **kwargs) -> dict:
        """Analyze cached Product Hunt results."""
        results = self._results_cache
        if not results:
            return {"summary": "No Product Hunt results to analyze.", "sections": {}, "raw": None}

        top = results[:3]
        summary = f"Found {len(results)} products. Top: {', '.join(r['title'] for r in top)}."
        return {
            "summary": summary,
            "sections": {"Top Products": "\n".join(f"- {r['title']}: {r['excerpt']}" for r in results[:5])},
            "raw": results,
        }

    def generate(self, type: str, **kwargs) -> str:
        """Generate content from Product Hunt results."""
        if not self._results_cache:
            return "No Product Hunt results available."
        lines = ["## Product Hunt\n"]
        for r in self._results_cache[:5]:
            lines.append(f"- **{r['title']}** — {r['excerpt']}")
            if r.get("url"):
                lines.append(f"  [{r['url']}]({r['url']})")
        return "\n".join(lines)

    def ingest(self, sources: list[str]) -> dict:
        """Ingest Product Hunt post URLs."""
        return {"source_count": len(sources), "indexed_ids": sources}

    def _parse_post(self, node: dict) -> dict:
        """Parse a Product Hunt post node into a SearchResult-like dict."""
        votes = node.get("votesCount", 0)
        name = node.get("name", "Unnamed")
        tagline = node.get("tagline") or ""
        url = node.get("url", "")
        description = node.get("description") or tagline

        excerpt = f"⬆ {votes} — {description}"

        # Score based on votes
        import math
        score = min(1.0, math.log10(votes + 1) / 4.0) if votes > 0 else 0.3

        return {
            "id": f"ph:{node.get('id', name)}",
            "title": name,
            "excerpt": excerpt[:400],
            "score": round(score, 3),
            "url": url,
            "votes": votes,
            "tagline": tagline,
            "source": "producthunt",
        }
