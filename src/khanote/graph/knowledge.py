"""Knowledge graph: nodes, edges, JSON persistence."""
from __future__ import annotations

import json
from pathlib import Path


class KnowledgeGraph:
    """Manage a session-based knowledge graph stored as JSON."""

    def __init__(self, graph_file: Path) -> None:
        self.graph_file = Path(graph_file)
        self.nodes: dict[str, dict] = {}
        self._edges: list[dict] = []
        self._load()

    def add_node(
        self,
        session_id: str,
        topic: str,
        date_str: str,
        researcher: str,
        tags: list[str],
        status: str,
    ) -> None:
        """Add or update a session node. Duplicate prevention: no-op if already present."""
        if session_id in self.nodes:
            return
        self.nodes[session_id] = {
            "id": session_id,
            "topic": topic,
            "date": date_str,
            "researcher": researcher,
            "tags": tags,
            "status": status,
        }

    def compute_edges(self) -> list[dict]:
        """Compute edges between nodes based on shared tags.

        Returns deduplicated list of edge dicts.
        """
        node_list = list(self.nodes.values())
        edges: list[dict] = []
        seen: set[frozenset] = set()

        for i, a in enumerate(node_list):
            for b in node_list[i + 1:]:
                pair = frozenset([a["id"], b["id"]])
                if pair in seen:
                    continue
                shared_tags = list(set(a["tags"]) & set(b["tags"]))
                if shared_tags:
                    edges.append({
                        "source": a["id"],
                        "target": b["id"],
                        "relationship": "shared_topic",
                        "shared_tags": shared_tags,
                    })
                    seen.add(pair)

        return edges

    def save(self) -> None:
        """Persist the graph to JSON file."""
        self.graph_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "nodes": list(self.nodes.values()),
            "edges": self.compute_edges(),
        }
        self.graph_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        """Load graph from JSON file if it exists."""
        if not self.graph_file.exists():
            return
        try:
            data = json.loads(self.graph_file.read_text(encoding="utf-8"))
            for node in data.get("nodes", []):
                self.nodes[node["id"]] = node
            self._edges = data.get("edges", [])
        except (json.JSONDecodeError, KeyError):
            pass  # Corrupt file — start fresh
