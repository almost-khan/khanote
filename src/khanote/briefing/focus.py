"""Focus selector — select top items from feed results weighted by user preferences."""
from __future__ import annotations

from khanote.preferences.models import Preferences

_DEFAULT_COUNT = 5
_INTEREST_BOOST = 0.3  # Score boost for items matching user interests


class FocusSelector:
    """Select the top N focus items from all feed results, weighted by preferences."""

    def __init__(self, prefs: Preferences) -> None:
        self._prefs = prefs

    def select(self, items: list[dict], count: int = _DEFAULT_COUNT) -> list[dict]:
        """Select top N items from feed results.

        Scoring:
        - Base score from each item's 'score' field
        - Interest boost if item text matches user interests

        Args:
            items: List of search result dicts.
            count: Number of items to return (default: _DEFAULT_COUNT).

        Returns:
            Top N items sorted by weighted score descending.
        """
        if not items:
            return []

        scored = [(self._weighted_score(item), item) for item in items]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:count]]

    def _weighted_score(self, item: dict) -> float:
        """Calculate weighted score for an item."""
        base = float(item.get("score", 0.5))
        boost = 0.0

        if self._prefs.interests:
            text = (
                (item.get("title", "") + " " + item.get("excerpt", "")).lower()
            )
            for interest in self._prefs.interests:
                # Normalize interest (ai-agents → ai agents)
                normalized = interest.replace("-", " ").replace("_", " ").lower()
                if normalized in text:
                    boost = _INTEREST_BOOST
                    break

        return base + boost
