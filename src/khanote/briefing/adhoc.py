"""Ad-hoc research orchestrator — with-argument mode of start-my-day."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from khanote.preferences.loader import PreferencesLoader
from khanote.registry.loader import RegistryLoader

# Simple query: shorter than this threshold, no complex connectors
_SIMPLE_QUERY_MAX_WORDS = 8
_COMPLEXITY_PATTERNS = [
    r"\b(and|including|also|as well as|relationship|compare|versus|vs\.?)\b",
    r"\b(latest|recent|current|new)\b.{20,}",  # long query with time qualifiers
]


def is_simple_query(query: str) -> bool:
    """Detect if a query is simple enough to skip decomposition.

    Simple queries:
    - Short (≤ _SIMPLE_QUERY_MAX_WORDS words)
    - No complex connectors or multiple dimensions

    Args:
        query: User's natural language query.

    Returns:
        True if simple (route to single researcher), False if complex (decompose).
    """
    words = query.strip().split()
    if len(words) <= _SIMPLE_QUERY_MAX_WORDS:
        return True

    for pattern in _COMPLEXITY_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False

    return len(words) <= 15


def _slugify(text: str) -> str:
    """Convert query text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50].strip("-") or "research"


class AdhocOrchestrator:
    """Orchestrate ad-hoc research queries: decompose → route → execute → synthesize."""

    def __init__(self, config_path: Path | str) -> None:
        self._config_path = Path(config_path)
        self._config_dir = self._config_path.parent
        # Cache config once to avoid repeated YAML reads per researcher load
        with self._config_path.open("r", encoding="utf-8") as f:
            self._config_data: dict = yaml.safe_load(f) or {}

    def run(
        self,
        query: str,
        researcher_overrides: dict | None = None,
    ) -> dict:
        """Execute ad-hoc research query.

        Flow:
        1. Load preferences + registry
        2. If simple query → direct execution with single researcher
        3. If complex query → broadcast to multiple available researchers
        4. Synthesize results → save report

        Args:
            query: User's natural language research query.
            researcher_overrides: Optional {name: researcher} for testing.

        Returns:
            dict with 'path' (Path) and 'content' (str markdown).
        """
        prefs_loader = PreferencesLoader(self._config_dir)
        prefs = prefs_loader.load_preferences()

        registry_loader = RegistryLoader()
        registry = registry_loader.load_with_custom(self._config_path)

        vault_path = self._load_vault_path()
        date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

        if is_simple_query(query):
            # Direct execution — use first available researcher or override
            results = self._execute_direct(query, registry, researcher_overrides)
        else:
            # Complex query — execute with available researchers
            results = self._execute_multi(query, registry, researcher_overrides)

        # Synthesize report
        content = self._generate_report(query, date_str, results, prefs)

        # Save to sessions directory
        slug = _slugify(query)
        session_dir = vault_path / "khanote" / "sessions" / f"{date_str}-{slug}"
        session_dir.mkdir(parents=True, exist_ok=True)
        output_path = session_dir / "report.md"
        output_path.write_text(content, encoding="utf-8")

        # Update query history
        researchers_used = list(researcher_overrides.keys()) if researcher_overrides else []
        prefs_loader.update_query_history(query, researchers_used)

        return {"path": output_path, "content": content}

    def _execute_direct(
        self, query: str, registry: dict, researcher_overrides: dict | None
    ) -> list[dict]:
        """Execute query directly with a single researcher."""
        overrides = researcher_overrides or {}

        # Try to find an available researcher
        for name, entry in registry.items():
            if entry.available or name in overrides:
                researcher = overrides.get(name) or self._load_researcher(name)
                if researcher is None:
                    continue
                try:
                    items = researcher.search(query)
                    return [{"researcher": name, "sub_query": query, "results": items}]
                except Exception:
                    continue

        # Fall back to overrides if no registry match
        for name, researcher in overrides.items():
            try:
                items = researcher.search(query)
                return [{"researcher": name, "sub_query": query, "results": items}]
            except Exception:
                continue

        return []

    def _execute_multi(
        self, query: str, registry: dict, researcher_overrides: dict | None
    ) -> list[dict]:
        """Broadcast query to multiple available researchers and collect results.

        Note: this does *not* decompose the query into sub-queries — the same
        query is sent to each researcher. True decomposition (split → route →
        merge) is planned but not yet implemented.
        """
        overrides = researcher_overrides or {}
        results = []

        # Use overrides for testing, otherwise try available researchers
        for name in overrides:
            researcher = overrides[name]
            try:
                items = researcher.search(query)
                results.append({"researcher": name, "sub_query": query, "results": items})
            except Exception:
                pass

        if not results:
            # Try available researchers from registry
            for name, entry in registry.items():
                if entry.available:
                    researcher = self._load_researcher(name)
                    if researcher:
                        try:
                            items = researcher.search(query)
                            results.append({"researcher": name, "sub_query": query, "results": items})
                        except Exception:
                            pass

        return results

    def _load_researcher(self, name: str):
        """Load a researcher by name from cached config."""
        try:
            from khanote.researchers import ResearcherFactory
            from khanote.models.config import ResearcherConfig

            researchers = self._config_data.get("research", {}).get("researchers", {})
            if name not in researchers:
                return None

            r_data = researchers[name]
            r_config = ResearcherConfig(**r_data)
            return ResearcherFactory.create(name, config=r_config)
        except Exception:
            return None

    def _load_vault_path(self) -> Path:
        """Load vault_path from cached config."""
        vault_path = self._config_data.get("vault_path", str(self._config_dir.parent))
        return Path(vault_path)

    def _generate_report(
        self, query: str, date_str: str, results: list[dict], prefs
    ) -> str:
        """Generate research report markdown with personalization."""
        slug = _slugify(query)
        lines = [
            f"# Research Report: {query}",
            "",
            f"**Date**: {date_str}",
            f"**slug**: {slug}",
            "",
            "## Executive Summary",
            "",
        ]

        if not results:
            lines.append("No results were retrieved for this query.")
            lines.append("")
        else:
            all_items = []
            for r in results:
                all_items.extend(r.get("results", []))

            if all_items:
                top = all_items[0]
                lines.append(
                    f"Research on '{query}' returned {len(all_items)} results across "
                    f"{len(results)} researcher(s). The most relevant finding: "
                    f"**{top.get('title', 'No title')}** — {top.get('excerpt', '')}."
                )
            lines.append("")

        # Key Findings
        lines.append("## Key Findings")
        lines.append("")
        finding_num = 1
        for r in results:
            for item in r.get("results", [])[:3]:
                title = item.get("title", "Untitled")
                excerpt = item.get("excerpt", "")
                lines.append(f"### Finding {finding_num}: {title}")
                lines.append(f"{excerpt}")
                lines.append(f"*Researcher: {r['researcher']}*")
                lines.append("")
                finding_num += 1

        # Methodology
        lines.append("## Methodology")
        lines.append("")
        lines.append("| Sub-query | Researcher | Results |")
        lines.append("|-----------|-----------|---------|")
        for r in results:
            n_results = len(r.get("results", []))
            lines.append(f"| {r['sub_query'][:40]} | {r['researcher']} | {n_results} items |")
        lines.append("")

        # References
        lines.append("## References")
        lines.append("")
        seen = set()
        for r in results:
            for item in r.get("results", []):
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
