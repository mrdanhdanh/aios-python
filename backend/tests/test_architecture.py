"""Architecture invariant tests (TASK-016): INV-001..INV-010 enforced via AST.

Pure static analysis — these tests NEVER import aios_core at runtime, so the
coverage report (--cov=aios_core) is unaffected. They fail the build when a
module violates a layering rule (e.g. workflow importing langgraph).
"""

import ast
from pathlib import Path

import pytest

from _arch_scan import SRC_ROOT, collect_imports, dir_imports, module_imports

AIOS = SRC_ROOT / "aios_core"

# INV-001/002 become active once TASK-013 (agents) / TASK-014 (tools) exist.
AGENTS_DIR = AIOS / "agents"
TOOLS_DIR = AIOS / "tools"


# -- INV-003: workflow must not know the engine ---------------------------------

def test_inv003_workflow_no_engine():
    hits = dir_imports(AIOS / "workflow", ["langgraph", "aios_core.models"])
    assert hits == [], f"INV-003 vi phạm: {hits}"


# -- INV-004: capability independence (premise — runs now) ----------------------

def test_inv004_capability_no_tool_impl():
    hits = dir_imports(AIOS / "capabilities", ["aios_core.models", "aios_core.workflow", "aios_core.tools"])
    assert hits == [], f"INV-004 vi phạm: {hits}"


# -- INV-005: control plane isolation -------------------------------------------

def test_inv005_rule_a_no_business_models():
    # Orchestrator (incl. goals/) must not import models — planner.py exempt.
    hits = dir_imports(
        AIOS / "orchestrator",
        ["aios_core.models"],
        exclude=["aios_core.orchestrator.planner"],
    )
    assert hits == [], f"INV-005 rule A vi phạm: {hits}"


def test_inv005_rule_b_planner_allowlist():
    # planner.py may ONLY import models.base + models.errors (allow-list — C2-01).
    # Cấm: (1) `aios_core.models` TRẦN chính xác (vì __init__ re-export providers),
    #      (2) mọi module provider cụ thể (openai/ollama/mock/registry).
    _, aios_mods = collect_imports(SRC_ROOT, "aios_core/orchestrator/planner")
    hits = []
    for mod in aios_mods:
        if mod == "aios_core.models":  # trần — from aios_core.models import OpenAIModel
            hits.append(f"planner -> {mod} (cấm trần: __init__ re-export providers)")
        for provider in ("openai_provider", "ollama_provider", "mock", "registry"):
            if mod == f"aios_core.models.{provider}" or mod.startswith(f"aios_core.models.{provider}."):
                hits.append(f"planner -> {mod} (cấm provider)")
    allowed = {"aios_core.models.base", "aios_core.models.errors"}
    extra = aios_mods - allowed - {"aios_core.orchestrator", "aios_core.workflow.library"}
    assert not hits, f"INV-005 rule B vi phạm: {hits}"
    assert not extra, f"planner import ngoài allow-list: {extra}"


# -- INV-007: policy first (hard — call-site) -----------------------------------

def test_inv007_policy_first_hard():
    src = (AIOS / "kernel" / "services" / "execution.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        # self._policy.evaluate(...) => Attribute(Attribute(Name(self), _policy), evaluate)
        if isinstance(node, ast.Attribute) and node.attr == "evaluate":
            value = node.value
            if isinstance(value, ast.Attribute) and value.attr == "_policy":
                found = True
                break
    assert found, "INV-007 vi phạm: execution.py phải có call-site self._policy.evaluate(...)"


# -- INV-009: event driven (4 business services; events.py = infrastructure) -----

def test_inv009_event_driven_partial():
    services = AIOS / "kernel" / "services"
    emitting = ["execution", "artifacts", "permissions", "policy"]
    for name in emitting:
        src = (services / f"{name}.py").read_text(encoding="utf-8")
        assert "EventType" in src or "EventBus" in src, (
            f"INV-009 vi phạm: {name}.py phải tham chiếu EventType/EventBus"
        )
    # Ghi nhận future (không fail): context/state/resource/scheduler chưa emit.
    future = ["context", "state", "resource", "scheduler"]
    pending = [n for n in future if "EventType" not in (services / f"{n}.py").read_text(encoding="utf-8")]
    assert pending == future, (
        f"Lưu ý: {set(future) - set(pending)} đã bắt đầu emit — cập nhật phép đếm INV-009"
    )


# -- INV-010: deterministic first (extended to catalog/KG/prompts) ---------------

def test_inv010_deterministic_first():
    for sub in ("orchestrator", "catalog", "knowledge_graph", "prompts"):
        hits = dir_imports(AIOS / sub, ["aios_core.models"])
        if sub == "orchestrator":
            hits = [h for h in hits if "orchestrator.planner" not in h]
        assert hits == [], f"INV-010 vi phạm ({sub}): {hits}"


# -- INV-006: contracts purity ----------------------------------------------------

def test_inv006_contracts_purity():
    hits = dir_imports(AIOS / "contracts", ["aios_core.kernel.services", "aios_core.kernel.events"])
    assert hits == [], f"INV-006 vi phạm: {hits}"


# -- INV-001/002: worker isolation (active once agents/ + tools/ exist) ----------

@pytest.mark.skipif(not AGENTS_DIR.is_dir(), reason="agents/ chưa tồn tại (TASK-013)")
def test_inv001_worker_no_runtime():
    hits = dir_imports(AGENTS_DIR, ["aios_core.kernel.services"])
    assert hits == [], f"INV-001 vi phạm: {hits}"


@pytest.mark.skipif(not AGENTS_DIR.is_dir(), reason="agents/ chưa tồn tại (TASK-013)")
def test_inv002_worker_no_direct_tool():
    # INV-002 active once agents/ exists (tools/ target không cần tồn tại — C1-01).
    hits = dir_imports(AGENTS_DIR, ["aios_core.tools"])
    assert hits == [], f"INV-002 vi phạm: {hits}"


# -- agents/ import allow-list (TASK-013 — Worker Plane hard isolation) ---------

_AGENTS_ALLOWED_AIOS = {"aios_core.models.base", "aios_core.models.errors"}
_AGENTS_ALLOWED_EXTERNAL = {
    "pydantic",
    "typing",
    "collections",
    "abc",
    "re",
    "logging",
    "ast",
    "dataclasses",
    "enum",
    "threading",
    "functools",
}


@pytest.mark.skipif(not AGENTS_DIR.is_dir(), reason="agents/ chưa tồn tại (TASK-013)")
def test_inv_agents_import_allowlist():
    """agents/ (Worker Plane) chỉ được import allow-list — C1-07/C2-06/R1.2.

    Loại trừ aios_core.agents* (intra-package) trước khi check subset; kiểm
    CẢ aios_mods lẫn external_top_level.
    """
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(AGENTS_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.agents")}  # intra-package
    bad_aios = aios_mods - _AGENTS_ALLOWED_AIOS
    bad_external = external - _AGENTS_ALLOWED_EXTERNAL
    assert not bad_aios, f"agents/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"agents/ import ngoài allow-list (external): {bad_external}"


# -- helper correctness ----------------------------------------------------------

def test_arch_scan_detects_violation(tmp_path):
    evil = tmp_path / "evil.py"
    evil.write_text("import aios_core.models\n", encoding="utf-8")
    _, aios_mods = collect_imports(tmp_path, "evil")
    assert "aios_core.models" in aios_mods


def test_arch_scan_detects_nested_import(tmp_path):
    # Import inside try/except and inside a function must be detected (C1-04).
    evil = tmp_path / "evil.py"
    evil.write_text(
        "def f():\n"
        "    try:\n"
        "        import langgraph\n"
        "    except ImportError:\n"
        "        pass\n"
        "def g():\n"
        "    from aios_core import models\n",
        encoding="utf-8",
    )
    external, aios_mods = collect_imports(tmp_path, "evil")
    assert "langgraph" in external
    assert "aios_core" in aios_mods  # from aios_core import models


def test_arch_scan_resolves_relative():
    # relative resolution: from ..models.base import X inside orchestrator/planner
    _, aios_mods = collect_imports(SRC_ROOT, "aios_core/orchestrator/planner")
    assert "aios_core.models.base" in aios_mods
    assert "aios_core.models.errors" in aios_mods


def test_arch_scan_ignores_future():
    _, aios_mods = collect_imports(SRC_ROOT, "aios_core/orchestrator/planner")
    assert "__future__" not in aios_mods
