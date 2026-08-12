"""Integration: Orchestrator M2 flow simulation (AC8)."""

from aios_core.capabilities import CapabilityRegistry
from aios_core.catalog import SystemCatalog
from aios_core.knowledge_graph import KnowledgeGraph
from aios_core.workflow import WorkflowDefinition, WorkflowLibrary


def test_orchestrator_flow_simulation():
    # 1. WorkflowLibrary (TASK-008) — real workflow
    library = WorkflowLibrary()
    library.register(
        WorkflowDefinition(
            name="crud-gen",
            version="1.0.0",
            description="CRUD API generator",
            nodes=[{"id": "a", "type": "task", "name": "A"}],
            permissions=["filesystem"],
        )
    )

    # 2. Capability registry
    caps = CapabilityRegistry()
    caps.register_capability("execute_code")
    caps.register_capability("read_file")
    caps.bind_tool("execute_code", "docker-tool")
    caps.register_agent_use("coder", "execute_code")

    # 3. Catalog + graph populated manually (M1; auto-sync is M2)
    catalog = SystemCatalog()
    catalog.index_entry("workflow", "crud-gen", {"description": "CRUD API generator"})
    catalog.index_entry("capability", "execute_code", {"tools": ["docker-tool"]})

    graph = KnowledgeGraph()
    graph.add_node("tool", "docker-tool")
    graph.add_node("capability", "execute_code")
    graph.add_node("agent", "coder")
    graph.add_node("workflow", "crud-gen")
    graph.add_edge("tool", "docker-tool", "provides", "capability", "execute_code")
    graph.add_edge("agent", "coder", "uses", "capability", "execute_code")
    graph.add_edge("workflow", "crud-gen", "requires", "capability", "execute_code")

    # 4. Queries (expected results)
    assert library.search("crud") == ["crud-gen"]
    assert [e.id for e in catalog.search("crud")] == ["crud-gen"]
    providers = graph.neighbors("capability", "execute_code", relation="provides")
    assert providers == [("provides", "docker-tool")]
    assert caps.agents_using("execute_code") == ["coder"]
    users = graph.neighbors("capability", "execute_code", relation="uses")
    assert ("uses", "coder") in users
    require = graph.neighbors("capability", "execute_code", relation="requires")
    assert ("requires", "crud-gen") in require
