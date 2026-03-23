"""Session metadata model."""
from __future__ import annotations

import re
from datetime import date
from enum import Enum

import yaml
from pydantic import BaseModel


class SessionStatus(str, Enum):
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Session(BaseModel):
    date: date
    topic: str
    researcher: str
    status: SessionStatus = SessionStatus.IN_PROGRESS
    sources_count: int = 0

    @property
    def slug(self) -> str:
        """Generate folder slug: YYYY-MM-DD_Topic-Name."""
        safe_topic = re.sub(r"[^\w\s-]", "", self.topic)
        safe_topic = re.sub(r"[\s_]+", "-", safe_topic).strip("-")
        return f"{self.date.isoformat()}_{safe_topic}"

    def to_frontmatter(self) -> str:
        """Render YAML frontmatter string (without --- delimiters)."""
        # Build manually to preserve date without quotes and field order
        lines = [
            f"date: {self.date.isoformat()}",
            f"topic: {self.topic}",
            f"researcher: {self.researcher}",
            f"status: {self.status.value}",
            f"sources_count: {self.sources_count}",
        ]
        return "\n".join(lines)

    @classmethod
    def from_frontmatter(cls, frontmatter: str) -> "Session":
        """Parse from YAML frontmatter string (without --- delimiters)."""
        data = yaml.safe_load(frontmatter)
        return cls(**data)
