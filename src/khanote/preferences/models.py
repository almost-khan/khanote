"""Preferences and UsageStats Pydantic v2 models for khanote."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────

class DiscoverConfig(BaseModel):
    """Configuration for the serendipity Discover section."""

    enabled: bool = True
    serendipity: float = 0.15
    count: int = 2
    strategy_weights: dict[str, float] = {
        "adjacent": 0.4,
        "trending": 0.3,
        "random": 0.2,
        "curated": 0.1,
    }
    blocked_domains: list[str] = []
    liked_topics: list[str] = []
    disliked_topics: list[str] = []

    @field_validator("serendipity")
    @classmethod
    def serendipity_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("serendipity must be in range [0.0, 1.0]")
        return v


class TopicStat(BaseModel):
    """Per-topic usage statistics."""

    name: str
    saved: int = 0
    skipped: int = 0
    last_seen: date


class ResearcherStat(BaseModel):
    """Per-researcher usage statistics."""

    name: str
    calls: int = 0
    last_used: date


class QueryRecord(BaseModel):
    """Record of a research query."""

    text: str
    date: date
    researchers: list[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Main models
# ─────────────────────────────────────────────────────────────────────────────

class Preferences(BaseModel):
    """User's explicit preferences. Stored in preferences.yaml."""

    language: str = "en-US"
    role: Literal["developer", "pm", "researcher", "mixed"] = "mixed"
    interests: list[str] = []
    depth: Literal["headlines", "summary", "detailed", "deep_dive"] = "summary"
    expertise: Literal["beginner", "intermediate", "expert"] = "intermediate"
    tone: Literal["formal_report", "professional_briefing", "casual_notes"] = "professional_briefing"
    discover: DiscoverConfig = DiscoverConfig()

    @field_validator("language")
    @classmethod
    def valid_bcp47(cls, v: str) -> str:
        """Validate BCP 47 language tag (e.g., en-US, zh-CN, fr-FR)."""
        pattern = r"^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$"
        if not re.match(pattern, v):
            raise ValueError(
                f"'{v}' is not a valid BCP 47 language tag. Examples: en-US, zh-CN, fr-FR"
            )
        return v


class UsageStats(BaseModel):
    """Implicit signals and machine-managed statistics. Stored in usage_stats.yaml."""

    topics: list[TopicStat] = []
    researchers: list[ResearcherStat] = []
    queries: list[QueryRecord] = []
    feed_last_run: dict[str, datetime] = {}
    api_key_declined: dict[str, int] = {}

    def prune(self, cutoff_days: int = 90) -> None:
        """Remove entries older than cutoff_days. Called on each write."""
        cutoff = date.today() - timedelta(days=cutoff_days)
        self.topics = [t for t in self.topics if t.last_seen >= cutoff]
        self.researchers = [r for r in self.researchers if r.last_used >= cutoff]
        self.queries = [q for q in self.queries if q.date >= cutoff]


__all__ = [
    "Preferences",
    "DiscoverConfig",
    "UsageStats",
    "TopicStat",
    "ResearcherStat",
    "QueryRecord",
]
