"""System knowledge: rule-based answers from catalog/graph/library (no LLM)."""

from __future__ import annotations

import re

from ..catalog import CatalogError, SystemCatalog
from ..knowledge_graph import GraphError, KnowledgeGraph
from ..workflow.library import WorkflowLibrary

PLURAL_TO_KIND = {
    "workflows": "workflow",
    "skills": "skill",
    "agents": "agent",
    "tools": "tool",
}


class SystemKnowledge:
    """Answer metadata questions via the system catalog/graph/library."""

    def __init__(
        self,
        catalog: SystemCatalog,
        graph: KnowledgeGraph,
        library: WorkflowLibrary,
    ) -> None:
        self._catalog = catalog
        self._graph = graph
        self._library = library

    def answer(self, question: str) -> str | None:
        lowered = question.lower().strip()

        how_many = re.search(r"how many (\w+)", lowered)
        if how_many:
            kind = PLURAL_TO_KIND.get(how_many.group(1))
            if kind is None:
                return None
            try:
                count = len(self._catalog.search("", kind=kind))
            except CatalogError:
                return None
            return f"{kind}s: {count}"

        who_uses = re.search(r"who uses (\w+)", lowered)
        if who_uses:
            capability = who_uses.group(1)
            try:
                neighbors = self._graph.neighbors("capability", capability)
            except GraphError:
                return None
            users = sorted({node_id for rel, node_id in neighbors if rel == "uses"})
            if not users:
                return "no agents use this capability"
            return f"agents using {capability}: {', '.join(users)}"

        workflow_query = re.search(r"workflow (\w+)", lowered)
        if workflow_query:
            names = self._library.search(workflow_query.group(1))
            if not names:
                return None
            return "Workflows: " + ", ".join(names)

        return None
