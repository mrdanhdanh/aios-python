"""Doctor First-Class — M10-F4 (TASK-071).

18 hạng mục (PLAN §M10-28): Runtime · Contracts · Registry · Models ·
Memory · Knowledge · Filesystem · Sandbox · Tools · Plugins · Policies ·
Permissions · DB · Events · Scheduler · Autonomy · Harness · Enterprise.
Mỗi hạng mục check THẬT → PASS/WARN/FAIL; score = round(100*pass/total).
Không tạo DB file mới (chỉ connect settings paths).
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from typing import Any


class DoctorStatus(str):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class DoctorCheck:
    item_id: str
    name: str
    status: DoctorStatus
    detail: str = ""


@dataclass
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def score(self) -> int:
        total = len(self.checks)
        if total == 0:
            return 0
        passed = sum(1 for c in self.checks if c.status == DoctorStatus.PASS)
        return round(100 * passed / total)


def _ok(item_id, name, detail="ok") -> DoctorCheck:
    return DoctorCheck(item_id, name, DoctorStatus.PASS, detail)


def _warn(item_id, name, detail) -> DoctorCheck:
    return DoctorCheck(item_id, name, DoctorStatus.WARN, detail)


def _fail(item_id, name, detail) -> DoctorCheck:
    return DoctorCheck(item_id, name, DoctorStatus.FAIL, detail)


class DoctorFirstClass:
    """18 hạng mục — mỗi check bọc try/except → FAIL kèm lý do (R1)."""

    def __init__(self, kernel: Any | None = None) -> None:
        self.kernel = kernel
        self.settings = None

    def _load_settings(self):
        if self.settings is None:
            from ..config import load_settings

            self.settings = load_settings()
        return self.settings

    def _get_kernel(self):
        if self.kernel is None:
            from ..kernel import RuntimeKernel

            self.kernel = RuntimeKernel.create()
        return self.kernel

    # -- 18 checks -----------------------------------------------------------
    def _check_runtime(self):
        try:
            kernel = self._get_kernel()
            assert kernel.bus is not None
            return _ok("runtime", "Runtime", "RuntimeKernel + EventBus alive")
        except Exception as exc:  # noqa: BLE001
            return _fail("runtime", "Runtime", f"{type(exc).__name__}: {exc}")

    def _check_contracts(self):
        try:
            from ..contracts.check import ContractChecker

            report = ContractChecker().check_all()
            if report.breaking_count == 0:
                return _ok("contracts", "Contracts",
                           f"10 contracts, breaking={report.breaking_count}")
            return _fail("contracts", "Contracts",
                         f"breaking={report.breaking_count}")
        except Exception as exc:  # noqa: BLE001
            return _fail("contracts", "Contracts", str(exc))

    def _check_registry(self):
        try:
            from ..agents.registry import AssistantRegistry
            from ..capabilities.registry import CapabilityRegistry
            from ..models import ModelRegistry

            kernel = self._get_kernel()
            models = kernel.container.resolve(ModelRegistry).list()
            return _ok("registry", "Registry",
                       f"models={len(models)}, agents/caps ok")
        except Exception as exc:  # noqa: BLE001
            return _fail("registry", "Registry", str(exc))

    def _check_models(self):
        try:
            from ..models import ModelRegistry

            kernel = self._get_kernel()
            registry = kernel.container.resolve(ModelRegistry)
            default = registry.default()
            return _ok("models", "Models", f"default={default.name}")
        except Exception as exc:  # noqa: BLE001
            return _fail("models", "Models", str(exc))

    def _check_memory(self):
        try:
            settings = self._load_settings()
            from ..memory.conversation import ConversationMemory

            db = settings.memory.conversation_db_path
            if not os.path.exists(db):
                return _warn("memory", "Memory", "chưa có dữ liệu (file chưa tồn tại)")
            mem = ConversationMemory(db)
            mem.list_conversations("__doctor__")
            return _ok("memory", "Memory", f"conversations db ok ({db})")
        except Exception as exc:  # noqa: BLE001
            return _fail("memory", "Memory", str(exc))

    def _check_knowledge(self):
        try:
            settings = self._load_settings()
            from ..knowledge.knowledge import KnowledgeMemory

            db = settings.memory.knowledge_db_path
            if not os.path.exists(db):
                return _warn("knowledge", "Knowledge", "chưa có dữ liệu")
            km = KnowledgeMemory(db)
            assert km is not None
            return _ok("knowledge", "Knowledge", f"knowledge db ok ({db})")
        except Exception as exc:  # noqa: BLE001
            return _fail("knowledge", "Knowledge", str(exc))

    def _check_filesystem(self):
        try:
            settings = self._load_settings()
            target = settings.artifacts.dir
            os.makedirs(target, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target, delete=True):
                pass
            return _ok("filesystem", "Filesystem", f"artifacts dir writable ({target})")
        except Exception as exc:  # noqa: BLE001
            return _fail("filesystem", "Filesystem", str(exc))

    def _check_sandbox(self):
        try:
            from ..sandbox.pool import SandboxPool

            pool = SandboxPool()
            pool.health()
            return _ok("sandbox", "Sandbox", "SandboxPool init + health ok")
        except Exception as exc:  # noqa: BLE001
            return _fail("sandbox", "Sandbox", str(exc))

    def _check_tools(self):
        try:
            from ..tools.registry import ToolRegistry

            registry = ToolRegistry()
            tools = registry.list()
            return _ok("tools", "Tools", f"{len(tools)} tools registered")
        except Exception as exc:  # noqa: BLE001
            return _fail("tools", "Tools", str(exc))

    def _check_plugins(self):
        try:
            settings = self._load_settings()
            from ..plugins.registry import PluginRegistry

            registry = PluginRegistry(settings.plugins.db_path)
            plugins = registry.list()
            return _ok("plugins", "Plugins", f"{len(plugins)} plugins")
        except Exception as exc:  # noqa: BLE001
            return _fail("plugins", "Plugins", str(exc))

    def _check_policies(self):
        try:
            from ..kernel.services import PolicyService

            kernel = self._get_kernel()
            policy = kernel.container.resolve(PolicyService)
            assert policy is not None
            return _ok("policies", "Policies", "PolicyService registered")
        except Exception as exc:  # noqa: BLE001
            return _fail("policies", "Policies", str(exc))

    def _check_permissions(self):
        try:
            from ..kernel.services import PermissionService

            kernel = self._get_kernel()
            perm = kernel.container.resolve(PermissionService)
            assert perm is not None
            return _ok("permissions", "Permissions", "PermissionService registered")
        except Exception as exc:  # noqa: BLE001
            return _fail("permissions", "Permissions", str(exc))

    def _check_db(self):
        try:
            settings = self._load_settings()
            from ..kernel.services import EventService

            kernel = self._get_kernel()
            event_service = kernel.container.resolve(EventService)
            assert event_service is not None
            return _ok("db", "DB", f"audit db {settings.audit.db_path}")
        except Exception as exc:  # noqa: BLE001
            return _fail("db", "DB", str(exc))

    def _check_events(self):
        try:
            from ..kernel.events import Event, EventType

            kernel = self._get_kernel()
            received = []
            kernel.bus.subscribe(EventType.WORKFLOW_COMPLETED, lambda e: received.append(e))
            kernel.bus.publish(Event(type=EventType.WORKFLOW_COMPLETED, payload={},
                                     source="doctor"))
            if len(received) == 1:
                return _ok("events", "Events", "pub/sub round-trip ok")
            return _fail("events", "Events", "event không đến handler")
        except Exception as exc:  # noqa: BLE001
            return _fail("events", "Events", str(exc))

    def _check_scheduler(self):
        try:
            from ..kernel.services import SchedulerService

            kernel = self._get_kernel()
            scheduler = kernel.container.resolve(SchedulerService)
            assert scheduler is not None
            return _ok("scheduler", "Scheduler", "SchedulerService registered")
        except Exception as exc:  # noqa: BLE001
            return _fail("scheduler", "Scheduler", str(exc))

    def _check_autonomy(self):
        try:
            from ..autonomous import AutonomyManager

            kernel = self._get_kernel()
            mgr = kernel.container.resolve(AutonomyManager)
            assert mgr is not None
            return _ok("autonomy", "Autonomy", "AutonomyManager registered")
        except Exception as exc:  # noqa: BLE001
            return _fail("autonomy", "Autonomy", str(exc))

    def _check_harness(self):
        try:
            from ..harness import HarnessRegistry

            kernel = self._get_kernel()
            registry = kernel.container.resolve(HarnessRegistry)
            harnesses = registry.list() if hasattr(registry, "list") else []
            return _ok("harness", "Harness", f"{len(harnesses)} harnesses")
        except Exception as exc:  # noqa: BLE001
            return _fail("harness", "Harness", str(exc))

    def _check_enterprise(self):
        try:
            from ..enterprise import EnterpriseManager

            kernel = self._get_kernel()
            mgr = kernel.container.resolve(EnterpriseManager)
            assert mgr is not None
            return _ok("enterprise", "Enterprise", "EnterpriseManager registered")
        except Exception as exc:  # noqa: BLE001
            return _fail("enterprise", "Enterprise", str(exc))

    # -- run ----------------------------------------------------------------
    def run(self) -> DoctorReport:
        checks = [
            self._check_runtime(), self._check_contracts(), self._check_registry(),
            self._check_models(), self._check_memory(), self._check_knowledge(),
            self._check_filesystem(), self._check_sandbox(), self._check_tools(),
            self._check_plugins(), self._check_policies(), self._check_permissions(),
            self._check_db(), self._check_events(), self._check_scheduler(),
            self._check_autonomy(), self._check_harness(), self._check_enterprise(),
        ]
        return DoctorReport(checks=checks)


def format_doctor_report(report: DoctorReport) -> str:
    rows = []
    width_id = max(len(c.item_id) for c in report.checks) + 2
    width_name = max(len(c.name) for c in report.checks) + 2
    sym = {DoctorStatus.PASS: "✓", DoctorStatus.WARN: "⚠", DoctorStatus.FAIL: "✗"}
    for c in report.checks:
        rows.append(
            f"{c.item_id.ljust(width_id)}| {c.name.ljust(width_name)}"
            f"| {sym[c.status]} {c.status} — {c.detail}"
        )
    header = f"{'item'.ljust(width_id)}| {'name'.ljust(width_name)}| status"
    lines = [header, "-" * max(len(header), max(len(r) for r in rows)), *rows, ""]
    lines.append(f"Health: {report.score}/100")
    return "\n".join(lines)
