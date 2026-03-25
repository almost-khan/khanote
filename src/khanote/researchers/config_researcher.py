"""ConfigResearcher — wraps any HTTP REST API as a researcher via config.yaml."""
from __future__ import annotations

import time
from typing import Any

import httpx

from khanote.models.config import EndpointConfig, ResearcherConfig
from khanote.researchers.base import ResearcherError
from khanote.templates.sop_loader import SopLoader

_NOOP_ANALYZE = {"summary": "", "sections": {}, "raw": None}
_NOOP_INGEST = {"source_count": 0, "indexed_ids": []}

_sop_loader = SopLoader()


class ConfigResearcher:
    """Config-driven researcher for HTTP REST APIs.

    Capabilities are declared in ResearcherConfig. For each method:
    - If an endpoint is declared: call the HTTP API and map the response.
    - If only an SOP is declared: fill the SOP prompt and return it.
    - Both declared: try endpoint first, fall back to SOP on failure.
    - Not declared at all: return a no-op response.
    """

    def __init__(self, name: str, config: ResearcherConfig) -> None:
        self.name = name
        self._config = config
        self._api_key = config.api_key or ""

    @property
    def capabilities(self) -> list[str]:
        return list(self._config.capabilities)

    # ── Researcher Protocol ────────────────────────────────────────────────────

    def search(self, query: str) -> list[dict]:
        if "search" not in self._config.capabilities:
            return []
        endpoint = self._get_endpoint("search")
        sop = self._get_sop("search")
        if endpoint:
            try:
                return self._call_search_endpoint(endpoint, query)
            except ResearcherError:
                if sop:
                    return self._sop_as_search(sop, query=query)
                raise
        if sop:
            return self._sop_as_search(sop, query=query)
        return []

    def ingest(self, sources: list[str]) -> dict:
        if "ingest" not in self._config.capabilities:
            return _NOOP_INGEST.copy()
        endpoint = self._get_endpoint("ingest")
        sop = self._get_sop("ingest")
        if endpoint:
            try:
                return self._call_ingest_endpoint(endpoint, sources)
            except ResearcherError:
                if sop:
                    return self._sop_as_ingest(sop, sources=sources)
                raise
        if sop:
            return self._sop_as_ingest(sop, sources=sources)
        return _NOOP_INGEST.copy()

    def analyze(self, query: str | None = None, **kwargs) -> dict:
        if "analyze" not in self._config.capabilities:
            return _NOOP_ANALYZE.copy()
        endpoint = self._get_endpoint("analyze")
        sop = self._get_sop("analyze")
        if endpoint:
            try:
                return self._call_analyze_endpoint(endpoint, query, **kwargs)
            except ResearcherError:
                if sop:
                    return self._sop_as_analyze(sop, query=query, **kwargs)
                raise
        if sop:
            return self._sop_as_analyze(sop, query=query, **kwargs)
        return _NOOP_ANALYZE.copy()

    def generate(self, type: str, **kwargs) -> str:
        if "generate" not in self._config.capabilities:
            return ""
        endpoint = self._get_endpoint("generate")
        sop = self._get_sop("generate")
        if endpoint:
            try:
                return self._call_generate_endpoint(endpoint, type, **kwargs)
            except ResearcherError:
                if sop:
                    return self._sop_as_generate(sop, **kwargs)
                raise
        if sop:
            return self._sop_as_generate(sop, **kwargs)
        return ""

    # ── Connectivity Test ──────────────────────────────────────────────────────

    def test_connectivity(self) -> dict:
        """Test API reachability. Returns {"status": "ok"|"failed", "message": str, "latency_ms": int}."""
        endpoints = self._config.endpoints
        if not endpoints:
            return {
                "status": "ok",
                "message": "No endpoints configured — researcher uses SOP mode only",
                "latency_ms": 0,
            }
        # Prefer search endpoint for test
        cap = "search" if "search" in endpoints else next(iter(endpoints))
        endpoint = endpoints[cap]
        start = time.monotonic()
        try:
            with httpx.Client(timeout=10.0) as client:
                headers = self._render_headers(endpoint.headers)
                resp = client.request(
                    method=endpoint.method,
                    url=endpoint.url,
                    headers=headers,
                    content=self._render_body(endpoint.body_template, query="test") if endpoint.method == "POST" else None,
                )
                resp.raise_for_status()
            latency = int((time.monotonic() - start) * 1000)
            return {"status": "ok", "message": "Connection successful", "latency_ms": latency}
        except httpx.HTTPStatusError as e:
            latency = int((time.monotonic() - start) * 1000)
            return {
                "status": "failed",
                "message": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                "latency_ms": latency,
            }
        except Exception as e:
            latency = int((time.monotonic() - start) * 1000)
            return {"status": "failed", "message": str(e), "latency_ms": latency}

    # ── Internal Helpers ───────────────────────────────────────────────────────

    def _get_endpoint(self, capability: str) -> EndpointConfig | None:
        if self._config.endpoints:
            return self._config.endpoints.get(capability)
        return None

    def _get_sop(self, capability: str) -> str | None:
        if self._config.sop:
            return self._config.sop.get(capability)
        return None

    def _render_headers(self, headers: dict[str, str]) -> dict[str, str]:
        return {k: v.replace("{api_key}", self._api_key) for k, v in headers.items()}

    def _render_body(self, template: str, **kwargs) -> bytes:
        body = template.replace("{api_key}", self._api_key)
        for k, v in kwargs.items():
            body = body.replace("{" + k + "}", str(v))
        return body.encode("utf-8")

    def _call_search_endpoint(self, endpoint: EndpointConfig, query: str) -> list[dict]:
        with httpx.Client(timeout=30.0) as client:
            headers = self._render_headers(endpoint.headers)
            resp = client.request(
                method=endpoint.method,
                url=endpoint.url,
                headers=headers,
                content=self._render_body(endpoint.body_template, query=query) if endpoint.method == "POST" else None,
                params={"query": query} if endpoint.method == "GET" else None,
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ResearcherError(
                    f"HTTP {e.response.status_code}", researcher=self.name
                ) from e
        data = resp.json()
        return self._map_search_results(data, endpoint.response_mapping)

    def _map_search_results(self, data: Any, mapping: dict[str, str]) -> list[dict]:
        """Extract results from API response using simple dot-notation mapping."""
        results_path = mapping.get("results", "$.results")
        raw_results = _extract_path(data, results_path)
        if not isinstance(raw_results, list):
            raw_results = []
        out = []
        for i, item in enumerate(raw_results):
            title_path = mapping.get("title", "$.title")
            excerpt_path = mapping.get("excerpt", "$.excerpt")
            score_path = mapping.get("score", "$.score")
            out.append({
                "id": str(i),
                "title": _extract_path(item, title_path) or "",
                "excerpt": _extract_path(item, excerpt_path) or "",
                "score": _extract_path(item, score_path) or 0.0,
            })
        return out

    def _call_ingest_endpoint(self, endpoint: EndpointConfig, sources: list[str]) -> dict:
        # Placeholder for ingest endpoint call
        with httpx.Client(timeout=30.0) as client:
            headers = self._render_headers(endpoint.headers)
            resp = client.request(
                method=endpoint.method,
                url=endpoint.url,
                headers=headers,
                content=self._render_body(endpoint.body_template, sources=",".join(sources)) if endpoint.method == "POST" else None,
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ResearcherError(f"HTTP {e.response.status_code}", researcher=self.name) from e
        return {"source_count": len(sources), "indexed_ids": [str(i) for i in range(len(sources))]}

    def _call_analyze_endpoint(self, endpoint: EndpointConfig, query: str | None, **kwargs) -> dict:
        with httpx.Client(timeout=30.0) as client:
            headers = self._render_headers(endpoint.headers)
            resp = client.request(
                method=endpoint.method,
                url=endpoint.url,
                headers=headers,
                content=self._render_body(endpoint.body_template, query=query or "") if endpoint.method == "POST" else None,
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ResearcherError(f"HTTP {e.response.status_code}", researcher=self.name) from e
        data = resp.json()
        summary = data.get("summary") or data.get("text") or str(data)[:500]
        return {"summary": summary, "sections": data, "raw": data}

    def _call_generate_endpoint(self, endpoint: EndpointConfig, content_type: str, **kwargs) -> str:
        with httpx.Client(timeout=30.0) as client:
            headers = self._render_headers(endpoint.headers)
            resp = client.request(
                method=endpoint.method,
                url=endpoint.url,
                headers=headers,
                content=self._render_body(endpoint.body_template, **kwargs) if endpoint.method == "POST" else None,
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ResearcherError(f"HTTP {e.response.status_code}", researcher=self.name) from e
        return resp.text

    # ── SOP fallback helpers ───────────────────────────────────────────────────

    def _sop_as_search(self, sop: str, **kwargs) -> list[dict]:
        filled = _sop_loader.fill_string(sop, **kwargs)
        return [{"id": "sop-0", "title": "SOP Prompt", "excerpt": filled, "score": 1.0}]

    def _sop_as_ingest(self, sop: str, **kwargs) -> dict:
        filled = _sop_loader.fill_string(sop, **kwargs)
        return {"source_count": 0, "indexed_ids": [], "sop_prompt": filled}

    def _sop_as_analyze(self, sop: str, **kwargs) -> dict:
        # Remove None values from kwargs before filling
        clean_kwargs = {k: str(v) for k, v in kwargs.items() if v is not None}
        filled = _sop_loader.fill_string(sop, **clean_kwargs)
        return {"summary": filled, "sections": {"sop_prompt": filled}, "raw": None}

    def _sop_as_generate(self, sop: str, **kwargs) -> str:
        return _sop_loader.fill_string(sop, **kwargs)


def _extract_path(data: Any, path: str) -> Any:
    """Simple JSONPath-like extraction. Supports '$.field' and '$.field.subfield'."""
    if not isinstance(path, str):
        return data
    # Strip leading $. prefix
    key = path.lstrip("$").lstrip(".")
    if not key:
        return data
    parts = key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and current:
            current = current[0].get(part) if isinstance(current[0], dict) else None
        else:
            return None
    return current
