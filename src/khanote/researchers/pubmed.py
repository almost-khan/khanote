"""PubMed researcher — NCBI E-utilities API for biomedical literature search."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from khanote.researchers.base import ResearcherError

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_MAX_RESULTS = 10
_TIMEOUT = 15.0


class PubMedResearcher:
    """Search NCBI PubMed database using E-utilities (esearch + efetch).

    Free API, no key required (optional API key for higher rate limits).
    Rate limit: 3 requests/second without key, 10/second with key.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._results_cache: list[dict] = []

    def search(self, query: str) -> list[dict]:
        """Search PubMed for articles matching the query.

        Args:
            query: Search query string.

        Returns:
            List of dicts with id, title, excerpt, score fields.
        """
        if not query.strip():
            return []

        # Step 1: esearch — get PMIDs
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": _MAX_RESULTS,
            "retmode": "xml",
            "usehistory": "n",
        }
        if self._api_key:
            params["api_key"] = self._api_key

        try:
            resp = httpx.get(_ESEARCH_URL, params=params, timeout=_TIMEOUT)
            pmids = self._parse_pmids(resp.text)
        except Exception as e:
            raise ResearcherError(f"PubMed esearch failed: {e}", researcher="pubmed") from e

        if not pmids:
            return []

        # Step 2: efetch — get article details
        fetch_params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        if self._api_key:
            fetch_params["api_key"] = self._api_key

        try:
            fetch_resp = httpx.get(_EFETCH_URL, params=fetch_params, timeout=_TIMEOUT)
            results = self._parse_articles(fetch_resp.text)
        except Exception as e:
            raise ResearcherError(f"PubMed efetch failed: {e}", researcher="pubmed") from e

        self._results_cache = results
        return results

    def analyze(self, query: str | None = None, **kwargs) -> dict:
        """Analyze cached PubMed results."""
        results = self._results_cache
        if not results:
            return {"summary": "No PubMed results to analyze.", "sections": {}, "raw": None}

        titles = [r["title"] for r in results[:5]]
        summary = f"Found {len(results)} PubMed articles. Top results: {', '.join(titles[:3])}."
        return {
            "summary": summary,
            "sections": {"Key Articles": "\n".join(f"- {r['title']}" for r in results[:5])},
            "raw": results,
        }

    def generate(self, type: str, **kwargs) -> str:
        """Generate content from PubMed results."""
        if not self._results_cache:
            return "No PubMed results available."
        lines = ["## PubMed Results\n"]
        for r in self._results_cache[:5]:
            lines.append(f"- **{r['title']}** — {r['excerpt']}")
            if r.get("url"):
                lines.append(f"  [Read]({r['url']})")
        return "\n".join(lines)

    def ingest(self, sources: list[str]) -> dict:
        """Ingest PubMed article URLs or PMIDs."""
        return {"source_count": len(sources), "indexed_ids": sources}

    def _parse_pmids(self, xml_text: str) -> list[str]:
        """Parse PMIDs from esearch XML response."""
        try:
            root = ET.fromstring(xml_text)
            id_list = root.find("IdList")
            if id_list is None:
                return []
            return [id_elem.text for id_elem in id_list.findall("Id") if id_elem.text]
        except ET.ParseError:
            return []

    def _parse_articles(self, xml_text: str) -> list[dict]:
        """Parse article details from efetch XML response."""
        try:
            root = ET.fromstring(xml_text)
            results = []
            for article in root.findall(".//PubmedArticle"):
                parsed = self._parse_article_element(article)
                if parsed:
                    results.append(parsed)
            return results
        except ET.ParseError:
            return []

    def _parse_article_xml(self, xml_fragment: str) -> dict | None:
        """Parse a single PubmedArticle XML fragment."""
        try:
            root = ET.fromstring(xml_fragment)
            return self._parse_article_element(root)
        except ET.ParseError:
            return None

    def _parse_article_element(self, article_elem) -> dict | None:
        """Parse a single PubmedArticle XML element."""
        try:
            medline = article_elem.find("MedlineCitation")
            if medline is None:
                return None

            pmid_elem = medline.find("PMID")
            pmid = pmid_elem.text if pmid_elem is not None else "unknown"

            article = medline.find("Article")
            if article is None:
                return None

            title_elem = article.find("ArticleTitle")
            title = title_elem.text if title_elem is not None else "Untitled"

            abstract_elem = article.find("Abstract/AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else ""

            # Authors
            authors = []
            for author in article.findall("AuthorList/Author")[:3]:
                last = author.findtext("LastName", "")
                first = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {first}".strip())

            # DOI
            doi = None
            for id_elem in article.findall("ELocationID"):
                if id_elem.get("EIdType") == "doi":
                    doi = id_elem.text

            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

            return {
                "id": f"pubmed:{pmid}",
                "title": title or "Untitled",
                "excerpt": (abstract or "")[:500],
                "score": 0.8,
                "url": url,
                "authors": authors,
                "doi": doi,
                "source": "pubmed",
            }
        except Exception:
            return None
