"""TASK-065 — Runtime Hardening: Failure Matrix 12 loại (M10-F2)."""

from __future__ import annotations

import sqlite3
import time

import pytest

from aios_core.config import ResourcesSettings
from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.kernel.hardening import (
    FAILURE_KINDS,
    FailureMatrix,
    FailureScenario,
    HardeningRunner,
    ScenarioStatus,
)
from aios_core.kernel.services import (
    EventService,
    ExecutionService,
    PolicyService,
    ResourceService,
    StateService,
)
from aios_core.kernel.execution_plan import ExecutionPlanBuilder
from aios_core.models import MockModel, ModelRegistry


def make_plan(nodes=None, **overrides):
    data = {
        "id": "harden-plan",
        "nodes": nodes or [
            {"id": "n1", "type": "task", "name": "first"},
            {"id": "n2", "type": "task", "name": "second", "depends_on": ["n1"]},
        ],
        "required_permissions": ["filesystem"],
    }
    data.update(overrides)
    return ExecutionPlanBuilder.from_dict(data)


def make_execution(tmp_path):
    bus = EventBus()
    return ExecutionService(
        EventService(bus, tmp_path / "audit.db"),
        PolicyService(bus),
        StateService(),
        ResourceService(),
    )


# ---------------------------------------------------------------------------
# AC1/AC7: 12 FailureKind + validation
# ---------------------------------------------------------------------------

def test_matrix_has_12_kinds():
    assert set(FAILURE_KINDS) == {
        "model", "tool", "agent", "process", "network", "db", "plugin",
        "worker_timeout", "resource", "memory_corruption", "checkpoint",
        "event_consumer",
    }


def test_duplicate_scenario_raises():
    m = FailureMatrix()
    sc = FailureScenario(
        scenario_id="s1", kind="model", target="t",
        fault_fn=lambda c: None, detect_fn=lambda c: True,
        contain_fn=lambda c: True, recover_fn=lambda c: True,
        resume_fn=lambda c: True,
    )
    m.register(sc)
    with pytest.raises(ValueError):
        m.register(sc)


def test_unknown_kind_raises():
    m = FailureMatrix()
    with pytest.raises(ValueError):
        m.register(FailureScenario(
            scenario_id="x", kind="bogus", target="t",
            fault_fn=lambda c: None, detect_fn=lambda c: True,
            contain_fn=lambda c: True, recover_fn=lambda c: True,
            resume_fn=lambda c: True,
        ))


def _ok_scenario(sid, kind):
    return FailureScenario(
        scenario_id=sid, kind=kind, target="t",
        fault_fn=lambda c: None, detect_fn=lambda c: True,
        contain_fn=lambda c: True, recover_fn=lambda c: True,
        resume_fn=lambda c: True,
    )


# ---------------------------------------------------------------------------
# AC4/AC5: runner + outcome
# ---------------------------------------------------------------------------

def test_runner_catches_scenario_failure():
    sc = FailureScenario(
        scenario_id="boom", kind="model", target="t",
        fault_fn=lambda c: (_ for _ in ()).throw(RuntimeError("fault crashed")),
        detect_fn=lambda c: True, contain_fn=lambda c: True,
        recover_fn=lambda c: True, resume_fn=lambda c: True,
    )
    runner = HardeningRunner(FailureMatrix([sc]))
    out = runner.run(sc)
    assert out.status == ScenarioStatus.FAIL
    assert "RuntimeError" in out.error


def test_runner_outcome_fields():
    runner = HardeningRunner(FailureMatrix([_ok_scenario("s", "model")]))
    out = runner.run_all()[0]
    assert out.status == ScenarioStatus.PASS
    assert out.detect and out.contain and out.recovered and out.resumed


# ---------------------------------------------------------------------------
# 12 scenarios thật — detect → contain → recover → resume
# ---------------------------------------------------------------------------

def test_scenario_model_failure():
    """Model chết: chat raise → contain (model khỏe chạy) → re-register → chạy lại."""
    from aios_core.models.base import ChatMessage

    registry = ModelRegistry(default_name="mock")
    registry.register("mock", MockModel(echo=True))
    registry.register("broken", MockModel(raise_error=RuntimeError("model died")))
    msg = [ChatMessage(role="user", content="hi")]

    def fault(ctx):
        pass

    def detect(ctx):
        try:
            registry.get("broken").chat(msg)
            return False
        except RuntimeError:
            return True

    def contain(ctx):
        return "mock" in registry.list() and registry.get("mock").chat(msg) is not None

    def recover(ctx):
        registry.register("broken", MockModel(echo=True))
        return True

    def resume(ctx):
        return registry.get("broken").chat(msg) is not None

    sc = FailureScenario("model", "model", "ModelRegistry", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_tool_failure():
    """Tool chết: run raise → contain (tool khác chạy) → replace → run lại."""
    from aios_core.tools.base import Tool, ToolContext, ToolInput, ToolOutput

    class FlakyTool(Tool):
        tool_type = "shell"
        required_scopes = ("filesystem",)

        def __init__(self, broken=False):
            super().__init__()
            self.broken = broken

        def _describe(self) -> str:
            return "flaky tool"

        def _run(self, input, context):
            if self.broken:
                raise RuntimeError("tool died")
            return ToolOutput(ok=True, result="ok")

    broken = FlakyTool(broken=True)
    good_other = FlakyTool(broken=False)

    def fault(ctx):
        ctx["tool"] = broken

    def detect(ctx):
        out = ctx["tool"].run(ToolInput(tool_id=broken.id),
                               ToolContext(permission_gate=lambda s: True))
        return not out.ok  # run() bắt exception → ToolOutput(ok=False)

    def contain(ctx):
        return good_other.run(ToolInput(tool_id=good_other.id),
                              ToolContext(permission_gate=lambda s: True)).ok

    def recover(ctx):
        ctx["tool"] = FlakyTool(broken=False)
        return True

    def resume(ctx):
        return ctx["tool"].run(ToolInput(tool_id=ctx["tool"].id),
                                ToolContext(permission_gate=lambda s: True)).ok

    sc = FailureScenario("tool", "tool", "Tool", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_agent_failure():
    """Agent chết: handle trả error (không crash) → contain (agent khác ok) → fallback."""
    from aios_core.agents.base import Assistant, AssistantRequest, AssistantResponse
    from aios_core.agents.registry import AssistantRegistry

    class Broken(Assistant):
        @property
        def name(self):
            return "broken"

        @property
        def description(self):
            return "broken"

        @property
        def intent(self):
            return "broken"

        def _process(self, request):
            raise RuntimeError("agent died")

    class General(Assistant):
        @property
        def name(self):
            return "general"

        @property
        def description(self):
            return "general"

        @property
        def intent(self):
            return "general"

        def _process(self, request):
            return AssistantResponse(text="general ok")

    registry = AssistantRegistry()
    registry.register(Broken())
    registry.register(General())

    def fault(ctx):
        pass

    def detect(ctx):
        resp = registry.get("broken").handle(AssistantRequest(text="x"))
        return resp.status == "error"

    def contain(ctx):
        return registry.get("general").handle(AssistantRequest(text="x")).text == "general ok"

    def recover(ctx):
        return True  # fallback đã sẵn sàng

    def resume(ctx):
        return registry.get("general") is not None

    sc = FailureScenario("agent", "agent", "Assistant", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_process_crash_resume(tmp_path):
    """Process chết: crash giữa node → resume từ snapshot — node done KHÔNG chạy lại."""
    svc = make_execution(tmp_path)
    calls = []

    def fault(ctx):
        def runner(n, r):
            calls.append(n.id)
            if n.id == "n2":
                raise RuntimeError("process died")
            return f"ok:{n.id}"

        ctx["result"] = svc.execute(make_plan(), {"n1": runner, "n2": runner})

    def detect(ctx):
        return ctx["result"].status.value == "failed"

    def contain(ctx):
        other = svc.execute(
            make_plan(id="other"), {"n1": lambda n, r: "a", "n2": lambda n, r: "b"}
        )
        return other.status.value == "completed"

    def recover(ctx):
        return True  # state snapshot còn nguyên

    def resume(ctx):
        before = len(calls)
        result = svc.resume("harden-plan", {"n1": lambda n, r: calls.append("n1-again") or "x",
                                            "n2": lambda n, r: calls.append("n2-again") or "y"})
        return result.status.value == "completed" and calls[before:] == ["n2-again"]

    sc = FailureScenario("process", "process", "ExecutionService", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_network_failure():
    """Network mất: REST tool raise ConnectionError → contain → phục hồi → retry."""
    from aios_core.tools.base import Tool, ToolContext, ToolInput, ToolOutput

    class NetTool(Tool):
        tool_type = "rest"
        required_scopes = ("network",)

        def __init__(self):
            super().__init__()
            self.network_down = False

        def _describe(self) -> str:
            return "rest tool"

        def _run(self, input, context):
            if self.network_down:
                raise ConnectionError("network down")
            return ToolOutput(ok=True, result="data")

    tool = NetTool()

    def fault(ctx):
        tool.network_down = True

    def detect(ctx):
        out = tool.run(ToolInput(tool_id=tool.id),
                       ToolContext(permission_gate=lambda s: True))
        return not out.ok  # error message: "tool.rest failed: network down"

    def contain(ctx):
        return True  # tool object vẫn tồn tại, không crash registry

    def recover(ctx):
        tool.network_down = False
        return True

    def resume(ctx):
        return tool.run(ToolInput(tool_id=tool.id),
                        ToolContext(permission_gate=lambda s: True)).ok

    sc = FailureScenario("network", "network", "REST tool", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_db_lost(tmp_path):
    """Database mất: file bị xóa → detect (no such table) → recreate → query OK."""
    db = tmp_path / "gone.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (x TEXT)")
    conn.execute("INSERT INTO t VALUES ('v1')")
    conn.commit()

    def fault(ctx):
        conn.close()
        db.unlink()

    def detect(ctx):
        try:
            c2 = sqlite3.connect(db)
            c2.execute("SELECT x FROM t")
            c2.close()
            return False
        except sqlite3.Error:
            return True

    def contain(ctx):
        return True  # process không crash

    def recover(ctx):
        conn2 = sqlite3.connect(db)
        conn2.execute("CREATE TABLE t (x TEXT)")
        conn2.execute("INSERT INTO t VALUES ('v2')")
        conn2.commit()
        conn2.close()
        return True

    def resume(ctx):
        c3 = sqlite3.connect(db)
        row = c3.execute("SELECT x FROM t").fetchone()
        c3.close()
        return row == ("v2",)

    sc = FailureScenario("db", "db", "SQLite", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_plugin_failure(tmp_path):
    """Plugin lỗi: manifest invalid → detect → contain (registry không crash) → không cài."""
    from aios_core.plugins.contracts import PluginManifest
    from aios_core.plugins.registry import PluginRegistry

    registry = PluginRegistry(tmp_path / "plugins.db")
    invalid = {"id": "bad.plugin", "version": "not-a-semver",
               "aios": {"min": "1.0.0"}, "provides": []}
    valid = {"id": "good.plugin", "name": "good", "version": "1.0.0",
             "aios": {"min": "1.0.0"}, "provides": []}

    def fault(ctx):
        pass

    def detect(ctx):
        try:
            PluginManifest.model_validate(invalid)
            return False
        except Exception:
            return True

    def contain(ctx):
        return registry.list() == []  # registry không crash, không cài plugin lỗi

    def recover(ctx):
        return True

    def resume(ctx):
        return PluginManifest.model_validate(valid).id == "good.plugin"

    sc = FailureScenario("plugin", "plugin", "PluginRegistry", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_worker_timeout(tmp_path):
    """Worker timeout: runner vượt timeout → FAILED → execution khác vẫn OK."""
    svc = make_execution(tmp_path)
    plan = make_plan(id="slow-plan", nodes=[
        {"id": "slow", "type": "task", "name": "slow", "timeout_s": 0.01},
    ])

    def fault(ctx):
        ctx["result"] = svc.execute(plan, {"slow": lambda n, r: time.sleep(0.2) or "done"})

    def detect(ctx):
        return ctx["result"].status.value == "failed"

    def contain(ctx):
        other = svc.execute(
            make_plan(id="other2"), {"n1": lambda n, r: "a", "n2": lambda n, r: "b"}
        )
        return other.status.value == "completed"

    def recover(ctx):
        return True

    def resume(ctx):
        fast = svc.execute(
            make_plan(id="fast"), {"n1": lambda n, r: "x", "n2": lambda n, r: "y"}
        )
        return fast.status.value == "completed"

    sc = FailureScenario("worker_timeout", "worker_timeout", "ExecutionService",
                         fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_resource_exhausted(tmp_path):
    """Resource hết: slot thứ 2 fail → queue → release → acquire thành công."""
    resources = ResourceService(ResourcesSettings(max_concurrent=1))

    def fault(ctx):
        assert resources.acquire_slot() is True

    def detect(ctx):
        return resources.acquire_slot() is False

    def contain(ctx):
        return resources.pending() >= 0  # queue không crash

    def recover(ctx):
        resources.release_slot()
        return True

    def resume(ctx):
        return resources.acquire_slot() is True

    sc = FailureScenario("resource", "resource", "ResourceService", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_memory_corruption(tmp_path):
    """Memory corruption: bảng messages hỏng → detect → recreate → đọc lại OK."""
    from aios_core.memory.conversation import ConversationMemory

    db = tmp_path / "mem.db"
    mem = ConversationMemory(str(db))
    sid = mem.create_conversation("s1")
    mem.add_message(sid, "user", "hello")

    def fault(ctx):
        raw = sqlite3.connect(db)
        raw.execute("DROP TABLE messages")
        raw.commit()
        raw.close()

    def detect(ctx):
        try:
            # instance cũ — bảng đã mất → raise (instance mới sẽ recreate bảng)
            mem.get_messages(sid)
            return False
        except sqlite3.Error:
            return True

    def contain(ctx):
        return True

    def recover(ctx):
        m3 = ConversationMemory(str(db))  # recreate bảng
        return True

    def resume(ctx):
        m4 = ConversationMemory(str(db))
        return m4.get_messages(sid) == []  # đọc OK, dữ liệu cũ mất nhưng không crash

    sc = FailureScenario("memory_corruption", "memory_corruption", "ConversationMemory",
                         fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_checkpoint_failure(tmp_path):
    """Checkpoint lỗi: snapshot raise → execution FAILED rõ → khôi phục → chạy tiếp."""
    class FlakyState(StateService):
        def __init__(self):
            super().__init__()
            self.fail_snapshot = False

        def snapshot(self, execution_id):
            if self.fail_snapshot:
                raise OSError("disk full")
            return super().snapshot(execution_id)

    state = FlakyState()
    svc = ExecutionService(
        EventService(EventBus(), tmp_path / "audit.db"),
        PolicyService(EventBus()),
        state,
        ResourceService(),
    )

    def fault(ctx):
        state.fail_snapshot = True

    def detect(ctx):
        result = svc.execute(make_plan(), {"n1": lambda n, r: "a", "n2": lambda n, r: "b"})
        return result.status.value == "failed" and "disk full" in result.reason

    def contain(ctx):
        return True  # chỉ snapshot lỗi — service vẫn dùng được

    def recover(ctx):
        state.fail_snapshot = False
        return True

    def resume(ctx):
        result = svc.execute(make_plan(), {"n1": lambda n, r: "a", "n2": lambda n, r: "b"})
        return result.status.value == "completed"

    sc = FailureScenario("checkpoint", "checkpoint", "StateService", fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


def test_scenario_event_consumer_failure():
    """Event consumer chết: handler raise → bus không crash → re-subscribe → nhận event mới."""
    bus = EventBus()
    received = []

    def fault(ctx):
        def bad_handler(event):
            raise RuntimeError("consumer died")

        bus.subscribe(EventType.WORKFLOW_STARTED, bad_handler)

    def detect(ctx):
        bus.publish(Event(type=EventType.WORKFLOW_STARTED, payload={}, source="t"))
        return True

    def contain(ctx):
        bus.subscribe(EventType.WORKFLOW_COMPLETED, lambda e: received.append(e))
        bus.publish(Event(type=EventType.WORKFLOW_COMPLETED, payload={}, source="t"))
        return len(received) == 1

    def recover(ctx):
        return True  # handler mới subscribe hoạt động

    def resume(ctx):
        bus.publish(Event(type=EventType.WORKFLOW_COMPLETED, payload={}, source="t"))
        return len(received) == 2

    sc = FailureScenario("event_consumer", "event_consumer", "EventBus",
                         fault, detect, contain, recover, resume)
    out = HardeningRunner(FailureMatrix([sc])).run(sc)
    assert out.status == ScenarioStatus.PASS, out.error


# ---------------------------------------------------------------------------
# AC3: matrix phủ 12 kind (12 scenario end-to-end có test riêng)
# ---------------------------------------------------------------------------

def test_matrix_covers_12_kinds():
    matrix = FailureMatrix([_ok_scenario(f"a{i}", k) for i, k in enumerate(FAILURE_KINDS)])
    assert len(matrix.kinds_covered()) == 12
