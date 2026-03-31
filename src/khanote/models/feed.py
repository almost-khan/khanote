"""Pydantic model for Feed — data pipeline binding a query to a researcher."""
from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, field_validator


class FeedStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ORPHANED = "orphaned"


class Feed(BaseModel):
    name: str
    researcher: str
    query: str
    keywords: list[str] = []
    source: str | None = None  # directory or file path for local researcher
    max_age_days: int | None = None
    frequency: Literal["daily"] = "daily"
    active: bool = True

    @field_validator("name")
    @classmethod
    def name_must_be_valid_key(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("feed name must not be empty")
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\-]*$", v):
            raise ValueError(
                "feed name must be alphanumeric with hyphens only (e.g., 'llm-papers')"
            )
        return v

    @field_validator("query")
    @classmethod
    def query_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("feed query must not be empty")
        return v

    def check_orphan(self, available_researchers: list[str]) -> FeedStatus:
        """Determine the feed's status given available researcher names."""
        if self.researcher not in available_researchers:
            return FeedStatus.ORPHANED
        if not self.active:
            return FeedStatus.PAUSED
        return FeedStatus.ACTIVE
