"""Dependency resolution for upgrade pipeline (TASK-020).

Deterministic DFS post-order: dependencies always precede their dependents;
children are visited in (name, version) order so the same input always
produces the same output (INV-010).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Dependency:
    name: str      # component_id
    version: str   # pinned version (deterministic — no ranges)


@dataclass(frozen=True)
class ComponentSpec:
    kind: str            # skill | workflow | prompt | capability | contract
    component_id: str
    version: str         # CURRENT version of the component
    dependencies: tuple[Dependency, ...] = ()


@dataclass(frozen=True)
class Resolution:
    ok: bool
    ordered: tuple[ComponentSpec, ...]  # topo order: dependencies first
    reason: str | None = None


# lookup(kind, component_id) -> ComponentSpec | None (DI from wiring/tests)
Lookup = Callable[[str, str], ComponentSpec | None]


class DependencyResolver:
    """Resolves the dependency closure of a root component."""

    def __init__(self, lookup: Lookup) -> None:
        self._lookup = lookup

    def resolve(self, root: ComponentSpec) -> Resolution:
        ordered: list[ComponentSpec] = []
        gray: set[str] = set()   # on the current DFS path → cycle
        black: set[str] = set()  # fully resolved

        def visit(spec: ComponentSpec, path: list[str]) -> str | None:
            key = f"{spec.kind}:{spec.component_id}"
            if key in gray:
                cycle = " -> ".join([*path, spec.component_id])
                return f"dependency cycle detected: {cycle}"
            if key in black:
                return None
            gray.add(key)
            for dep in sorted(spec.dependencies, key=lambda d: (d.name, d.version)):
                child = self._lookup(spec.kind, dep.name)
                if child is None:
                    return f"missing dependency: {dep.name} (required by {spec.component_id})"
                if child.version != dep.version:
                    return (
                        f"dependency conflict: {dep.name} pinned at {dep.version} "
                        f"but installed version is {child.version}"
                    )
                err = visit(child, [*path, spec.component_id])
                if err:
                    return err
            gray.discard(key)
            black.add(key)
            ordered.append(spec)
            return None

        err = visit(root, [])
        if err:
            return Resolution(ok=False, ordered=(), reason=err)
        return Resolution(ok=True, ordered=tuple(ordered))
