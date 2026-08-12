"""Agent selector + System knowledge tests."""

from aios_core.catalog import SystemCatalog
from aios_core.knowledge_graph import KnowledgeGraph
from aios_core.orchestrator import AgentSelector, SystemKnowledge
from aios_core.workflow import WorkflowDefinition, WorkflowLibrary


def test_agent_selector_mapping():
    sel = AgentSelector()
    assert sel.select("coding") == "coder"
    assert sel.select("medical") == "doctor"
    assert sel.select("system") == "system_doctor"
    assert sel.select("chat") == "general"
    assert sel.select("skill") is None  # unknown → None
    assert sel.select("nonsense") is None


def test_agent_selector_custom():
    sel = AgentSelector(mapping={"coding": "senior-coder"})
    assert sel.select("coding") == "senior-coder"


def make_env():
    library = WorkflowLibrary()
    library.register(
        WorkflowDefinition(
            name="crud_generator",
            version="1.0.0",
            description="CRUD API generator",
            nodes=[{"id": "a", "type": "task", "name": "A"}],
        )
    )
    catalog = SystemCatalog()
    catalog.index_entry("workflow", "crud_generator", {"description": "CRUD API generator"})
    catalog.index_entry("skill", "python-skill", {"tags": ["python"]})
    graph = KnowledgeGraph()
    graph.add_node("capability", "execute_code")
    graph.add_node("agent", "coder")
    graph.add_edge("agent", "coder", "uses", "capability", "execute_code")
    return SystemKnowledge(catalog, graph, library)


def test_how_many_workflows():
    sk = make_env()
    assert sk.answer("how many workflows") == "workflows: 1"
    assert sk.answer("how many skills") == "skills: 1"
    assert sk.answer("how many agents") == "agents: 0"


def test_who_uses_capability():
    sk = make_env()
    assert sk.answer("who uses execute_code") == "agents using execute_code: coder"


def test_who_uses_unknown_capability():
    sk = make_env()
    assert sk.answer("who uses ghost_cap") is None  # GraphError caught → None


def test_workflow_keyword():
    sk = make_env()
    assert sk.answer("workflow crud") == "Workflows: crud_generator"


def test_unknown_question():
    sk = make_env()
    assert sk.answer("what is the meaning of life") is None
