"""Tests for PubMed researcher (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch



class TestPubMedResearcher:
    """T079: PubMed researcher tests."""

    def test_implements_researcher_protocol(self):
        from khanote.researchers.pubmed import PubMedResearcher
        from khanote.researchers.base import Researcher
        r = PubMedResearcher()
        assert isinstance(r, Researcher)

    def test_search_returns_list(self):
        from khanote.researchers.pubmed import PubMedResearcher
        r = PubMedResearcher()
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" ?>
        <eSearchResult>
          <IdList><Id>12345678</Id></IdList>
        </eSearchResult>"""
        mock_fetch = MagicMock()
        mock_fetch.text = """<?xml version="1.0" ?>
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>12345678</PMID>
              <Article>
                <ArticleTitle>AI in Healthcare</ArticleTitle>
                <Abstract><AbstractText>Study on AI applications.</AbstractText></Abstract>
                <AuthorList>
                  <Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
                </AuthorList>
              </Article>
            </MedlineCitation>
          </PubmedArticle>
        </PubmedArticleSet>"""

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = [mock_response, mock_fetch]
            results = r.search("AI healthcare")
        assert isinstance(results, list)

    def test_search_result_has_required_fields(self):
        from khanote.researchers.pubmed import PubMedResearcher
        r = PubMedResearcher()
        # Direct result parsing test
        result = r._parse_article_xml("""
        <PubmedArticle>
          <MedlineCitation>
            <PMID>99999999</PMID>
            <Article>
              <ArticleTitle>Test Title</ArticleTitle>
              <Abstract><AbstractText>Test abstract.</AbstractText></Abstract>
            </Article>
          </MedlineCitation>
        </PubmedArticle>""")
        assert result is not None
        assert "id" in result
        assert "title" in result
        assert "excerpt" in result

    def test_analyze_returns_summary(self):
        from khanote.researchers.pubmed import PubMedResearcher
        r = PubMedResearcher()
        result = r.analyze(query="AI healthcare", results="test results")
        assert isinstance(result, dict)
        assert "summary" in result

    def test_ingest_returns_structure(self):
        from khanote.researchers.pubmed import PubMedResearcher
        r = PubMedResearcher()
        result = r.ingest(["https://pubmed.ncbi.nlm.nih.gov/12345678/"])
        assert "source_count" in result
        assert "indexed_ids" in result

    def test_generate_returns_string(self):
        from khanote.researchers.pubmed import PubMedResearcher
        r = PubMedResearcher()
        result = r.generate(type="summary")
        assert isinstance(result, (str, bytes))

    def test_empty_search_results_graceful(self):
        from khanote.researchers.pubmed import PubMedResearcher
        r = PubMedResearcher()
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" ?><eSearchResult><IdList></IdList></eSearchResult>"""
        with patch("httpx.get", return_value=mock_response):
            results = r.search("very obscure medical query xyz123")
        assert results == []
