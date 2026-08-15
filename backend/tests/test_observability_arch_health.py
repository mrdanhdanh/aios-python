"""ArchitectureHealth tests (TASK-021) — scans tmp dirs (never touches src)."""

from pathlib import Path

from aios_core.observability.arch_health import ArchitectureHealth


def _write(pkg: Path, rel: str, content: str) -> None:
    path = pkg / (rel.replace(".", "/") + ".py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_healthy_when_no_violations(tmp_path):
    pkg = tmp_path / "src"
    _write(pkg, "workflow/definition", "x = 1\n")
    _write(pkg, "orchestrator/planner", "y = 2\n")
    _write(pkg, "agents/general", "z = 3\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert report.healthy
    assert report.violations == ()


def test_layer_violation_detected(tmp_path):
    pkg = tmp_path / "src"
    _write(
        pkg,
        "agents/evil",
        "from aios_core.kernel.services import ExecutionService\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    kinds = {v.kind for v in report.violations}
    assert "layer" in kinds
    assert any("kernel.services" in v.message for v in report.violations)


def test_workflow_engine_violation(tmp_path):
    pkg = tmp_path / "src"
    _write(pkg, "workflow/evil", "import langgraph\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any("langgraph" in v.message for v in report.violations)


def test_contract_violation_detected(tmp_path):
    pkg = tmp_path / "src"
    _write(pkg, "contracts/evil", "from aios_core.kernel.events import EventBus\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(v.kind == "contract" for v in report.violations)


def test_orchestrator_planner_exempt(tmp_path):
    pkg = tmp_path / "src"
    _write(pkg, "orchestrator/planner", "from aios_core.models.base import BaseModel\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert report.healthy


def test_policy_check_against_real_src():
    """Policy check chạy trên src thật (execution.py phải có self._policy.evaluate)."""
    from aios_core.observability.arch_scan import SRC_ROOT

    report = ArchitectureHealth().scan(package_dir=SRC_ROOT)
    policy_violations = [v for v in report.violations if v.kind == "policy"]
    assert policy_violations == [], f"INV-007 vi phạm: {policy_violations}"


def test_policy_missing_detected(tmp_path):
    pkg = tmp_path / "src"
    _write(
        pkg,
        "aios_core/kernel/services/execution",
        "x = 1\n",  # không có self._policy.evaluate
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert any(v.kind == "policy" for v in report.violations)


def test_nested_aios_core_layout_scans_layer_violations(tmp_path):
    """Regresi (review M4): scanner phải chạy trên layout thật backend/src/aios_core.

    Trước fix, scan() dùng target = package_dir / sub → trên cây thật (agents/
    nằm dưới aios_core/, không phải dưới package_dir) mọi layer/contract check
    bị skip silently. Test này giả lập layout lồng nhau và chứng minh violation
    ở tầng sâu vẫn bị phát hiện.
    """
    pkg = tmp_path / "src"                       # ~ backend/src
    aios = pkg / "aios_core"                    # ~ backend/src/aios_core
    _write(
        aios,
        "agents/evil",
        "from aios_core.kernel.services import ExecutionService\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    kinds = {v.kind for v in report.violations}
    assert "layer" in kinds
    assert any("kernel.services" in v.message for v in report.violations)


def test_nested_aios_core_layout_policy_check(tmp_path):
    """Regresi: policy check cũng chạy được trên layout lồng nhau."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "kernel/services/execution",
        "x = 1\n",  # thiếu self._policy.evaluate
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert any(v.kind == "policy" for v in report.violations)


# ---------------------------------------------------------------------------
# M5 — Core Intelligence: runtime scanner must cover INV-011..016 (PLAN §M5
# yêu cầu "observability đầy đủ"). Các rule layer cho memory/context/models.
# router/orchestrator.planning/kernel.graph/kernel.scheduler được thêm cùng
# đợt review M5; test này khoá vào không cho quay lại trạng thái "scanner bỏ
# qua M5" (cf. M4 F1 silent-skip).
# ---------------------------------------------------------------------------

def test_m5_real_src_healthy():
    """INV-011..016: scanner chạy trên src thật phải xanh (gồm M5 packages)."""
    from aios_core.observability.arch_scan import SRC_ROOT

    report = ArchitectureHealth().scan(package_dir=SRC_ROOT)
    assert report.healthy, f"M5 scanner vi phạm: {report.violations}"


def test_m5_memory_isolation_fires(tmp_path):
    """memory/ không được import orchestrator/agents/tools (INV-011)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(aios, "memory/evil", "from aios_core.orchestrator.planner import x\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(v.kind == "layer" and "memory" in v.module for v in report.violations)


def test_m5_context_no_knowledge_fires(tmp_path):
    """context/ (intelligence) không import knowledge/models (INV-012)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(aios, "context/evil", "from aios_core.knowledge.graph import y\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(v.kind == "layer" and "context" in v.module for v in report.violations)


def test_m5_planning_no_models_fires(tmp_path):
    """orchestrator/planning không import models/knowledge (INV-014)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(aios, "orchestrator/planning/evil", "from aios_core.models.base import z\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "orchestrator/planning" in v.module
        for v in report.violations
    )


def test_m5_graph_no_orchestrator_fires(tmp_path):
    """kernel/graph không import orchestrator/models (INV-015)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(aios, "kernel/graph/evil", "from aios_core.orchestrator.planner import w\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "kernel/graph" in v.module
        for v in report.violations
    )


def test_m5_scheduler_no_orchestrator_fires(tmp_path):
    """kernel/scheduler không import orchestrator/models (INV-016)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(aios, "kernel/scheduler/evil", "from aios_core.orchestrator.planner import w\n")
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "kernel/scheduler" in v.module
        for v in report.violations
    )


# ---------------------------------------------------------------------------
# M6 — AIOS Harness: runtime scanner must cover INV-017..022 (PLAN §M6 yêu cầu
# "observability đầy đủ"). Rule layer cho harness/ được thêm cùng đợt review M6;
# test này khoá vào không cho quay lại trạng thái "scanner bỏ qua M6" (cf. M5 F1).
# ---------------------------------------------------------------------------

def test_m6_real_src_healthy():
    """INV-017..021: scanner chạy trên src thật phải xanh (gồm harness)."""
    from aios_core.observability.arch_scan import SRC_ROOT

    report = ArchitectureHealth().scan(package_dir=SRC_ROOT)
    harness_violations = [v for v in report.violations if "harness" in v.module]
    assert harness_violations == [], f"M6 scanner vi phạm: {harness_violations}"


def test_m6_harness_isolation_fires(tmp_path):
    """harness/ không được import kernel.services.execution (INV-017)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "harness/evil",
        "from aios_core.kernel.services.execution import ExecutionService\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "harness" in v.module
        for v in report.violations
    )
    assert any("kernel.services" in v.message for v in report.violations)


def test_m6_harness_no_control_plane_fires(tmp_path):
    """harness/ không được import orchestrator/models/memory (INV-017/018)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "harness/evaluation/evil",
        "from aios_core.orchestrator.planner import x\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "harness" in v.module
        for v in report.violations
    )


# ---------------------------------------------------------------------------
# M7 — Enterprise: runtime scanner must cover INV-022..029 (PLAN §M7 yêu cầu
# "observability đầy đủ"). Rule layer cho enterprise/ được thêm cùng đợt review
# M7; test này khoá vào không cho quay lại trạng thái "scanner bỏ qua M7"
# (cf. M5 F1 silent-skip).
# ---------------------------------------------------------------------------

def test_m7_real_src_healthy():
    """INV-022..029: scanner chạy trên src thật phải xanh (gồm enterprise)."""
    from aios_core.observability.arch_scan import SRC_ROOT

    report = ArchitectureHealth().scan(package_dir=SRC_ROOT)
    ent_violations = [v for v in report.violations if "enterprise" in v.module]
    assert ent_violations == [], f"M7 scanner vi phạm: {ent_violations}"


def test_m7_enterprise_isolation_fires(tmp_path):
    """enterprise/ không được import kernel.services.execution (INV-029)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "enterprise/evil",
        "from aios_core.kernel.services.execution import ExecutionService\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "enterprise" in v.module
        for v in report.violations
    )
    assert any("kernel.services" in v.message for v in report.violations)


def test_m7_enterprise_no_orchestrator_fires(tmp_path):
    """enterprise/ không được import orchestrator/models (INV-022..029)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "enterprise/evil",
        "from aios_core.orchestrator.planner import x\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "enterprise" in v.module
        for v in report.violations
    )


# ---------------------------------------------------------------------------
# M9 — Autonomous: runtime scanner must cover INV-030..034 (PLAN §M9 yêu cầu
# "observability đầy đủ"). Rule layer cho autonomous/ được thêm cùng đợt review
# M9; test này khoá vào không cho quay lại trạng thái "scanner bỏ qua M9"
# (cf. M5 F1 silent-skip — cùng pattern M7).
# ---------------------------------------------------------------------------

def test_m9_real_src_healthy():
    """INV-030..034: scanner chạy trên src thật phải xanh (gồm autonomous)."""
    from aios_core.observability.arch_scan import SRC_ROOT

    report = ArchitectureHealth().scan(package_dir=SRC_ROOT)
    aut_violations = [v for v in report.violations if "autonomous" in v.module]
    assert aut_violations == [], f"M9 scanner vi phạm: {aut_violations}"


def test_m9_autonomous_isolation_fires(tmp_path):
    """autonomous/ không được import kernel.services.execution (INV-030)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "autonomous/evil",
        "from aios_core.kernel.services.execution import ExecutionService\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "autonomous" in v.module
        for v in report.violations
    )
    assert any("kernel.services" in v.message for v in report.violations)


def test_m9_autonomous_no_worker_plane_fires(tmp_path):
    """autonomous/ không được import agents/tools (INV-030 — Worker Plane)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "autonomous/evil",
        "from aios_core.agents.base import BaseAgent\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "autonomous" in v.module
        for v in report.violations
    )


# ---------------------------------------------------------------------------
# M8 — Ecosystem: runtime scanner must cover plugins/ extension/ ecosystem/
# (PLAN §M8 yêu cầu "observability đầy đủ" cho ecosystem boundary). Rule layer
# cho 3 package được thêm cùng đợt review M8; test này khoá vào không cho quay
# lại trạng thái "scanner bỏ qua M8" (cf. M5 F1 silent-skip).
# ---------------------------------------------------------------------------

def test_m8_real_src_healthy():
    """M8: scanner chạy trên src thật phải xanh (gồm plugins/extension/ecosystem)."""
    from aios_core.observability.arch_scan import SRC_ROOT

    report = ArchitectureHealth().scan(package_dir=SRC_ROOT)
    m8_violations = [
        v for v in report.violations
        if v.module.startswith("plugins")
        or v.module.startswith("extension")
        or v.module.startswith("ecosystem")
    ]
    assert m8_violations == [], f"M8 scanner vi phạm: {m8_violations}"


def test_m8_plugins_isolation_fires(tmp_path):
    """plugins/ không được import agents/tools (M8-E2 allow-list)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "plugins/evil",
        "from aios_core.agents.general import GeneralAgent\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "plugins" in v.module
        for v in report.violations
    )


def test_m8_extension_isolation_fires(tmp_path):
    """extension/ không được import orchestrator/kernel (M8-E3 allow-list)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "extension/evil",
        "from aios_core.orchestrator.planner import x\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "extension" in v.module
        for v in report.violations
    )


def test_m8_ecosystem_isolation_fires(tmp_path):
    """ecosystem/ không được import kernel.services.execution (M8 allow-list)."""
    pkg = tmp_path / "src"
    aios = pkg / "aios_core"
    _write(
        aios,
        "ecosystem/evil",
        "from aios_core.kernel.services.execution import ExecutionService\n",
    )
    report = ArchitectureHealth().scan(package_dir=pkg)
    assert not report.healthy
    assert any(
        v.kind == "layer" and "ecosystem" in v.module
        for v in report.violations
    )
