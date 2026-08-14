# Evaluation — TASK-030 (Execution Verification, M6-H2)

## Tiêu chí chấp nhận (AC) — đối chiếu
| AC | Yêu cầu | Kết quả |
|----|---------|---------|
| AC1 | Contracts (CheckKind 5 loại, Check, VerificationTask, CheckResult, Verdict 4 trạng thái) | ✅ `harness/execution/contracts.py` — extra="forbid" |
| AC2 | Evidence: plan/graph/tool-results/runtime-events + resolution 3 bước | ✅ `evidence.py` — C1-01/P3-08, filter execution_id, sort asc |
| AC3 | 5 kinds checks deterministic | ✅ `pipeline.py` — FILE_EXISTS/CONTAINS/TEST_RUN/COVERAGE/CUSTOM |
| AC4 | Verdict 5 nhánh + INV-019 | ✅ FAIL > INCONCLUSIVE > PASS; skip → INCONCLUSIVE; 6 arch tests |
| AC5 | Harness run/verify + persist trước raise | ✅ persist → raise VerificationError; state giữ verdict fail |
| AC6 | Replay round-trip integrity | ✅ `replay.py` — tamper detection (verdict/evidence flags) |
| AC7 | Config + wiring runtime_kernel | ✅ ExecutionSettings + registry.register("verification") |
| AC8 | INV-019 AST + behavioral | ✅ 6 arch tests (rglob, no kernel impl, literal FAIL) |
| AC9 | Allow-list additive | ✅ +`pathlib` external (R2-1); _HARNESS_ALLOWED_AIOS KHÔNG MOD |
| AC10 | Test count ≥1169, coverage ≥90% | ✅ 1210 tests, 95.26% |

## Review resolution
- R2-1 (pathlib): thêm vào `_HARNESS_ALLOWED_EXTERNAL` ✓
- R2-2 (wiring object): `EvidenceServices(state/events/artifacts)` — không phải dict ✓
- R3-1..07: P3-08 3 bước, `to_dict()` cho Event dataclass, truncation heuristic + truncated param, replay dict-level, AC5 dùng FILE_EXISTS, metrics deterministic ✓

## Metrics
- Tests: 1124 → **1210** (+86); pass rate 100%; coverage 95.20% → **95.26%**
- Module mới: `harness/execution/` 7 file (~600 LOC)
- Failures gặp khi implement: namespace mislabel (plan cho graph), events candidates prefix, EventService __call__ (tránh bằng duck-typing), pytest addopts coverage

## Bài học
1. Duck-typing tránh được allow-list mở rộng cho events — Protocol + instance wiring là đủ
2. Test arch behavioral (persist-before-raise) phải dùng literal cụ thể (`raise VerificationError(`) — docstring chứa "raise" làm assertion sai
3. `model_construct` bypass pydantic enum để test nhánh unknown kind
4. Coverage toàn suite tăng dù thêm module mới — test mới phủ đủ 6 module execution

## Kết luận
**TASK-030 HOÀN TẤT** — 10/10 AC, hard gate đầy đủ (spec v3 → critique ×2 → review APPROVED → implement → test → evaluate).
