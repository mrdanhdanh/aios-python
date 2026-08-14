# STATS.md — Tổng hợp tiến độ

> Cập nhật định kỳ (mỗi milestone hoặc theo yêu cầu). Dữ liệu cho đánh giá hệ thống.

## M0 — Development Foundation

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 1 (TASK-001) |
| Task done | 1 |
| Số critique đã resolve | 2 / 2 |
| Bypass đã dùng | 1 |
| Commit | 5 |

## M1 — Core Runtime ✅

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 9 (TASK-002 → 009) — **TẤT CẢ done** |
| Task done | 9/9 |
| Tests (cuối M1) | **346 pass — coverage 95.30%** |
| Critique resolve | 9 task × 2 vòng (trung bình 20+ vấn đề/task) |
| Review | 9 task (0-1 R1 mỗi task) |
| Bypass | 0 |
| Deliverable M1 | `aiagent run workflow.yaml --simulate` ✓ |
| Commit | ~30 commits |
| Critique resolve (TASK-004) | v1: 11 (2 P1 + 6 P2 + 3 P3); v2: 15 (1 P1 + 6 P2 + 8 P3) |
| Review (TASK-004) | 0 R1 + 5 R2 + 6 R3 — resolved trước implement |
| Bypass đã dùng | 0 |
| Commit | TASK-004: 1 (eb64795) |

## Ghi chú

- Thống kê mở rộng theo milestone; cập nhật sau mỗi task.

## Bài học (lessons learned)

> Nguồn: `evaluation.md` của từng task.

1. **Critique ×2 tìm ra vấn đề thật, kể cả task "nhỏ"**: gitignore chặn cả `.vscode/` sẽ gây khó từ M1; rule phân loại TASK vs fix nhỏ thiếu → agent tự quyết tùy hứng. Không nên bỏ qua phản biện.
2. **Cần rule định lượng để agent phân loại công việc**: "> 30 phút hoặc chạm nhiều file → TASK mới; ngược lại → bypass ghi log" — giúp nhất quán, dễ đánh giá.
3. **Tách rõ verify "tự động" vs "thủ công" ngay trong test.md**: AC về agent picker cần người dùng xác nhận — ghi rõ để không bị bỏ sót.
4. **TASK tự dogfood quy trình** (chính task này đi qua đủ 8 bước) — hiệu quả, phát hiện lỗi quy trình ngay khi tạo quy trình.
5. **Commit thường xuyên theo bước** (4 commit cho M0) — mỗi bước hoàn chỉnh là một mốc khôi phục được.
6. **Claim kỹ thuật phải kiểm chứng bằng spike test** — `extra="forbid"` bắt typo env là claim SAI cơ chế (pydantic-settings v2), critique-2 bắt được.
7. **pydantic v2**: default callable phải dùng `Field(default_factory=...)`; truyền `None` override default — helper phải filter.
8. **hatchling không cho readme ngoài project dir** — README package đặt trong `backend/`.
9. **Bảng AC ↔ checklist trong review** giúp phát hiện bước thiếu (VD thiếu venv step) trước khi code.
10. **pydantic v2: validator method trùng tên trong subclass REPLACE validator kế thừa** (key theo tên method) — đổi tên hoặc khai báo lại.
11. **pydantic v2 clears `__abstractmethods__`** khi complete model — ABC không enforce trên BaseModel; dùng `validate()` runtime làm enforcement point.
12. **Class không định nghĩa `__init__` (kế thừa object) có `*args/**kwargs`** — container phải skip, không ném lỗi varargs.
13. **Shallow copy dict trong test**: `dict(VALID_DATA)` share nested list → mutation test đầu hỏng test sau; luôn deepcopy.
14. **2 vòng critique có giá trị cộng dồn**: vòng 2 bắt mâu thuẫn do chính resolution vòng 1 tạo ra — không gộp được.
15. **Model validator raise ValueError → pydantic wrap thành ValidationError** ("Value error, ...") — match regex theo nội dung thật.
16. **Path guard phải dùng `is_relative_to` sau resolve** — `startswith` prefix string bị bypass bằng thư mục sibling (`artifacts2`).
17. **Persistence phải có cơ chế tường minh từ spec** — `list()` cần sidecar, không thể tự bịa lúc code.
18. **Một khái niệm một định nghĩa** — "pending" xuất hiện 3 chỗ với 2 nghĩa; spec phải nhất quán.
19. **Timebase không trộn**: metadata `created: datetime` + TTL `_created_mono` (monotonic) tách bạch.
20. **EventBus.publish nhận Event object** — wrapper service phải tạo Event trước.
21. **Tên biến unpack phải khớp ngữ nghĩa index** — in-index lưu (rel, source_kind, source_id): dùng `_sk, source_id`, không dùng tk/ti chung.
22. **Fixture tên ngắn dễ conflict** — g/cat thiếu tham số → FixtureFunctionDefinition; tên rõ + tham số tường minh.
23. **Thread-safe test: id phải unique theo thread** — agent-{i} × 2 thread = 50 unique không phải 100.
24. **Regex lookaround + scan escape-first** — validate template lúc construct (object hỏng không tồn tại).

## M2 — Developer Edition ✅ (2026-08-13)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 6 (TASK-010, 012, 016, 013, 014, 015) — TẤT CẢ done |
| Task done | 6/6 |
| Tests (cuối M2) | **669 pass — 0 skip — coverage 95.51%** |
| Critique resolve | 6 task × 2 vòng: 16+31+23+25+27+27 = **149 vấn đề resolved** |
| Review | 6 task (TASK-016/013/015 CHANGES REQUESTED → R1 fix) |
| Bypass | 1 (test scope_isolation) |
| Invariants | **INV-001..010 chốt + 4 allow-list tests bật** (agents/tools/skills/sandbox) |
| Deliverable M2 | Decision Pipeline + 4 assistants + 6 tools + skills lifecycle + sandbox pool ✓ |
| Commit | ~36 commits |

## Bài học M2 (bổ sung)

25. **Allow-list AST check top-level không bắt module con** — `urllib.request` lọt qua external check; phải AST walk module con (R3 TASK-014).
26. **Cấm trần `from aios_core import X`** — scanner trả "aios_core" ∉ allow-set → phải dùng dotted import (C2-01 TASK-015).
27. **Optimistic concurrency cho multi-instance SQLite** — RLock chỉ serialize 1 instance; `UPDATE WHERE state=old` + rowcount==0 (R2 TASK-015).
28. **DB CHECK chỉ enforce domain, không enforce transition** — đừng claim "enforce 2 tầng" quá mức (C1-02 TASK-015).
29. **Extractor substring phải lọc keyword con** — "sốt" ⊂ "sốt cao" sau longest-match (TASK-013).
30. **No-exec marker test phải assert đúng chiều** — "marker VẪN tồn tại" (không exec), không phải "không tồn tại" (C1-01 TASK-014).
31. **Evict idle test dùng time.monotonic() base** — không số giả (TASK-015).
32. **PowerShell Set-Content phá encoding tiếng Việt** — tuyệt đối không dùng để sửa file markdown có dấu; dùng công cụ edit (bài học đắt giá TASK-015).
33. **Dependent check khi rollback/remove** — constraint vỡ âm thầm nếu không quét dependents (R1 TASK-015).
34. **Gate fail-closed: gate None/False/RAISE đều DENY** — không side effect không kiểm soát (TASK-014).
35. **System Brain pattern** — Orchestrator hỏi qua Catalog→KG→SystemKnowledge, không đọc registry trực tiếp (TASK-016).

## M3 — Desktop Edition ✅ (2026-08-13)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 3 (TASK-017 API, 018 Dashboard, 019 Extension) — TẤT CẢ done |
| Task done | 3/3 |
| Tests | Backend **689 pass — 95.10%**; Dashboard vitest **12/12**; Extension vitest **19/19** + tsc clean + build emit |
| Critique resolve | 3 task × 2 vòng (TASK-019: 13+3; TASK-018: —; TASK-017: —) |
| Review | 3 task (TASK-019 CHANGES REQUESTED → 3 R2 + 7 R3 resolved) |
| Bypass | 1 (vitest require → import) |
| Deliverable M3 | FastAPI REST+WS, Dashboard 10 tabs, VS Code extension 9 lệnh ✓ |
| Commit | 3 (16c998f, 33b6b05, 298e4bb) |

## M4 — Platform Edition ✅ (2026-08-13)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 3 (TASK-020 Upgrade, 021 Observability, 022 Orchestrator v2) — TẤT CẢ done |
| Task done | 3/3 |
| Tests (cuối M4) | **809 pass — 0 skip — coverage 94.92%** (M2: 669 → M4: +140 test) |
| Critique resolve | TASK-020: 31 vấn đề (9 P1); TASK-021: 36 (9 P1); TASK-022: 24 (7 P1) = **91 vấn đề resolved** |
| Review | 3 task (020 CHANGES REQUESTED 1R1+3R2; 021 APPROVED có điều kiện 3 amendment; 022 APPROVED có điều kiện 1R2+3R3) |
| Bypass | 1 (fix `_metrics()` db suffix — R2-1 TASK-022) |
| Invariants | +2 allow-list tests (upgrade/ + observability/) — tổng 6 allow-list |
| Deliverable M4 | Upgrade pipeline 6 bước + Observability (metrics/prompt-history/profiler/doctor/arch-health/eval v2) + Orchestrator v2 (advisor/supervisor/collector/goal reporter) ✓ |
| Commit | 5 (f1f8f90, 362cdb3, f46e086, 9145637 + cleanup) |

## M5 — Core Intelligence ✅ (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 6 (TASK-023 Memory/Context, 024 Context Optimizer, 025 Model Router, 026 Planning, 027 Execution Graph, 028 Parallel Scheduler) — TẤT CẢ done |
| Task done | 6/6 |
| Tests (cuối M5) | **1086 pass — coverage 95.22%** (M4: 809 → M5: +277 test) |
| Critique resolve | 6 task × 2 vòng (~180 vấn đề) — spec-writer/critic/reviewer subagent 5 lần không phản hồi → orchestrator tự viết/phản biện/review độc lập (ghi rõ trong file) |
| Review | 6 task (028 CHANGES REQUESTED 1R1; còn lại APPROVED có điều kiện) |
| Invariants | INV-011..016 + 6 allow-list (memory/context/models/router/planning/graph/scheduler) |
| Deliverable M5 | Memory Coordinator + Context Optimizer + Model Router + Planning Engine + Execution Graph + Parallel Scheduler ✓ |
| Commit | 6 (0e9e7d2, 352d251, a73563d, 012a584, 53c13c7, 06602d9) |

## M6 — AIOS Harness ✅ (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 6 (TASK-029 Harness Kernel, 030 Execution Verification, 031 Test & Simulation, 032 Evaluation, 033 Benchmark + Regression Gate, 034 Doctor & Readiness) — TẤT CẢ done |
| Task done | 6/6 |
| Tests (cuối M6) | **1521 pass — coverage 95.35%** (M5: 1086 → M6: +435 test) |
| Critique resolve | 6 task × 2 vòng — spec-writer/critic/reviewer subagent không phản hồi phần lớn phiên → orchestrator tự phản biện/review độc lập (ghi rõ trong file, hard gate giữ nguyên) |
| Review | 6 task (029 CHANGES REQUESTED 1R1; 030 APPROVED có điều kiện 2R2; còn lại APPROVED) |
| Invariants | INV-017 Harness Isolation · INV-018 Evidence First · INV-019 Verification Before Verdict · INV-020 Evaluation Determinism · INV-021 Release Gate + doctor INV-022 (13 kinds, policy gate) |
| Harnesses đăng ký | 6: verification, test, evaluation, benchmark, doctor, readiness |
| Deliverable M6 | harness/ 4 subsystem (execution, testing, evaluation, benchmark, doctor) + evidence mọi run (INV-018) + replay + scenario/simulation + trajectory + regression gate + readiness score ✓ |
| Commit | 6 (b62ac75, 117fbfe, c543816, 9c7f3e0, b8762f1, + cuối) |

## Bài học M3-M4 (bổ sung)

36. **VS Code Selection không có `.text`** — phải `document.getText(selection)`; stub test theo API thật, không bịa (P1 TASK-019).
37. **vitest ESM: `require()` module TS fail** — dùng `import` (TASK-019).
38. **Hook-injection giữ allow-list sạch** — upgrade/observability không import skills/catalog: wiring cung cấp hook/lookup (TASK-020/021).
39. **"Chỉ migrate ROOT, dependency chỉ resolve"** — resolve full closure nhưng mutation chỉ root, tránh vỡ state machine (C2-03 TASK-020).
40. **Event-driven aggregation: duration từ Event.timestamp** — start/finish ghép theo execution_id, UPDATE row mới nhất (re-run an toàn) (TASK-021).
41. **AST scan engine 1 nguồn sự thật** — move `_arch_scan.py` vào src, tests dùng shim (P1-5 TASK-021).
42. **Move file đổi SRC_ROOT phải tính lại parents** — parents[2] khi sâu hơn 1 cấp (P1-1 TASK-021 critique-2).
43. **`in (set1, set2)` là tuple membership, không phải set union** — bug tool metrics (TASK-021).
44. **DB suffix convention phải khớp giữa wiring và CLI** — `db_path + ".metrics"`; CLI đọc sai DB = số liệu 0 âm thầm (R2-1 TASK-022).
45. **Supervisor timebase: clock() float monotonic tách khỏi datetime** — trộn 2 loại = TypeError (P1-1 TASK-022).
