# TASK-091 — M13-P2: Meta-Harness (P2) — SPEC v3

> Milestone: M13 Harness Trust & Behavioral Conformance (Issue #9, nhánh `feature/ISSUE-9-m13-harness-trust`)
> Nâng cấp: P2 — Meta-Harness — verify the verifier với verification path ĐỘC LẬP (chống circular) + adversarial fail-closed
> Dependency: P0 (TASK-089 ✅) → P1 (TASK-090 ✅) → P2 → (P3 TASK-092 ∥ P4 TASK-093)
> Trạng thái: `in-progress` (hard gate) — v3 tích hợp resolution critique-1 (2 P1 + 5 P2 + 3 P3) + critique-2 (1 P1 + 4 P2 + 5 P3). **P1-1 (v2 chưa áp dụng đúng): BROKEN_VERIFIER/VERIFY_SKIPPED phải `fail_closed=True` (Meta đạt mục tiêu adversarial) để suite 8-case có thể PASS** (P1-1 fix applied)

## 1. Mục tiêu

**Verify the verifier** (PLAN §M13-7): Meta-Harness cố tình tạo false positive/negative, malformed evidence, broken verifier, corrupted artifact, replay mismatch, skipped verification → chứng minh Harness **thất bại đúng cách** (fail-closed) khi bị phá.

**🔴 Chống circular (PLAN §M13-7)**: Meta-Harness có verification path **độc lập tối thiểu**:
```
Production verifier → Meta test oracle → Expected invariant
```
**Oracle là hằng số hardcode** (P2-1) — engine KHÔNG gọi hàm production để tính `expected_state`. Residual circularity (oracle cùng nguồn spec) được ghi nhận; M16/dsh là path độc lập thật (PLAN §M16).

**Kết quả**: cover 2 negative-path còn thiếu của TASK-090 (CORRUPTED_EVIDENCE + REPLAY_MISMATCH) → `aiagent harness coverage` READY (8/8).

## 2. Phạm vi

**In:**
- Module mới `backend/src/aios_core/harness/meta/` (contracts + engine + harness + errors)
- Wiring: đăng ký harness `id="meta"` vào `HarnessRegistry`
- CLI: `aiagent harness meta` (mở rộng group `harness`)
- Tests: `backend/tests/test_harness_meta.py`
- Cập nhật TASK-090: negative CORRUPTED_EVIDENCE + REPLAY_MISMATCH → covered=True (evidence `module:aios_core.harness.meta`) + `_COMPONENT_MODULES["meta"]` + make_registry thêm MetaHarness

**Out:**
- P3 Trust Separation (TASK-092), P4 Docs/ADR (TASK-093)
- KHÔNG sửa Runtime/Orchestrator (INV-017..021 giữ nguyên)
- KHÔNG sửa verifier production (verification/execution) — Meta chỉ test qua API
- KHÔNG thêm invariant mới (INV-001..035 frozen)

## 3. Thiết kế

### 3.1 Contracts (`harness/meta/contracts.py`)

```python
class MetaCase(str, Enum):
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    MALFORMED_EVIDENCE = "malformed_evidence"
    BROKEN_VERIFIER = "broken_verifier"
    CORRUPTED_ARTIFACT = "corrupted_artifact"
    REPLAY_MISMATCH = "replay_mismatch"
    SKIPPED_VERIFICATION = "skipped_verification"
    VERIFY_SKIPPED = "verify_skipped"        # case 8 (P2-4)

class MetaOracle(str, Enum):  # P2-4: chuẩn hóa expected_state
    NOT_PASS = "not_pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    TAMPER = "tamper"
    CORRUPT = "corrupt"

class MetaCaseResult(BaseModel):  # extra="forbid"
    case: MetaCase
    verifier_state: str          # Verdict.value | "TAMPER:..." | "corrupt" | "COMPLETED"
    expected_state: MetaOracle   # oracle (hardcode — KHÔNG gọi hàm production) (P2-4)
    fail_closed: bool            # P1-1: Meta ĐẠT mục tiêu adversarial của case (không đồng nghĩa verifier fail-closed)
    detail: str

class MetaStatus(str, Enum):
    PASS = "pass"                # mọi case fail_closed=True
    FAIL = "fail"                # có case bỏ lọt (verifier không fail-closed)

class MetaReport(BaseModel):  # extra="forbid"
    cases: list[MetaCaseResult]
    all_fail_closed: bool
    status: MetaStatus
    metrics: dict                # {total, fail_closed, by_case: dict[str,int]} (P3-3)
    summary: str
    reproducible: dict           # {aios_version, python_version, registry_harness_ids} (P3-2)
```

### 3.2 Engine (`harness/meta/engine.py`)

```python
class MetaHarnessEngine:
    """Thuần — chạy 8 adversarial cases. Oracle hardcode (P2-1)."""

    def run(self) -> MetaReport
```

**8 cases (mỗi case: build adversarial input → chạy verifier production → so oracle hardcode):**

| Case | Adversarial input | Verifier (production) | Oracle (hardcode) | fail_closed khi |
|------|-------------------|----------------------|-------------------|-----------------|
| FALSE_POSITIVE | evidence thiếu critical (no plan.json) + check_results pass | `compute_verdict` | not_pass (INCONCLUSIVE) | verifier_state != "pass" |
| FALSE_NEGATIVE | check_results fail | `compute_verdict` | fail | verifier_state == "fail" |
| MALFORMED_EVIDENCE | evidence rỗng | `has_critical_evidence` + `compute_verdict` | not_pass | verifier_state != "pass" |
| BROKEN_VERIFIER | stub verifier luôn trả PASS với evidence thiếu | stub (giả lập hỏng) | not_pass | **Meta PHÁT HIỆN stub trả PASS trên evidence thiếu → fail_closed=True (P1-1 scenario a: bắt được verifier hỏng = thành công)** |
| CORRUPTED_ARTIFACT | content bytes + ref cố ý sai | sha256 check (tự viết — P2-2) | corrupt | `sha256(content) != ref` → phát hiện |
| REPLAY_MISMATCH | evidence `{"verdict":"pass","check_results":[CheckResult(passed=False)],"critical_evidence":True}` | `replay_verdict` | tamper | `"TAMPER" in verifier_state` (msg — P2-3) |
| SKIPPED_VERIFICATION | check skipped=True + passed=True | `CheckResult.effectively_passed` + `compute_verdict` | not_pass (INV-035) | verifier_state != "pass" |
| VERIFY_SKIPPED | harness `verify()` no-op | `HarnessRunner.execute` | not_pass | **Meta PHÁT HIỆN run COMPLETED mà không verify → fail_closed=True (P1-1 scenario a)** (P2-4) |

**Fail-closed semantics (P1-1 + P3-1)**: `fail_closed` = **Meta đạt được mục tiêu adversarial của case** (không đồng nghĩa "verifier fail-closed"). Với 6 case đầu: mục tiêu = "verifier KHÔNG PASS khi expected không PASS" → `fail_closed = (verifier_state != "pass")`. Với BROKEN_VERIFIER + VERIFY_SKIPPED: mục tiêu = "Meta phát hiện verifier hỏng/skip" → `fail_closed = True` (scenario a). Scenario (b) — "verifier dưới test KHÔNG fail-closed = Meta FAIL" — đẩy vào **AC16 (negative test, KHÔNG nằm trong 8-case live)**. `all_fail_closed = all(c.fail_closed)`. Status = PASS nếu all_fail_closed else FAIL → suite 8-case có thể `all_fail_closed=True` → `status=PASS` → exit 0 → coverage READY (AC13/AC15 reachable). Engine GỌI `has_critical_evidence(evidence)` TRƯỚC `compute_verdict` (P3-5).

**Chống circular (P2-1)**: `expected_state` là hằng số hardcode trong engine — KHÔNG gọi `compute_verdict`/`replay_verdict`/`has_critical_evidence` để suy ra expected. AC16 kiểm chứng: monkeypatch production function trả sai → Meta phát hiện → fail_closed=False → status FAIL.

### 3.3 Harness (`harness/meta/harness.py`) + errors

```python
# errors.py
class MetaError(HarnessError): ...

class MetaHarness(Harness):  # id="meta", name="meta-harness" (P2-3), version="1.0.0"
    def __init__(self, engine: MetaHarnessEngine | None = None, *,
                 state_service: StateService | None = None) -> None
        # engine = MetaHarnessEngine(state_service) nếu engine is None (P2-2: route state_service vào engine cho case 8)
    def run(self, ctx) -> Any   # → engine.run() → report.model_dump
    def verify(self, ctx, payload) -> None
        # strict → status != PASS → raise MetaError (fail-closed INV-035)
    def _persist / get_report(run_id)
```

### 3.4 Wiring + CLI

- Wiring: `MetaHarness(engine, state_service)` — id="meta", name="meta-harness" (P2-3)
- CLI: thêm parser group `harness` + subcommand `meta` + handler `_harness_meta` (P3-2) + dispatch branch + plumbing `--no-strict`; `aiagent harness meta [--no-strict]` → JSON document + exit 0 (PASS) / 1 (FAIL)

### 3.5 Cập nhật TASK-090 (negative-path 8/8)

- `_NEGATIVE_PATHS`: CORRUPTED_EVIDENCE + REPLAY_MISMATCH → covered=True, evidence="module:aios_core.harness.meta"
- `_COMPONENT_MODULES["meta"] = "aios_core.harness.meta"` (P2-5)
- `make_registry` (test_harness_coverage.py) thêm `MetaHarness` → component total 7→8 (P2-5)
- **4 test coverage cần cập nhật (P1-2 + P2-1)**: `test_negative_8_of_8` (rename từ `test_negative_6_of_8`, →8/8, ratio 1.0) (P3-1), `test_metrics_and_summary` (→"negative 8/8"), `test_ready_when_meta_covered` (rename từ `test_fail_closed_not_ready`, →replay 1.0, overall 1.0, READY) (P3-1), `test_components_8_exclude_self` (rename từ `test_components_7_exclude_self`, assert `comp.total == 8`) (P2-1). `test_ready_when_replay_covered` vẫn pass (override thủ công).
- Ghi nhận giới hạn (P3-3): evidence = module tồn tại, không phải meta PASS — marker mạnh hơn defer M13.2.

## 4. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm chứng |
|---|----|-----------------|
| AC1 | MetaCase đủ 8 cases (enum) | Unit test |
| AC2 | FALSE_POSITIVE: evidence thiếu critical + check pass → INCONCLUSIVE → fail_closed=True | Unit test |
| AC3 | FALSE_NEGATIVE: check fail → FAIL → fail_closed=True | Unit test |
| AC4 | MALFORMED_EVIDENCE: evidence rỗng → INCONCLUSIVE → fail_closed=True | Unit test |
| AC5 | BROKEN_VERIFIER: stub luôn PASS với evidence thiếu → Meta PHÁT HIỆN (fail_closed=True, scenario a) → status có thể PASS (P1-1) | Unit test |
| AC6 | CORRUPTED_ARTIFACT: sha256(content) != ref → phát hiện → fail_closed=True (P2-2) | Unit test |
| AC7 | REPLAY_MISMATCH: evidence tampered → replay_verdict msg chứa TAMPER → fail_closed=True (P2-3) | Unit test |
| AC8 | SKIPPED_VERIFICATION: check skipped + passed → effectively_passed=False → INCONCLUSIVE → fail_closed=True (INV-035) | Unit test |
| AC9 | VERIFY_SKIPPED: harness verify() no-op → HarnessRunner COMPLETED → Meta PHÁT HIỆN (fail_closed=True, scenario a) → status có thể PASS (P2-4) | Integration test |
| AC10 | MetaReport: all_fail_closed + status + metrics + summary + reproducible (không timestamp) | Unit test |
| AC11 | Harness id="meta" registry + lifecycle + persist round-trip | Test wiring + harness |
| AC12 | Fail-closed (INV-035): strict + status FAIL → MetaError → HarnessRunStatus.DIAGNOSED/FAILED; not-strict → COMPLETED | Test harness |
| AC13 | CLI `aiagent harness meta`: PASS → exit 0; FAIL → exit 1; JSON document | Test CLI thật |
| AC14 | Full suite không regression + arch-health 0 + doctor healthy | Chạy full pytest + arch-health + doctor |
| AC15 | Cập nhật TASK-090: negative 8/8 → `aiagent harness coverage` READY; 3 test coverage cập nhật (P1-2) | Chạy coverage CLI + test |
| AC16 | Chống circular (P2-1) + scenario (b) (P1-1): monkeypatch **module-level** `compute_verdict`/`replay_verdict` (P3-4) trả sai (luôn PASS trên evidence thiếu) → Meta phát hiện verifier dưới test KHÔNG fail-closed → fail_closed=False → status FAIL (negative test, KHÔNG nằm trong 8-case live) | Unit test |
| AC17 | Determinism: run 2 lần → report giống hệt | Unit test |

## 5. Rủi ro & giả định

- **R1**: Meta dùng verifier production qua API — KHÔNG sửa chúng (INV-017).
- **R2**: BROKEN_VERIFIER dùng stub (path độc lập — giả lập hỏng) → chống circular.
- **R3**: CORRUPTED_ARTIFACT tự viết sha256 check (engine thuần) — `hashlib` đã trong allow-list.
- **R4**: KHÔNG import sqlite3/httpx/socket/requests/os (INV-020b precedent).
- **R5**: KHÔNG sửa Runtime/Orchestrator; KHÔNG thêm invariant; 4 invariant track giữ nguyên.
- **R6**: Residual circularity (oracle cùng nguồn spec) ghi nhận — M16/dsh là path độc lập thật.

## 6. Test strategy

`Unit → Contract → Integration → Architecture → E2E → Regression`:
- Unit: engine 8 cases (mỗi case 1+ test) + monkeypatch chống circular (AC16)
- Contract: pydantic + extra="forbid"
- Integration: HarnessRunner.execute (cả 2 nhánh diagnose) + VERIFY_SKIPPED + registry wiring
- Architecture: arch-health 0 violations (allow-list nếu cần)
- E2E: CLI thật + coverage READY sau cập nhật
- Regression: full suite không giảm (3 test coverage cập nhật có chủ đích)