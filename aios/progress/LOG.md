# LOG.md — Nhật ký hành động dự án AIOS

> Format: `YYYY-MM-DD HH:MM | TASK-xxx | bước | việc đã làm | kết quả | artifact`
> Entry `[bypass]` = fix nhỏ làm nhanh, có lý do.
> Entry mới ghi LÊN ĐẦU file (mới nhất trước).

| Thời gian | Task | Bước | Việc đã làm | Kết quả | Artifact |
|-----------|------|------|-------------|---------|----------|
| 2026-08-13 | M2-review | review-brief | Tạo M2 review brief (template v2): 12 tiêu chí AC từ PLAN.md + deliverable 21 mục + Architecture Compliance (INV-001..010) + Offline-First verification + Anti-fake-test; ghi chú TASK-015 pending → V2/V3 INCONCLUSIVE | done | `reviews/M2-review-brief.md` |
| 2026-08-13 | TASK-014 | T4 | evaluation.md: 14/14 AC, 622 pass + 0 skip, coverage 96.15% | done — commit | `evaluation.md`, `PROGRESS.md` |
| 2026-08-13 | TASK-014 | T3 | 73 test mới (tools_base 13, tool_stubs 22, tool_registry 14, arch allow-list); fix 3 (import Tool, mcp regex, unavailable id) | 622 pass | `backend/tests/` |
| 2026-08-13 | TASK-014 | T1-T2 | tools/ package: base.py (template run 1-6 fail-closed), 6 stub tool (no-exec/ast.parse/urlparse/mock), registry.py (RLock + bind_capabilities ngoài lock); test_architecture.py: allow-list tools/ + urllib AST check | done | `backend/src/aios_core/tools/` |
| 2026-08-13 | TASK-014 | critique+review | critic ×2: 27 vấn đề resolved (1 P1 no-exec assertion ngược, 7 P2...); reviewer APPROVED + 3 lưu ý (duration_s error, gate-raise test, urllib AST) | 17/17 + 10/10 | `critique-1/2.md`, `review.md` |
| 2026-08-13 | TASK-014 | spec | spec-writer: 14 AC, allow-list tools/ cứng, gate fail-closed, binding qua callable | approved | `spec.md` |
| 2026-08-13 | TASK-013 | T4 | evaluation.md: 12/12 AC, 549 pass + 0 skip (INV-001/002 bật), coverage 96.03% | done — commit | `evaluation.md`, `PROGRESS.md` |
| 2026-08-13 | TASK-013 | T3 | 47 test mới (base 9, coder 11, doctor 12, system 7, registry 8, arch allow-list); fix 5 bài học: state[step_name]+flat merge, MockModel responses, extractor substring (sốt⊂sốt cao), __future__ scanner, danger-only need_more_info | 549 pass | `backend/tests/` |
| 2026-08-13 | TASK-013 | T1-T2 | agents/ package: base (template handle + event sink best-effort), general, coder (7 steps + self-fix, repr-escape, exec ns), doctor (Safety 4 invariants, KB-miss cautious), system_doctor, registry (RLock + selector); test_architecture.py: INV-002 skip chỉ agents/ + allow-list 2 set exclude agents* | done | `backend/src/aios_core/agents/` |
| 2026-08-13 | TASK-013 | critique+review | critic ×2: 25 vấn đề resolved (1 Critical, 5 Major...); reviewer CHANGES REQUESTED → R1.1 (extractor union default KB) + R1.2 (allow-list exclude intra-package) | 14/14 + 11/11 resolved | `critique-1/2.md`, `review.md` |
| 2026-08-13 | TASK-013 | spec | spec-writer: 12 AC, Worker Plane allow-list cứng, wiring registry cạnh AgentSelector | approved | `spec.md` |
| 2026-08-13 | TASK-016 | T4 | evaluation.md: 10/10 AC, 502 pass + 2 skip, coverage 95.96%; bài học rule B (cấm trần == chính xác, prefix cho nhánh) | done — commit | `evaluation.md`, `PROGRESS.md` |
| 2026-08-13 | TASK-016 | T3 | `_arch_scan.py` (SRC_ROOT parents[1] + assert fail-fast; 2 tập full dotted; mọi Import node; dot-boundary) + 12 arch tests; fix rule B chặn nhầm models.base | 12 pass, 2 skip (INV-001/002 chờ agents/) | `backend/tests/_arch_scan.py`, `test_architecture.py` |
| 2026-08-13 | TASK-016 | T1-T2 | architecture.md: §7 10 INV + §1.1 Control/Execution Plane + §3.1-3.3 (KB/KG, Context/Memory, 3 vai) + bảng tiến độ cập nhật; ADR-0004 (4 INV chốt + gap sandbox); PLAN.md link + ADR index 0001..0004 + Architecture Health→M4 | done | `docs/architecture.md`, `docs/adr/0004`, `docs/PLAN.md` |
| 2026-08-13 | TASK-016 | critique+review | critic ×2: 23 vấn đề (1 P1 rule B bypass, 5 P2, ...) resolved; reviewer CHANGES REQUESTED → R1 fix (SRC_ROOT off-by-one parents[2]→[1]) | 13/13 + 10/10 resolved | `critique-1/2.md`, `review.md` |
| 2026-08-13 | TASK-016 | spec | Phân tích 12 điểm user → spec: 10 INV + AST tests + docs reference | approved | `spec.md` |
| 2026-08-13 | TASK-012 | T8 | evaluation.md: 12/12 AC, 490 pass (428+62), coverage 95.96%; xử lý đủ R1-R6; 6 bài học mới | done — commit | `evaluation.md`, `PROGRESS.md` |
| 2026-08-13 | TASK-012 | T7 | 62 test mới (goal 14 / queue 14 / broker 10 / recovery 11 / import+policy 3); fix: subscribe(event_type, handler), query_audit trả Event, COALESCE(MAX,-1)+1, reorder 2 pha, state machine pending→queued→running→completed, history recovery theo spec | 490 pass, 0 fail | `backend/tests/` |
| 2026-08-13 | TASK-012 | T1-T6 | Implement `orchestrator/goals/`: goal.py (state machine + cascade cancel + resume recompute), task_queue.py (dequeue RETURNING, reorder 2 pha, recover_stale_running, enqueue atomic), permission_broker.py (ask_scopes, default-deny no-approver, audit schema C2-04), failure_recovery.py (retry→fallback→report, ERROR mọi fail), schema.py (shared DDL — fix circular import), build_goal_modules; kernel additive: EventType +6, PolicyDecision.ask_scopes 5 nhánh, GoalsSettings + config.yaml | done | `backend/src/aios_core/orchestrator/goals/` |
| 2026-08-13 | TASK-012 | critique+review | critic ×2: 31 vấn đề (3 Critical, 6 Major, 22 Minor) resolved; reviewer APPROVED (R1-R6 bắt buộc xử lý khi code) | 16/16 + 15/15 resolved | `critique-1.md`, `critique-2.md`, `review.md` |
| 2026-08-13 | TASK-012 | spec | spec-writer: 12 AC, wiring Phương án B (constructor injection, không wire RuntimeKernel), 1 DB goals.db 3 bảng | approved | `spec.md` |
| 2026-08-13 | docs | [bypass] | Tạo `docs/architecture.md`: sơ đồ 7 tầng + Orchestrator modules + luồng request + tiến độ milestone theo trạng thái hiện tại (M1 done, M2 in-progress) — lý do: tài liệu tham chiếu, không đổi hành vi hệ thống | done | `docs/architecture.md` |
| 2026-08-12 | TASK-011 | T10 | [bypass] fix test `test_scope_isolation`: đúng thiết kế default `inherit=False`, đổi assertion sang `inherit=True` cho nhánh fallback | done — 428 pass, coverage 95.76% | `tests/test_context.py` |
| 2026-08-12 | TASK-011 | T9 | pytest 428 pass, coverage 95.76%; fix 5 lỗi thật (cli `from_yaml`/`nodes`/`str(_db_path)`; context default `inherit=False`; resource `acquire_slot_wait` chờ ngoài cond-lock; benchmark `get` O(1) thay `tools_for` O(n); dedup `SNAPSHOT_SAVED` emit) | done — 9/9 AC, coverage ≥95% giữ | `backend/tests/`, `backend/src/` |
| 2026-08-12 | TASK-011 | T1-T8 | Implement 9 findings F-001..F-009: cli subcommands (doctor/catalog/workflow validate/contract validate) + DI `RuntimeKernel.create()`; contract field-evolution test; resource FIFO queue + `pending()`; context PARENT inheritance; `SNAPSHOT_SAVED` + `TOOL_STARTED`/`TOOL_FINISHED` events; catalog `rebuild()`/`_revision`/`is_stale()`; 3 ADR + link PLAN.md; benchmark harness | done | `workflow/cli.py`, `kernel/services/`, `catalog/catalog.py`, `docs/adr/`, `tests/test_benchmark.py` |
| 2026-08-12 | TASK-010 | K3 | pytest 402 pass, coverage 94.96%; fix 2 (matcher path bị rule chặn — sửa test; RuntimeError ≠ ModelError) | done — 10/10 AC, offline-first 90% verify | `backend/tests/` |
| 2026-08-12 | TASK-010 | K1-K2 | Implement orchestrator v1: normalizer/rule_engine/workflow_matcher/planner/agent_selector/system_knowledge/orchestrator | done | `orchestrator/` |
| 2026-08-12 | TASK-010 | review | Reviewer: 2 R1 blocking (Yêu cầu #5 dừng cứng mâu thuẫn Phạm vi #5; reset llm_calls chưa pin) + 3 R2 + 8 R3 — resolve hết | done | `tasks/TASK-010/review.md` |
| 2026-08-12 | TASK-010 | critique-2 | Critic v2: 3 P1 (intent None mâu thuẫn #/!skill; Yêu cầu #5; longest vs priority) + 8 P2 + 8 P3 — resolve hết | done | `tasks/TASK-010/critique-2.md` |
| 2026-08-12 | TASK-010 | critique-1 | Critic v1: 3 P1 (false positive substring; matcher không bao giờ chạy; llm_calls/AC6) + 9 P2 + 8 P3 — resolve hết | done | `tasks/TASK-010/critique-1.md` |
| 2026-08-12 | M1-review | [bypass] F-001..F-007 | Remediation M1 findings: thêm 12 test targeted (models/prompts/vector/cli/knowledge_graph) → 358 pass, coverage 95.63%; fix `test_simulate_prints_reason` (patch đúng `aios_core.kernel.services.ExecutionService`); erratum coverage F-001..F-005 trong `M1-review-independent.md` (số subset giả → full-suite thật: graph 98%, cli 95%, ollama 94%, openai 74%, prompts 97%, vector 99%); F-007 thêm hash `a3426de` vào `PROGRESS.md`; F-006 audit LOG TASK-002..009 | done | `backend/tests/`, `reviews/M1-review-independent.md`, `PROGRESS.md` |
| 2026-08-12 | M1-review | [bypass] F-006 | Audit lifecycle TASK-002..009: mỗi task đủ spec→critique×2→review→implement→test→evaluate→commit (số liệu: T002 32 tests/96.14%/commit 7a270ff+486fb9f; T003 107/94.82%/20AC; T004 162/94.77%/commit eb64795; T005 207/95.32%/commit a3426de; T006 233/94.73%; T007 270/94.90%; T008 300/94.92%; T009 346/95.30% — M1 done). Detail evaluation.md mỗi task | done — F-006 addressed | `tasks/TASK-00*/evaluation.md`, `PROGRESS.md` |
| 2026-08-12 | M1-review | review-brief | Tạo M1 review brief (điền từ template): 7 tiêu chí AC từ PLAN.md + deliverable 16 mục (code/test/hồ sơ) + cách kiểm chứng từng tiêu chí | done | `reviews/M1-review-brief.md` |
| 2026-08-12 | M0-review | [bypass] F-004 | Commit M0-review-brief.md (đã sửa nhưng chưa commit — vi phạm AGENTS.md §4) | done — commit 92f1321 | `reviews/M0-review-brief.md` |
| 2026-08-12 | M0-review | [bypass] F-001 | Thêm quy tắc explicit "không bypass hard gate bằng cách tự tuyên bố hoàn thành" vào orchestrator agent | done — commit 3b7d8b6 | `.github/agents/aios-orchestrator.agent.md` |
| 2026-08-12 | M0-review | [bypass] F-002 | Cập nhật STATS.md M0: bypass 0 → 1 (khớp LOG.md có 1 entry bypass) | done — commit 3b7d8b6 | `aios/progress/STATS.md` |
| 2026-08-12 | M0-review | [bypass] F-003 | Thêm heading "Constraints" + "Expected Artifacts" rõ ràng vào TASK-001/spec.md | done — commit 3b7d8b6 | `tasks/TASK-001/spec.md` |
| 2026-08-12 | M0-review | review-brief | Tạo review brief (template dùng chung + bản M0 điền sẵn) để đem cho model khác review độc lập — tự chứa: bối cảnh, deliverable, tiêu chí AC, phương pháp, format báo cáo | done | `reviews/REVIEW-BRIEF-TEMPLATE.md`, `reviews/M0-review-brief.md` |
| 2026-08-12 | M0-review | review | Tạo bản review M0 (hồi tố, bằng chứng repo: git history 5 commits, 4 agent files, TASK-001 8 file, PROGRESS/LOG/STATS) — 5/5 mục tiêu + 4/5 verification pass, 5 findings (F1 test.md checkbox, F2 bypass chưa thực hành, F3/F4/F5 quan sát) | done — M0 ĐẠT | `aios/progress/reviews/M0-review.md` |
| 2026-08-12 | M0-review | [bypass] | Fix hồ sơ TASK-001/test.md: tick checkbox B4.5 + Kết luận (đã pass 2026-08-11 nhưng chưa tick) — lý do: fix nhỏ 2 dòng, không đổi hành vi | done — F1 resolved; **bypass thật đầu tiên (kiểm chứng F2)** | `tasks/TASK-001/test.md` |
| 2026-08-12 | TASK-009 | J3 | pytest 346 pass, coverage 95.30%; fix 5 (fixture conflict, self-loop, in-index unpack, integration relation, thread id) | done — 9/9 AC, **M1 HOÀN TẤT** | `backend/tests/` |
| 2026-08-12 | TASK-009 | J1-J2 | Implement capabilities/prompts/catalog/knowledge_graph + PLAN amend (3 chỗ) | done | 4 module mới |
| 2026-08-12 | TASK-009 | review | Reviewer: APPROVED — spec đã pin đầy đủ (unknown/idempotent/ordering) | done | `tasks/TASK-009/review.md` |
| 2026-08-12 | TASK-009 | critique-2 | Critic v2: 5 P2 (Yêu cầu #2 stale, construct-vs-register, evaluations, PLAN 2 chỗ, validation algorithm) + 10 P3 | done | `tasks/TASK-009/critique-2.md` |
| 2026-08-12 | TASK-009 | critique-1 | Critic v1: 4 P1 (prompt regex, duplicate phá versioning, evaluate write-only, PLAN mâu thuẫn) + 7 P2 + 7 P3 — resolve hết | done | `tasks/TASK-009/critique-1.md` |
| 2026-08-12 | TASK-008 | I1-I2 | Implement workflow package (dag helper, definition, compiler, library, cli) + refactor ExecutionPlan | done | `workflow/`, `kernel/dag.py` |
| 2026-08-12 | TASK-008 | review | Reviewer: APPROVED — verify 270 baseline, policy, merge khớp engine, refactor an toàn (2 R2 + 3 R3) | done | `tasks/TASK-008/review.md` |
| 2026-08-12 | TASK-008 | critique-2 | Critic v2: 0 P1 — 5 P2 (retries=0 sai, type pin, extra forbid, CLI test, simulate bắt buộc) + 5 P3 | done | `tasks/TASK-008/critique-2.md` |
| 2026-08-12 | TASK-008 | critique-1 | Critic v1: 2 P1 (YAML/CLI không chủ, canonical name) + 8 P2 + 9 P3 — resolve hết | done | `tasks/TASK-008/critique-1.md` |
| 2026-08-12 | TASK-007 | H1-H2 | Implement memory (conversation/session/vector) + knowledge (chunks/embedder/knowledge) + Settings | done | `memory/`, `knowledge/` |
| 2026-08-12 | TASK-007 | review | Reviewer: 1 R1 (AC5 toán học — 500/500/100) + 2 R2 + 6 R3 — resolve hết | done | `tasks/TASK-007/review.md` |
| 2026-08-12 | TASK-007 | critique-2 | Critic v2: 1 P1 (storage topology) + 4 P2 + 5 P3 — resolve hết | done | `tasks/TASK-007/critique-2.md` |
| 2026-08-12 | TASK-007 | critique-1 | Critic v1: 4 P1 (chunk text, limit mâu thuẫn, hash() cross-process, zero-vector) + 8 P2 + 17 P3 — resolve hết | done | `tasks/TASK-007/critique-1.md` |
| 2026-08-12 | TASK-006 | G1-G2 | Implement models package (contract/mock/openai/ollama/registry) + RuntimeKernel wire + ModelsSettings | done | `models/` |
| 2026-08-12 | TASK-006 | review | Reviewer: APPROVED có điều kiện (2 R2: delenv determinism, responses=None) + 4 R3 | done | `tasks/TASK-006/review.md` |
| 2026-08-12 | TASK-006 | critique-2 | Critic v2: 2 P1 (chat thứ tự check, Yêu cầu #6 stale) + 3 P2 + 10 P3 — resolve hết | done | `tasks/TASK-006/critique-2.md` |
| 2026-08-12 | TASK-006 | critique-1 | Critic v1: 3 P1 (registry DI, seam, timeout) + 7 P2 + 9 P3 — resolve hết | done | `tasks/TASK-006/critique-1.md` |
| 2026-08-12 | TASK-005 | F1-F2 | Implement scheduler/state/resource/execution + RuntimeKernel + contract changes (timeout_s float, WORKFLOW_CANCELLED, resources settings) | done | `kernel/`, `kernel/services/` |
| 2026-08-12 | TASK-005 | review | Reviewer: 2 R1 (cancel check order, register EventBus) + 2 R2 + 2 R3 — resolve hết | done | `tasks/TASK-005/review.md` |
| 2026-08-12 | TASK-005 | critique-2 | Critic v2: 1 P1 (runner contract) + 3 P2 + 10 P3 — resolve hết | done | `tasks/TASK-005/critique-2.md` |
| 2026-08-12 | TASK-005 | critique-1 | Critic v1: 3 P1 (DI Path|str, timeout_s int, resume thiếu plan) + 10 P2 + 9 P3 — resolve hết | done | `tasks/TASK-005/critique-1.md` |
| 2026-08-12 | TASK-004 | E1-E2 | Implement 5 services (context, event+audit, artifact sidecar, permission, policy) + Settings mở rộng | done — commit eb64795 | `kernel/services/` |
| 2026-08-12 | TASK-004 | review | Reviewer: 0 R1, 5 R2 vá nhẹ (pending mâu thuẫn, fake clock trap, sandbox defer, default policy, on_ask flow) — resolve hết | done | `tasks/TASK-004/review.md` |
| 2026-08-12 | TASK-004 | critique-2 | Critic v2: 1 P1 (timebase mâu thuẫn) + 6 P2 + 8 P3 — resolve hết | done | `tasks/TASK-004/critique-2.md` |
| 2026-08-12 | TASK-004 | critique-1 | Critic v1: 2 P1 (path guard startswith bypass, list thiếu cơ chế) + 6 P2 + 3 P3 — resolve hết | done | `tasks/TASK-004/critique-1.md` |
| 2026-08-12 | TASK-003 | D2-D4 | Implement: fix 5 lỗi thật (pydantic validator shadowing, object.__init__, event bus sync wrap, test deepcopy, abstractmethods) | done | `container.py`, `kernel/events.py`, `kernel/execution_plan.py`, `contracts/` |
| 2026-08-12 | TASK-003 | D1 | Implement: semver helper + contracts (ContractVersion, ContractMetadata, ArtifactContract, CompatibilityChecker) | done | `semver.py`, `contracts/` |
| 2026-08-12 | TASK-003 | review | Reviewer: CHANGES REQUESTED — R1 (thiếu bước update aios_core/__init__.py), R2×2 (flush re-raise, pytest root), R3×4 — resolve hết | done | `tasks/TASK-003/review.md` |
| 2026-08-12 | TASK-003 | critique-2 | Critic vòng 2: bắt 2 P1 mới do resolution v1 tạo ra (AC2 case 6 mâu thuẫn rule; check_upgrade đảo tham số) + 8 P2 + P3 — resolve hết | done | `tasks/TASK-003/critique-2.md` |
| 2026-08-12 | TASK-003 | critique-1 | Critic vòng 1: 2 P1 (compatibility sai chiều, async fire-and-forget) + 8 P2 + 8 P3 — resolve hết | done | `tasks/TASK-003/critique-1.md` |
| 2026-08-12 | TASK-003 | plan/spec | Tách TASK-003 (foundations) khỏi TASK-004 (services), viết spec kernel foundations | done | `tasks/TASK-003/spec.md` |
| 2026-08-11 | TASK-002 | C2.8 | venv + `pip install -e ".[dev]"` — aios-core 0.1.0 (fix readme path ngoài project dir; fix pydantic default factory) | done — AC1 pass | `backend/.venv` |
| 2026-08-11 | TASK-002 | C2 | Implement aios_core: config (search order + env validate + whitelist), logging (contextvars + JSON + idempotent), metadata (semver + make_component_metadata), healthcheck (worst-wins + edge cases) | done | `backend/src/aios_core/` |
| 2026-08-11 | TASK-002 | C1 | Scaffold cây monorepo 25 thư mục + .gitkeep + sdk stubs | done | `backend/*`, `dashboard/`, `extension/`, `skills/`, `docker/`, `sdk/` |
| 2026-08-11 | TASK-002 | review | Reviewer (subagent): CHANGES REQUESTED — 1 R1 (thiếu venv step) + 3 R2 (whitelist AIOS_CONFIG_PATH, timestamp default_factory, test.md/evaluation.md steps) + 4 R3 — resolve toàn bộ | done | `tasks/TASK-002/review.md` |
| 2026-08-11 | TASK-002 | critique-2 | Critic (subagent) vòng 2: bắt claim SAI cơ chế (extra=forbid không bắt typo env) + 6 P2 + 3 P3 — resolve toàn bộ | done | `tasks/TASK-002/critique-2.md` |
| 2026-08-11 | TASK-002 | critique-1 | Critic (subagent) vòng 1: 3 P1 + 6 P2 + 5 P3 (gitignore mâu thuẫn, HealthReport thiếu định nghĩa, config path mơ hồ...) — resolve toàn bộ | done | `tasks/TASK-002/critique-1.md` |
| 2026-08-11 | TASK-002 | spec | Viết spec.md TASK-002 (M1-P0: scaffold + aios_core) | done | `tasks/TASK-002/spec.md` |
| 2026-08-11 | TASK-001 | B4 | Người dùng xác nhận: agent picker hiển thị AIOS Orchestrator + 3 subagent; hard gate từ chối đúng | done — M0 ĐÓNG, TASK-001 done | `tasks/TASK-001/test.md` |
| 2026-08-11 | TASK-002 | spec | Viết spec.md TASK-002 (M1-P0: scaffold + aios_core) | done | `tasks/TASK-002/spec.md` |
| 2026-08-11 | TASK-001 | evaluate | Điền evaluation.md: 7/7 AC pass, kết luận ĐẠT spec | done | `tasks/TASK-001/evaluation.md` |
| 2026-08-11 | TASK-001 | stats | Cập nhật STATS.md: M0 done, 5 bài học | done | `aios/progress/STATS.md` |
| 2026-08-11 | TASK-001 | B4 | Verify tự động: B4.1 (git sạch), B4.4 (frontmatter 4 file hợp lệ), B4.5 (progress khớp) | done — 3/3 pass | `tasks/TASK-001/test.md` |
| 2026-08-11 | TASK-001 | B3 | Commit toàn bộ M0 (agent files + progress + fixes critique) | done — 08f1efa, c2d1032 | `git log` |
| 2026-08-11 | TASK-001 | B2 | Tạo progress system: PROGRESS.md, LOG.md, STATS.md (+ mục Bài học) | done | `aios/progress/` |
| 2026-08-11 | TASK-001 | spec | Viết spec.md cho TASK-001 (mục tiêu, phạm vi, AC, rủi ro) | done | `tasks/TASK-001/spec.md` |
| 2026-08-11 | TASK-001 | critique-1 | Critic phản biện vòng 1: tìm 1 P1 (gitignore ignore cả .vscode/), 1 P2 (thiếu rule phân loại task), 1 P3 (template verify) | done — 3/3 đã resolve: sửa .gitignore, thêm rule vào agent orchestrator, thêm ghi chú template | `tasks/TASK-001/critique-1.md` |
| 2026-08-11 | TASK-001 | critique-2 | Critic phản biện vòng 2: kiểm tra resolution vòng 1 (ok), tìm P2 mới (kiểm chứng subagent khi verify), P3 (STATS thiếu Bài học) | done — đã thêm bước B4.2 vào test.md + mục Bài học vào STATS.md | `tasks/TASK-001/critique-2.md` |
| 2026-08-11 | TASK-001 | tasks | Breakdown checklist B0–B4 (13 bước) | done | `tasks/TASK-001/tasks.md` |
| 2026-08-11 | TASK-001 | review | Reviewer: APPROVED có điều kiện (AC3/AC4 cần verify thủ công B4) | done | `tasks/TASK-001/review.md` |
| 2026-08-11 | TASK-001 | implement | Toàn bộ artifact M0 tạo xong (agents + progress + fixes) | done | `tasks/TASK-001/implementation/README.md` |
| 2026-08-11 | TASK-001 | B1 | Tạo 4 VS Code custom agent: aios-orchestrator (Control Plane, hard gate + bypass rules), spec-writer, critic (2 vòng phản biện), reviewer | done — 4 file tạo xong | `.github/agents/*.agent.md` |
| 2026-08-11 | TASK-001 | B0 | git init + git config local (AIAGENT Dev), tạo docs/PLAN.md (plan v6 đầy đủ), AGENTS.md, .gitignore | done — commit e50b715 | `docs/PLAN.md`, `AGENTS.md`, `.gitignore` |
| 2026-08-11 | TASK-001 | plan | Bắt đầu M0: tạo TASK-001, xác định 5 bước B0–B4 | done — checklist tạo trong tasks.md | `aios/progress/tasks/TASK-001/tasks.md` |
