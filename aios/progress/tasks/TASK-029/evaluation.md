# TASK-029 — Evaluation (Harness Kernel, H1)

**Ngày**: 2026-08-15 | **Trạng thái**: DONE ✅

## Đối chiếu tiêu chí chấp nhận (10/10 AC pass — xem test.md)

| AC | Kết quả | Bằng chứng |
|----|---------|------------|
| AC1 Contracts | ✅ | TestContracts (5 test) |
| AC2 Errors | ✅ | hierarchy |
| AC3 Lifecycle | ✅ | TestLifecycle (6 test — 8×8 matrix) |
| AC4 Context | ✅ | TestContext (4 test) |
| AC5 Registry | ✅ | TestRegistry (4 test) |
| AC6 Runner + INV-018 | ✅ | TestRunner (11 test) + test_inv018_every_run_has_evidence |
| AC7 Queries | ✅ | get_run/get_result/get_evidence + restart fallback |
| AC8 INV-017 | ✅ | 5 arch test + duck-typed stub |
| AC9 Wiring | ✅ | test_harness_wired + 1124/95.20% |
| AC10 Deterministic | ✅ | trừ timestamps + ref (B2) |

## Đánh giá so với PLAN.md §M6-2
- **H1 Harness Kernel** đúng PLAN: contract chung `Harness → Context · Run · Event · Result · Artifact · Report` — 6 contract + lifecycle + registry + runner; không harness nào tự tạo infrastructure riêng (TASK-030..034 kế thừa)
- **Harness lifecycle** đúng: CREATED→PREPARING→VALIDATING→RUNNING→VERIFYING→COMPLETED; RUNNING→FAILED→DIAGNOSED (+ mở rộng mọi phase → FAILED — D4, COMPLETED→FAILED — C1-02, CREATED→FAILED — B1)
- **HarnessRun** đầy đủ: run_id/harness/target/version/environment/started_at/status — truy ngược Release → Run → Trace → Evaluation → Failure
- **INV-017 Harness Isolation**: harness/ chỉ import config + kernel.services.state/artifacts + contracts.artifact — KHÔNG chui execution/resource/scheduler/policy/permissions/context — AST 5 test + behavioral
- **INV-018 Evidence First**: mọi run (kể cả FAILED/DIAGNOSED) tạo ≥ 2 HarnessArtifact (events + report) qua ArtifactService — checksum tamper-evident, restart-safe fallback

## Bài học
1. **Vị trí lệch PLAN có lý do**: `aios_core/harness/` thay vì `aios/harness/` root (packaging/arch-scan single root) — quyết định mở qua critic, được chấp nhận
2. **Windows path chars**: run_id chứa `:` → OSError 123 — sanitize regex toàn bộ ký tự bất hợp lệ (B4)
3. **Evidence phải trong finally** — hook on_failure/diagnose raise không được chặn evidence (C1-03 — 2 lần critic bắt)
4. **Pydantic PrivateAttr** cho sink — model_dump không serialize callable
5. **Catch-all exception policy** ngoài hook → FAILED từ phase hiện tại (B1) — mọi đường code đều có status hợp lệ

## Đề xuất cho task sau
- **TASK-030 (H2 Execution Verification)**: dùng HarnessRunner + HarnessRun + evidence — thêm Verification contract (Preconditions/Postconditions/Verdict) + Evidence Package + Replay
- **TASK-031..034 (H3-H5)**: kế thừa contracts/lifecycle/registry/runner — allow-list harness/ đã phủ subdir (rglob)

## Kết luận
- [x] ĐẠT spec (10/10 AC)
- [x] INV-017/018 enforced; additive only
- [x] Coverage 95.20% (toàn suite 1124 pass)
