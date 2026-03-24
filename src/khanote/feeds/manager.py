"""Feed manager — add, list, pause, resume, remove, clone feeds in config.yaml."""
from __future__ import annotations

from pathlib import Path

import yaml

from khanote.models.feed import Feed


class FeedValidationError(Exception):
    """Raised when feed validation fails."""


class FeedManager:
    """CRUD operations on the `feeds` section of config.yaml."""

    def __init__(self, config_path: Path | str) -> None:
        self._path = Path(config_path)

    # ── Read ───────────────────────────────────────────────────────────────────

    def list_feeds(self) -> dict[str, Feed]:
        """Return all configured feeds as {name: Feed}."""
        data = self._read()
        feeds_data = data.get("feeds") or {}
        return {
            name: Feed(name=name, **feed_data)
            for name, feed_data in feeds_data.items()
        }

    def get_feed(self, name: str) -> Feed:
        feeds = self.list_feeds()
        if name not in feeds:
            raise KeyError(f"Feed '{name}' not found")
        return feeds[name]

    # ── Write ──────────────────────────────────────────────────────────────────

    def add_feed(
        self,
        name: str,
        researcher: str,
        query: str,
        keywords: list[str] | None = None,
        max_age_days: int | None = None,
        frequency: str = "daily",
        active: bool = True,
    ) -> Feed:
        """Add a feed to config.yaml.

        Raises FeedValidationError if:
        - name already exists
        - researcher is not in the config
        """
        data = self._read()
        self._validate_name_unique(name, data)
        self._validate_researcher_exists(researcher, data)

        # Validate feed model (raises ValidationError if invalid)
        feed = Feed(
            name=name,
            researcher=researcher,
            query=query,
            keywords=keywords or [],
            max_age_days=max_age_days,
            frequency=frequency,  # type: ignore[arg-type]
            active=active,
        )

        feeds = data.setdefault("feeds", {})
        feeds[name] = self._feed_to_dict(feed)
        self._write(data)
        return feed

    def pause_feed(self, name: str) -> None:
        """Set feed active=False."""
        self._update_feed_field(name, "active", False)

    def resume_feed(self, name: str) -> None:
        """Set feed active=True."""
        self._update_feed_field(name, "active", True)

    def remove_feed(self, name: str) -> None:
        """Delete feed entry from config.yaml."""
        data = self._read()
        feeds = data.get("feeds") or {}
        if name not in feeds:
            raise KeyError(f"Feed '{name}' not found")
        del feeds[name]
        if not feeds:
            data.pop("feeds", None)
        self._write(data)

    def clone_feed(self, source_name: str, new_name: str) -> Feed:
        """Clone an existing feed under a new name."""
        data = self._read()
        feeds = data.get("feeds") or {}
        if source_name not in feeds:
            raise KeyError(f"Source feed '{source_name}' not found")
        self._validate_name_unique(new_name, data)
        clone = dict(feeds[source_name])
        feeds[new_name] = clone
        self._write(data)
        return Feed(name=new_name, **clone)

    # ── Orphan detection ───────────────────────────────────────────────────────

    def detect_orphans(self) -> list[str]:
        """Return names of feeds whose researcher no longer exists or is disabled."""
        data = self._read()
        researchers = data.get("research", {}).get("researchers", {})
        available = [
            name for name, r in researchers.items()
            if r.get("enabled", True)
        ]
        feeds = data.get("feeds") or {}
        return [
            name for name, feed in feeds.items()
            if feed.get("researcher") not in available
        ]

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _read(self) -> dict:
        with self._path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write(self, data: dict) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def _update_feed_field(self, name: str, field: str, value) -> None:
        data = self._read()
        feeds = data.get("feeds") or {}
        if name not in feeds:
            raise KeyError(f"Feed '{name}' not found")
        feeds[name][field] = value
        self._write(data)

    def _validate_name_unique(self, name: str, data: dict) -> None:
        feeds = data.get("feeds") or {}
        if name in feeds:
            raise FeedValidationError(f"Feed '{name}' already exists")

    def _validate_researcher_exists(self, researcher: str, data: dict) -> None:
        researchers = data.get("research", {}).get("researchers", {})
        if researcher not in researchers:
            raise FeedValidationError(
                f"Researcher '{researcher}' not found in config. "
                f"Add it first with /khanote.researcher.add"
            )
        if not researchers[researcher].get("enabled", True):
            raise FeedValidationError(
                f"Researcher '{researcher}' is disabled"
            )

    @staticmethod
    def _feed_to_dict(feed: Feed) -> dict:
        d: dict = {
            "researcher": feed.researcher,
            "query": feed.query,
            "frequency": feed.frequency,
            "active": feed.active,
        }
        if feed.keywords:
            d["keywords"] = feed.keywords
        if feed.max_age_days is not None:
            d["max_age_days"] = feed.max_age_days
        return d
