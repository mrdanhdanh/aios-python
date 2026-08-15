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


# -- harness/ import allow-list + INV-017/018 (TASK-029, M6-H1) ----------------

_HARNESS_ALLOWED_AIOS = {
    "aios_core.config",
    "aios_core.logging",
    "aios_core.kernel.services.state",
    "aios_core.kernel.services.artifacts",
    "aios_core.contracts.artifact",
}
_HARNESS_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "datetime", "enum", "re", "json", "threading",
    "time", "abc", "collections", "pathlib",  # pathlib: TASK-030 FILE_EXISTS/
    # CONTAINS checks (R2-1 review) — B7: top-level (collections.abc -> collections)
    "yaml",  # TASK-031: scenarios loader (safe_load — C2-07)
}


@pytest.mark.skipif(not (AIOS / "harness").is_dir(),
                    reason="harness/ chưa tồn tại (TASK-029)")
def test_inv017_harness_import_allowlist():
    """harness/ chỉ import allow-list — CẤM kernel.services.execution|resource|
    scheduler|policy|permissions|context + orchestrator/models/memory/knowledge
    kể cả TYPE_CHECKING. Loop rglob (C3-07: phủ subdir H2-H5 tương lai)."""
    harness_dir = AIOS / "harness"
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(harness_dir.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.harness")}
    bad_aios = aios_mods - _HARNESS_ALLOWED_AIOS
    bad_external = external - _HARNESS_ALLOWED_EXTERNAL
    assert not bad_aios, f"harness/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"harness/ import ngoài allow-list (external): {bad_external}"


def test_inv017_harness_no_kernel_impl():
    """INV-017: harness/ không chui kernel implementation (rglob đệ quy)."""
    hits = dir_imports(AIOS / "harness", [
        "aios_core.kernel.services.execution",
        "aios_core.kernel.services.resource",
        "aios_core.kernel.services.scheduler",
        "aios_core.kernel.services.policy",
        "aios_core.kernel.services.permissions",
        "aios_core.kernel.services.context",
    ])
    assert hits == [], f"INV-017 vi phạm: {hits}"


def test_inv017_harness_no_god_object():
    """contracts.py là leaf (import-based — C2-04 v2); runner/registry/lifecycle
    tách module; không def execute("""
    contracts_src = (AIOS / "harness" / "contracts.py").read_text(encoding="utf-8")
    tree = ast.parse(contracts_src)
    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    # leaf: chỉ stdlib/pydantic — không import aios_core nào
    for node in imports:
        mod = getattr(node, "module", None) or ""
        assert not mod.startswith("aios_core"), \
            f"contracts.py không được import aios_core: {mod}"
    # runner.execute() là public API chính — chỉ registry/lifecycle/context
    # không được định nghĩa execute (trách nhiệm duy nhất thuộc runner).
    for name in ("registry.py", "lifecycle.py", "context.py"):
        src = (AIOS / "harness" / name).read_text(encoding="utf-8")
        assert "def execute(" not in src, f"{name} không được định nghĩa execute"


def test_inv018_runner_builds_evidence():
    """INV-018: runner.py phải chứa literal HarnessArtifact( (build evidence)."""
    runner_src = (AIOS / "harness" / "runner.py").read_text(encoding="utf-8")
    assert "HarnessArtifact(" in runner_src
    assert "finally" in runner_src  # evidence trong finally (C1-03)


# -- harness/execution/ (TASK-030 — Execution Verification, INV-019) ----------

@pytest.mark.skipif(not (AIOS / "harness" / "execution").is_dir(),
                    reason="harness/execution chưa tồn tại (TASK-030)")
def test_inv019_execution_no_kernel_impl():
    """INV-019: harness/execution/ không import kernel.services.events|execution|
    |graph|planning (duck-typed EvidenceServices — P1-02 v2)."""
    hits = dir_imports(AIOS / "harness" / "execution", [
        "aios_core.kernel.services.events",
        "aios_core.kernel.services.execution",
        "aios_core.kernel.graph",
        "aios_core.orchestrator.planning",
        "aios_core.kernel.services.resource",
        "aios_core.kernel.services.scheduler",
    ])
    assert hits == [], f"INV-019 vi phạm: {hits}"


@pytest.mark.skipif(not (AIOS / "harness" / "execution").is_dir(),
                    reason="harness/execution chưa tồn tại (TASK-030)")
def test_inv019_verification_uses_duck_typing():
    """EvidenceServices phải khai báo attribute (state/events/artifacts),
    KHÔNG import type thật từ kernel.services."""
    contracts_src = (AIOS / "harness" / "execution" / "contracts.py").read_text(
        encoding="utf-8")
    assert "class EvidenceServices" in contracts_src
    assert "Callable" in contracts_src or "state:" in contracts_src
    tree = ast.parse(contracts_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("aios_core.kernel"), \
                f"contracts.py không được import kernel: {mod}"


@pytest.mark.skipif(not (AIOS / "harness" / "execution").is_dir(),
                    reason="harness/execution chưa tồn tại (TASK-030)")
def test_inv019_verdict_fail_raises():
    """INV-019 (behavioral): verification.py phải raise VerificationError khi
    verdict FAIL — literal `VerificationError(` cạnh `result.verdict ==
    Verdict.FAIL`."""
    src = (AIOS / "harness" / "execution" / "verification.py").read_text(
        encoding="utf-8")
    assert "VerificationError(" in src
    assert "Verdict.FAIL" in src
    assert "raise" in src


@pytest.mark.skipif(not (AIOS / "harness" / "execution").is_dir(),
                    reason="harness/execution chưa tồn tại (TASK-030)")
def test_inv019_verdict_order_fail_first():
    """compute_verdict: FAIL (check-derived) xét TRƯỚC evidence/skip (C2-06)."""
    src = (AIOS / "harness" / "execution" / "pipeline.py").read_text(
        encoding="utf-8")
    assert "failures" in src
    fail_pos = src.index("Verdict.FAIL")
    inconclusive_pos = src.index("Verdict.INCONCLUSIVE")
    assert fail_pos < inconclusive_pos


@pytest.mark.skipif(not (AIOS / "harness" / "execution").is_dir(),
                    reason="harness/execution chưa tồn tại (TASK-030)")
def test_inv019_persist_before_verify_raise():
    """AC5: verification.py persist (update_state/ArtifactContract) TRƯỚC
    raise VerificationError trong cùng hook verify."""
    src = (AIOS / "harness" / "execution" / "verification.py").read_text(
        encoding="utf-8")
    persist_pos = src.find("_persist_verification")
    fail_check_pos = src.find("Verdict.FAIL")
    assert persist_pos != -1 and fail_check_pos != -1
    # trong verify(): persist gọi trước raise
    verify_block = src[src.find("def verify"):src.find("def _persist_verification")]
    assert "_persist_verification" in verify_block
    assert verify_block.index("_persist_verification") < \
        verify_block.index("raise VerificationError(")


@pytest.mark.skipif(not (AIOS / "harness" / "execution").is_dir(),
                    reason="harness/execution chưa tồn tại (TASK-030)")
def test_inv019_verdict_artifact_convention():
    """P2-05: verdict.json convention — id `harness:{run_id}:verdict` +
    metadata kind='verdict' (khớp _evidence_contract H1 — get_evidence fallback)."""
    src = (AIOS / "harness" / "execution" / "verification.py").read_text(
        encoding="utf-8")
    assert "harness:{ctx.run_id}:verdict" in src
    assert '"kind": "verdict"' in src


# -- harness/testing/ (TASK-031 — Test & Simulation, INV-020) -----------------

@pytest.mark.skipif(not (AIOS / "harness" / "testing").is_dir(),
                    reason="harness/testing chưa tồn tại (TASK-031)")
def test_inv020_testing_no_kernel_impl():
    """INV-020a: testing/ không import kernel.services.execution|events|resource
    |scheduler + kernel.graph|orchestrator.planning (simulation dùng fake)."""
    hits = dir_imports(AIOS / "harness" / "testing", [
        "aios_core.kernel.services.execution",
        "aios_core.kernel.services.events",
        "aios_core.kernel.services.resource",
        "aios_core.kernel.services.scheduler",
        "aios_core.kernel.graph",
        "aios_core.orchestrator.planning",
    ])
    assert hits == [], f"INV-020 vi phạm: {hits}"


@pytest.mark.skipif(not (AIOS / "harness" / "testing").is_dir(),
                    reason="harness/testing chưa tồn tại (TASK-031)")
def test_inv020_simulation_no_side_effects():
    """INV-020b: simulation/testing không side effect — AST literal: không
    import sqlite3/httpx/socket/requests/os trong 2 module chạy."""
    forbidden = ("sqlite3", "httpx", "socket", "requests", "os")
    for name in ("simulation.py", "testing.py"):
        src = (AIOS / "harness" / "testing" / name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        for mod in imports:
            assert mod.split(".")[0] not in forbidden, \
                f"{name} side-effect import: {mod}"


@pytest.mark.skipif(not (AIOS / "harness" / "testing").is_dir(),
                    reason="harness/testing chưa tồn tại (TASK-031)")
def test_inv020_testharness_uses_runner_and_raises():
    """INV-020c (behavioral): testing.py chứa literal `SimulationRunner(` +
    `TestError(` — test chạy qua runner, fail → raise."""
    src = (AIOS / "harness" / "testing" / "testing.py").read_text(encoding="utf-8")
    assert "SimulationRunner(" in src
    assert "TestError(" in src
    assert "raise" in src


@pytest.mark.skipif(not (AIOS / "harness" / "testing").is_dir(),
                    reason="harness/testing chưa tồn tại (TASK-031)")
def test_inv020_loader_safe_load():
    """scenarios.py phải dùng yaml.safe_load (C2-07 — không full_load)."""
    src = (AIOS / "harness" / "testing" / "scenarios.py").read_text(encoding="utf-8")
    assert "yaml.safe_load" in src
    assert "full_load" not in src


# -- harness/evaluation/ (TASK-032 — Evaluation, INV-020) ---------------------

@pytest.mark.skipif(not (AIOS / "harness" / "evaluation").is_dir(),
                    reason="harness/evaluation chưa tồn tại (TASK-032)")
def test_inv020_evaluation_no_kernel_or_models():
    """INV-020e: evaluation/ không import kernel.services.execution|events +
    kernel.graph|orchestrator.planning + aios_core.models* (LLM judge stub
    offline — deterministic). StateService hợp lệ (allow-list H1)."""
    hits = dir_imports(AIOS / "harness" / "evaluation", [
        "aios_core.kernel.services.execution",
        "aios_core.kernel.services.events",
        "aios_core.kernel.graph",
        "aios_core.orchestrator.planning",
    ])
    assert hits == [], f"INV-020 vi phạm: {hits}"
    models_hits = dir_imports(AIOS / "harness" / "evaluation",
                              ["aios_core.models"])
    assert models_hits == [], f"INV-020 vi phạm (models): {models_hits}"


@pytest.mark.skipif(not (AIOS / "harness" / "evaluation").is_dir(),
                    reason="harness/evaluation chưa tồn tại (TASK-032)")
def test_inv020_llm_judge_reproducible():
    """INV-020f: llm judge phải lưu model/prompt_version/temperature để
    reproducible — literal trong evaluators.py."""
    src = (AIOS / "harness" / "evaluation" / "evaluators.py").read_text(
        encoding="utf-8")
    assert "reproducible" in src
    assert "prompt_version" in src
    assert "temperature" in src


@pytest.mark.skipif(not (AIOS / "harness" / "evaluation").is_dir(),
                    reason="harness/evaluation chưa tồn tại (TASK-032)")
def test_inv020_evaluation_engine_raises():
    """INV-020g (behavioral): evaluation.py chứa literal `Engine(` +
    `EvaluationError(` — đánh giá qua engine, fail → raise."""
    src = (AIOS / "harness" / "evaluation" / "evaluation.py").read_text(
        encoding="utf-8")
    assert "Engine(" in src
    assert "EvaluationError(" in src
    assert "raise" in src


@pytest.mark.skipif(not (AIOS / "harness" / "evaluation").is_dir(),
                    reason="harness/evaluation chưa tồn tại (TASK-032)")
def test_inv020_suite_loader_safe_load():
    """INV-020h: suites.py dùng yaml.safe_load (pattern C2-07)."""
    src = (AIOS / "harness" / "evaluation" / "suites.py").read_text(encoding="utf-8")
    assert "yaml.safe_load" in src
    assert "full_load" not in src


# -- harness/benchmark/ (TASK-033 — Benchmark + Regression Gate, INV-021) -----

@pytest.mark.skipif(not (AIOS / "harness" / "benchmark").is_dir(),
                    reason="harness/benchmark chưa tồn tại (TASK-033)")
def test_inv021_benchmark_no_kernel_impl():
    """INV-021a: benchmark/ không import kernel.services.execution|events|
    resource|scheduler + kernel.graph|orchestrator.planning (run_fn injectable)."""
    hits = dir_imports(AIOS / "harness" / "benchmark", [
        "aios_core.kernel.services.execution",
        "aios_core.kernel.services.events",
        "aios_core.kernel.services.resource",
        "aios_core.kernel.services.scheduler",
        "aios_core.kernel.graph",
        "aios_core.orchestrator.planning",
    ])
    assert hits == [], f"INV-021 vi phạm: {hits}"


@pytest.mark.skipif(not (AIOS / "harness" / "benchmark").is_dir(),
                    reason="harness/benchmark chưa tồn tại (TASK-033)")
def test_inv021_gate_blocks_release():
    """INV-021b (behavioral): benchmark.py chứa literal `GateBlockedError(` +
    type `RegressionGate` — gate fail → raise block release."""
    src = (AIOS / "harness" / "benchmark" / "benchmark.py").read_text(encoding="utf-8")
    assert "GateBlockedError(" in src
    assert "RegressionGate" in src
    assert "blocked" in src


@pytest.mark.skipif(not (AIOS / "harness" / "benchmark").is_dir(),
                    reason="harness/benchmark chưa tồn tại (TASK-033)")
def test_inv021_benchmark_no_side_effects():
    """INV-021c: benchmark/ không side effect (AST — pattern INV-020b)."""
    forbidden = ("sqlite3", "httpx", "socket", "requests", "os")
    for py in (AIOS / "harness" / "benchmark").rglob("*.py"):
        src = py.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden, \
                        f"{py.name} side-effect import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden, \
                    f"{py.name} side-effect import: {node.module}"


@pytest.mark.skipif(not (AIOS / "harness" / "benchmark").is_dir(),
                    reason="harness/benchmark chưa tồn tại (TASK-033)")
def test_inv021_persist_before_block():
    """INV-021d: persist TRƯỚC raise GateBlockedError trong verify (evidence-first)."""
    src = (AIOS / "harness" / "benchmark" / "benchmark.py").read_text(encoding="utf-8")
    verify_block = src[src.find("def verify"):src.find("def _persist")]
    assert "_persist" in verify_block
    assert verify_block.index("_persist") < verify_block.index("raise GateBlockedError")


# -- harness/doctor/ (TASK-034 — Doctor & Readiness) --------------------------

@pytest.mark.skipif(not (AIOS / "harness" / "doctor").is_dir(),
                    reason="harness/doctor chưa tồn tại (TASK-034)")
def test_inv017_doctor_no_kernel_impl():
    """doctor/ không import kernel.services (INV-017 Harness Isolation):
    execution|events|resource|scheduler + kernel.graph|orchestrator.planning
    (checks injectable)."""
    hits = dir_imports(AIOS / "harness" / "doctor", [
        "aios_core.kernel.services.execution",
        "aios_core.kernel.services.events",
        "aios_core.kernel.services.resource",
        "aios_core.kernel.services.scheduler",
        "aios_core.kernel.graph",
        "aios_core.orchestrator.planning",
    ])
    assert hits == [], f"INV-017 vi phạm: {hits}"


@pytest.mark.skipif(not (AIOS / "harness" / "doctor").is_dir(),
                    reason="harness/doctor chưa tồn tại (TASK-034)")
def test_inv017_doctor_13_kinds():
    """DoctorKind phải đủ 13 loại (PLAN §H5, INV-017 Harness contract)."""
    src = (AIOS / "harness" / "doctor" / "contracts.py").read_text(encoding="utf-8")
    kinds = [
        "ARCHITECTURE", "RUNTIME", "WORKFLOW", "AGENT", "CAPABILITY", "TOOL",
        "MEMORY", "MODEL", "POLICY", "REGISTRY", "PERFORMANCE", "SECURITY",
        "EVIDENCE",
    ]
    for kind in kinds:
        assert f"{kind} = " in src, f"thiếu DoctorKind.{kind}"
    assert src.count("= \"") >= 13


@pytest.mark.skipif(not (AIOS / "harness" / "doctor").is_dir(),
                    reason="harness/doctor chưa tồn tại (TASK-034)")
def test_inv021_readiness_policy_gate():
    """Hard gate policy (INV-021 Release Gate): readiness.py chứa literal
    `RELEASE BLOCKED` + `policy_violations` (policy violation > 0 → block dù
    overall cao)."""
    src = (AIOS / "harness" / "doctor" / "readiness.py").read_text(encoding="utf-8")
    assert "RELEASE BLOCKED" in src
    assert "policy_violations" in src


@pytest.mark.skipif(not (AIOS / "harness" / "doctor").is_dir(),
                    reason="harness/doctor chưa tồn tại (TASK-034)")
def test_inv018_persist_before_raise():
    """doctor.py + readiness.py: persist TRƯỚC raise (INV-018 Evidence First).
    Dùng rfind — early-return raise (no results) đứng trước persist."""
    for name, err in (("doctor.py", "DoctorError"),
                      ("readiness.py", "ReadinessError")):
        src = (AIOS / "harness" / "doctor" / name).read_text(encoding="utf-8")
        verify_block = src[src.find("def verify"):src.find("def _persist")]
        assert "_persist" in verify_block
        assert verify_block.index("_persist") < \
            verify_block.rfind(f"raise {err}")


def test_inv017_no_harness_in_kernel():
    """kernel/services không import harness (đảo chiều)."""
    hits = dir_imports(AIOS / "kernel" / "services", ["aios_core.harness"])
    assert hits == [], f"INV-017 vi phạm: {hits}"


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


# -- enterprise/ import allow-list (M7 — TASK-035..TASK-042) ------------------
# PLAN §M7 defines INV-022..INV-029 for the Enterprise milestone. These 8
# invariants are enforced below as test_inv022_..test_inv029_* using the
# canonical INV numbering. The M6-H5 Doctor/Readiness tests (TASK-034) are
# labeled with their own M6 invariants instead (INV-017 Harness Isolation /
# INV-018 Evidence First / INV-021 Release Gate — see test_inv017_*
# /test_inv018_*/test_inv021_* in the harness section) so each invariant has
# exactly one owner (no duplicate INV labels).

ENTERPRISE_DIR = AIOS / "enterprise"

_ENTERPRISE_ALLOWED_AIOS = set()  # self-contained: only intra-package imports
_ENTERPRISE_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "enum", "dataclasses", "datetime", "time",
    "uuid", "hashlib", "json", "collections", "abc", "threading",
    "functools", "re", "copy", "math",
}


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_m7_enterprise_import_allowlist():
    """enterprise/ (Control Plane — Enterprise) chỉ import intra-package +
    pydantic/stdlib. KHÔNG import kernel/services/orchestrator/models/memory/
    knowledge/tools/agents/capabilities/workflow/harness — giữ control-plane
    isolation (INV-029) và không God Object."""
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(ENTERPRISE_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.enterprise")}
    bad_aios = aios_mods - _ENTERPRISE_ALLOWED_AIOS
    bad_external = external - _ENTERPRISE_ALLOWED_EXTERNAL
    assert not bad_aios, f"enterprise/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"enterprise/ import ngoài allow-list (external): {bad_external}"


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv022_identity_first_call_site():
    """INV-022 Identity First: identity.py phải reject execution thiếu Principal
    — literal `raise NoPrincipalError` trong require()."""
    src = (ENTERPRISE_DIR / "identity.py").read_text(encoding="utf-8")
    assert "raise NoPrincipalError" in src
    assert "def require(" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv023_tenant_isolation_deny_default():
    """INV-023 Tenant Isolation: tenancy.py deny-by-default — literal
    `CrossTenantAccessDenied` được raise khi scope mismatch."""
    src = (ENTERPRISE_DIR / "tenancy.py").read_text(encoding="utf-8")
    assert "class CrossTenantAccessDenied" in src
    assert "raise CrossTenantAccessDenied" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv024_credential_isolation_scope_check():
    """INV-024 Credential Isolation: security.py kiểm scope trước khi resolve —
    literal `CredentialError` + `_assert_scope`."""
    src = (ENTERPRISE_DIR / "security.py").read_text(encoding="utf-8")
    assert "class CredentialError" in src
    assert "_assert_scope" in src
    assert "raise CredentialError" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv025_resource_fairness_quota_gate():
    """INV-025 Resource Fairness: governance.py deny khi vượt quota (no override)
    — literal `QuotaExceeded` + `check_fairness`."""
    src = (ENTERPRISE_DIR / "governance.py").read_text(encoding="utf-8")
    assert "class QuotaExceeded" in src
    assert "def check_fairness" in src
    assert "raise QuotaExceeded" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv026_distributed_lease_single_active():
    """INV-026 Distributed Execution Safety: scheduler.py một execution chỉ một
    active lease — literal `LeaseError` khi acquire trùng."""
    src = (ENTERPRISE_DIR / "scheduler.py").read_text(encoding="utf-8")
    assert "class LeaseError" in src
    assert "already has active lease" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv027_audit_completeness_chain():
    """INV-027 Audit Completeness: operations.py audit tamper-evident (hash
    chain) + action nhạy cảm phải có evidence — literal `verify_integrity`."""
    src = (ENTERPRISE_DIR / "operations.py").read_text(encoding="utf-8")
    assert "class CentralAuditStore" in src
    assert "def verify_integrity" in src
    assert "previous_hash" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv028_sandbox_boundary_untrusted():
    """INV-028 Sandbox Boundary: security.py untrusted tool phải qua sandbox —
    literal `SandboxBypassError`."""
    src = (ENTERPRISE_DIR / "security.py").read_text(encoding="utf-8")
    assert "class SandboxBypassError" in src
    assert "untrusted tool requires a sandbox profile" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_inv029_control_plane_isolation_router():
    """INV-029 Control Plane Isolation: runtime.py router gate tenant_class —
    literal `tenant_classes` + `ControlPlaneIsolationError` handling."""
    src = (ENTERPRISE_DIR / "runtime.py").read_text(encoding="utf-8")
    assert "tenant_classes" in src
    assert "class ControlPlaneIsolationError" in src


@pytest.mark.skipif(not ENTERPRISE_DIR.is_dir(), reason="enterprise/ chưa tồn tại (M7)")
def test_m7_enterprise_no_god_object():
    """enterprise/ không God Object: facade EnterpriseManager điều phối các
    module con; mỗi module tập trung 1 nhóm (identity/tenancy/runtime/scheduler/
    governance/security/operations/dashboard)."""
    init_src = (ENTERPRISE_DIR / "__init__.py").read_text(encoding="utf-8")
    for module in ("identity", "tenancy", "runtime", "scheduler",
                   "governance", "security", "operations", "dashboard"):
        assert f"from .{module} import" in init_src, f"thiếu import .{module}"


# -- plugins/ import allow-list (M8 — TASK-044) --------------------------------
# PLAN §M8-E2: plugin lifecycle REUSES the skills 10-state machine — only
# skills.base/skills.errors + semver + metadata are allowed aios imports.
# Plugins must NOT touch kernel/services/orchestrator/models/memory/knowledge/
# tools/agents/capabilities/workflow/harness/enterprise (plugin boundary).

PLUGINS_DIR = AIOS / "plugins"

_PLUGINS_ALLOWED_AIOS = {
    "aios_core.skills.base",
    "aios_core.skills.errors",
    "aios_core.semver",
    "aios_core.metadata",
}
_PLUGINS_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "enum", "dataclasses", "datetime", "time",
    "uuid", "hashlib", "json", "collections", "abc", "threading",
    "functools", "re", "copy", "math", "pathlib", "sqlite3", "contextlib",
}


@pytest.mark.skipif(not PLUGINS_DIR.is_dir(), reason="plugins/ chưa tồn tại (M8)")
def test_m8_plugins_import_allowlist():
    """plugins/ chỉ import skills.base/errors + semver + metadata (aios) và
    pydantic/stdlib — không chạm Runtime/Registry/DB/Filesystem (M8-E2)."""
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(PLUGINS_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.plugins")}
    bad_aios = aios_mods - _PLUGINS_ALLOWED_AIOS
    bad_external = external - _PLUGINS_ALLOWED_EXTERNAL
    assert not bad_aios, f"plugins/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"plugins/ import ngoài allow-list (external): {bad_external}"


@pytest.mark.skipif(not PLUGINS_DIR.is_dir(), reason="plugins/ chưa tồn tại (M8)")
def test_m8_plugins_reuse_skills_state_machine():
    """M8-E2: PluginState = SkillState + assert_transition từ skills.base —
    KHÔNG định nghĩa state machine thứ hai."""
    contracts_src = (PLUGINS_DIR / "contracts.py").read_text(encoding="utf-8")
    manager_src = (PLUGINS_DIR / "manager.py").read_text(encoding="utf-8")
    assert "from ..skills.base import SkillState, assert_transition" in contracts_src
    assert "PluginState = SkillState" in contracts_src
    assert "assert_transition(current, op)" in manager_src


@pytest.mark.skipif(not PLUGINS_DIR.is_dir(), reason="plugins/ chưa tồn tại (M8)")
def test_m8_plugins_compat_fail_fast():
    """M8-E2: compat range parse fail-fast + check trong resolve/validate."""
    compat_src = (PLUGINS_DIR / "compat.py").read_text(encoding="utf-8")
    assert "PluginCompatibilityError" in compat_src
    manager_src = (PLUGINS_DIR / "manager.py").read_text(encoding="utf-8")
    assert "check_compatibility" in manager_src
    assert "raise PluginCompatibilityError" in manager_src


@pytest.mark.skipif(not PLUGINS_DIR.is_dir(), reason="plugins/ chưa tồn tại (M8)")
def test_m8_plugins_provides_active_only():
    """M8-E2: provides index chỉ chứa plugin active (ENABLED/RELOADED)."""
    manager_src = (PLUGINS_DIR / "manager.py").read_text(encoding="utf-8")
    assert "SkillState.ENABLED" in manager_src
    assert "SkillState.RELOADED" in manager_src
    assert "def provides(" in manager_src


# -- extension/ import allow-list (M8 — TASK-045) ------------------------------

EXTENSION_DIR = AIOS / "extension"

_EXTENSION_ALLOWED_AIOS = {"aios_core.semver"}
_EXTENSION_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "enum", "dataclasses", "datetime", "time",
    "uuid", "hashlib", "json", "collections", "abc", "threading",
    "functools", "re", "copy", "math",
}


@pytest.mark.skipif(not EXTENSION_DIR.is_dir(), reason="extension/ chưa tồn tại (M8)")
def test_m8_extension_import_allowlist():
    """extension/ (TASK-045) chỉ import semver + pydantic/stdlib — pure
    namespace + matrix, không chạm kernel/plugins/ecosystem."""
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(EXTENSION_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.extension")}
    assert not (aios_mods - _EXTENSION_ALLOWED_AIOS), f"extension/ import ngoài allow-list: {aios_mods - _EXTENSION_ALLOWED_AIOS}"
    assert not (external - _EXTENSION_ALLOWED_EXTERNAL), f"extension/ import ngoài allow-list: {external - _EXTENSION_ALLOWED_EXTERNAL}"


@pytest.mark.skipif(not EXTENSION_DIR.is_dir(), reason="extension/ chưa tồn tại (M8)")
def test_m8_extension_namespace_gate():
    """M8-E3: 4 namespace + gate allowed_namespaces fail-closed."""
    contracts_src = (EXTENSION_DIR / "contracts.py").read_text(encoding="utf-8")
    for value in ("internal", "public", "extension", "experimental"):
        assert value in contracts_src
    matrix_src = (EXTENSION_DIR / "matrix.py").read_text(encoding="utf-8")
    assert "def assert_namespace_allowed" in matrix_src
    assert "raise CompatibilityViolation" in matrix_src


@pytest.mark.skipif(not EXTENSION_DIR.is_dir(), reason="extension/ chưa tồn tại (M8)")
def test_m8_extension_matrix_fail_closed():
    """M8-E3: missing runtime contract → error (fail-closed)."""
    matrix_src = (EXTENSION_DIR / "matrix.py").read_text(encoding="utf-8")
    assert "missing runtime contract" in matrix_src
    assert "ok=not errors" in matrix_src


# -- ecosystem/ import allow-list (M8 — TASK-046..049) --------------------------

ECOSYSTEM_DIR = AIOS / "ecosystem"

_ECOSYSTEM_ALLOWED_AIOS = {"aios_core.semver", "aios_core.metadata"}
_ECOSYSTEM_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "enum", "dataclasses", "datetime", "time",
    "uuid", "hashlib", "json", "collections", "abc", "threading",
    "functools", "re", "copy", "math", "pathlib", "sqlite3", "contextlib", "hmac",
}


@pytest.mark.skipif(not ECOSYSTEM_DIR.is_dir(), reason="ecosystem/ chưa tồn tại (M8)")
def test_m8_ecosystem_import_allowlist():
    """ecosystem/ (TASK-046..049) chỉ import semver/metadata + pydantic/stdlib
    (+ hmac cho marketplace) — độc lập kernel/plugins/extension/harness."""
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(ECOSYSTEM_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.ecosystem")}
    assert not (aios_mods - _ECOSYSTEM_ALLOWED_AIOS), f"ecosystem/ import ngoài allow-list: {aios_mods - _ECOSYSTEM_ALLOWED_AIOS}"
    assert not (external - _ECOSYSTEM_ALLOWED_EXTERNAL), f"ecosystem/ import ngoài allow-list: {external - _ECOSYSTEM_ALLOWED_EXTERNAL}"


@pytest.mark.skipif(not ECOSYSTEM_DIR.is_dir(), reason="ecosystem/ chưa tồn tại (M8)")
def test_m8_ecosystem_registry_pure_index():
    """M8-E4: registry chỉ index/search — không nhúng certification/marketplace."""
    registry_src = (ECOSYSTEM_DIR / "registry.py").read_text(encoding="utf-8")
    assert "class EcosystemRegistry" in registry_src
    assert "from .certification" not in registry_src
    assert "from .marketplace" not in registry_src


@pytest.mark.skipif(not ECOSYSTEM_DIR.is_dir(), reason="ecosystem/ chưa tồn tại (M8)")
def test_m8_ecosystem_certification_harness_gate():
    """M8-E7: certification = Harness gate — fail check → COMMUNITY; security
    fail hard-block CERTIFIED+; evidence bắt buộc."""
    cert_src = (ECOSYSTEM_DIR / "certification.py").read_text(encoding="utf-8")
    assert "CertLevel.COMMUNITY" in cert_src
    assert "CertLevel.VERIFIED" in cert_src
    assert "CertLevel.CERTIFIED" in cert_src
    assert "CertLevel.ENTERPRISE_CERTIFIED" in cert_src
    assert "security_failed" in cert_src
    assert "evidence" in cert_src


@pytest.mark.skipif(not ECOSYSTEM_DIR.is_dir(), reason="ecosystem/ chưa tồn tại (M8)")
def test_m8_ecosystem_marketplace_trust_chain():
    """M8-E6: 9 bước trust chain + raw key không serialize."""
    mp_src = (ECOSYSTEM_DIR / "marketplace.py").read_text(encoding="utf-8")
    for step in ("download", "manifest_validation", "signature_verification",
                 "dependency_check", "permission_analysis", "compatibility_check",
                 "security_scan", "harness_certification", "install"):
        assert step in mp_src, f"thiếu bước trust chain: {step}"
    contracts_src = (ECOSYSTEM_DIR / "contracts.py").read_text(encoding="utf-8")
    assert "signing_key: str" not in contracts_src  # chỉ lưu fingerprint


@pytest.mark.skipif(not ECOSYSTEM_DIR.is_dir(), reason="ecosystem/ chưa tồn tại (M8)")
def test_m8_ecosystem_devkit_deterministic_no_overwrite():
    """M8-E5: scaffold deterministic + no-overwrite + name regex."""
    devkit_src = (ECOSYSTEM_DIR / "devkit.py").read_text(encoding="utf-8")
    assert "refusing to overwrite" in devkit_src
    assert "_NAME_RE" in devkit_src


def test_arch_scan_ignores_future():
    _, aios_mods = collect_imports(SRC_ROOT, "aios_core/orchestrator/planner")
    assert "__future__" not in aios_mods


# -- autonomous/ import allow-list + INV-030..034 (M9 — TASK-050..062) --------
# Autonomy Layer đứng TRÊN Orchestrator (PLAN §M9-31/32): Autonomous →
# Orchestrator → Runtime. autonomous/ KHÔNG chạm tools/agents (Worker Plane —
# act qua injectable, INV-030) và KHÔNG import memory/knowledge trực tiếp
# (World ≠ Memory, TASK-052; memory autonomous là store riêng TASK-057).

AUTONOMOUS_DIR = AIOS / "autonomous"

_AUTONOMOUS_ALLOWED_AIOS = {
    "aios_core.kernel.events",
    "aios_core.kernel.services",
}
_AUTONOMOUS_ALLOWED_EXTERNAL = {
    "pydantic", "typing", "enum", "dataclasses", "datetime", "time",
    "uuid", "hashlib", "json", "collections", "abc", "threading",
    "functools", "re", "copy", "math", "pathlib", "sqlite3", "contextlib",
    "calendar",  # test daily trigger hour (tests/ không nằm trong scan)
}


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_m9_autonomous_import_allowlist():
    """autonomous/ chỉ import kernel.events + kernel.services (aios) — CẤM
    tools/agents/models/memory/knowledge/orchestrator/harness/enterprise/
    capabilities/workflow/contracts kể cả TYPE_CHECKING. Loop rglob."""
    aios_mods: set[str] = set()
    external: set[str] = set()
    for py in sorted(AUTONOMOUS_DIR.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        ext, mods = collect_imports(SRC_ROOT, rel)
        external |= ext
        aios_mods |= {m for m in mods if not m.startswith("aios_core.autonomous")}
    bad_aios = aios_mods - _AUTONOMOUS_ALLOWED_AIOS
    bad_external = external - _AUTONOMOUS_ALLOWED_EXTERNAL
    assert not bad_aios, f"autonomous/ import ngoài allow-list (aios): {bad_aios}"
    assert not bad_external, f"autonomous/ import ngoài allow-list (external): {bad_external}"


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_m9_autonomous_no_worker_plane():
    """Autonomy Layer không chạm Worker Plane: không import tools/agents
    (INV-030 — hành động qua governor + injectable, không tool trực tiếp)."""
    hits = dir_imports(AUTONOMOUS_DIR, ["aios_core.tools", "aios_core.agents"])
    assert hits == [], f"INV-030 vi phạm (autonomous chạm Worker): {hits}"


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_m9_world_not_memory():
    """TASK-052: World State ≠ Memory — world.py không import memory/knowledge."""
    hits = dir_imports(AUTONOMOUS_DIR / "world.py", ["aios_core.memory", "aios_core.knowledge"])
    assert hits == [], f"World ≠ Memory vi phạm: {hits}"


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_inv030_governor_gate_call_site():
    """INV-030 (hard): loop.py PHẢI gọi governor.check_action trước Act —
    literal `governor.check_action(` + guard `decision.decision` STOP."""
    loop_src = (AUTONOMOUS_DIR / "loop.py").read_text(encoding="utf-8")
    assert "governor.check_action(" in loop_src, \
        "INV-030 vi phạm: loop.py thiếu governor.check_action("
    assert "AutonomyDecision.STOP" in loop_src
    # governor.py là nơi duy nhất trả AutonomyDecision — loop không tự quyết
    governor_src = (AUTONOMOUS_DIR / "governor.py").read_text(encoding="utf-8")
    assert "def check_action(" in governor_src
    assert "GovernorDecision(" in governor_src


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_inv031_budget_enforce_literals():
    """INV-031 (hard): governor.py enforce đủ 7 budget limits — literal
    max_steps/max_cost/max_duration_s/max_tool_calls/max_llm_calls/max_retries/
    max_parallel_agents + reason 'budget.' prefix."""
    src = (AUTONOMOUS_DIR / "governor.py").read_text(encoding="utf-8")
    for field in ("max_steps", "max_cost", "max_duration_s", "max_tool_calls",
                  "max_llm_calls", "max_retries", "max_parallel_agents"):
        assert f"self._budget.{field}" in src, f"INV-031 thiếu {field}"
    assert '"budget.' in src


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_inv032_checkpoint_resume_literals():
    """INV-032 (hard): long_horizon.py phải có checkpoint() + resume() +
    persist — execution dài hạn checkpoint/resume được."""
    src = (AUTONOMOUS_DIR / "long_horizon.py").read_text(encoding="utf-8")
    assert "def checkpoint(" in src
    assert "def resume(" in src
    assert "INSERT INTO autonomous_checkpoints" in src
    assert "UPDATE autonomous_sessions" in src


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_inv033_experiment_via_evidence():
    """INV-033 (hard): experimentation.py verdict CHỈ từ evidence — literal
    `evidence` + `_evaluate` + INCONCLUSIVE khi thiếu; deploy chỉ khi ACCEPTED."""
    src = (AUTONOMOUS_DIR / "experimentation.py").read_text(encoding="utf-8")
    assert "self._evaluate(" in src
    assert "INCONCLUSIVE" in src
    assert "if not evidence or metric is None" in src
    assert "ExperimentVerdict.ACCEPTED" in src
    assert "raise ExperimentError" in src


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_inv034_memory_promote_gate():
    """INV-034 (hard): memory.py promote phải double gate — literal
    `not entry.validated` + `_PROMOTE_MIN_CONFIDENCE` + raise
    MemoryPromotionError."""
    src = (AUTONOMOUS_DIR / "memory.py").read_text(encoding="utf-8")
    assert "INV-034" in src
    assert "not entry.validated" in src
    assert "_PROMOTE_MIN_CONFIDENCE" in src
    assert "raise MemoryPromotionError" in src


@pytest.mark.skipif(not AUTONOMOUS_DIR.is_dir(), reason="autonomous/ chưa tồn tại (M9)")
def test_m9_autonomous_no_god_object():
    """autonomous/ không God Object: facade AutonomyManager điều phối; mỗi
    module không định nghĩa execute( (chỉ loop chạy pipeline); contracts leaf."""
    init_src = (AUTONOMOUS_DIR / "__init__.py").read_text(encoding="utf-8")
    for module in ("goal", "planner", "world", "loop", "governor", "recovery",
                   "long_horizon", "memory", "stuck", "experimentation",
                   "evaluation", "multi_agent", "scheduler"):
        assert f"from .{module} import" in init_src, f"facade thiếu .{module}"
    # goal.py execute() = lifecycle transition (EXECUTING) — không phải
    # execution pipeline; các module khác không định nghĩa execute(
    for name in ("planner.py", "world.py", "governor.py", "recovery.py",
                 "long_horizon.py", "memory.py", "stuck.py", "experimentation.py",
                 "evaluation.py", "multi_agent.py", "scheduler.py"):
        src = (AUTONOMOUS_DIR / name).read_text(encoding="utf-8")
        assert "def execute(" not in src, f"{name} không được định nghĩa execute"
    contracts_src = (AUTONOMOUS_DIR / "contracts.py").read_text(encoding="utf-8")
    tree = ast.parse(contracts_src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            assert not mod.startswith("aios_core"), \
                f"contracts.py không được import aios_core: {mod}"
