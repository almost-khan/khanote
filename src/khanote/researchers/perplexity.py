"""Perplexity researcher — uses Sonar API for analysis."""
from __future__ import annotations

import hashlib
import uuid

import httpx

from khanote.researchers.base import ResearcherError

_SONAR_API = "https://api.perplexity.ai/chat/completions"
_DEFAULT_MODEL = "sonar"
_DEEP_RESEARCH_MODEL = "sonar-deep-research"


class PerplexityResearcher:
    """Stable researcher using Perplexity Sonar API."""

    status = "stable"

    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self.api_key = api_key
        self.model = model
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        self._ingested: list[str] = []

    def ingest(self, sources: list[str]) -> dict:
        """Record sources for subsequent analysis."""
        self._ingested.extend(sources)
        indexed_ids = [hashlib.md5(s.encode()).hexdigest()[:8] for s in sources]
        return {"source_count": len(sources), "indexed_ids": indexed_ids}

    def analyze(self, query: str | None = None) -> dict:
        """Analyze ingested sources using Sonar API."""
        sources_text = "\n".join(self._ingested) if self._ingested else "(no sources provided)"
        prompt = (
            f"{query}\n\nSources:\n{sources_text}"
            if query
            else f"Summarize and analyze the following sources:\n{sources_text}"
        )
        try:
            response = self._client.post(
                _SONAR_API,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return {
                "summary": content,
                "sections": {"Analysis": content},
                "raw": response.json(),
            }
        except httpx.HTTPError as e:
            raise ResearcherError(f"Perplexity API error: {e}", researcher="perplexity") from e

    def generate(self, type: str, **kwargs) -> str | bytes:
        """Generate content using Sonar API."""
        prompt = kwargs.get("prompt", f"Generate a {type} based on previous analysis.")
        try:
            response = self._client.post(
                _SONAR_API,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            raise ResearcherError(f"Perplexity generate error: {e}", researcher="perplexity") from e

    def search(self, query: str) -> list[dict]:
        """Search using Sonar API."""
        try:
            response = self._client.post(
                _SONAR_API,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": f"Search: {query}"}],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            # Return a single synthesized result
            return [{
                "id": hashlib.md5(content.encode()).hexdigest()[:8],
                "title": f"Perplexity result for: {query}",
                "excerpt": content[:200],
                "score": 1.0,
            }]
        except httpx.HTTPError as e:
            raise ResearcherError(f"Perplexity search error: {e}", researcher="perplexity") from e
