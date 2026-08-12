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
    from aios_core.workflow import cli as cli_module
    from aios_core.kernel import services as services_module

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

    monkeypatch.setattr(services_module, "ExecutionService", FakeExecutionService)
    code = cli_module.main(["run", workflow_yaml, "--simulate"])
    out = capsys.readouterr().out
    assert code == 0
    assert "best-effort warning" in out
