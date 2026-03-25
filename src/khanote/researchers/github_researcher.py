"""GitHub researcher — search repositories via GitHub REST API."""
from __future__ import annotations

import os

import httpx

from khanote.researchers.base import ResearcherError

_SEARCH_URL = "https://api.github.com/search/repositories"
_MAX_RESULTS = 10
_TIMEOUT = 15.0


class GitHubResearcher:
    """Search GitHub repositories using the REST API.

    Free tier: 60 requests/hour unauthenticated, 5000/hour with token.
    Set GITHUB_TOKEN environment variable for authenticated access.
    """

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN")
        self._results_cache: list[dict] = []

    def _headers(self) -> dict:
        """Build request headers."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "khanote/1.0",
        }
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        return headers

    def search(self, query: str) -> list[dict]:
        """Search GitHub repositories matching the query.

        Args:
            query: Search query string.

        Returns:
            List of dicts with id, title, excerpt, score fields.
        """
        if not query.strip():
            params = {"q": "stars:>1000 sort:stars", "per_page": _MAX_RESULTS}
        else:
            params = {"q": query, "sort": "stars", "order": "desc", "per_page": _MAX_RESULTS}

        try:
            resp = httpx.get(
                _SEARCH_URL,
                params=params,
                headers=self._headers(),
                timeout=_TIMEOUT,
            )
            data = resp.json()
            items = data.get("items", [])
            results = [self._parse_repo(item) for item in items]
            self._results_cache = results
            return results
        except Exception as e:
            raise ResearcherError(f"GitHub search failed: {e}", researcher="github") from e

    def analyze(self, query: str | None = None, **kwargs) -> dict:
        """Analyze cached GitHub results."""
        results = self._results_cache
        if not results:
            return {"summary": "No GitHub results to analyze.", "sections": {}, "raw": None}

        top_names = [r["title"] for r in results[:3]]
        summary = f"Found {len(results)} GitHub repositories. Top: {', '.join(top_names)}."
        return {
            "summary": summary,
            "sections": {"Top Repositories": "\n".join(f"- {r['title']}: {r['excerpt']}" for r in results[:5])},
            "raw": results,
        }

    def generate(self, type: str, **kwargs) -> str:
        """Generate content from GitHub results."""
        if not self._results_cache:
            return "No GitHub results available."
        lines = ["## GitHub Repositories\n"]
        for r in self._results_cache[:5]:
            lines.append(f"- **[{r['title']}]({r.get('url', '')})**")
            lines.append(f"  {r['excerpt']}")
        return "\n".join(lines)

    def ingest(self, sources: list[str]) -> dict:
        """Ingest GitHub repository URLs."""
        return {"source_count": len(sources), "indexed_ids": sources}

    def _parse_repo(self, repo: dict) -> dict:
        """Parse a GitHub repository API response into a SearchResult-like dict."""
        stars = repo.get("stargazers_count", 0)
        lang = repo.get("language", "")
        desc = repo.get("description") or ""
        lang_str = f" [{lang}]" if lang else ""
        excerpt = f"⭐ {stars}{lang_str} — {desc}"

        # Normalize score: log-scale stars to 0-1 range
        import math
        score = min(1.0, math.log10(stars + 1) / 5.0) if stars > 0 else 0.1

        return {
            "id": f"github:{repo.get('id', repo.get('full_name', 'unknown'))}",
            "title": repo.get("full_name") or repo.get("name", "unknown"),
            "excerpt": excerpt[:400],
            "score": round(score, 3),
            "url": repo.get("html_url"),
            "stars": stars,
            "language": lang,
            "source": "github",
        }
