"""Knowledge graph: component relations (agent/skill/workflow/capability/...).

NOTE: this is the RELATION GRAPH (component metadata), distinct from
``aios_core.knowledge`` (RAG chunks from TASK-007).
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .errors import GraphError

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """In-memory directed graph with reverse lookup.

    Edges are stored both ways; ``neighbors`` returns the ORIGINAL relation
    label with the other endpoint, deduplicated.
    """

    def __init__(self) -> None:
        self._nodes: dict[tuple[str, str], dict[str, Any]] = {}
        self._out: dict[tuple[str, str], list[tuple[str, str, str]]] = {}  # (sk, si) -> [(relation, tk, ti)]
        self._in: dict[tuple[str, str], list[tuple[str, str, str]]] = {}  # (tk, ti) -> [(relation, sk, si)]
        self._lock = threading.RLock()

    # -- nodes ----------------------------------------------------------------

    def add_node(self, kind: str, id: str, properties: dict[str, Any] | None = None) -> None:
        key = (kind, id)
        with self._lock:
            if key in self._nodes:
                logger.warning("Overwriting graph node %s/%s", kind, id)
            self._nodes[key] = dict(properties or {})
            self._out.setdefault(key, [])
            self._in.setdefault(key, [])

    def get_node(self, kind: str, id: str) -> dict[str, Any]:
        with self._lock:
            props = self._nodes.get((kind, id))
            if props is None:
                raise GraphError(f"Unknown graph node: {kind}/{id}")
            return dict(props)

    def delete_node(self, kind: str, id: str) -> None:
        key = (kind, id)
        with self._lock:
            if key not in self._nodes:
                raise GraphError(f"Unknown graph node: {kind}/{id}")
            # Cascade edges: drop any edge referencing this node (both directions).
            for tkey in list(self._in.keys()):
                self._in[tkey] = [e for e in self._in[tkey] if (e[1], e[2]) != key]
            for skey in list(self._out.keys()):
                self._out[skey] = [e for e in self._out[skey] if (e[1], e[2]) != key]
            del self._nodes[key]
            self._out.pop(key, None)
            self._in.pop(key, None)

    # -- edges ----------------------------------------------------------------

    def add_edge(
        self, source_kind: str, source_id: str, relation: str, target_kind: str, target_id: str
    ) -> None:
        if not relation:
            raise ValueError("relation must not be empty")
        skey, tkey = (source_kind, source_id), (target_kind, target_id)
        with self._lock:
            if skey not in self._nodes:
                raise GraphError(f"Unknown graph node: {source_kind}/{source_id}")
            if tkey not in self._nodes:
                raise GraphError(f"Unknown graph node: {target_kind}/{target_id}")
            edge = (relation, target_kind, target_id)
            if edge in self._out.get(skey, []):
                return  # idempotent skip
            self._out.setdefault(skey, []).append(edge)
            self._in.setdefault(tkey, []).append((relation, source_kind, source_id))

    # -- queries --------------------------------------------------------------

    def neighbors(
        self, kind: str, id: str, relation: str | None = None
    ) -> list[tuple[str, str]]:
        key = (kind, id)
        with self._lock:
            if key not in self._nodes:
                raise GraphError(f"Unknown graph node: {kind}/{id}")
            seen: set[tuple[str, str]] = set()
            result: list[tuple[str, str]] = []
            # Outgoing edges: entry = (relation, target_kind, target_id) → other end = target_id.
            for rel, _tk, target_id in self._out.get(key, []):
                if relation is not None and rel != relation:
                    continue
                item = (rel, target_id)
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            # Incoming edges: entry = (relation, source_kind, source_id) → other end = source_id.
            for rel, _sk, source_id in self._in.get(key, []):
                if relation is not None and rel != relation:
                    continue
                item = (rel, source_id)
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

    def find(
        self,
        kind: str | None = None,
        property_key: str | None = None,
        property_value: Any = None,
    ) -> list[tuple[str, str]]:
        with self._lock:
            results: list[tuple[str, str]] = []
            for (k, i), props in self._nodes.items():
                if kind is not None and k != kind:
                    continue
                if property_key is not None:
                    if property_key not in props:
                        continue
                    if property_value is not None and props[property_key] != property_value:
                        continue
                results.append((k, i))
            return sorted(results)
