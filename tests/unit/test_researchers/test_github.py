"""Tests for GitHub researcher (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch



class TestGitHubResearcher:
    """T080: GitHub researcher tests."""

    def test_implements_researcher_protocol(self):
        from khanote.researchers.github_researcher import GitHubResearcher
        from khanote.researchers.base import Researcher
        r = GitHubResearcher()
        assert isinstance(r, Researcher)

    def test_search_returns_list(self):
        from khanote.researchers.github_researcher import GitHubResearcher
        r = GitHubResearcher()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 1,
                    "name": "awesome-ai",
                    "full_name": "user/awesome-ai",
                    "description": "Awesome AI framework",
                    "html_url": "https://github.com/user/awesome-ai",
                    "stargazers_count": 1000,
                    "language": "Python",
                }
            ]
        }
        mock_response.status_code = 200
        with patch("httpx.get", return_value=mock_response):
            results = r.search("AI agents")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_result_has_required_fields(self):
        from khanote.researchers.github_researcher import GitHubResearcher
        r = GitHubResearcher()
        repo_data = {
            "id": 1,
            "name": "test-repo",
            "full_name": "user/test-repo",
            "description": "Test repository",
            "html_url": "https://github.com/user/test-repo",
            "stargazers_count": 500,
            "language": "Python",
        }
        result = r._parse_repo(repo_data)
        assert "id" in result
        assert "title" in result
        assert "excerpt" in result
        assert "score" in result

    def test_analyze_returns_dict(self):
        from khanote.researchers.github_researcher import GitHubResearcher
        r = GitHubResearcher()
        result = r.analyze(query="AI frameworks")
        assert isinstance(result, dict)
        assert "summary" in result

    def test_ingest_returns_structure(self):
        from khanote.researchers.github_researcher import GitHubResearcher
        r = GitHubResearcher()
        result = r.ingest(["https://github.com/openai/openai-python"])
        assert "source_count" in result

    def test_empty_search_returns_list(self):
        from khanote.researchers.github_researcher import GitHubResearcher
        r = GitHubResearcher()
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_response.status_code = 200
        with patch("httpx.get", return_value=mock_response):
            results = r.search("very-unlikely-query-xyz123456789")
        assert isinstance(results, list)

    def test_optional_token_auth(self):
        """GitHub researcher works with or without GITHUB_TOKEN."""
        from khanote.researchers.github_researcher import GitHubResearcher
        r = GitHubResearcher(token=None)
        assert r is not None
        r_with_token = GitHubResearcher(token="test-token")
        assert r_with_token is not None
