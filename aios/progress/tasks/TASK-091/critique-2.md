# Critique vòng 2 — TASK-091 (M13-P2: Meta-Harness)

> Phản biện độc lập (round 2) bởi critic agent — 2026-08-17
> Đọc: `spec.md` (SPEC v2 — đã tích hợp resolution critique-1) + `critique-1.md` (round 1, đã RESOLVED hết) + code thật:
> - `harness/execution/evidence.py` (`has_critical_evidence`)
> - `harness/execution/contracts.py` (`CheckResult.effectively_passed`, `Verdict`)
> - `harness/execution/pipeline.py` (`compute_verdict` — signature thật)
> - `harness/execution/replay.py` (`replay_verdict` — signature thật: `tuple[Verdict, str]`)
> - `harness/contracts.py`, `harness/registry.py` (`Harness` ABC, `HarnessRegistry`)
> - `harness/runner.py` (`HarnessRunner.execute` lifecycle)
> - `harness/coverage/{coverage,readiness}.py` (`_NEGATIVE_PATHS`, `_COMPONENT_MODULES`, `make_registry` caller)
> - `kernel/runtime_kernel.py` (DI wiring — xác nhận không cần sửa)
> - `workflow/cli.py` (group `harness`: đã có `behavioral` + `coverage`)
> - `tests/test_harness_coverage.py` (`make_registry`, 3 test cần sửa + `test_components_7_exclude_self`)
>
> **Góc nhìn khác vòng 1**: Round 1 tập trung vào "Meta vĩnh viễn FAIL" và thiếu AC. Vòng 2 xác minh xem
> resolution round 1 có được áp dụng ĐÚNG vào spec v2 hay không, và cross-check 8 cases vs signature thật của
> `compute_verdict` / `replay_verdict` / `has_critical_evidence` / `CheckResult.effectively_passed`, wiring
> `MetaHarness`, CLI group, và 3 test coverage.

## 0. Tóm tắt cross-check signature thật (dùng làm baseline)

| Hàm thật | Signature | Trả về |
|---|---|---|
| `compute_verdict` | `(check_results, has_critical_evidence: bool, truncated=False)` | `Verdict` ∈ {PASS, PASS_WITH_WARNING, FAIL, INCONCLUSIVE} |
| `replay_verdict` | `(evidence: dict) -> tuple[Verdict, str]` | `(verdict, msg)` — msg = `"TAMPER: stored=... != recomputed=..."` nếu lệch |
| `has_critical_evidence` | `(evidence: dict) -> bool` | bool (False nếu `namespace==""` hoặc thiếu `plan.json`/`execution-graph.json`) |
| `CheckResult.effectively_passed` | property | `passed and not skipped and not error` |

- `Harness` (ABC, `registry.py`) **KHÔNG có `__init__`**, nhưng có 3 abstract prop bắt buộc: `id`, `name`, `version`. `HarnessRegistry.register()` raise nếu bất kỳ trong 3 rỗng.
- `HarnessRunner.execute()` gọi `prepare→validate→run→verify→complete`; `verify()` no-op (default base) → vẫn chạy tới `COMPLETED` (bằng chứng: base `Harness.verify` là no-op).
- `make_registry()` (`test_harness_coverage.py:36`) đăng ký **7** harness → component total (exclude self) = 7. `test_components_7_exclude_self` assert `comp.total == 7`.
- CLI group `harness` (`workflow/cli.py:210`) đã có subparser `behavioral` (TASK-089) + `coverage` (TASK-090); **chưa có `meta`**.
- `coverage.py`: `_NEGATIVE_PATHS` có `CORRUPTED_EVIDENCE`/`REPLAY_MISMATCH = (False, "")`; `_COMPONENT_MODULES` chưa có `"meta"`.

## 1. Phân loại findings (khác góc nhìn vòng 1)

### P1 — Phải sửa trước khi implement

#### P1-1 — Spec v2 CHƯA thật sự resolve round-1 P1-1: BROKEN_VERIFIER / VERIFY_SKIPPED làm Meta không bao giờ PASS

- **Vấn đề (phát hiện độc lập, góc nhìn "kiểm chứng resolution")**: Round-1 P1-1 đã chỉ ra "BROKEN_VERIFIER semantics đảo ngược → Meta vĩnh viễn FAIL" và resolution yêu cầu *"Tách 2 khái niệm: (a) Meta bắt được verifier hỏng = thành công (fail_closed=True); (b) verifier dưới test không fail-closed = Meta FAIL. Thêm test riêng (b)."* Nhưng spec v2 **vẫn ghi ngược lại** ở bảng 3.2 và AC5/AC9:
  - Bảng 3.2 BROKEN_VERIFIER: *"verifier_state != 'pass' → stub trả PASS → fail_closed=False → Meta FAIL (P1-1: bắt được verifier hỏng = phát hiện...)"* — mâu thuẫn nội tại: vừa ghi `fail_closed=False → Meta FAIL`, vừa ghi parenthetical "bắt được = phát hiện" (tức thành công).
  - AC5: *"BROKEN_VERIFIER: ... fail_closed=False → Meta status FAIL (bắt được verifier hỏng)"*.
  - AC9: *"VERIFY_SKIPPED: ... fail_closed=False → Meta FAIL"*.
  - Vì `all_fail_closed = all(c.fail_closed)` và `status=PASS iff all_fail_closed`, nếu 2 case 7 & 8 **luôn** `fail_closed=False` thì **MetaReport.status LUÔN FAIL** → CLI exit 0 (AC13) và `harness coverage` READY (AC15) **không bao giờ đạt được**. Tức là goal cốt lõi của task ("cover 2 negative-path còn thiếu → READY 8/8") trở nên unreachable. Đây chính là bug round-1 đã nêu, nhưng resolution chưa được áp dụng vào spec v2.
- **RESOLVED (sửa spec như thế nào)**:
  1. Trong §3.2, **định nghĩa lại `fail_closed`** = *"Meta đạt được mục tiêu adversarial của case (kỳ vọng của case được thỏa mãn)"*, **KHÔNG** đồng nghĩa với "verifier under test fail-closed". Đây là cách giải quyết round-1 P1-1 (a).
  2. **BROKEN_VERIFIER (case 7)** = scenario (a): engine cố ý dùng stub trả PASS trên evidence thiếu → engine *phát hiện* vi phạm oracle → `fail_closed=True` (Meta thành công phát hiện verifier hỏng). Ghi `verifier_state="pass"` (stub output), `expected_state="not_pass"` (oracle), `detail="detected broken verifier: stub returned pass on missing evidence"`.
  3. **VERIFY_SKIPPED (case 8)** = scenario (a): harness `verify()` no-op → `HarnessRunner` COMPLETED → engine *phát hiện* "completed without verification" → `fail_closed=True` (Meta thành công phát hiện).
  4. **Đẩy scenario (b) vào AC16** (đã có, negative test, KHÔNG nằm trong 8-case live suite): monkeypatch `compute_verdict`/`replay_verdict` trả sai → `fail_closed=False` → `status=FAIL`. AC16 giữ nguyên vai trò chứng minh Meta sẽ FAIL khi verifier thật không fail-closed.
  5. Sửa bảng 3.2: cột "fail_closed khi" của BROKEN_VERIFIER & VERIFY_SKIPPED → *"Meta phát hiện vi phạm oracle/no-verify → fail_closed=True"*. Sửa AC5 → *"fail_closed=True (Meta phát hiện verifier hỏng)"*; AC9 tương tự.
  6. Kết quả: 8-case suite có thể `all_fail_closed=True` → `status=PASS` → CLI exit 0 → coverage READY. AC13/AC15 reachable.

### P2 — Nên sửa

#### P2-1 — Danh sách 3 test coverage cập nhật BỊ THIẾU `test_components_7_exclude_self`

- **Vấn đề**: §3.5 + P2-5 nói "make_registry thêm MetaHarness → component total 7→8" và liệt kê 3 test (`test_negative_6_of_8`, `test_metrics_and_summary`, `test_fail_closed_not_ready`). Nhưng `test_components_7_exclude_self` (`test_harness_coverage.py:116`) assert `comp.total == 7`. Khi `make_registry()` thêm `MetaHarness`, component total = 8 → test này **SẬP**. Đây là test thứ 4 bắt buộc sửa nhưng không nằm trong danh sách spec.
- **RESOLVED**: Trong §3.5, bổ sung test thứ 4: rename `test_components_7_exclude_self` → `test_components_8_exclude_self` và assert `comp.total == 8`. Ghi rõ `test_report_ratios`/`test_dimensions_total_positive` vẫn pass (ratio vẫn 1.0 vì coverage đầy đủ; tổng contract/state/... không đổi).

#### P2-2 — Wiring `MetaHarness(engine, state_service)` chưa chỉ rõ engine lấy `state_service` ở đâu (case 8 VERIFY_SKIPPED)

- **Vấn đề**: §3.2 gọi engine là "thuần" nhưng case 8 cần `HarnessRunner` + một harness `verify()` no-op + `state_service` (để `HarnessRunner(state_service)`). `MetaHarnessEngine` trong spec chỉ có `def run(self) -> MetaReport` — **không có tham số `state_service`**. Vậy engine không thể dựng `HarnessRunner` cho case 8. Wiring bị hổng.
- **RESOLVED**: Trong §3.3, `MetaHarness.__init__(self, engine, *, state_service)` phải truyền `state_service` vào engine: `self._engine = engine; self._engine.bind(state_service)` hoặc `engine = MetaHarnessEngine(state_service)`. Trong §3.2 bổ sung: case 8 dựng `HarnessRunner(state_service)` (artifact_service=None) + một `NoVerifyHarness(Harness)` cục bộ có `verify()` no-op và `run()` trả payload giả, rồi `runner.execute(noharness, ctx)` và断言 `run.status == COMPLETED` → `fail_closed=True`.

#### P2-3 — `MetaHarness` thiếu property `name` (abstract bắt buộc)

- **Vấn đề**: `Harness` ABC có `@property @abstractmethod def name(self)`. Spec §3.3 chỉ ghi `id="meta", version="1.0.0"` — **thiếu `name`**. `HarnessRegistry.register()` sẽ raise `HarnessRegistrationError("id/name/version must be non-empty")` khi đăng ký `MetaHarness`.
- **RESOLVED**: Trong §3.3, thêm `name = "meta-harness"` (class attr hoặc property) cho `MetaHarness`.

#### P2-4 — `verifier_state` / `expected_state` vocabulary & type không nhất quán

- **Vấn đề**: `verifier_state: str` nhận cả (1) `Verdict.value` ("pass"/"fail"/"inconclusive") cho compute_verdict, (2) **message string** `"TAMPER: stored=... != recomputed=..."` cho replay (spec ghi `fail_closed = "TAMPER" in verifier_state` — tức field này là msg, không phải token), (3) "corrupt"/"ok" cho sha256. `expected_state` cũng lộn xộn: "not_pass"/"fail"/"inconclusive"/"tamper"/"corrupt". Field `extra="forbid"` nhưng kiểu giá trị tự do → test AC2–AC9 dễ flaky và CLI output khó đọc.
- **RESOLVED**: Trong §3.1 `MetaCaseResult`, chuẩn hóa docstring: `verifier_state` = output thô của production function (Verdict.value cho compute_verdict; msg cho replay; "corrupt"/"ok" cho sha256). `expected_state` = token oracle chuẩn hóa (dùng enum nội bộ `MetaOracle {NOT_PASS, FAIL, INCONCLUSIVE, TAMPER, CORRUPT}` thay vì string tự do). `fail_closed` tính bởi logic so sánh **riêng per-case** (không dùng công thức chung sai cho case 7/8 — xem P1-1). Cập nhật AC2–AC9 theo token chuẩn.

### P3 — Góp ý (tích hợp vào spec v3)

#### P3-1 — Tên 3 test coverage gây hiểu lầm sau update
- **Vấn đề**: `test_negative_6_of_8` sau sửa kỳ vọng 8/8 nhưng giữ tên 6/8; `test_fail_closed_not_ready` sau sửa assert READY (replay 1.0) nhưng tên ngụ ý NOT_READY.
- **RESOLVED**: Rename → `test_negative_8_of_8` và `test_ready_when_meta_covered`. `test_ready_when_replay_covered` (line 232) giữ nguyên (vẫn pass — manual override giờ trùng với default).

#### P3-2 — CLI `aiagent harness meta` underspecify handler + dispatch
- **Vấn đề**: §3.4 chỉ ghi "`aiagent harness meta [--no-strict]`" nhưng không nói thêm `_harness_meta(args)` handler và dispatch branch `if args.command=="harness" and args.harness_command=="meta": return _harness_meta(args)` (mirror `_harness_coverage` line 349), cũng như plumbing `--no-strict` → `MetaHarness(strict=...)`.
- **RESOLVED**: Bổ sung vào §3.4: (1) định nghĩa `_harness_meta`, (2) branch dispatch, (3) `--no-strict` map vào `MetaHarness(..., strict=not args.no_strict)`.

#### P3-3 — `MetaReport.metrics` quá vague ("counts only")
- **Vấn đề**: §3.1 ghi `metrics: dict # counts only` không định nghĩa key → test AC10 khó assert.
- **RESOLVED**: Định nghĩa tường minh `metrics = {"cases_total": 8, "fail_closed_total": int, "fail_open_total": int, "by_case": {case: bool}}`.

#### P3-4 — AC16 monkeypatch phải hướng vào import module-level
- **Vấn đề**: AC16 monkeypatch `compute_verdict`/`replay_verdict`. Nếu engine import chúng kiểu `from .pipeline import compute_verdict` (bound name), monkeypatch `aios_core.harness.execution.pipeline.compute_verdict` sẽ không ảnh hưởng đến tên đã bound trong engine → test AC16 âm tính giả.
- **RESOLVED**: Ghi chú AC16: engine phải gọi qua module (`import aios_core.harness.execution.pipeline as P; P.compute_verdict(...)`) HOẶC test monkeypatch đúng symbol mà engine reference. Thêm assertion trong AC16 rằng sau monkeypatch, ít nhất 1 case có `fail_closed=False` và `status==FAIL`.

#### P3-5 — Engine phải gọi `has_critical_evidence(evidence)` trước `compute_verdict`
- **Vấn đề**: Bảng 3.2 ghi "Verifier (production): compute_verdict" — nhưng `compute_verdict` nhận `has_critical_evidence: bool`, không nhận evidence dict. Dễ implement sai (truyền dict).
- **RESOLVED**: Trong §3.2 note: với case dùng `compute_verdict`, engine gọi `crit = has_critical_evidence(evidence)` rồi `compute_verdict(check_results, crit, truncated)`.

## 2. Đối chiếu 6 điểm yêu cầu (a)–(f)

- **(a) Tính khả thi 8 cases vs signature thật**: 6/8 cases (FALSE_POSITIVE, FALSE_NEGATIVE, MALFORMED_EVIDENCE, CORRUPTED_ARTIFACT, REPLAY_MISMATCH, SKIPPED_VERIFICATION) **khả thi** với signature thật (`compute_verdict(check_results, bool, bool)`, `replay_verdict(dict)->tuple`, `has_critical_evidence(dict)->bool`, `CheckResult.effectively_passed`). 2 cases còn lại (BROKEN_VERIFIER, VERIFY_SKIPPED) khả thi về mặt gọi hàm, nhưng **semantics `fail_closed` bị nghịch lý** → xem **P1-1**.
- **(b) Engine có gọi production function để tính `expected_state` (vi phạm chống circular P2-1) không**: **KHÔNG**. `expected_state` là hardcode trong engine (INCONCLUSIVE / FAIL / TAMPER / CORRUPT / NOT_PASS). Engine chỉ gọi production function để lấy `verifier_state` (verifier under test), không dùng để suy `expected_state`. AC16 là bằng chứng đúng (monkeypatch production → Meta vẫn fail_closed đúng hướng). Lưu ý thêm P3-4 để AC16 thực sự hiệu lực.
- **(c) Wiring `MetaHarness(engine, state_service)` có khớp `Harness.__init__` thật không**: `Harness` ABC **không có `__init__`** → `MetaHarness.__init__(engine, state_service)` hợp lệ. NHƯNG: (i) thiếu `name` property (P2-3) → register sẽ fail; (ii) `state_service` chưa được route vào engine cho case 8 (P2-2).
- **(d) CLI parser group `harness` có trùng TASK-089/090 không**: **KHÔNG trùng** — group `harness` đã có `behavioral` (TASK-089) + `coverage` (TASK-090); `meta` là subcommand MỚI, không collision. Tuy nhiên spec thiếu định nghĩa `_harness_meta` + dispatch branch (P3-2).
- **(e) 3 test coverage cập nhật có đúng tên hàm thật không**: Tên **tồn tại thật** (`test_negative_6_of_8` line 142, `test_metrics_and_summary` line 175, `test_fail_closed_not_ready` line 223). Nhưng danh sách **thiếu `test_components_7_exclude_self`** (line 116, assert total==7) sẽ sập khi thêm MetaHarness → P2-1. Ngoài ra tên 2 test đầu gây hiểu lầm sau update → P3-1.
- **(f) MetaReport có field dư thừa hoặc thiếu không**: `all_fail_closed` dư thừa (tính từ `cases`) nhưng chấp nhận làm tiện ích. `reproducible` khớp shape `HarnessCoverageReport` (tốt). Thiếu: `metrics` chưa định nghĩa key (P3-3); `MetaCaseResult` thiếu chuẩn hóa `verifier_state`/`expected_state` (P2-4). Không thiếu field cốt lõi.

## Mức sẵn sàng v2: 3/5

> Lý do: cấu trúc spec v2 đã tốt hơn v1 (đã có 8 cases, AC16 chống circular, 3 test coverage được liệt kê), nhưng **round-1 P1-1 chưa được áp dụng đúng** (BROKEN_VERIFIER/VERIFY_SKIPPED vẫn ghi `fail_closed=False → Meta FAIL` → Meta không bao giờ PASS → AC13/AC15 unreachable). Cộng thêm P2-1 (thiếu test update), P2-2 (wiring state_service), P2-3 (thiếu `name`), P2-4 (vocabulary lộn xộn). Sau khi áp dụng các RESOLVED ở trên → spec v3 đạt 5/5.

## Kết luận

- [x] Tất cả findings (1 P1 + 4 P2 + 5 P3) đã có giải pháp **RESOLVED** cụ thể sửa spec v2.
- [x] Sau khi apply: 8-case suite có thể `all_fail_closed=True` → `status=PASS` → CLI exit 0 → `harness coverage` READY (8/8 negative, replay 1.0, overall 1.0).
- [x] Không vi phạm INV-017..021 (không sửa Runtime/Orchestrator), không thêm invariant (INV-001..035 frozen), tái dùng `compute_verdict`/`replay_verdict`/`has_critical_evidence`/`CheckResult.effectively_passed` đúng signature.
- ➡️ **Spec v2 → Spec v3** (tích hợp P1-1 semantics fix + P2-1..P2-4 + P3-1..P3-5).
