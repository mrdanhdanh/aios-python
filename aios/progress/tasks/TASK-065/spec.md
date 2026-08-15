# TASK-065 — M10-F3: Runtime Hardening (Failure Matrix)

## Mục tiêu
PLAN §M10-11/12: 9 services phải chứng minh hoạt động ĐÚNG khi gặp lỗi thật. Failure Matrix 12 loại (Model chết · Tool chết · Agent chết · Process chết · Network mất · Database mất · Plugin lỗi · Worker timeout · Resource hết · Memory corruption · Checkpoint lỗi · Event consumer chết) với mục tiêu: `failure → detect → contain → recover → resume` (KHÔNG `entire execution lost`).

## Phạm vi
- `kernel/hardening.py`: `FailureKind` (12 loại) + `FailureScenario` (id, kind, target, fault_fn, detect_fn, contain_fn, recover_fn) + `FailureMatrix` (registry 12 scenario) + `HardeningRunner` (chạy scenario trên RuntimeKernel thật: inject fault → verify detect → contain → recover → resume; trả `ScenarioOutcome`)
- Scenario target dùng component thật: ModelRegistry (model chết), ToolRegistry/tool (tool chết), AgentRegistry (agent chết), EventBus consumer (consumer chết), StateService/ExecutionService (checkpoint lỗi), ResourceService (resource hết), SchedulerService (worker timeout), plugins registry (plugin lỗi), SQLite (db mất — dùng temp db bị xóa), ContextService (memory corruption)
- Network mất: tool REST với transport lỗi (mock)
- Process chết: mô phỏng bằng crash-point trong execution (raise + journal resume)

## Ngoài phạm vi
- Không sửa 9 services (chỉ test + failure scenario helpers — additive)
- Không failure injection vào production code path (chỉ test hook)

## Input
- `kernel/services/*` (execution, state, resource, scheduler, event, artifact...)
- `tests/` hiện có (pattern test thật)

## Output
- `backend/src/aios_core/kernel/hardening.py` + `tests/test_hardening.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | FailureMatrix có ĐỦ 12 FailureKind (model/tool/agent/process/network/db/plugin/worker_timeout/resource/memory_corruption/checkpoint/event_consumer) | Unit test set compare |
| AC2 | Mỗi scenario: detect (phát hiện lỗi) → contain (cô lập, không lan) → recover → resume (không chạy lại phần đã xong) | Chạy từng scenario thật |
| AC3 | Ít nhất 8/12 loại có scenario chạy được end-to-end (fault → outcome) trên RuntimeKernel thật | test thật (pytest) |
| AC4 | `HardeningRunner.run_all()` trả outcome per-scenario (PASS/FAIL) + tổng kết; scenario lỗi không crash cả suite | test |
| AC5 | ScenarioOutcome ghi rõ: detect_time, contain, recovered, resumed (bool) | test |
| AC6 | Không sửa hành vi 9 services (regression: full suite pass) | pytest full |
| AC7 | `FailureKind` deterministic, `extra=forbid`, validation (id trùng → raise) | test |
| AC8 | Đóng DoD: LOG.md + PROGRESS.md + commit | checklist |

## Ghi chú
- Process chết/DB mất mô phỏng bằng fault injection có kiểm soát (không kill thật tiến trình pytest).
- "Resume không chạy lại" = verify qua snapshot/journal hiện có (StateService) — checkpoint count trước/sau.
