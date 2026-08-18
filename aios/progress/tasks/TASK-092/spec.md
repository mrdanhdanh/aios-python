# TASK-092 — M13-P3: Trust Separation (System Readiness ≠ Harness Trust) + Release Gate

> Milestone: M13 Harness Trust & Behavioral Conformance (Issue #8, nhánh `feature/ISSUE-8-m13-harness-trust`)
> Nâng cấp: P3 — Tách System Readiness ≠ Harness Trust; release gate yêu cầu CẢ 2 PASS
> Dependency: P0 (TASK-089 ✅) → P1 (TASK-090 ✅) → P2 (TASK-091 ✅) → P3 → (P4 TASK-093)
> Trạng thái: `in-progress` (hard gate)

## 1. Mục tiêu

**Tách biệt hai khái niệm độc lập** (PLAN §M13-P3):
- **System Readiness** = `HarnessReadinessReport` (từ `HarnessReadinessScorer` / `CoverageHarness`) — đo xem *hệ thống dưới test* (harness coverage) đã sẵn sàng ship chưa. Status: `READY` / `NOT_READY`.
- **Harness Trust** = `MetaReport` (từ `MetaHarnessEngine` / `MetaHarness`) — đo xem *chính các verifier* có đáng tin không. Status: `PASS` / `FAIL`.

**Release Gate** = tổ hợp ĐỘC LẬP: yêu cầu CẢ System Readiness `READY` VÀ Harness Trust `PASS` → mới `PASS` (cho phép release). Fail-closed: nếu một trong hai fail → release `BLOCKED`.

**🔴 Tách biệt thật (không ghép tên)**: Release Gate là pure combiner — NÓ KHÔNG biết *cách* tính readiness hay trust, chỉ nhìn report của hai score độc lập. Chứng minh: (a) readiness READY nhưng trust FAIL → BLOCKED; (b) trust PASS nhưng readiness NOT_READY → BLOCKED. → "System Readiness ≠ Harness Trust" là thật, không phải label.

## 2. Phạm vi

**In:**
- Module mới `backend/src/aios_core/harness/release/` (contracts + engine + harness + errors)
- Wiring: đăng ký `ReleaseGateHarness` (id="release") vào `HarnessRegistry` (sau coverage + meta)
- CLI: `aiagent harness release` (mở rộng group `harness`)
- Tests: `backend/tests/test_harness_release.py`
- Cập nhật coverage: `_COMPONENT_MODULES["release"] = "aios_core.harness.release"` (component coverage chính xác)
- Cập nhật 4 registry test + `test_registry_has_coverage` (thêm "release" → 10 harness runtime)

**Out:**
- P4 Docs/ADR (TASK-093) — ADR-0008 Harness Trust + INV-036 (nếu được duyệt)
- KHÔNG sửa Runtime/Orchestrator (INV-017..021 giữ nguyên)
- KHÔNG sửa verifier production / readiness scorer / meta engine — Release Gate chỉ tổ hợp report
- KHÔNG thêm invariant mới (INV-001..035 frozen; INV-036 thuộc TASK-093 qua ADR)

## 3. Thiết kế

### 3.1 Contracts (`harness/release/contracts.py`)

```python
class ReleaseGateStatus(str, Enum):
    PASS = "pass"        # cả 2 score PASS → cho phép release
    BLOCKED = "blocked"  # ít nhất 1 score fail → chặn release

class ReleaseGateReport(BaseModel):  # extra="forbid"
    system_readiness: dict   # {status: str, summary: str} (từ HarnessReadinessReport)
    harness_trust: dict      # {status, summary} (từ MetaReport)
    both_pass: bool
    status: ReleaseGateStatus
    summary: str
    reproducible: dict       # {aios_version, python_version} (KHÔNG timestamp)
```

### 3.2 Engine (`harness/release/engine.py`)

```python
class ReleaseGateEngine:
    """Thuần — combiner 2 score độc lập (KHÔNG tính readiness/trust)."""

    def evaluate(self, readiness: HarnessReadinessReport,
                 meta: MetaReport) -> ReleaseGateReport:
        sr_ready = readiness.status == HarnessReadinessStatus.READY
        ht_pass = meta.status == MetaStatus.PASS
        both = sr_ready and ht_pass
        status = ReleaseGateStatus.PASS if both else ReleaseGateStatus.BLOCKED
        # summary chỉ rõ lý do block (tách biệt rõ ràng)
        ...
```

**Logic fail-closed**: `status = PASS iff (readiness==READY and meta==PASS)`. Bất kỳ cặp nào khác → `BLOCKED`. Engine là pure function (không I/O, deterministic) → dễ unit test + monkeypatch.

### 3.3 Harness (`harness/release/harness.py`) + errors

```python
# errors.py
class ReleaseGateError(HarnessError): ...

class ReleaseGateHarness(Harness):  # id="release", name="release-gate", version="1.0.0"
    def __init__(self, coverage_harness: Harness, meta_harness: Harness, *,
                 state_service: StateService | None = None,
                 engine: ReleaseGateEngine | None = None) -> None
        # dependency injection 2 sub-harness (KHÔNG import concrete class —
        # tuân INV-017; chỉ type Harness ABC)
    def run(self, ctx) -> Any
        # chạy coverage_harness + meta_harness qua HarnessRunner (public API)
        # → lấy payload readiness + meta → engine.evaluate → report.model_dump
    def verify(self, ctx, payload) -> None
        # strict → status != PASS → raise ReleaseGateError (fail-closed INV-035)
    def _persist / get_report(run_id)
```

**Tách biệt trong harness**: `run()` chạy 2 sub-harness qua `HarnessRunner` (public API, INV-017 compliant), thu payload, build `HarnessReadinessReport` + `MetaReport` từ payload, gọi `engine.evaluate`. Harness KHÔNG import concrete `CoverageHarness`/`MetaHarness` (chỉ type `Harness` ABC) → không coupling nội bộ.

### 3.4 Wiring + CLI

- Wiring (`runtime_kernel.py`, sau meta): `ReleaseGateHarness(coverage_harness, meta_harness, state_service=...)` → register id="release" + container.
- CLI: thêm parser `harness release` + `--no-strict` + handler `_harness_release` + dispatch. `aiagent harness release [--no-strict]` → JSON document + exit 0 (PASS) / 1 (BLOCKED).

### 3.5 Cập nhật coverage (component accuracy)

- `_COMPONENT_MODULES["release"] = "aios_core.harness.release"` (component coverage chính xác; default `'aios_core.harness'` vẫn pass nhưng thiếu rõ ràng).

### 3.6 Cập nhật registry tests

- 4 test `test_harness_{benchmark,doctor,evaluation,testing}.py::TestConfigWiring::test_harness_registry_all_m6` — thêm `"release"` vào set kỳ vọng (10 harness).
- `test_harness_coverage.py::TestWiring::test_registry_has_coverage` — assert `len(reg.list()) == 10`.

## 4. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm chứng |
|---|----|-----------------|
| AC1 | Hai score độc lập: `HarnessReadinessReport` (System Readiness) và `MetaReport` (Harness Trust) là 2 type riêng từ 2 engine/harness | Unit test (import + assert khác class) |
| AC2 | `ReleaseGateEngine.evaluate(readiness, meta)` là pure function (không I/O, deterministic) | Unit test |
| AC3 | Release gate PASS yêu cầu CẢ `readiness.status==READY` VÀ `meta.status==PASS` | Unit test (cả 2 PASS → PASS) |
| AC4 | Fail-closed: readiness `NOT_READY` (meta PASS) → `BLOCKED` (chứng minh readiness một mình không đủ) | Unit test |
| AC5 | Fail-closed: meta `FAIL` (readiness READY) → `BLOCKED` (chứng minh trust một mình không đủ) | Unit test |
| AC6 | `ReleaseGateReport` shape: system_readiness + harness_trust + both_pass + status + summary + reproducible (không timestamp) | Unit test (extra="forbid") |
| AC7 | `ReleaseGateHarness` id="release" registry + lifecycle + persist round-trip | Test wiring + harness |
| AC8 | Fail-closed (INV-035): strict + status BLOCKED → `ReleaseGateError` → `DIAGNOSED`/`FAILED`; not-strict → `COMPLETED` | Test harness |
| AC9 | CLI `aiagent harness release`: PASS → exit 0; BLOCKED → exit 1; JSON document | Test CLI thật |
| AC10 | Full suite không regression + arch-health 0 + doctor healthy | Chạy full pytest + arch-health + doctor |
| AC11 | Determinism: evaluate 2 lần → report giống hệt | Unit test |
| AC12 | Tách biệt thật: AC4 + AC5 chứng minh System Readiness ≠ Harness Trust (2 path BLOCKED độc lập) | Unit test (tổng hợp AC4+AC5) |

## 5. Rủi ro & giả định

- **R1**: Release Gate là pure combiner — KHÔNG tính readiness/trust (tái dùng report có sẵn). INV-017 compliant (chỉ import contracts + Harness ABC + HarnessRunner public API).
- **R2**: Harness `run()` chạy sub-harness qua `HarnessRunner` (public API) — không import concrete class (type `Harness` ABC).
- **R3**: KHÔNG sửa Runtime/Orchestrator; KHÔNG thêm invariant; 4 invariant track giữ nguyên.
- **R4**: INV-036 (Harness Trust) thuộc TASK-093 (ADR riêng) — TASK-092 KHÔNG thêm invariant.
- **R5**: Thêm `release` harness vào runtime → component coverage map `"release"→"aios_core.harness.release"` (default `'aios_core.harness'` vẫn pass, nhưng thêm cho rõ ràng). KHÔNG phá READY (TASK-091).

## 6. Test strategy

`Unit → Contract → Integration → Architecture → E2E → Regression`:
- Unit: engine.evaluate (AC2-6, AC11, AC12) — construct reports trực tiếp
- Contract: pydantic + extra="forbid" (AC6)
- Integration: HarnessRunner.execute trên ReleaseGateHarness (cả 2 nhánh diagnose) + registry wiring (AC7/AC8)
- Architecture: arch-health 0 violations (INV-017 — chỉ import contracts/ABC/Runner)
- E2E: CLI thật `aiagent harness release` (AC9)
- Regression: full suite không giảm + 4 registry test + test_registry_has_coverage cập nhật (AC10)
