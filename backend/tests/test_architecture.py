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
SKILLS_DIR = AIOS / "skills"  # TASK-015
SANDBOX_DIR = AIOS / "sandbox"  # TASK-015
UPGRADE_DIR = AIOS / "upgrade"  # TASK-020 (M4-P7)
OBSERVABILITY_DIR = AIOS / "observability"  # TASK-021 (M4-P8)
MEMORY_DIR = AIOS / "memory"  # TASK-023 (M5-P9)


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


# -- tools/ import allow-list (TASK-014 — Execution Plane hard isolation) -------

_TOOLS_ALLOWED_AIOS = {"aios_core.metadata"}
_TOOLS_ALLOWED_EXTERNAL = {
    "pydantic",
    "urllib",  # chỉ urllib.parse — check module-con ở dưới (C1-04/R3)
    "typing",
    "collections",
    "abc",
    "re",
    "logging",
    "ast",
    "threading",
    "functools",
    "time",
    "enum",
    "dataclasses",
}


@pytest.mark.skipif(not TOOLS_DIR.is_dir(), reason="tools/ chưa tồn tại (TASK-014)")
def test_inv_tools_import_allowlist():
    """tools/ (Execution Plane) chỉ import metadata + pydantic + stdlib.

    R3: urllib module-con check bằng AST walk — mọi import chạm 'urllib.*'
    phải == 'urllib.parse' (collect_imports nén external về top-level nên
    external check không bắt được urllib.request).
    """
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(TOOLS_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.tools")}  # intra-package
        # R3: AST walk chặn urllib.request/error/robotparser (và import urllib trần)
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "urllib" or alias.name.startswith("urllib."):
                        assert alias.name == "urllib.parse", (
                            f"tools/ import urllib không hợp lệ: {alias.name} ({rel})"
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "urllib" or node.module.startswith("urllib."):
                    assert node.module == "urllib.parse", (
                        f"tools/ import urllib không hợp lệ: {node.module} ({rel})"
                    )
    bad_aios = aios_mods - _TOOLS_ALLOWED_AIOS
    bad_external = external - _TOOLS_ALLOWED_EXTERNAL
    assert not bad_aios, f"tools/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"tools/ import ngoài allow-list (external): {bad_external}"


# -- skills/ + sandbox/ import allow-list (TASK-015 — Execution Plane) ----------

_SKILLS_ALLOWED_AIOS = {"aios_core.metadata", "aios_core.semver"}  # C1-04
_SKILLS_ALLOWED_EXTERNAL = {
    "pydantic",
    "sqlite3",
    "typing",
    "collections",
    "abc",
    "re",
    "logging",
    "threading",
    "functools",
    "time",
    "enum",
    "dataclasses",
    "json",
    "uuid",
    "pathlib",
    "contextlib",
    "datetime",
}
_SANDBOX_ALLOWED_EXTERNAL = {
    "pydantic",
    "threading",
    "time",
    "uuid",
    "dataclasses",
    "enum",
    "typing",
    "logging",
    "collections",
}


@pytest.mark.skipif(not SKILLS_DIR.is_dir(), reason="skills/ chưa tồn tại (TASK-015)")
def test_inv_skills_import_allowlist():
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(SKILLS_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.skills")}  # intra-package
    bad_aios = aios_mods - _SKILLS_ALLOWED_AIOS
    bad_external = external - _SKILLS_ALLOWED_EXTERNAL
    assert not bad_aios, f"skills/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"skills/ import ngoài allow-list (external): {bad_external}"


@pytest.mark.skipif(not SANDBOX_DIR.is_dir(), reason="sandbox/ chưa tồn tại (TASK-015)")
def test_inv_sandbox_import_allowlist():
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(SANDBOX_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.sandbox")}
    assert not aios_mods, f"sandbox/ import aios_core ngoài allow-list: {aios_mods}"
    bad_external = external - _SANDBOX_ALLOWED_EXTERNAL
    assert not bad_external, f"sandbox/ import ngoài allow-list (external): {bad_external}"


# -- memory/ import allow-list + INV-011 (TASK-023 — Memory Isolation) -----------

_MEMORY_ALLOWED_AIOS = {"aios_core.kernel.services"}
_MEMORY_ALLOWED_EXTERNAL = {
    "pydantic",
    "typing",
    "datetime",
    "time",
    "enum",
    "math",
    "hashlib",
    "re",
    "json",
    # File M1 có sẵn (conversation/vector/session): sqlite3, uuid, pathlib,
    # contextlib, abc — giữ nguyên, không đổi hành vi (additive only).
    "sqlite3",
    "uuid",
    "pathlib",
    "contextlib",
    "abc",
}


@pytest.mark.skipif(not MEMORY_DIR.is_dir(), reason="memory/ chưa tồn tại (TASK-023)")
def test_inv_memory_import_allowlist():
    """memory/ chỉ import allow-list; CẤM aios_core.knowledge kể cả TYPE_CHECKING
    (collect_imports đếm mọi Import node — C2-01). KnowledgeSource duck-typed.
    """
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(MEMORY_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.memory")}
    bad_aios = aios_mods - _MEMORY_ALLOWED_AIOS
    bad_external = external - _MEMORY_ALLOWED_EXTERNAL
    assert not bad_aios, f"memory/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"memory/ import ngoài allow-list (external): {bad_external}"


@pytest.mark.skipif(not AGENTS_DIR.is_dir(), reason="agents/ chưa tồn tại (TASK-013)")
def test_inv011_memory_isolation():
    """INV-011: Agent KHÔNG được import memory/knowledge trực tiếp.

    Đã được allow-list agents bao phủ (chỉ {models.base, models.errors}) —
    test này tường minh hóa invariant (C3-02).
    """
    hits = dir_imports(AGENTS_DIR, ["aios_core.memory", "aios_core.knowledge"])
    assert hits == [], f"INV-011 vi phạm: {hits}"

# -- context/ import allow-list (TASK-024 — Context Optimizer) ----------------

_CONTEXT_ALLOWED_AIOS = {
    "aios_core.kernel.services",
    "aios_core.memory",
    "aios_core.memory.contracts",
    "aios_core.memory.coordinator",
}
_CONTEXT_ALLOWED_EXTERNAL = {
    "pydantic",
    "typing",
    "datetime",
    "enum",
    "re",
    "hashlib",
    "math",
    "json",  # C2-01 (vòng 2): _serialize_value dùng json.dumps
}


@pytest.mark.skipif(not (AIOS / "context").is_dir(), reason="context/ chưa tồn tại (TASK-024)")
def test_inv_context_import_allowlist():
    """context/ (intelligence) chỉ import kernel.services + memory — CẤM
    models/knowledge/orchestrator/contracts kể cả TYPE_CHECKING (C2-01)."""
    context_dir = AIOS / "context"
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(context_dir.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.context")}
    bad_aios = aios_mods - _CONTEXT_ALLOWED_AIOS
    bad_external = external - _CONTEXT_ALLOWED_EXTERNAL
    assert not bad_aios, f"context/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"context/ import ngoài allow-list (external): {bad_external}"


# -- planning/ import allow-list + INV-014 (TASK-026) --------------------------

_PLANNING_ALLOWED_AIOS = {
    "aios_core.kernel.execution_plan",
    "aios_core.kernel.services",
    "aios_core.kernel.dag",
    "aios_core.capabilities",
    "aios_core.capabilities.registry",
    "aios_core.workflow.library",
    "aios_core.orchestrator.errors",
    "aios_core.logging",
}
_PLANNING_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "enum", "dataclasses", "re", "time", "threading",
    "abc", "logging", "collections",
}


@pytest.mark.skipif(not (AIOS / "orchestrator" / "planning").is_dir(),
                    reason="planning/ chưa tồn tại (TASK-026)")
def test_inv_planning_import_allowlist():
    """planning/ chỉ import allow-list — CẤM models/knowledge/context/contracts
    kể cả TYPE_CHECKING (bài học C2-01). Loop qua mọi file (C2-12 v2)."""
    planning_dir = AIOS / "orchestrator" / "planning"
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(planning_dir.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {
            m for m in mods
            if not m.startswith("aios_core.orchestrator.planning")
            and not m.startswith("aios_core.orchestrator")
        }
    bad_aios = aios_mods - _PLANNING_ALLOWED_AIOS
    bad_external = external - _PLANNING_ALLOWED_EXTERNAL
    assert not bad_aios, f"planning/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"planning/ import ngoài allow-list (external): {bad_external}"


def test_inv014_planning_gate():
    """INV-014: engine phải validate plan trước khi trả (AST call-site)."""
    src = (AIOS / "orchestrator" / "planning" / "engine.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "validate":
            value = node.value
            if isinstance(value, ast.Attribute) and value.attr == "_validator":
                found = True
                break
    assert found, "INV-014 vi phạm: engine.py phải có call-site self._validator.validate(...)"


def test_inv014_runtime_no_planning():
    """Runtime services không được phụ thuộc planning (intelligence ở trên)."""
    hits = dir_imports(AIOS / "kernel" / "services", ["aios_core.orchestrator.planning"])
    assert hits == [], f"INV-014 vi phạm: {hits}"


def test_inv014_validation_has_8_rules():
    """INV-014: validator phải kiểm đủ 8 hạng mục PLAN §14."""
    src = (AIOS / "orchestrator" / "planning" / "validation.py").read_text(encoding="utf-8")
    for rule in ("CONTRACT", "CAPABILITY", "PERMISSION", "POLICY",
                 "DEPENDENCY", "RESOURCE", "CYCLE", "TIMEOUT"):
        assert f"ValidationRule.{rule}" in src, f"INV-014 thiếu rule {rule}"


def test_inv014_no_god_object():
    """planning/ không God Object: engine điều phối 6 module con."""
    src = (AIOS / "orchestrator" / "planning" / "engine.py").read_text(encoding="utf-8")
    for component in ("GoalAnalyzer", "TaskDecomposer", "DependencyAnalyzer",
                      "CapabilityResolver", "RiskAnalyzer", "ExecutionPlanner",
                      "PlanValidator"):
        assert component in src, f"engine thiếu component {component}"


# -- kernel/graph/ import allow-list + INV-015 (TASK-027) ----------------------

_GRAPH_ALLOWED_AIOS = {
    "aios_core.kernel.execution_plan",
    "aios_core.kernel.dag",
    "aios_core.kernel.services.state",
    "aios_core.kernel.services",
    "aios_core.config",
    "aios_core.logging",
}
_GRAPH_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "enum", "dataclasses", "threading",
    "concurrent", "time", "logging", "datetime",
}


@pytest.mark.skipif(not (AIOS / "kernel" / "graph").is_dir(),
                    reason="kernel/graph/ chưa tồn tại (TASK-027)")
def test_inv_graph_import_allowlist():
    """kernel/graph/ chỉ import allow-list — CẤM orchestrator/models/memory/
    context/knowledge/tools/agents/capabilities/workflow/contracts/execution/
    resource/scheduler/runtime_kernel kể cả TYPE_CHECKING."""
    graph_dir = AIOS / "kernel" / "graph"
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(graph_dir.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.kernel.graph")}
    bad_aios = aios_mods - _GRAPH_ALLOWED_AIOS
    bad_external = external - _GRAPH_ALLOWED_EXTERNAL
    assert not bad_aios, f"kernel/graph/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"kernel/graph/ import ngoài allow-list (external): {bad_external}"


def test_inv015_graph_acyclicity_gate():
    """INV-015: contracts.py VÀ executor.py phải chứa literal validate_dag(."""
    contracts = (AIOS / "kernel" / "graph" / "contracts.py").read_text(encoding="utf-8")
    executor = (AIOS / "kernel" / "graph" / "executor.py").read_text(encoding="utf-8")
    assert "validate_dag(" in contracts, "INV-015: contracts.py thiếu validate_dag("
    assert "validate_dag(" in executor, "INV-015: executor.py thiếu validate_dag("


def test_inv015_planning_no_graph():
    """planning/ (intelligence) không import kernel.graph (không đảo chiều)."""
    hits = dir_imports(AIOS / "orchestrator" / "planning", ["aios_core.kernel.graph"])
    assert hits == [], f"INV-015 vi phạm: {hits}"


def test_inv015_graph_no_god_object():
    """graph layer không God Object: executor điều phối, state machine tách."""
    executor = (AIOS / "kernel" / "graph" / "executor.py").read_text(encoding="utf-8")
    state_machine = (AIOS / "kernel" / "graph" / "state_machine.py").read_text(encoding="utf-8")
    converter = (AIOS / "kernel" / "graph" / "converter.py").read_text(encoding="utf-8")
    assert "GraphStateMachine" in executor
    assert "def execute(" not in state_machine
    assert "def execute(" not in converter
    assert "def plan_to_graph(" not in executor
    assert "import executor" not in contracts_src() or True  # leaf check below


def contracts_src() -> str:
    return (AIOS / "kernel" / "graph" / "contracts.py").read_text(encoding="utf-8")


def test_inv015_contracts_leaf():
    """contracts.py không import executor/converter/state_machine (leaf)."""
    src = contracts_src()
    assert "executor" not in src
    assert "converter" not in src
    assert "state_machine" not in src


# -- kernel/scheduler/ import allow-list + INV-016 (TASK-028) ------------------

_SCHEDULER_ALLOWED_AIOS = {
    "aios_core.kernel.graph",
    "aios_core.kernel.graph.contracts",
    "aios_core.kernel.graph.errors",
    "aios_core.kernel.graph.state_machine",
    "aios_core.kernel.graph.executor",
    "aios_core.kernel.graph.converter",
    "aios_core.kernel.services.state",
    "aios_core.kernel.services.resource",
    "aios_core.kernel.execution_plan",  # C2-06 v2: contracts thuần, toàn dir
    "aios_core.config",
    "aios_core.logging",
}
_SCHEDULER_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "threading", "time", "logging",
}


@pytest.mark.skipif(not (AIOS / "kernel" / "scheduler").is_dir(),
                    reason="kernel/scheduler/ chưa tồn tại (TASK-028)")
def test_inv016_scheduler_import_allowlist():
    """kernel/scheduler/ chỉ import allow-list; services.execution CHỈ trong
    execution_runner.py (INV-016 — R1-1: exclude DOTTED)."""
    scheduler_dir = AIOS / "kernel" / "scheduler"
    aios_mods: set[str] = set()
    external: set[str] = set()
    runner_mods: set[str] = set()
    for py in sorted(scheduler_dir.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        clean = {m for m in mods if not m.startswith("aios_core.kernel.scheduler")}
        aios_mods |= clean
        if rel == "aios_core.kernel.scheduler.execution_runner":
            runner_mods |= clean
    bad_aios = aios_mods - _SCHEDULER_ALLOWED_AIOS
    bad_external = external - _SCHEDULER_ALLOWED_EXTERNAL
    assert not bad_aios, f"scheduler/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"scheduler/ import ngoài allow-list (external): {bad_external}"
    # services.execution chỉ hợp lệ trong execution_runner.py
    for mod in aios_mods - runner_mods:
        assert "kernel.services.execution" not in mod, (
            f"INV-016: {mod} chạm ExecutionService (chỉ execution_runner.py)")


def test_inv016_scheduler_call_sites():
    """INV-016: call-sites literal — acquire/release trong scheduler.py,
    execution_service.execute trong execution_runner.py."""
    scheduler_src = (AIOS / "kernel" / "scheduler" / "scheduler.py").read_text(encoding="utf-8")
    runner_src = (AIOS / "kernel" / "scheduler" / "execution_runner.py").read_text(encoding="utf-8")
    assert "acquire_slot_wait(" in scheduler_src
    assert "release_slot(" in scheduler_src
    assert "execution_service.execute(" in runner_src


def test_inv016_scheduler_no_god_object():
    """scheduler/ không God Object: không ThreadPoolExecutor, không def execute("""
    for name in ("scheduler.py", "execution_runner.py", "contracts.py", "errors.py"):
        src = (AIOS / "kernel" / "scheduler" / name).read_text(encoding="utf-8")
        assert "ThreadPoolExecutor" not in src, f"{name} không được dùng ThreadPool"
        assert "def execute(" not in src, f"{name} không được định nghĩa execute"


def test_inv016_scheduler_no_private_access():
    """INV-016: scheduler/ không chạm private attrs của Resource/Execution
    (giới hạn v1: chỉ bắt Name._attr — P3-03)."""
    for name in ("scheduler.py", "execution_runner.py"):
        src = (AIOS / "kernel" / "scheduler" / name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                value = node.value
                if isinstance(value, ast.Name) and value.id != "self":
                    assert False, f"INV-016: {name} truy cập private {node.attr}"


def test_inv016_graph_no_scheduler():
    """kernel/graph/ không import scheduler (đảo chiều)."""
    hits = dir_imports(AIOS / "kernel" / "graph", ["aios_core.kernel.scheduler"])
    assert hits == [], f"INV-016 vi phạm: {hits}"


def test_inv016_planning_no_scheduler():
    """planning/ (intelligence) không import scheduler."""
    hits = dir_imports(AIOS / "orchestrator" / "planning", ["aios_core.kernel.scheduler"])
    assert hits == [], f"INV-016 vi phạm: {hits}"


# -- models/router/ import allow-list (TASK-025 — Model Router) ---------------

_ROUTER_ALLOWED_AIOS = {
    "aios_core.models.base",
    "aios_core.models.errors",
    "aios_core.models.registry",
    "aios_core.models.capability",
}
_ROUTER_ALLOWED_EXTERNAL = {
    "pydantic",
    "typing",
    "datetime",
    "enum",
    "abc",
    "dataclasses",
    "threading",  # R2-1: health/router RLock
}


@pytest.mark.skipif(not (AIOS / "models" / "router").is_dir(), reason="models/router/ chưa tồn tại (TASK-025)")
def test_inv_router_import_allowlist():
    """models/router/ (routing intelligence) chỉ import models.{base,errors,registry,capability}
    + intra — CẤM kernel/orchestrator/context/memory/contracts kể cả TYPE_CHECKING."""
    router_dir = AIOS / "models" / "router"
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(router_dir.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.models.router")}
    bad_aios = aios_mods - _ROUTER_ALLOWED_AIOS
    bad_external = external - _ROUTER_ALLOWED_EXTERNAL
    assert not bad_aios, f"models/router/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"models/router/ import ngoài allow-list (external): {bad_external}"


# -- INV-013: no God Object (TASK-025 §5.4) -----------------------------------

@pytest.mark.skipif(not (AIOS / "models" / "router").is_dir(), reason="models/router/ chưa tồn tại (TASK-025)")
def test_inv013_no_god_object():
    """ModelRouter chỉ điều phối: import đủ 6 module; không logic cost;
    không đảo chiều import."""
    router_dir = AIOS / "models" / "router"
    _, router_mods = collect_imports(SRC_ROOT, "aios_core/models/router/router")
    policy_sources = {"aios_core.models.router.policy", "aios_core.models.router.contracts"}
    for needed in ("selector", "cost", "availability", "health", "fallback"):
        assert f"aios_core.models.router.{needed}" in router_mods, (
            f"router.py thiếu import {needed}"
        )
    assert router_mods & policy_sources, "router.py thiếu nguồn policy"
    # cost logic không nằm trong router.py
    src = (router_dir / "router.py").read_text(encoding="utf-8")
    for forbidden in ("estimate_cost", "quality_score", "latency_ms", "balanced_score"):
        # only as a function definition/import — not implemented here
        assert f"def {forbidden}" not in src, f"router.py không được định nghĩa {forbidden}"
    # không đảo chiều: selector/fallback không import router
    for sub in ("selector", "fallback"):
        _, mods = collect_imports(SRC_ROOT, f"aios_core/models/router/{sub}")
        assert not any(m == "aios_core.models.router.router" for m in mods), (
            f"{sub}.py không được import router"
        )


# -- INV-013: selection via router only (TASK-025 §5.1) ------------------------

_INV013_EXEMPTIONS = {
    "aios_core.kernel.runtime_kernel",  # composition root (wiring)
    "aios_core.api.wiring",  # composition root (orchestrator default)
    "aios_core",  # root __init__ re-export (C2-01 v2)
}


@pytest.mark.skipif(not (AIOS / "models" / "router").is_dir(), reason="models/router/ chưa tồn tại (TASK-025)")
def test_inv013_selection_via_router_only():
    """INV-013: model selection phải qua ModelRouter. Mọi module ngoài models/
    import ModelRegistry (hoặc aios_core.models trần — collect_imports match
    2 chiều) đều bị chặn, trừ composition roots (wiring/re-export).
    Lưu ý: AST đếm MỌI Import node kể cả TYPE_CHECKING (bài học TASK-023 C2-01)."""
    violations: list[str] = []
    for py in sorted(SRC_ROOT.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        if not rel.startswith("aios_core"):
            continue
        if rel in _INV013_EXEMPTIONS:
            continue
        if rel.startswith("aios_core.models"):
            continue
        ext, mods = collect_imports(SRC_ROOT, rel)
        hits = [m for m in mods if m == "aios_core.models.registry"
                or m.startswith("aios_core.models.registry.")
                or m == "aios_core.models"]
        if hits:
            violations.append(f"{rel} -> {hits}")
    assert not violations, f"INV-013 vi phạm (phải qua ModelRouter): {violations}"

# -- upgrade/ import allow-list (TASK-020 — control plane, hook-injected) -------

_UPGRADE_ALLOWED_AIOS = {
    "aios_core.contracts",
    "aios_core.semver",
    "aios_core.kernel.events",
    "aios_core.skills.errors",  # SkillMigrator catch SkillError/SkillStateError (R1-1)
}
_UPGRADE_ALLOWED_EXTERNAL = {
    "sqlite3",
    "pathlib",
    "contextlib",
    "json",
    "dataclasses",
    "typing",
    "datetime",
    "uuid",
    "collections",
    "logging",
}


@pytest.mark.skipif(not UPGRADE_DIR.is_dir(), reason="upgrade/ chưa tồn tại (TASK-020)")
def test_inv_upgrade_import_allowlist():
    """upgrade/ (control plane) chỉ import allow-list — migrators hook-injected."""
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(UPGRADE_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.upgrade")}
    bad_aios = aios_mods - _UPGRADE_ALLOWED_AIOS
    bad_external = external - _UPGRADE_ALLOWED_EXTERNAL
    assert not bad_aios, f"upgrade/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"upgrade/ import ngoài allow-list (external): {bad_external}"


# -- observability/ import allow-list (TASK-021 — control plane) ---------------

_OBSERVABILITY_ALLOWED_AIOS = {
    "aios_core.kernel.events",
    "aios_core.kernel.services",
    "aios_core.healthcheck",
    "aios_core.semver",
    "aios_core.logging",
}
_OBSERVABILITY_ALLOWED_EXTERNAL = {
    "sqlite3",
    "pathlib",
    "contextlib",
    "json",
    "dataclasses",
    "typing",
    "datetime",
    "uuid",
    "collections",
    "time",
    "ast",
    "statistics",
    "logging",
}


@pytest.mark.skipif(not OBSERVABILITY_DIR.is_dir(), reason="observability/ chưa tồn tại (TASK-021)")
def test_inv_observability_import_allowlist():
    """observability/ (control plane) chỉ import allow-list — diagnostics hooks."""
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(OBSERVABILITY_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.observability")}
    bad_aios = aios_mods - _OBSERVABILITY_ALLOWED_AIOS
    bad_external = external - _OBSERVABILITY_ALLOWED_EXTERNAL
    assert not bad_aios, f"observability/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"observability/ import ngoài allow-list (external): {bad_external}"


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
