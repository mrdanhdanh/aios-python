"""Knowledge graph: component relation graph (NOT the RAG knowledge store)."""

from .errors import GraphError
from .graph import KnowledgeGraph

__all__ = ["GraphError", "KnowledgeGraph"]
