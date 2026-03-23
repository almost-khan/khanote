"""arXiv researcher — arXiv API search + Semantic Scholar enrichment."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

from khanote.researchers.base import ResearcherError

_ARXIV_API = "https://export.arxiv.org/api/query"
_S2_API = "https://api.semanticscholar.org/graph/v1/paper"
_ATOM_NS = "http://www.w3.org/2005/Atom"


class ArxivResearcher:
    """Stable researcher using arXiv API + optional Semantic Scholar enrichment."""

    status = "stable"

    def __init__(self, semantic_scholar_api_key: str | None = None) -> None:
        self.s2_key = semantic_scholar_api_key
        self._client = httpx.Client(timeout=30.0)
        self._ingested: list[str] = []

    def ingest(self, sources: list[str]) -> dict:
        """Record sources (arXiv IDs or URLs) for analysis."""
        self._ingested.extend(sources)
        return {"source_count": len(sources), "indexed_ids": list(range(len(sources)))}

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search arXiv for papers matching query."""
        try:
            response = self._client.get(
                _ARXIV_API,
                params={
                    "search_query": f"all:{query}",
                    "max_results": max_results,
                    "sortBy": "relevance",
                },
            )
            response.raise_for_status()
            return self._parse_arxiv_results(response.text)
        except httpx.HTTPError as e:
            raise ResearcherError(f"arXiv API error: {e}", researcher="arxiv") from e

    def analyze(self, query: str | None = None) -> dict:
        """Analyze ingested sources or search results."""
        if query:
            results = self.search(query)
        elif self._ingested:
            results = [{"id": s, "title": s, "excerpt": "", "score": 0.5} for s in self._ingested]
        else:
            results = []

        summary_parts = []
        for r in results[:5]:
            summary_parts.append(f"- **{r['title']}** (score: {r['score']:.2f})\n  {r['excerpt']}")

        summary = "\n".join(summary_parts) if summary_parts else "No results found."
        return {
            "summary": summary,
            "sections": {
                "Top Papers": summary,
                "Methodology": "arXiv API search with relevance scoring",
            },
            "raw": results,
        }

    def generate(self, type: str, **kwargs) -> str | bytes:
        """Generate a structured summary of ingested papers."""
        return f"arXiv summary for {type}: {', '.join(self._ingested[:3])}"

    def _parse_arxiv_results(self, xml_text: str) -> list[dict]:
        """Parse arXiv Atom feed into result dicts."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        results = []
        for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
            arxiv_id = entry.findtext(f"{{{_ATOM_NS}}}id", "").split("/abs/")[-1].split("v")[0]
            title = (entry.findtext(f"{{{_ATOM_NS}}}title") or "").strip()
            summary = (entry.findtext(f"{{{_ATOM_NS}}}summary") or "").strip()
            published = entry.findtext(f"{{{_ATOM_NS}}}published", "")
            score = self._score_result(published)
            results.append({
                "id": arxiv_id,
                "title": title,
                "excerpt": summary[:300],
                "score": score,
            })
        return results

    def _score_result(self, published_str: str) -> float:
        """Score based on recency (0.0–1.0)."""
        try:
            dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            age_days = (datetime.now(tz=timezone.utc) - dt).days
            return max(0.1, 1.0 - age_days / 3650)  # Decay over 10 years
        except Exception:
            return 0.5
