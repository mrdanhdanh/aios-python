"""Workflow CLI tests (main() direct — offline deterministic)."""

import pytest

from aios_core.workflow.cli import main


@pytest.fixture
def workflow_yaml(tmp_path):
    path = tmp_path / "wf.yaml"
    path.write_text(
        "name: cli-wf\nversion: 0.1.0\n"
        "nodes:\n"
        "  - id: a\n    type: task\n    name: A\n"
        "  - id: b\n    type: task\n    name: B\n    depends_on: [a]\n",
        encoding="utf-8",
    )
    return str(path)


def test_run_simulate(workflow_yaml, capsys):
    code = main(["run", workflow_yaml, "--simulate"])
    out = capsys.readouterr().out
    assert code == 0
    assert "cli-wf" in out
    assert "completed" in out


def test_simulate_required(workflow_yaml):
    with pytest.raises(SystemExit) as exc:
        main(["run", workflow_yaml])
    assert exc.value.code == 2  # argparse error


def test_run_failing_node(workflow_yaml, tmp_path, capsys, monkeypatch):
    # A workflow whose node runner fails → exit code 1
    from aios_core.workflow import cli as cli_module

    class FakeResult:
        status = type("S", (), {"value": "failed"})()
        reason = "node a failed: boom"
        node_results = {}

    monkeypatch.setattr(cli_module, "_run_simulate", lambda f: (print("failed"), 1)[1])
    code = cli_module.main(["run", workflow_yaml, "--simulate"])
    assert code == 1


def test_simulate_prints_reason(workflow_yaml, capsys, monkeypatch):
    # When execution yields a reason, the CLI must surface it (covers reason branch).
    # Patch the DI container's resolve so ExecutionService is the fake one.
    from aios_core.kernel import services as services_module
    from aios_core.container import Container as _Container

    class FakeStatus:
        value = "completed"

    class FakeResult:
        status = FakeStatus()
        reason = "best-effort warning"
        node_results = {}

    class FakeExecutionService:
        def __init__(self, *args, **kwargs):
            pass

        def execute(self, plan, runner):
            return FakeResult()

    real_exec = services_module.ExecutionService
    orig_resolve = _Container.resolve

    def _fake_resolve(self, interface):
        if interface is real_exec:
            return FakeExecutionService()
        return orig_resolve(self, interface)

    monkeypatch.setattr(_Container, "resolve", _fake_resolve)
    from aios_core.workflow import cli as cli_module

    code = cli_module.main(["run", workflow_yaml, "--simulate"])
    out = capsys.readouterr().out
    assert code == 0
    assert "best-effort warning" in out


def test_doctor_runs(capsys):
    from aios_core.workflow import cli as cli_module

    code = cli_module.main(["doctor"])
    out = capsys.readouterr().out
    assert code == 0
    assert '"kernel": "ok"' in out


def test_catalog_list_empty(capsys):
    from aios_core.workflow import cli as cli_module

    code = cli_module.main(["catalog", "list"])
    out = capsys.readouterr().out
    assert code == 0
    assert "<empty>" in out


def test_workflow_validate_valid(workflow_yaml, capsys):
    from aios_core.workflow import cli as cli_module

    code = cli_module.main(["workflow", "validate", workflow_yaml])
    out = capsys.readouterr().out
    assert code == 0
    assert "VALID" in out


def test_workflow_validate_missing_file(capsys):
    from aios_core.workflow import cli as cli_module

    code = cli_module.main(["workflow", "validate", "does-not-exist.yaml"])
    assert code == 1
    assert "INVALID" in capsys.readouterr().out


def test_contract_validate_valid(tmp_path, capsys):
    from aios_core.workflow import cli as cli_module

    contract_file = tmp_path / "c.json"
    contract_file.write_text(
        '{"id": "c1", "name": "c1", "version": "1.0.0", "author": "o", '
        '"license": "MIT", "description": "d", "contract_version": "1.0.0", '
        '"schema_version": "1.0.0"}',
        encoding="utf-8",
    )
    code = cli_module.main(["contract", "validate", str(contract_file)])
    out = capsys.readouterr().out
    assert code == 0
    assert "VALID" in out


def test_no_direct_executionservice_in_cli():
    # AC2 gate: cli must not construct ExecutionService directly in its path.
    import inspect

    from aios_core.workflow import cli as cli_module

    src = inspect.getsource(cli_module)
    assert "ExecutionService(" not in src, "cli must resolve services via DI, not construct directly"
