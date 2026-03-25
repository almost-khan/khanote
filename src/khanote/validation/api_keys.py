"""Lightweight API key validators for khanote init wizard.

Each validator sends a single minimal HTTP request with a 5-second timeout.
A failing key is a warning, not a blocker — init always completes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import httpx


@dataclass
class ApiKeyValidationResult:
    """Result of a lightweight API key ping."""
    researcher: str
    key_name: str | None
    valid: bool | None = None  # True=✓  False=✗  None=skipped/timeout
    error: str | None = None


# ── Per-researcher validators ─────────────────────────────────────────────────

def _validate_perplexity(key: str) -> ApiKeyValidationResult:
    try:
        resp = httpx.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "sonar", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=5.0,
        )
        if resp.status_code == 200:
            return ApiKeyValidationResult("perplexity", "PERPLEXITY_API_KEY", valid=True)
        return ApiKeyValidationResult("perplexity", "PERPLEXITY_API_KEY", valid=False, error=f"HTTP {resp.status_code}")
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        return ApiKeyValidationResult("perplexity", "PERPLEXITY_API_KEY", valid=None, error=str(exc))


def _validate_newsapi(key: str) -> ApiKeyValidationResult:
    try:
        resp = httpx.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "us", "pageSize": "1", "apiKey": key},
            timeout=5.0,
        )
        if resp.status_code == 200:
            return ApiKeyValidationResult("newsapi", "NEWSAPI_KEY", valid=True)
        return ApiKeyValidationResult("newsapi", "NEWSAPI_KEY", valid=False, error=f"HTTP {resp.status_code}: {resp.text[:80]}")
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        return ApiKeyValidationResult("newsapi", "NEWSAPI_KEY", valid=None, error=str(exc))


def _validate_producthunt(key: str) -> ApiKeyValidationResult:
    try:
        resp = httpx.post(
            "https://api.producthunt.com/v2/api/graphql",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"query": "{ __typename }"},
            timeout=5.0,
        )
        if resp.status_code == 200:
            return ApiKeyValidationResult("producthunt", "PRODUCTHUNT_TOKEN", valid=True)
        return ApiKeyValidationResult("producthunt", "PRODUCTHUNT_TOKEN", valid=False, error=f"HTTP {resp.status_code}")
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        return ApiKeyValidationResult("producthunt", "PRODUCTHUNT_TOKEN", valid=None, error=str(exc))


def _validate_notebooklm(key: str) -> ApiKeyValidationResult:
    try:
        resp = httpx.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": key},
            timeout=5.0,
        )
        if resp.status_code == 200:
            return ApiKeyValidationResult("notebooklm", "GOOGLE_API_KEY", valid=True)
        return ApiKeyValidationResult("notebooklm", "GOOGLE_API_KEY", valid=False, error=f"HTTP {resp.status_code}")
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        return ApiKeyValidationResult("notebooklm", "GOOGLE_API_KEY", valid=None, error=str(exc))


# Registry of researchers that require keys → validator function
VALIDATORS: dict[str, Callable[[str], ApiKeyValidationResult]] = {
    "perplexity": _validate_perplexity,
    "newsapi": _validate_newsapi,
    "producthunt": _validate_producthunt,
    "notebooklm": _validate_notebooklm,
}

# Researchers with no required key (validation skipped)
_NO_KEY_RESEARCHERS = {"arxiv", "pubmed", "github", "hackernews", "rss"}


def validate_api_key(researcher: str, key_value: str | None) -> ApiKeyValidationResult:
    """Validate *key_value* for *researcher*.

    Returns ApiKeyValidationResult with:
    - valid=True  if key is confirmed working
    - valid=False if key is confirmed invalid
    - valid=None  if validation was skipped (no key, free researcher, timeout)
    """
    if researcher in _NO_KEY_RESEARCHERS or not key_value:
        return ApiKeyValidationResult(researcher, key_name=None, valid=None)

    validator = VALIDATORS.get(researcher)
    if validator is None:
        return ApiKeyValidationResult(researcher, key_name=None, valid=None)

    return validator(key_value)
