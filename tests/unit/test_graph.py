"""Tests for knowledge graph (TDD)."""
from __future__ import annotations

import json

import pytest

from khanote.graph.knowledge import KnowledgeGraph


@pytest.fixture
def graph_file(tmp_path):
    return tmp_path / "graph_data.json"


@pytest.fixture
def graph(graph_file):
    return KnowledgeGraph(graph_file=graph_file)


class TestNodeCreation:
    def test_add_node_stores_session_data(self, graph):
        graph.add_node(
            session_id="khanote/2026-03-22_AI-Agents",
            topic="AI Agents",
            date_str="2026-03-22",
            researcher="perplexity",
            tags=["agent", "llm"],
            status="completed",
        )
        assert "khanote/2026-03-22_AI-Agents" in graph.nodes

    def test_add_node_persists_to_file(self, graph, graph_file):
        graph.add_node("khanote/2026-03-22_Test", "Test", "2026-03-22", "arxiv", [], "completed")
        graph.save()
        data = json.loads(graph_file.read_text())
        assert any(n["id"] == "khanote/2026-03-22_Test" for n in data["nodes"])

    def test_add_duplicate_node_does_not_duplicate(self, graph):
        for _ in range(3):
            graph.add_node("khanote/2026-03-22_Test", "Test", "2026-03-22", "arxiv", [], "completed")
        assert len([n for n in graph.nodes.values() if n["id"] == "khanote/2026-03-22_Test"]) == 1


class TestEdgeCreation:
    def test_shared_tags_creates_edge(self, graph):
        graph.add_node("khanote/2026-03-20_MCP", "MCP Servers", "2026-03-20", "arxiv", ["agent", "mcp"], "completed")
        graph.add_node("khanote/2026-03-22_AI", "AI Agents", "2026-03-22", "perplexity", ["agent", "llm"], "completed")
        edges = graph.compute_edges()
        assert any(
            e["relationship"] == "shared_topic" and "agent" in e["shared_tags"]
            for e in edges
        )

    def test_no_shared_tags_no_edge(self, graph):
        graph.add_node("khanote/a", "Topic A", "2026-03-20", "arxiv", ["python"], "completed")
        graph.add_node("khanote/b", "Topic B", "2026-03-22", "arxiv", ["rust"], "completed")
        edges = graph.compute_edges()
        assert len(edges) == 0

    def test_edges_not_duplicated(self, graph):
        graph.add_node("khanote/a", "A", "2026-03-20", "arxiv", ["ai"], "completed")
        graph.add_node("khanote/b", "B", "2026-03-22", "arxiv", ["ai"], "completed")
        edges1 = graph.compute_edges()
        edges2 = graph.compute_edges()
        # Same edges computed twice should not duplicate
        assert len(edges1) == len(edges2)


class TestPersistence:
    def test_load_from_file(self, graph_file):
        data = {
            "nodes": [{"id": "khanote/2026-03-22_Test", "topic": "Test", "date": "2026-03-22",
                        "researcher": "arxiv", "tags": [], "status": "completed"}],
            "edges": [],
        }
        graph_file.write_text(json.dumps(data))
        g = KnowledgeGraph(graph_file=graph_file)
        assert "khanote/2026-03-22_Test" in g.nodes

    def test_save_and_reload(self, graph, graph_file):
        graph.add_node("khanote/2026-03-22_Test", "Test", "2026-03-22", "perplexity", ["ai"], "completed")
        graph.save()
        g2 = KnowledgeGraph(graph_file=graph_file)
        assert "khanote/2026-03-22_Test" in g2.nodes
