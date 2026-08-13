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
