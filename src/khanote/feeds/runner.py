"""Feed runner — execute a feed: search → analyze via researcher → return results."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from khanote.feeds.manager import FeedManager
from khanote.models.feed import Feed


class FeedRunner:
    """Run one or all feeds by loading their researcher and executing search + analyze."""

    def __init__(self, config_path: Path | str) -> None:
        self._config_path = Path(config_path)
        self._manager = FeedManager(config_path)
        # Cache config once to avoid repeated YAML reads
        with self._config_path.open("r", encoding="utf-8") as f:
            self._config_data: dict = yaml.safe_load(f) or {}

    def run_feed(
        self,
        feed_name: str,
        researcher_override=None,
    ) -> dict | None:
        """Run a single feed.

        Args:
            feed_name: Name of the feed to run.
            researcher_override: Optional researcher instance (for testing).

        Returns:
            {"feed_name": str, "results": list[dict], "analysis": dict}
            or None if feed is inactive.
        """
        feed = self._manager.get_feed(feed_name)

        if not feed.active:
            return {"feed_name": feed_name, "skipped": True, "reason": "feed is paused"}

        researcher = researcher_override or self._load_researcher(feed)
        if researcher is None:
            return {
                "feed_name": feed_name,
                "skipped": True,
                "reason": f"researcher '{feed.researcher}' unavailable",
            }

        # Step 1: Search
        results: list[dict] = []
        try:
            raw_results = researcher.search(feed.query)
            results = self._apply_filters(raw_results, feed)
        except Exception as e:
            return {
                "feed_name": feed_name,
                "results": [],
                "analysis": {},
                "error": f"search failed: {e}",
            }

        if not results:
            return {
                "feed_name": feed_name,
                "results": [],
                "analysis": {},
                "error": "no results",
            }

        # Step 2: Analyze
        analysis: dict = {}
        try:
            results_text = "\n".join(
                f"- {r.get('title', '')}: {r.get('excerpt', '')}" for r in results
            )
            analysis = researcher.analyze(
                query=feed.query,
                results=results_text,
            )
        except Exception as e:
            # Preserve partial results on analysis failure
            return {
                "feed_name": feed_name,
                "results": results,
                "analysis": {},
                "error": f"analysis failed (partial results preserved): {e}",
            }

        return {
            "feed_name": feed_name,
            "results": results,
            "analysis": analysis,
        }

    def run_all_feeds(self, researcher_overrides: dict | None = None) -> list[dict]:
        """Run all active feeds concurrently.

        Uses a thread pool to parallelize network-bound feed execution.
        """
        feeds = self._manager.list_feeds()
        overrides = researcher_overrides or {}
        feed_names = list(feeds.keys())

        if not feed_names:
            return []

        results: list[dict] = []
        max_workers = min(len(feed_names), 8)
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(self.run_feed, name, overrides.get(name)): name
                for name in feed_names
            }
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)
        return results

    def _load_researcher(self, feed: Feed):
        """Load the researcher bound to this feed from cached config."""
        from khanote.researchers import ResearcherFactory
        from khanote.models.config import ResearcherConfig

        researchers = self._config_data.get("research", {}).get("researchers", {})
        if feed.researcher not in researchers:
            return None

        r_data = researchers[feed.researcher]
        if not r_data.get("enabled", True):
            return None

        try:
            r_config = ResearcherConfig(**r_data)
            return ResearcherFactory.create(feed.researcher, config=r_config)
        except Exception:
            return None

    def _apply_filters(self, results: list[dict], feed: Feed) -> list[dict]:
        """Apply keyword filters to search results.

        Returns only matching results. If no keywords match, returns an empty
        list with a ``filter_bypassed`` marker rather than silently returning
        all unfiltered results.
        """
        if not feed.keywords:
            return results
        filtered = []
        for r in results:
            text = (r.get("title", "") + " " + r.get("excerpt", "")).lower()
            if any(kw.lower() in text for kw in feed.keywords):
                filtered.append(r)
        return filtered
