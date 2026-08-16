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

## M4 — Review độc lập (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Review type | Self-review (AIOS Orchestrator), đọc code + chạy test + chạy scanner cây thật |
| Findings | 1 P1 (F1) + 2 P3 (F2, F3) |
| F1 (P1) | `ArchitectureHealth.scan()` skip silent layer/contract check trên cây thật (base-dir mismatch `backend/src/agents` không tồn tại) + `rel` dot-form sai định dạng cho `collect_imports`. **ĐÃ TỰ SỬA** (aios_root + slash-form + exempt slash-form) |
| F2 (P3) | `orchestrator/__init__.py` không export module M4 (inconsistency, không phải bug) |
| F3 (P3) | advisor rule 1+5 dedup collapse (đúng spec) |
| Test regresi thêm | 2 (`test_nested_aios_core_layout_scans_layer_violations`, `test_nested_aios_core_layout_policy_check`) |
| Full suite sau fix | **1636 passed, 0 fail** |

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

## M5 — Review độc lập (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Review type | Self-review (AIOS Orchestrator), đọc code + chạy test + chạy scanner cây thật |
| Findings | 1 P2 (F1) + 1 P3 (F2) |
| F1 (P2) | runtime `ArchitectureHealth.scan()` không cover M5 packages — vi phạm PLAN §M5 "observability đầy đủ". **ĐÃ TỰ SỬA** (thêm 6 M5 layer rule vào `observability/arch_health.py` + 6 test regresi `tests/test_observability_arch_health.py`) |
| F2 (P3) | M5 thiếu milestone review doc (M0/M3/M4 có) — process. **ĐÃ TỰ SỬA** (viết `reviews/M5-review.md` + `reviews/M5-review-brief.md`) |
| Test regresi thêm | 6 (`test_m5_real_src_healthy`, `test_m5_memory_isolation_fires`, `test_m5_context_no_knowledge_fires`, `test_m5_planning_no_models_fires`, `test_m5_graph_no_orchestrator_fires`, `test_m5_scheduler_no_orchestrator_fires`) |
| Verify sau fix | scanner `SRC_ROOT` → `healthy=True, 0 violations`; 15/15 arch-health test pass (gồm 6 mới); 335 arch+M5 test pass |
| Kết luận | **M5 ĐẠT** V1–V8 (sau F1); không P1 |

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
| Milestone review (2026-08-15) | **TỰ REVIEW** — đọc code TASK-029..034 + spec, chạy 406 harness + 29 INV-017..022 arch + 18 observability scanner = 424 test (đều pass) |
| Findings | 1 P2 (F1) + 2 P3 (F2 đánh số INV-022 overlap M7; F3 thiếu review doc) |
| F1 (P2) | runtime `ArchitectureHealth.scan()` không cover `harness/` packages — vi phạm PLAN §M6 "observability đầy đủ" (gap tương tự M5 F1). **ĐÃ TỰ SỬA** (thêm 1 M6 `harness` layer rule vào `observability/arch_health.py` + 3 test regresi `tests/test_observability_arch_health.py`) |
| F2 (P3) | Doctor gán INV-022 overlap với M7 Identity First (PLAN/ADR: M6=INV-017..021, M7=INV-022..029) — observation, không renumber (behavior đúng, test pass) |
| F3 (P3) | M6 thiếu milestone review doc (M0/M3/M4/M5 có) — process. **ĐÃ TỰ SỬA** (viết `reviews/M6-review.md` + `reviews/M6-review-brief.md`) |
| Test regresi thêm | 3 (`test_m6_real_src_healthy`, `test_m6_harness_isolation_fires`, `test_m6_harness_no_control_plane_fires`) |
| Verify sau fix | scanner `SRC_ROOT` → `healthy=True` cho harness (0 violations); 18/18 arch-health test pass (gồm 3 mới); 424 M6 test pass |
| Kết luận | **M6 ĐẠT** V1–V8 (sau F1); không P1 |

## M7 — Enterprise ✅ (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 8 (TASK-035 Identity, 036 Tenancy, 037 Distributed Runtime, 038 Distributed Scheduler, 039 Governance, 040 Security, 041 Operations, 042 Operations+Dashboard) — TẤT CẢ done |
| Task done | 8/8 |
| Tests (cuối M7) | **1560 pass — coverage 95.05%** (M6: 1521 → M7: +39 test enterprise + 8 INV) |
| Invariants | INV-022 Identity First · INV-023 Tenant Isolation · INV-024 Credential Isolation · INV-025 Resource Fairness · INV-026 Distributed Execution Safety · INV-027 Audit Completeness · INV-028 Sandbox Boundary · INV-029 Control Plane Isolation |
| Package | `backend/src/aios_core/enterprise/` (identity/tenancy/runtime/scheduler/governance/security/operations/dashboard/contracts + `EnterpriseManager` facade) |
| Deliverable M7 | enterprise/ 7 nhóm (E1–E7) + 8 invariant + tenant dashboard + audit tamper-evident + lease/failover ✓ |
| Commit | M7 impl (1) + review fix (1) |
| Milestone review (2026-08-15) | **TỰ REVIEW** — đọc code TASK-035..042 + spec, chạy 29 enterprise + 8 INV-022..029 + 2 package-level + 3 new arch-health regresi = 42 M7-related test (đều pass) |
| Findings | 1 P2 (F1 scanner không cover enterprise) + 1 P2 (F2 thiếu implementation/ hard-gate) + 1 P3 (F3 nhãn INV-022 xung đột M6/M7) |
| F1 (P2) | runtime `ArchitectureHealth.scan()` không cover `enterprise/` — vi phạm PLAN §M7 "observability đầy đủ" (gap tương tự M5/M6 F1). **ĐÃ TỰ SỬA** (thêm 1 `enterprise` layer rule vào `observability/arch_health.py` + 3 test regresi `tests/test_observability_arch_health.py`) |
| F2 (P2) | TASK-035..042 thiếu `implementation/` (8th hard-gate file) — mirrors M3 F1. **ĐÃ TỰ SỬA** (thêm `implementation/README.md` cho 8 folder) |
| F3 (P3) | 4 test M6-H5 (TASK-034) dùng nhãn `test_inv022_*` (INV-022 của M7) → M7 phải rename `test_m7_inv022..`. **ĐÃ TỰ SỬA** (rename 4 test M6-H5 → INV-017/018/021 đúng nhãn; rename M7 `test_m7_inv022..` → `test_inv022..` canonical; rewrite comment) |
| Test regresi thêm | 3 (`test_m7_real_src_healthy`, `test_m7_enterprise_isolation_fires`, `test_m7_enterprise_no_orchestrator_fires`) |
| Verify sau fix | scanner `SRC_ROOT` → `healthy=True, 0 violations` (enterprise đã cover); 42/42 M7 test pass; 150 pass cho enterprise+arch-health+architecture |
| Kết luận | **M7 ĐẠT** V1–V7 PASS; V8 P2→RESOLVED (F1/F2/F3); không P1 |

## M8 — Ecosystem ✅ (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 7 (TASK-043 Public SDK, 044 Plugin Runtime, 045 Extension Contracts, 046 Ecosystem Registry, 047 Developer Kit, 048 Marketplace/Hub, 049 Certification) — TẤT CẢ done |
| Task done | 7/7 |
| Tests (cuối M8) | **1639 pass** (M7: 1560 → M8: +79 test) |
| Invariants | Tái dụng INV-022..029 (Enterprise) làm ecosystem boundary guardrails — M8 KHÔNG định nghĩa invariant mới |
| Packages | `sdk/python/` + `plugins/` + `extension/` + `ecosystem/` (registry/devkit/marketplace/certification) |
| Deliverable M8 | Public SDK + Plugin Runtime (reuse SkillState) + Extension Contracts (namespace/matrix fail-closed) + Ecosystem Registry + Developer Kit + Marketplace (9-step trust chain + HMAC) + Certification (Harness gate M6) ✓ |
| Commit | M8 impl (1) + review fix (1) |
| Milestone review (2026-08-15) | **TỰ REVIEW** — đọc code TASK-043..049 + spec, chạy 62 functional + 20 m8/INV-022..029 arch + 25 observability scanner = 107 M8 test (đều pass) |
| Findings | 1 P2 (F1) + 2 P3 (F2 thiếu review doc; F3 tái dụng INV-022..029 không conflict) |
| F1 (P2) | runtime `ArchitectureHealth.scan()` không cover `plugins/`/`extension/`/`ecosystem/` — vi phạm PLAN §M8 "observability đầy đủ" (gap tương tự M5/M6/M7 F1). **ĐÃ TỰ SỬA** (thêm 3 M8 layer rule vào `observability/arch_health.py` + 4 test regresi `tests/test_observability_arch_health.py`) |
| F2 (P3) | M8 thiếu milestone review doc (M0/M3/M4/M5/M6/M7 có) — process. **ĐÃ TỰ SỬA** (viết `reviews/M8-review.md` + `reviews/M8-review-brief.md`) |
| F3 (P3) | M8 tái dụng INV-022..029 (Enterprise) làm ecosystem boundary — không invariant mới, không conflict (M7 review F3 đã chuẩn hóa nhãn) — observation |
| Test regresi thêm | 4 (`test_m8_real_src_healthy`, `test_m8_plugins_isolation_fires`, `test_m8_extension_isolation_fires`, `test_m8_ecosystem_isolation_fires`) |
| Verify sau fix | scanner `SRC_ROOT` → `healthy=True` cho M8 (0 violations); 25/25 arch-health test pass (gồm 4 mới); 107 M8 test pass |
| Kết luận | **M8 ĐẠT** V1–V8 (sau F1); không P1 |

## M9 — Autonomous ✅ (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 13 (TASK-050 Goal, 051 Planner, 052 World, 053 Loop, 054 Governor, 055 Recovery, 056 Long-Horizon, 057 Memory, 058 Experimentation, 059 Multi-Agent, 060 Evaluation, 061 Stuck, 062 Scheduler) — TẤT CẢ done |
| Task done | 13/13 |
| Tests (cuối M9) | **1780 pass — coverage 94.46%** (M8: 1639 → M9: +141 test autonomous + 9 INV) |
| Invariants | INV-030 Governor Gate · INV-031 Autonomy Budget · INV-032 Long-Horizon Checkpoint/Resume · INV-033 Evidence-First Self-Improvement · INV-034 Memory⇸Unverified Knowledge |
| Package | `backend/src/aios_core/autonomous/` (goal/planner/world/loop/governor/recovery/long_horizon/memory/experimentation/evaluation/multi_agent/stuck/scheduler/contracts/errors + `AutonomyManager` facade) |
| Deliverable M9 | autonomous/ 4 phase (P1 foundation, P2 long-running, P3 adaptive, P4 ecosystem) + 5 invariant + 8-step governor-gated loop + circuit breaker + checkpoint/resume + 6-kind memory + experimentation canary + multi-agent delegation + proactive scheduler ✓ |
| Commit | M9 impl (1) + review fix (1) |
| Milestone review (2026-08-15) | **TỰ REVIEW** — đọc code TASK-050..062 + spec, chạy 129 autonomous + 9 INV-030..034 arch + 3 new arch-health regresi = 141 M9-related test (đều pass); full suite 1793 pass |
| Findings | 1 P2 (F1 scanner không cover autonomous) + 2 P3 observation (F2/F3 không apply — TASK-050..062 đã đủ 8-file, INV-030..034 không collision) |
| F1 (P2) | runtime `ArchitectureHealth.scan()` không cover `autonomous/` — vi phạm PLAN §M9 "observability đầy đủ" (gap tương tự M5/M6/M7/M8 F1, chưa áp dụng cho M9). **ĐÃ TỰ SỬA** (thêm 1 `autonomous` layer rule vào `observability/arch_health.py` + 3 test regresi `tests/test_observability_arch_health.py`) |
| F2 (P3 observation, không apply) | TASK-050..062 ĐỦ 8-file hard gate (implementation/ CÓ — M9 học từ M7 F2, không lặp lại) |
| F3 (P3 observation, không apply) | nhãn INV-030..034 KHÔNG xung đột (canonical, cuối cùng trước M10 freeze); test `test_inv030..inv034_*` không collision với milestone khác |
| Test regresi thêm | 3 (`test_m9_real_src_healthy`, `test_m9_autonomous_isolation_fires`, `test_m9_autonomous_no_worker_plane_fires`) |
| Verify sau fix | scanner `SRC_ROOT` → `healthy=True, 0 violations` (autonomous đã cover); 3/3 new test pass; full suite 1793 pass |
| Kết luận | **M9 ĐẠT** V1–V7 PASS; V8 P2→RESOLVED (F1); không P1 |

## M10 — AIOS 1.0 ✅ (2026-08-15)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 13 (TASK-063 Freeze, 064 Contract 1.0, 065 Hardening, 066 Durable, 067 Safety, 068 Kill Switch, 069 SLO, 070 Security, 071 DX, 072 Dashboard, 073 Certification, 074 Migration, 075 Perf&Cost) — TẤT CẢ done |
| Task done | 13/13 (đủ 8-file hard gate mỗi task) |
| Tests (cuối M10) | **1939 pass** (M9: 1793 → +146) + dashboard vitest 13/13 + extension 19/19 |
| Phase | P1 Freeze (063,064) → P2 Harden (065,066,069) → P3 Secure (067,068,070) → P4 Productize (071,072,075) → P5 Certify (073,074) — 5 commit phase |
| Invariants | **Freeze INV-001..034** (Constitution 1.0 — vi phạm = release blocker; +2 enforcement test INV-008/012 bổ sung) |
| Deliverable | `aiagent conformance` → **AIOS 1.0 READY** (9/9 areas · 20/20 GS-001..020 · 5/5 gates A–E); `aiagent health` 100/100; `aiagent contract check` breaking 0; `aiagent slo` READY; `aiagent security-check` SECURE; `aiagent migrate`; `aiagent cost/performance`; `aiagent stop/emergency-stop`; Dashboard 11 tabs + Execution Timeline |
| Package mới | `harness/certification/` · `security/` · `cli/` · `kernel/{durability,kill_switch,hardening}.py` · `contracts/{catalog,check}.py` · `observability/{slo,performance}.py` · `upgrade/migration.py` · `api/routers/m10.py` |
| Milestone review (2026-08-15) | **TỰ REVIEW** — full suite 1939 + conformance READY + doctor 100/100 + contract 0 breaking |
| Findings | 1 P2 (F1: 2 invariant chưa enforce trực tiếp — INV-008/012 → +2 test) + 2 P3 (F2 certification layer rule; F3 auth/authz WARN ghi nhận 1.1) |
| Kết luận | **M10 ĐẠT (ACCEPTED)** — không P1; AIOS 1.0 READY |

## M11 — Deterministic Artifact & Interaction Runtime ✅ (2026-08-16, Issue #4)

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 6 (TASK-078 Verification Fail-Closed, 079 RenderReplay/DeterministicHarness, 080 VisualEvidence+UIState, 081 Asset Capability Architecture, 082 Creative+Vendor+Reference, 083 SkillDistiller+StaticDeploy) — TẤT CẢ done |
| Task done | 6/6 (đủ 8-file hard gate mỗi task) |
| Tests (cuối M11) | **2052 pass** (M10: 1939 → +113: 30+18+16+15+16+18 unit mới) |
| Phase | P0 Verification Integrity (078) → P1 Deterministic Visual Runtime (079) → P2 Visual Observability (080) → P3 Asset Capability (081) + P3b/c/d (082) → P4 Ecosystem & DX (083) — 6 commit phase |
| Invariants | **+INV-035** (Verification Fail-Closed — Core Invariant MỚI, không vi phạm INV-001..034): Verification State Model (PASS duy nhất terminal success; FAIL/ERROR/BLOCKED; non-terminal UNKNOWN/NOT_EXECUTED/MISSING_EVIDENCE/SKIPPED — cấm → PASS) |
| Deliverable | `aiagent conformance` → **AIOS 1.0 READY** (10/10 areas — +verification · 20/20 GS · 6/6 gates — +gate_f_verification); `aiagent verify-state` (INV-035 fail-closed YES); `aiagent render-replay` (stable=True); `aiagent visual-probe` (bắt state_diff scale 3→2); `aiagent asset list/match/produce` (skill agent-sprite-forge thật); `aiagent reference describe`; `aiagent skill distill`; `aiagent deploy --static`; `aiagent security-check` SECURE (12 checks — +vendor_integrity R8) |
| Package mới | `verification/` (Verification Kernel INV-035) · `rendering/` (asset/contracts/evidence/harness/idempotency/matcher/prng/probe/reference/registry/replay/timeline/ui_state/workflows) · `observability/visual.py` · `ecosystem/{distiller,deploy}.py` |
| Nâng cấp R1–R12 | **12/12 xong**: R2 INV-035 · R3 RenderReplay/DeterministicHarness · R1 VisualEvidence/VisualRegressionProbe · R10 UI State Contract · R9 AssetPipeline Contract · R4 Asset Registry · R11 Discovery/Routing · R6 Creative Domain · R8 Vendor Integrity · R12 Reference-Asset · R5 SkillDistiller · R7 Static Deploy |
| Roadmap | P0 → P1 → P2 → P3 → P4 đủ 5 tầng (dependency R2→R3→(R10∥R1)→R9→(R4∥R11)→R6→(R8∥R12)→R5→R7) |
| Milestone review | **TỰ REVIEW** — full suite 2052 + conformance READY (10 areas/6 gates) + doctor healthy + arch-health 0 violations + security SECURE |
| Findings | 0 P1/P2 — 3 bài học chính: (1) allow-list M8 ecosystem chỉ semver/metadata (arch scanner bắt distiller import skills → mirror validation); (2) deploy marker `.aios/` phải exclude khỏi manifest (determinism); (3) pre-route creative phải optional (`creative_matcher=None` → hành vi cũ) |
| Kết luận | **M11 ĐẠT (ACCEPTED)** — 6/6 task, 81 task toàn dự án |

## Tổng kết toàn dự án (M0–M11)

| Chỉ số | Giá trị |
|--------|---------|
| Milestone | 12/12 done (M0–M11) |
| Task | **81 task** (M0:1, M1:9, M2:7, M3:3, M4:3, M5:6, M6:6, M7:8, M8:7, M9:13, M10:13, M11:6) |
| Tests | **2052 pytest + 13 vitest dashboard + 19 vitest extension** |
| Invariants | INV-001..035 (Constitution 1.0 + M11 amendment INV-035) |
| Deliverable cuối | `aiagent conformance` → **AIOS 1.0 READY** (10 areas · 20 GS · 6 gates) |

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
