"""Daily briefing orchestrator — no-argument mode of start-my-day."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from khanote.briefing.dedup import deduplicate
from khanote.briefing.focus import FocusSelector
from khanote.feeds.runner import FeedRunner
from khanote.preferences.loader import PreferencesLoader
from khanote.preferences.models import Preferences, UsageStats

# Frequency → timedelta mapping
_FREQUENCY_INTERVALS: dict[str, timedelta] = {
    "daily": timedelta(hours=24),
    "weekly": timedelta(days=7),
    "hourly": timedelta(hours=1),
}


def build_discover_context(prefs: Preferences, stats: UsageStats) -> dict:
    """Build the discover context dict from preferences and usage stats.

    This is passed to the discover SOP template as template variables.

    Args:
        prefs: User preferences including discover settings and interests.
        stats: Usage stats with recent topics.

    Returns:
        dict with keys: domain_name, interests, recent_topics, blocked_domains,
                        liked_topics, disliked_topics, strategy_weights.
    """
    recent_topics = [t.name for t in sorted(stats.topics, key=lambda t: t.last_seen, reverse=True)[:10]]

    return {
        "domain_name": ", ".join(prefs.interests) if prefs.interests else "general",
        "interests": prefs.interests,
        "recent_topics": recent_topics,
        "blocked_domains": prefs.discover.blocked_domains,
        "liked_topics": prefs.discover.liked_topics,
        "disliked_topics": prefs.discover.disliked_topics,
        "strategy_weights": prefs.discover.strategy_weights,
    }


def is_feed_due(feed_name: str, frequency: str, stats: UsageStats) -> bool:
    """Determine if a feed should run based on its last execution time.

    Args:
        feed_name: Name of the feed.
        frequency: Feed frequency string (daily, weekly, etc.).
        stats: Current usage stats with feed_last_run timestamps.

    Returns:
        True if the feed is due to run (never run, or interval elapsed).
    """
    last_run = stats.feed_last_run.get(feed_name)
    if last_run is None:
        return True

    interval = _FREQUENCY_INTERVALS.get(frequency)
    if interval is None:
        return True  # Unknown frequency — always run

    # Ensure last_run is timezone-aware
    if last_run.tzinfo is None:
        last_run = last_run.replace(tzinfo=timezone.utc)

    elapsed = datetime.now(tz=timezone.utc) - last_run
    return elapsed >= interval


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:60].strip("-") or "briefing"


class DailyBriefingOrchestrator:
    """Orchestrate the daily briefing: load feeds → execute → deduplicate → generate file."""

    def __init__(self, config_path: Path | str) -> None:
        self._config_path = Path(config_path)
        self._config_dir = self._config_path.parent

    def run(self, researcher_overrides: dict | None = None) -> dict:
        """Execute the daily briefing flow.

        Args:
            researcher_overrides: Optional {feed_name: researcher} for testing.

        Returns:
            dict with 'path' (Path to output file) and 'content' (str markdown).
        """
        # Load preferences and stats
        prefs_loader = PreferencesLoader(self._config_dir)
        prefs = prefs_loader.load_preferences()
        stats = prefs_loader.load_usage_stats()

        # Load vault path from config
        vault_path = self._load_vault_path()

        # Execute all feeds
        runner = FeedRunner(self._config_path)
        all_results = runner.run_all_feeds(researcher_overrides=researcher_overrides)

        # Collect all results
        all_items: list[dict] = []
        feed_sections: dict[str, list[dict]] = {}
        errors: list[str] = []

        for feed_result in all_results:
            feed_name = feed_result.get("feed_name", "unknown")
            if feed_result.get("skipped"):
                continue
            if feed_result.get("error") and not feed_result.get("results"):
                errors.append(f"{feed_name}: {feed_result['error']}")
                continue

            results = feed_result.get("results", [])
            # Tag results with source feed
            tagged = [{**r, "source": feed_name} for r in results]
            all_items.extend(tagged)
            feed_sections[feed_name] = tagged

        # Deduplicate across feeds
        deduped = deduplicate(all_items)

        # Select focus items
        selector = FocusSelector(prefs)
        focus_items = selector.select(deduped, count=5)

        # Generate briefing content
        date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        content = self._generate_briefing(date_str, focus_items, feed_sections, errors, prefs, stats)

        # Extract slug from content
        slug = self._extract_slug(content) or "daily-briefing"
        filename = f"{date_str}-{slug}.md"

        # Save to vault
        briefings_dir = vault_path / "khanote" / "briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)
        output_path = briefings_dir / filename
        output_path.write_text(content, encoding="utf-8")

        # Update usage stats
        for feed_result in all_results:
            feed_name = feed_result.get("feed_name")
            if feed_name and not feed_result.get("skipped"):
                prefs_loader.update_feed_last_run(feed_name)

        # Show API key hints for missing researchers
        self._show_registry_hints()

        return {"path": output_path, "content": content}

    def _show_registry_hints(self) -> None:
        """Show hints for researchers that are unavailable due to missing keys."""
        try:
            from khanote.registry.loader import RegistryLoader
            loader = RegistryLoader()
            entries = loader.load()
            for name, entry in entries.items():
                # Hints available for CLI output — stored, not printed here
                loader.get_hint_message(name, entry)
        except Exception:
            pass

    def _load_vault_path(self) -> Path:
        """Load vault_path from config.yaml."""
        with self._config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        vault_path = data.get("vault_path", str(self._config_dir.parent))
        return Path(vault_path)

    def _generate_briefing(
        self,
        date_str: str,
        focus_items: list[dict],
        feed_sections: dict[str, list[dict]],
        errors: list[str],
        prefs: Preferences,
        stats: UsageStats | None = None,
    ) -> str:
        """Generate the briefing markdown content."""
        # Build discover context for Discover section
        build_discover_context(prefs, stats or UsageStats())
        show_discover = (
            prefs.discover.enabled
            and prefs.discover.serendipity > 0.0
        )

        lines = [
            f"# Daily Briefing: {date_str}",
            "",
            f"**slug**: daily-briefing-{date_str}",
            "",
        ]

        # Top Story
        if focus_items:
            top = focus_items[0]
            lines += [
                "## Top Story",
                f"**{top.get('title', 'No title')}** — {top.get('excerpt', '')}",
                f"*Source: {top.get('source', 'unknown')}*",
                "",
            ]

        # Your Focus
        if focus_items:
            lines.append("## Your Focus")
            for item in focus_items:
                title = item.get("title", "Untitled")
                excerpt = item.get("excerpt", "")
                source = item.get("source", "unknown")
                lines.append(f"- **{title}** — {excerpt} *(via {source})*")
            lines.append("")

        # Your Feeds
        if feed_sections:
            lines.append("## Your Feeds")
            for feed_name, items in feed_sections.items():
                lines.append(f"\n### {feed_name}")
                for item in items[:4]:
                    title = item.get("title", "Untitled")
                    excerpt = item.get("excerpt", "")
                    lines.append(f"- **{title}** — {excerpt}")
            lines.append("")

        # Discover section
        if show_discover and (feed_sections or focus_items):
            interests_str = ", ".join(prefs.interests) if prefs.interests else "general topics"
            lines += [
                "## Discover",
                f"*Expanding beyond {interests_str}:*",
                "",
                "> Use `khanote discover like <topic>` or `khanote discover dislike <topic>` to tune future recommendations.",
                "",
            ]

        # Errors section
        if errors:
            lines.append("## Feed Errors")
            for err in errors:
                lines.append(f"- {err}")
            lines.append("")

        # Sources
        all_items = [item for items in feed_sections.values() for item in items]
        if all_items:
            lines.append("## Sources")
            seen: set = set()
            for item in all_items:
                url = item.get("url") or item.get("id", "")
                title = item.get("title", "Unknown")
                if url not in seen:
                    seen.add(url)
                    if url:
                        lines.append(f"- [{title}]({url})")
                    else:
                        lines.append(f"- {title}")
            lines.append("")

        return "\n".join(lines)

    def _extract_slug(self, content: str) -> str:
        """Extract slug from briefing content."""
        for line in content.split("\n"):
            if line.startswith("**slug**:"):
                slug_part = line.split(":", 1)[1].strip()
                return _slugify(slug_part)
        return "daily-briefing"
