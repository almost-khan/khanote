"""Preferences loader — read/write preferences.yaml and usage_stats.yaml."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from khanote.preferences.models import (
    Preferences,
    QueryRecord,
    ResearcherStat,
    TopicStat,
    UsageStats,
)

# Path to built-in data directory
_DATA_DIR = Path(__file__).parent.parent / "data"
_STARTER_FEEDS_YAML = _DATA_DIR / "starter_feeds.yaml"


class PreferencesLoader:
    """Read/write preferences.yaml and usage_stats.yaml from the khanote config directory."""

    def __init__(self, config_dir: Path | str) -> None:
        self._dir = Path(config_dir)

    @property
    def _preferences_path(self) -> Path:
        return self._dir / "preferences.yaml"

    @property
    def _usage_stats_path(self) -> Path:
        return self._dir / "usage_stats.yaml"

    # ── Preferences ────────────────────────────────────────────────────────────

    def load_preferences(self) -> Preferences:
        """Load preferences.yaml, create with defaults if missing."""
        if not self._preferences_path.exists():
            return Preferences()
        with self._preferences_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return _prefs_from_dict(data)

    def save_preferences(self, prefs: Preferences) -> None:
        """Write preferences to preferences.yaml."""
        self._dir.mkdir(parents=True, exist_ok=True)
        data = _prefs_to_dict(prefs)
        with self._preferences_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    # ── Usage Stats ────────────────────────────────────────────────────────────

    def load_usage_stats(self) -> UsageStats:
        """Load usage_stats.yaml, create with defaults if missing."""
        if not self._usage_stats_path.exists():
            return UsageStats()
        with self._usage_stats_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return _stats_from_dict(data)

    def save_usage_stats(self, stats: UsageStats) -> None:
        """Write usage stats to usage_stats.yaml. Prunes old entries first."""
        stats.prune()
        self._dir.mkdir(parents=True, exist_ok=True)
        data = _stats_to_dict(stats)
        with self._usage_stats_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    # ── Usage Stat Updates ─────────────────────────────────────────────────────

    def update_topic_stats(self, topic: str, saved: bool = True) -> None:
        """Update topic statistics after briefing/report generation."""
        stats = self.load_usage_stats()
        existing = next((t for t in stats.topics if t.name == topic), None)
        if existing is None:
            existing = TopicStat(name=topic, saved=0, skipped=0, last_seen=date.today())
            stats.topics.append(existing)
        if saved:
            existing.saved += 1
        else:
            existing.skipped += 1
        existing.last_seen = date.today()
        self.save_usage_stats(stats)

    def update_researcher_usage(self, researcher_name: str) -> None:
        """Track researcher usage after each run."""
        stats = self.load_usage_stats()
        existing = next((r for r in stats.researchers if r.name == researcher_name), None)
        if existing is None:
            existing = ResearcherStat(name=researcher_name, calls=0, last_used=date.today())
            stats.researchers.append(existing)
        existing.calls += 1
        existing.last_used = date.today()
        self.save_usage_stats(stats)

    def update_query_history(self, text: str, researchers: list[str]) -> None:
        """Add a query record to history."""
        stats = self.load_usage_stats()
        stats.queries.append(QueryRecord(text=text, date=date.today(), researchers=researchers))
        self.save_usage_stats(stats)

    def update_feed_last_run(self, feed_name: str) -> None:
        """Record the last execution time for a feed."""
        stats = self.load_usage_stats()
        stats.feed_last_run[feed_name] = datetime.now(tz=timezone.utc)
        self.save_usage_stats(stats)

    def increment_api_key_declined(self, researcher_name: str) -> None:
        """Increment the count of times user declined to provide a key."""
        stats = self.load_usage_stats()
        stats.api_key_declined[researcher_name] = (
            stats.api_key_declined.get(researcher_name, 0) + 1
        )
        self.save_usage_stats(stats)

    # ── Starter Feeds ──────────────────────────────────────────────────────────

    def _load_starter_feeds_yaml(self) -> dict:
        """Load the built-in starter_feeds.yaml."""
        if not _STARTER_FEEDS_YAML.exists():
            return {}
        with _STARTER_FEEDS_YAML.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def select_starter_feeds(self, role: str, interests: list[str]) -> list[dict]:
        """Select starter feed definitions for a given role + interests list.

        Falls back to 'general' interest if specific interest not found.
        """
        all_feeds = self._load_starter_feeds_yaml()
        role_feeds = all_feeds.get(role, all_feeds.get("mixed", {}))

        selected: list[dict] = []
        seen_names: set[str] = set()

        for interest in interests:
            interest_feeds = role_feeds.get(interest) or role_feeds.get("general", [])
            for feed in interest_feeds:
                if feed["name"] not in seen_names:
                    seen_names.add(feed["name"])
                    selected.append(dict(feed))

        # If no feeds found (unknown interests), fall back to general
        if not selected:
            for feed in role_feeds.get("general", []):
                if feed["name"] not in seen_names:
                    seen_names.add(feed["name"])
                    selected.append(dict(feed))

        return selected

    def write_starter_feeds_to_config(
        self, config_path: Path | str, feeds: list[dict]
    ) -> None:
        """Write selected starter feeds into an existing config.yaml."""
        config_path = Path(config_path)
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        existing_feeds = data.setdefault("feeds", {})

        for feed in feeds:
            name = feed["name"]
            if name not in existing_feeds:
                feed_entry: dict[str, Any] = {
                    "researcher": feed["researcher"],
                    "query": feed.get("query", ""),
                    "frequency": feed.get("frequency", "daily"),
                    "active": True,
                }
                if feed.get("keywords"):
                    feed_entry["filters"] = {"keywords": feed["keywords"]}
                existing_feeds[name] = feed_entry

        # Ensure the researchers from feeds exist in config (add as disabled stubs)
        researchers = data.setdefault("research", {}).setdefault("researchers", {})
        for feed in feeds:
            r_name = feed["researcher"]
            if r_name not in researchers:
                researchers[r_name] = {"enabled": True}

        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# ─────────────────────────────────────────────────────────────────────────────
# Serialization helpers
# ─────────────────────────────────────────────────────────────────────────────

def _prefs_to_dict(prefs: Preferences) -> dict:
    """Convert Preferences to a YAML-serializable dict."""
    d = prefs.model_dump(mode="json")
    return d


def _prefs_from_dict(data: dict) -> Preferences:
    """Parse Preferences from a dict loaded from YAML."""
    return Preferences(**data)


def _stats_to_dict(stats: UsageStats) -> dict:
    """Convert UsageStats to a YAML-serializable dict."""
    d: dict = {}

    if stats.topics:
        d["topics"] = [
            {"name": t.name, "saved": t.saved, "skipped": t.skipped, "last_seen": str(t.last_seen)}
            for t in stats.topics
        ]

    if stats.researchers:
        d["researchers"] = [
            {"name": r.name, "calls": r.calls, "last_used": str(r.last_used)}
            for r in stats.researchers
        ]

    if stats.queries:
        d["queries"] = [
            {"text": q.text, "date": str(q.date), "researchers": q.researchers}
            for q in stats.queries
        ]

    if stats.feed_last_run:
        d["feed_last_run"] = {
            name: dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
            for name, dt in stats.feed_last_run.items()
        }

    if stats.api_key_declined:
        d["api_key_declined"] = dict(stats.api_key_declined)

    return d


def _stats_from_dict(data: dict) -> UsageStats:
    """Parse UsageStats from a dict loaded from YAML."""
    from datetime import date as date_type

    topics = []
    for t in data.get("topics", []):
        last_seen = t.get("last_seen")
        if isinstance(last_seen, str):
            last_seen = date_type.fromisoformat(last_seen)
        elif isinstance(last_seen, date_type):
            pass
        else:
            last_seen = date_type.today()
        topics.append(TopicStat(
            name=t["name"],
            saved=t.get("saved", 0),
            skipped=t.get("skipped", 0),
            last_seen=last_seen,
        ))

    researchers = []
    for r in data.get("researchers", []):
        last_used = r.get("last_used")
        if isinstance(last_used, str):
            last_used = date_type.fromisoformat(last_used)
        elif isinstance(last_used, date_type):
            pass
        else:
            last_used = date_type.today()
        researchers.append(ResearcherStat(
            name=r["name"],
            calls=r.get("calls", 0),
            last_used=last_used,
        ))

    queries = []
    for q in data.get("queries", []):
        q_date = q.get("date")
        if isinstance(q_date, str):
            q_date = date_type.fromisoformat(q_date)
        elif isinstance(q_date, date_type):
            pass
        else:
            q_date = date_type.today()
        queries.append(QueryRecord(
            text=q["text"],
            date=q_date,
            researchers=q.get("researchers", []),
        ))

    feed_last_run = {}
    for name, ts in data.get("feed_last_run", {}).items():
        if isinstance(ts, str):
            try:
                feed_last_run[name] = datetime.fromisoformat(ts)
            except ValueError:
                feed_last_run[name] = datetime.now(tz=timezone.utc)
        elif isinstance(ts, datetime):
            feed_last_run[name] = ts
        else:
            feed_last_run[name] = datetime.now(tz=timezone.utc)

    return UsageStats(
        topics=topics,
        researchers=researchers,
        queries=queries,
        feed_last_run=feed_last_run,
        api_key_declined=data.get("api_key_declined", {}),
    )
