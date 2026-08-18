"""Backward Compatibility Suite — M12-P2 C3 (TASK-086, Issue #7).

Cross-version checks: dữ liệu/component format cũ (v0/v1) chạy được trên
AIOS 1.1.0. Fail-closed: check được phép raise — runner bắt (kể cả
BaseException — review R2) → (False, detail).
"""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Sequence
from uuid import uuid4

from ..contracts.compatibility import CompatibilityChecker
from ..plugins.compat import check_compatibility
from .compatibility import AIOS_VERSION

Kind = Literal["workflow", "plugin", "contract", "extension", "migrated"]


class _NullSink:
    """Sink rỗng cho redirect_stdout — KHÔNG import io (review R1:
    ``io`` không nằm trong _UPGRADE_ALLOWED_EXTERNAL)."""

    def write(self, _text: str) -> int:
        return 0

    def flush(self) -> None:
        pass


@dataclass(frozen=True)
class BackwardCheck:
    id: str
    kind: Kind
    description: str
    run: Callable[[], tuple[bool, str]]  # được phép raise — runner bắt


@dataclass(frozen=True)
class BackwardCheckResult:
    id: str
    kind: Kind
    ok: bool
    detail: str


@dataclass
class BackwardCompatibilityReport:
    ok: bool
    results: list[BackwardCheckResult] = field(default_factory=list)
    fail_closed: bool = True


# ---------------------------------------------------------------------------
# Fixtures v0 (spec §3.2)
# ---------------------------------------------------------------------------

_PLUGIN_V0 = {
    "id": "demo", "name": "demo", "version": "1.0.0",
    "aios": {"min": "1.0.0", "max": "*"},
}
_WORKFLOW_V0 = {
    "name": "demo_flow", "version": "0.1.0",
    "nodes": [{"id": "n1", "type": "task", "name": "n1"}],
}
_WORKFLOW_V0_YAML = "name: demo_flow\nversion: 0.1.0\nnodes:\n  - id: n1\n    type: task\n    name: n1\n"
_CONTRACT_V0 = {
    "id": "agent", "name": "Agent Contract", "version": "1.0.0",
    "schema_ref": ("aios_core.agents.base", "Assistant"), "lifecycle": "stable",
}
_EXTENSION_ALLOWED = ("extension",)  # theo PLAN §M8-E3 (4 namespace M8)

#: payload output của TASK-085 (migrated 1.0→1.1)
_MIGRATED_PLUGIN = {
    "id": "demo", "name": "demo", "version": "1.0.0",
    "aios": {"min": "1.0.0", "compatible": ["1.0.0", "1.1.0"]},
}
_MIGRATED_WORKFLOW = {"name": "demo_flow", "version": "1.1.0",
                      "nodes": [{"id": "n1", "type": "task", "name": "n1"}]}
_MIGRATED_CONTRACT = {
    "id": "agent", "name": "Agent Contract", "version": "1.1.0",
    "schema_ref": ("aios_core.agents.base", "Assistant"), "lifecycle": "stable",
}


# ---------------------------------------------------------------------------
# 9 checks (5 kind)
# ---------------------------------------------------------------------------

def _check_workflow_v0_parse() -> tuple[bool, str]:
    from ..workflow.compiler import MockCompiler
    from ..workflow.definition import WorkflowDefinition

    wf = WorkflowDefinition.model_validate(_WORKFLOW_V0)
    MockCompiler().compile(wf)
    return True, f"parsed+compiled v{_WORKFLOW_V0['version']}"


def _check_workflow_v0_run_simulate() -> tuple[bool, str]:
    from ..workflow.cli import _run_simulate

    wf_path = Path.cwd() / f"_compat_wf_{uuid4().hex}.yaml"
    wf_path.write_text(_WORKFLOW_V0_YAML, encoding="utf-8")
    try:
        with contextlib.redirect_stdout(_NullSink()):
            rc = _run_simulate(str(wf_path))
    finally:
        wf_path.unlink(missing_ok=True)
    if rc != 0:
        return False, f"simulate exit {rc} (expect 0)"
    return True, "simulate completed (exit 0)"


def _check_plugin_v0_load() -> tuple[bool, str]:
    from ..plugins.contracts import PluginManifest

    manifest = PluginManifest.validate_manifest(**_PLUGIN_V0)
    ok = check_compatibility("1.0.0", "*", AIOS_VERSION)
    if not ok:
        return False, f"check_compatibility(1.0.0,*,{AIOS_VERSION}) = False"
    return True, f"manifest {manifest.id}@{manifest.version} compatible"


def _check_plugin_v1_compatible_field() -> tuple[bool, str]:
    from ..plugins.contracts import PluginManifest

    manifest = PluginManifest.model_validate(_MIGRATED_PLUGIN)
    if manifest.aios.compatible != ["1.0.0", "1.1.0"]:
        return False, f"compatible round-trip fail: {manifest.aios.compatible!r}"
    return True, f"compatible field parsed: {manifest.aios.compatible}"


def _check_contract_v0_compat() -> tuple[bool, str]:
    ok = CompatibilityChecker.is_compatible(installed="1.1.0", required="1.0.0")
    up = CompatibilityChecker.check_upgrade("1.0.0", "1.1.0")
    if not ok or not up.compatible:
        return False, f"is_compatible={ok} check_upgrade.compatible={up.compatible}"
    return True, "1.0-built contract compatible on 1.1 (minor bump)"


def _check_contract_v0_catalog() -> tuple[bool, str]:
    from ..contracts.catalog import ContractDefinition

    contract = ContractDefinition.model_validate(_CONTRACT_V0)
    if not contract.schema_exists():
        return False, f"schema_ref {contract.schema_ref} không import được"
    return True, f"contract {contract.id} v{contract.version} parsed + schema exists"


def _check_extension_v0_matrix() -> tuple[bool, str]:
    from ..extension.errors import CompatibilityViolation
    from ..extension.matrix import assert_namespace_allowed

    assert_namespace_allowed("extension", _EXTENSION_ALLOWED)  # PASS — không raise
    try:
        assert_namespace_allowed("internal", _EXTENSION_ALLOWED)
    except CompatibilityViolation:
        return True, "extension namespace PASS / internal gate FAIL (đúng gate)"
    return False, "internal namespace KHÔNG bị chặn — gate hỏng"


def _check_migrated_110_data() -> tuple[bool, str]:
    from ..contracts.catalog import ContractDefinition
    from ..plugins.contracts import PluginManifest
    from ..workflow.definition import WorkflowDefinition

    plugin = PluginManifest.model_validate(_MIGRATED_PLUGIN)
    if plugin.aios.compatible != ["1.0.0", "1.1.0"]:
        return False, "plugin compatible round-trip fail"
    workflow = WorkflowDefinition.model_validate(_MIGRATED_WORKFLOW)
    if workflow.version != "1.1.0":
        return False, f"workflow version {workflow.version} != 1.1.0"
    contract = ContractDefinition.model_validate(_MIGRATED_CONTRACT)
    if contract.version != "1.1.0":
        return False, f"contract version {contract.version} != 1.1.0"
    return True, "migrated plugin/workflow/contract re-parse OK"


def _check_migrated_v0_formats() -> tuple[bool, str]:
    from ..plugins.contracts import PluginManifest
    from ..upgrade.migration import MigrationFormats
    from ..workflow.definition import WorkflowDefinition

    config = MigrationFormats.config_v0_to_v1(
        {"autonomous": {"budget": {"max_duration_s": 7200.0}}}
    )
    if config.get("autonomous", {}).get("budget", {}).get("max_duration_seconds") != 7200.0:
        return False, "config v0→v1 thiếu max_duration_seconds"
    workflow = MigrationFormats.workflow_v0_to_v1(_WORKFLOW_V0)
    WorkflowDefinition.model_validate(workflow)  # raise → fail-closed
    plugin = MigrationFormats.plugin_v0_to_v1(
        {"id": "demo", "name": "demo", "version": "1.0.0", "aios": {"min": "1.0.0", "max": "*"}}
    )
    PluginManifest.model_validate(plugin)  # raise → fail-closed
    return True, "v0→v1 formats re-parse OK (config/workflow/plugin)"


# ---------------------------------------------------------------------------
# Suite
# ---------------------------------------------------------------------------

class BackwardCompatibilitySuite:
    """Registry + runner fail-closed cho các scenario cũ→mới trên AIOS 1.1."""

    CHECKS: tuple[BackwardCheck, ...] = (
        BackwardCheck("workflow-v0-parse", "workflow",
                      "WorkflowDefinition v0 (không timeout_s) parse + compile",
                      _check_workflow_v0_parse),
        BackwardCheck("workflow-v0-run-simulate", "workflow",
                      "Workflow v0 chạy simulate trên runtime 1.1",
                      _check_workflow_v0_run_simulate),
        BackwardCheck("plugin-v0-load", "plugin",
                      "PluginManifest v0 + check_compatibility trên 1.1",
                      _check_plugin_v0_load),
        BackwardCheck("plugin-v1-compatible-field", "plugin",
                      "AiosRange.compatible (migrate 1.0→1.1) parse round-trip",
                      _check_plugin_v1_compatible_field),
        BackwardCheck("contract-v0-compat", "contract",
                      "Component built cho 1.0 chạy trên 1.1 (semver)",
                      _check_contract_v0_compat),
        BackwardCheck("contract-v0-catalog", "contract",
                      "Contract payload v0 parse + schema_exists",
                      _check_contract_v0_catalog),
        BackwardCheck("extension-v0-matrix", "extension",
                      "Extension namespace gate 2 chiều (M8)",
                      _check_extension_v0_matrix),
        BackwardCheck("migrated-110-data", "migrated",
                      "Payload TASK-085 (migrated) re-parse qua model thật",
                      _check_migrated_110_data),
        BackwardCheck("migrated-v0-formats", "migrated",
                      "MigrationFormats v0→v1 outputs hợp lệ trên 1.1",
                      _check_migrated_v0_formats),
    )

    def __init__(self, checks: Sequence[BackwardCheck] | None = None) -> None:
        self._checks = tuple(checks) if checks is not None else self.CHECKS

    def run(self) -> BackwardCompatibilityReport:
        results: list[BackwardCheckResult] = []
        for check in self._checks:
            try:
                ok, detail = check.run()
            except BaseException as exc:  # noqa: BLE001 — fail-closed (review R2)
                ok, detail = False, f"{type(exc).__name__}: {exc}"
            results.append(BackwardCheckResult(check.id, check.kind, ok, detail))
        return BackwardCompatibilityReport(
            ok=all(r.ok for r in results), results=results, fail_closed=True
        )
