"""Harness Coverage contracts (M13-P1, TASK-090).

Coverage là model đa chiều (PLAN §M13-5b) — KHÔNG quy "test count =
coverage". 9 dimensions + 8 negative-path + Harness Readiness (7 dims).
"coverage" ở đây = Harness Coverage model (độ phủ kiểm chứng) — KHÁC
test coverage / ArtifactType.COVERAGE / CheckKind.COVERAGE (P3-1 v1).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict

from ..doctor.contracts import HardGate  # tái dùng (P3-G v2)


class CoverageDimension(str, Enum):
    """9 chiều coverage (PLAN §M13-5b)."""

    COMPONENT = "component"
    CONTRACT = "contract"
    STATE = "state"
    TRANSITION = "transition"
    EVENT = "event"
    FAILURE_MODE = "failure_mode"
    SCENARIO = "scenario"
    VERIFICATION_PATH = "verification_path"
    ARTIFACT = "artifact"


class NegativePath(str, Enum):
    """8 negative-path coverage — quan trọng với trust layer (P2-F v2)."""

    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    VIOLATION = "violation"
    TIMEOUT = "timeout"
    EXCEPTION = "exception"
    CORRUPTED_EVIDENCE = "corrupted_evidence"
    REPLAY_MISMATCH = "replay_mismatch"


class CoverageItem(BaseModel):
    """Một mục coverage trong một dimension.

    Evidence quy ước (P1-A v2): `module:<importable>` (importlib.util.
    find_spec) hoặc `path:<anchored backend root>` (pathlib.Path.exists)
    — cwd-independent. covered=True → evidence bắt buộc.
    """

    model_config = ConfigDict(extra="forbid")

    dimension: CoverageDimension
    id: str
    covered: bool
    evidence: str


class DimensionCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: CoverageDimension
    total: int
    covered: int
    ratio: float  # covered/total (0 nếu total=0 — không div0)


class NegativePathCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: NegativePath
    covered: bool
    evidence: str  # covered=True → non-empty + tồn tại; covered=False → "" (AC18)


class HarnessCoverageReport(BaseModel):
    """KHÔNG có status (P3-2 v1) — readiness quyết định."""

    model_config = ConfigDict(extra="forbid")

    dimensions: dict[str, DimensionCoverage]  # key = dimension.value
    negative_paths: dict[str, NegativePathCoverage]  # key = path.value
    overall_ratio: float  # mean các dimension ratio
    negative_path_ratio: float  # covered/8
    metrics: dict  # counts only
    summary: str
    reproducible: dict  # {aios_version, registry_harness_ids, python_version} (P3-F v2)


class HarnessReadinessStatus(str, Enum):
    READY = "ready"
    NOT_READY = "not_ready"


class HarnessReadinessReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimensions: dict[str, float]  # 7 dims: structural/contract/behavioral/
    # failure/replay/scenario/production
    overall: float
    status: HarnessReadinessStatus
    hard_gates: list[HardGate] = []  # typed (P3-G v2)
    summary: str
    metrics: dict
    reproducible: dict