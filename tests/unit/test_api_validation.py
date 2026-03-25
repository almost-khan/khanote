"""Tests for API key validation helpers."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import httpx

from khanote.validation.api_keys import (
    validate_api_key,
    ApiKeyValidationResult,
    VALIDATORS,
)


class TestApiKeyValidationResult:
    def test_valid_result(self):
        r = ApiKeyValidationResult(researcher="perplexity", key_name="PERPLEXITY_API_KEY", valid=True)
        assert r.valid is True
        assert r.error is None

    def test_invalid_result(self):
        r = ApiKeyValidationResult(researcher="perplexity", key_name="PERPLEXITY_API_KEY", valid=False, error="401 Unauthorized")
        assert r.valid is False
        assert r.error == "401 Unauthorized"

    def test_skipped_result(self):
        r = ApiKeyValidationResult(researcher="arxiv", key_name=None, valid=None)
        assert r.valid is None


class TestValidateApiKey:
    def test_skips_researcher_without_required_key(self):
        result = validate_api_key("arxiv", None)
        assert result.valid is None
        assert result.researcher == "arxiv"

    def test_skips_when_key_value_empty(self):
        result = validate_api_key("perplexity", "")
        assert result.valid is None

    def test_valid_perplexity_key(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("httpx.post", return_value=mock_response):
            result = validate_api_key("perplexity", "sk-test-key")
        assert result.valid is True
        assert result.researcher == "perplexity"

    def test_invalid_perplexity_key(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        with patch("httpx.post", return_value=mock_response):
            result = validate_api_key("perplexity", "sk-bad-key")
        assert result.valid is False
        assert result.error is not None

    def test_network_error_returns_none(self):
        with patch("httpx.post", side_effect=httpx.RequestError("timeout")):
            result = validate_api_key("perplexity", "sk-test-key")
        assert result.valid is None
        assert result.error is not None

    def test_timeout_returns_none(self):
        with patch("httpx.post", side_effect=httpx.TimeoutException("5s timeout")):
            result = validate_api_key("perplexity", "sk-test-key")
        assert result.valid is None

    def test_valid_newsapi_key(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("httpx.get", return_value=mock_response):
            result = validate_api_key("newsapi", "test-news-key")
        assert result.valid is True

    def test_invalid_newsapi_key(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "apiKey invalid"
        with patch("httpx.get", return_value=mock_response):
            result = validate_api_key("newsapi", "bad-key")
        assert result.valid is False

    def test_unknown_researcher_skipped(self):
        result = validate_api_key("unknown-researcher", "some-key")
        assert result.valid is None

    def test_validators_dict_has_expected_keys(self):
        assert "perplexity" in VALIDATORS
        assert "newsapi" in VALIDATORS
        assert "producthunt" in VALIDATORS
        assert "notebooklm" in VALIDATORS
        # Free researchers not in validators
        assert "arxiv" not in VALIDATORS
        assert "hackernews" not in VALIDATORS
