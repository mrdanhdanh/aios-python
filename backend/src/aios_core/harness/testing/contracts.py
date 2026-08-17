"""Test & Simulation contracts (TASK-031, H3): scenario, fault, outcome."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class TestLevel(str, Enum):
    """12 test levels (PLAN §H3) — harness điều phối, không thay pytest/vitest."""

    UNIT = "unit"
    CONTRACT = "contract"
    ARCHITECTURE = "architecture"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    AGENT = "agent"
    CAPABILITY = "capability"
    TOOL = "tool"
    POLICY = "policy"
    PERMISSION = "permission"
    E2E = "e2e"
    REGRESSION = "regression"


class FaultType(str, Enum):
    TIMEOUT = "timeout"
    FAILURE = "failure"
    EXHAUSTED = "exhausted"


class Fault(BaseModel):
    """Chaos nhẹ: attempts = retries + 1 (C2-04).

    recoverable=False (M13-P0, TASK-089): fault không bao giờ recover —
    injector trả fault mọi lần → runner retry fail → SimulationStatus.ERROR.
    Default True giữ hành vi cũ (inject 1 lần/target, retry thành công).
    """

    model_config = ConfigDict(extra="forbid")

    target: str  # "model" | "tool.<name>" | "resource"
    type: FaultType
    params: dict = {}
    recoverable: bool = True


class ExpectedResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str | None = None
    agent: str | None = None
    policy: str | None = None  # "allow"/"deny"; None → bỏ qua so sánh policy
    required_capabilities: list[str] = []
    tests_pass: bool = True
    no_policy_bypass: bool = True


class Scenario(BaseModel):
    """Scenario Definition (yaml/json — không hard-code test)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    level: TestLevel = TestLevel.WORKFLOW
    input: dict  # request: str bắt buộc
    environment: dict = {"mode": "simulation"}
    expect: ExpectedResult
    faults: list[Fault] = []
    tags: list[str] = []


class SimulationStatus(str, Enum):
    SUCCESS = "success"
    MISMATCH = "mismatch"  # expectation lệch
    ERROR = "error"  # fault không recover / runner exception


class SimulationOutcome(BaseModel):
    """Deterministic outcome — metrics chỉ counts (C1-04, không timing)."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    status: SimulationStatus
    intent: str | None = None
    agent: str | None = None
    policy: str | None = None
    executed_nodes: list[str] = []
    tool_calls: list[dict] = []  # mọi attempt; cap 100 (C2-06)
    faults_injected: list[dict] = []
    recovery_events: list[dict] = []
    expectation_matches: dict[str, bool] = {}
    verification: dict[str, bool] = {}
    summary: str = ""
    metrics: dict = {}
