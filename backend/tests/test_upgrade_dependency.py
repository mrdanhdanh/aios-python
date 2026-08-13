"""DependencyResolver tests (TASK-020)."""

import pytest

from aios_core.upgrade.dependency import ComponentSpec, Dependency, DependencyResolver


def make_registry(specs: list[ComponentSpec]):
    return {f"{s.kind}:{s.component_id}": s for s in specs}


def resolver_for(specs: list[ComponentSpec]) -> DependencyResolver:
    reg = make_registry(specs)

    def lookup(kind: str, component_id: str):
        return reg.get(f"{kind}:{component_id}")

    return DependencyResolver(lookup)


def test_topo_order_dependencies_first():
    """Root depends on B which depends on A → ordered [A, B, root]."""
    a = ComponentSpec("skill", "a", "1.0.0")
    b = ComponentSpec("skill", "b", "1.0.0", (Dependency("a", "1.0.0"),))
    root = ComponentSpec("skill", "root", "1.0.0", (Dependency("b", "1.0.0"),))
    res = resolver_for([a, b, root]).resolve(root)
    assert res.ok
    assert [s.component_id for s in res.ordered] == ["a", "b", "root"]


def test_topo_order_stable_sort():
    """Sibling dependencies visited in (name, version) order — deterministic."""
    a1 = ComponentSpec("skill", "a", "1.0.0")
    z = ComponentSpec("skill", "z", "1.0.0")
    root = ComponentSpec(
        "skill", "root", "1.0.0",
        (Dependency("z", "1.0.0"), Dependency("a", "1.0.0")),
    )
    res = resolver_for([a1, z, root]).resolve(root)
    assert [s.component_id for s in res.ordered] == ["a", "z", "root"]


def test_deterministic_same_input_same_output():
    a = ComponentSpec("skill", "a", "1.0.0")
    b = ComponentSpec("skill", "b", "1.0.0", (Dependency("a", "1.0.0"),))
    root = ComponentSpec("skill", "root", "1.0.0", (Dependency("b", "1.0.0"),))
    r1 = resolver_for([a, b, root]).resolve(root)
    r2 = resolver_for([a, b, root]).resolve(root)
    assert r1.ordered == r2.ordered


def test_missing_dependency_fails():
    root = ComponentSpec("skill", "root", "1.0.0", (Dependency("ghost", "1.0.0"),))
    res = resolver_for([root]).resolve(root)
    assert not res.ok
    assert "missing dependency: ghost" in res.reason


def test_cycle_detected_with_path():
    a = ComponentSpec("skill", "a", "1.0.0", (Dependency("b", "1.0.0"),))
    b = ComponentSpec("skill", "b", "1.0.0", (Dependency("a", "1.0.0"),))
    root = ComponentSpec("skill", "root", "1.0.0", (Dependency("a", "1.0.0"),))
    res = resolver_for([a, b, root]).resolve(root)
    assert not res.ok
    assert "cycle" in res.reason
    assert "a" in res.reason and "b" in res.reason


def test_self_cycle_detected():
    a = ComponentSpec("skill", "a", "1.0.0", (Dependency("a", "1.0.0"),))
    res = resolver_for([a]).resolve(a)
    assert not res.ok
    assert "cycle" in res.reason


def test_conflict_pin_vs_installed_version():
    """Pin khai báo khác version installed → conflict."""
    b = ComponentSpec("skill", "b", "2.0.0")
    root = ComponentSpec("skill", "root", "1.0.0", (Dependency("b", "1.5.0"),))
    res = resolver_for([b, root]).resolve(root)
    assert not res.ok
    assert "conflict" in res.reason


def test_diamond_dependency_ok():
    """A được 2 nhánh dùng cùng version — hợp lệ, resolve 1 lần."""
    a = ComponentSpec("skill", "a", "1.0.0")
    b = ComponentSpec("skill", "b", "1.0.0", (Dependency("a", "1.0.0"),))
    c = ComponentSpec("skill", "c", "1.0.0", (Dependency("a", "1.0.0"),))
    root = ComponentSpec(
        "skill", "root", "1.0.0",
        (Dependency("b", "1.0.0"), Dependency("c", "1.0.0")),
    )
    res = resolver_for([a, b, c, root]).resolve(root)
    assert res.ok
    assert [s.component_id for s in res.ordered] == ["a", "b", "c", "root"]


def test_component_spec_frozen():
    spec = ComponentSpec("skill", "x", "1.0.0")
    with pytest.raises(Exception):
        spec.component_id = "y"  # type: ignore[misc]
