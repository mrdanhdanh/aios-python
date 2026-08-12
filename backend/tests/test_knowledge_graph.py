"""Knowledge graph tests."""

import pytest

from aios_core.knowledge_graph import GraphError, KnowledgeGraph


@pytest.fixture
def graph():
    g = KnowledgeGraph()
    g.add_node("tool", "docker-tool", {"name": "docker"})
    g.add_node("capability", "execute_code", {"version": "1.0"})
    g.add_node("agent", "coder", {"role": "coding"})
    g.add_edge("tool", "docker-tool", "provides", "capability", "execute_code")
    g.add_edge("agent", "coder", "uses", "capability", "execute_code")
    return g


def test_add_node_overwrite_warning(graph):
    graph.add_node("tool", "docker-tool", {"name": "docker2"})
    assert graph.get_node("tool", "docker-tool")["name"] == "docker2"


def test_get_node_unknown(graph):
    with pytest.raises(GraphError, match="Unknown graph node"):
        graph.get_node("agent", "ghost")


def test_add_edge_missing_node(graph):
    with pytest.raises(GraphError, match="Unknown graph node"):
        graph.add_edge("agent", "ghost", "uses", "capability", "execute_code")


def test_add_edge_empty_relation(graph):
    with pytest.raises(ValueError, match="relation"):
        graph.add_edge("agent", "coder", "", "capability", "execute_code")


def test_add_edge_idempotent(graph):
    graph.add_edge("agent", "coder", "uses", "capability", "execute_code")  # duplicate
    assert len(graph.neighbors("agent", "coder")) == 1


def test_neighbors_bidirectional_original_relation(graph):
    neighbors = graph.neighbors("capability", "execute_code")
    assert ("provides", "docker-tool") in neighbors
    assert ("uses", "coder") in neighbors
    assert len(neighbors) == 2  # dedup


def test_neighbors_relation_filter(graph):
    assert graph.neighbors("capability", "execute_code", relation="uses") == [("uses", "coder")]


def test_neighbors_unknown(graph):
    with pytest.raises(GraphError):
        graph.neighbors("agent", "ghost")


def test_find_property(graph):
    assert graph.find(kind="tool") == [("tool", "docker-tool")]
    assert graph.find(property_key="version", property_value="1.0") == [("capability", "execute_code")]
    # value=None → any node having the key
    assert graph.find(property_key="version") == [("capability", "execute_code")]
    # typed comparison: "1.0" (str) != 1.0 (float)
    assert graph.find(property_key="version", property_value=1.0) == []


def test_delete_node_cascade(graph):
    graph.delete_node("capability", "execute_code")
    with pytest.raises(GraphError):
        graph.get_node("capability", "execute_code")
    assert graph.neighbors("agent", "coder") == []
    assert graph.neighbors("tool", "docker-tool") == []


def test_self_loop_allowed(graph):
    graph.add_edge("agent", "coder", "mentors", "agent", "coder")
    assert ("mentors", "coder") in graph.neighbors("agent", "coder")
