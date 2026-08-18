# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## ✅ M12 — AIOS 1.1 Compatibility (2026-08-16 — DONE ✅, Issue #7)

> PLAN.md §M12 (P17): **Issue #7** — user duyệt "nâng cấp hệ thống" → roadmap §43: AIOS 1.1 Compatibility (bước đầu sau M11). KHÔNG thêm Core feature, KHÔNG thêm invariant — INV-001..035 giữ nguyên frozen. 5 nâng cấp C1–C5, 5 task (TASK-084..088).
> **Trạng thái**: 5/5 task done — full suite **2118 PASS / 0 FAIL** + conformance **11 areas + 20 GS + 7 gates → AIOS 1.1 READY** + arch-health 0 violations + doctor healthy.
> **Nhánh**: `feature/ISSUE-7-aios-1-1-compatibility` (từ `verify` @ `d4185a6`) — **PR #8 draft chưa push/merge** (theo yêu cầu user "khoan PR"). Chờ: push → PR #8 → merge vào `verify` → kiểm tra → promotion `release: verify → master` → Issue #7 close.

| Phase | Nội dung | Nâng cấp | Task | Trạng thái |
|-------|----------|----------|------|------------|
| P0 | Version & Compatibility Baseline | C1 version bump 1.0→1.1 toàn hệ thống (contract/config/CLI/metadata) + Compatibility Matrix registry | TASK-084 | `done` ✅ (12/12 AC — __version__ 1.1.0 + catalog 1.1.0 + compat matrix 14 entry + CLI compat + full suite 2071) |
| P1 | Migration 1.0→1.1 thật | C2 upgrade pipeline end-to-end trên dữ liệu thật (plan → backup → dry-run → validate → rollback) | TASK-085 | `done` ✅ (12/12 AC — migration_110.py 4 transforms + Aios110Migrator matrix-gated + CLI migrate nhánh 1.0→1.1 + fix bug engine.apply + full suite 2098) |
| P2 | Backward Compatibility | C3 plugin v0→v1 · contract v0→v1 · workflow v0→v1 chạy trên 1.1 + test chéo | TASK-086 | `done` ✅ (10/10 AC — backward_compat.py 9 check 5 kind + CLI compat verify + fix AiosRange.compatible parse-only + full suite 2109) |
| P3 | Compatibility Conformance | C4 mở rộng `aiagent conformance` area `compatibility` + gate (giữ 10 areas/6 gates) | TASK-087 | `done` ✅ (8/8 AC — area compatibility + gate_g + 11 areas/7 gates → AIOS 1.1 READY + full suite 2118) |
| P4 | Docs & ADR | C5 ADR-0007 (compatibility policy) + migration guide 1.0→1.1 + PLAN §M12 | TASK-088 | `done` ✅ (10/10 AC — ADR-0007 + docs/guides/migration-1.0-to-1.1.md + PLAN §M12 DONE + README links — **M12 HOÀN TẤT 5/5 TASK**) |

Dependency order: C1 → C2 → C3 → (C4 ∥ C5)
## ✅ M13 — Harness Trust & Behavioral Conformance (2026-08-17 — DONE ✅, Issue #8) · TRUST

> PLAN.md §M13 (P18): bước tiếp theo SAU M12 (AIOS 1.1 Compatibility). KHÔNG sửa Runtime/Orchestrator (giữ INV-017..021). Mở rộng Harness từ "test/certify framework" → **trust layer tự xác minh (self-validating) + production-grade**. Nguồn: tự đánh giá độ harness 2026-08-16 (4/5 — Certified & Gated, chưa Autonomous) + đề xuất người dùng (5 ưu tiên + roadmap). **Harness Track (M13→M15) FROZEN** sau 6 điểm chỉnh sửa.
> **Trạng thái**: 5/5 task done — full suite **2254 PASS / 0 FAIL** + release gate PASS (system_ready + harness_trust) + 4 invariant track (FAIL-CLOSED ✅ + INDEPENDENT VERIFICATION ✅ + PERMISSION BOUNDARY 📋 M14 + CERTIFIED BASELINE/ROLLBACK 📋 M14). Nhánh: `feature/ISSUE-8-m13-harness-trust`.
> **4 invariant xuyên suốt track**: FAIL-CLOSED (INV-035) + INDEPENDENT VERIFICATION + PERMISSION BOUNDARY + CERTIFIED BASELINE/ROLLBACK.

| Phase | Nội dung | Ưu tiên | Task | Trạng thái |
|-------|----------|---------|------|------------|
| P0 | Behavioral Conformance — execute N lần (configurable: quick=100/std=1k/stress=10k/soak=duration) + repeat + fault-inject + evidence compare + regression gate | Behavioral | TASK-089 | `done` ✅ (17/17 AC — engine N lần + repeat + Fault.recoverable + evidence digest + gate expose + CLI `aiagent harness behavioral` + full suite 2172) |
| P1 | Harness Coverage model (9 chiều + negative-path) + Doctor Readiness scoring | Coverage | TASK-090 | `done` ✅ (19/19 AC — coverage 9 chiều + negative 6/8 + readiness 7 dims + CLI `aiagent harness coverage` + full suite 2207) |
| P2 | Meta-Harness — verify the verifier với verification path ĐỘC LẬP (chống circular) + adversarial fail-closed | Meta | TASK-091 | `done` ✅ (17/17 AC — 8 adversarial cases + chống circular monkeypatch + CLI `aiagent harness meta` exit 0 + coverage READY 8/8 + full suite 2234) |
| P3 | System Readiness ≠ Harness Trust; release gate cả 2 PASS | Trust | TASK-092 | `done` ✅ (12/12 AC — release gate pure combiner + 2 path BLOCKED + CLI `aiagent harness release` exit 0 + full suite 2254) |
| P4 | Docs & ADR — ADR Harness Trust + behavioral spec + PLAN §M13 | Docs | TASK-093 | `done` ✅ (ADR-0008 + behavioral spec + PLAN §M13 DONE — M13 HOÀN TẤT 5/5) |

Dependency order: P0 → P1 → P2 → (P3 ∥ P4)
> **Deviation P0 (TASK-089)**: gate v1 chỉ expose (finding) — gate-as-blocker thuộc M14; soak v1 = loop-stability test. Chi tiết: PLAN §M13 P0 + TASK-089/evaluation.md.
> **Deviation P1 (TASK-090)**: coverage v1 = declared + auto-collect (KHÔNG quét test files); **fail-closed thật** — `aiagent harness coverage` trả NOT_READY (replay gate 0.5 < 0.75) cho tới khi TASK-091 cover đủ; production 0.0 + excluded overall v1. Chi tiết: PLAN §M13 P1 + TASK-090/evaluation.md.
> **Deviation P2 (TASK-091)**: Oracle hardcode (MetaOracle enum) — engine KHÔNG gọi verifier production để tính expected_state (chống circular P2-1); engine reference `pipeline.compute_verdict` module-level để monkeypatch AC16 hoạt động; `fail_closed` = "Meta đạt mục tiêu adversarial" (P1-1 fix: BROKEN_VERIFIER/VERIFY_SKIPPED scenario a detect = success = True → suite PASS reachable). Scenario (b) đẩy vào AC16 negative test. Chi tiết: PLAN §M13 P2 + TASK-091/evaluation.md.
## ✅ M14 — Controlled Self-Healing (DONE ✅) · HEAL

> PLAN.md §M14 (P19): đóng vòng lặp tự phục hồi có kiểm soát (Detect→Diagnose→Generate Fix→Risk→Simulate→Meta-Verify→Permission→Human Approval→Apply→Re-test→Rollback if needed→Certify). **NGUYÊN TẮC**: Harness KHÔNG tự sửa tiêu chuẩn để tự PASS; mọi apply thực cần Permission Broker + Human Approval + Certified Baseline/Rollback. Cần M13 (Meta-Harness + Trust Separation) làm nền.
> **Trạng thái**: 5/5 task done — full suite **2331 PASS / 0 FAIL** + closed-loop pipeline (Detect→Diagnose→Generate→Risk→Simulate→Meta-Verify→Apply→Certify). Nhánh: `feature/ISSUE-8-m14-controlled-self-healing`.

| Phase | Nội dung | Task | Trạng thái |
|-------|----------|------|------------|
| P0 | Detect & Diagnose — failure corpus + localization | TASK-094 | `done` ✅ |
| P1 | Candidate Generate + Risk Scoring | TASK-095 | `done` ✅ |
| P2 | Simulation + Meta-Verify Gate (KHÔNG relax criteria) | TASK-096 | `done` ✅ |
| P3 | Permission Broker + Human Approval + Apply + Re-test + Rollback (restore certified state) + Certify + Certified Baseline | TASK-097 | `done` ✅ |
| P4 | Docs & ADR — INV-037 Remediation Integrity + kill-switch | TASK-098 | `done` ✅ |

Dependency order: P0 → P1 → P2 → P3 → (P4 song song cuối)

## ✅ M15 — Autonomous Harness (DONE ✅) · AUTONOMY

> PLAN.md §M15 (P20): đích cuối harness track — vòng lặp tự chủ (autonomous) detect→diagnose→fix→verify→apply→certify, Improvement Engine, Continuous Certification, Autonomy Policy + Trust Budget/Autonomy Levels + kill-switch. **Autonomy ≠ Permission**: Autonomy Engine quyết định "có nên tự làm?", Permission Broker quyết định "có được phép?". Giữ fail-closed + permission boundary + human oversight high-risk. Cần M14 làm nền.
> **Trạng thái**: 5/5 task done — full suite **2360 PASS / 0 FAIL** + 16 harness total + closed-loop pipeline (Detect→Diagnose→Generate→Risk→Simulate→Meta-Verify→Apply→Certify→Autonomous→DSH Oracle). Nhánh: `feature/ISSUE-8-m14-controlled-self-healing`.

| Phase | Nội dung | Task | Trạng thái |
|-------|----------|------|------------|
| P0 | Autonomous Loop Orchestrator | TASK-099 | `done` ✅ |
| P1 | Improvement Engine (failure-corpus learning) | TASK-100 | `done` ✅ |
| P2 | Continuous Certification (low-risk auto) | TASK-101 | `done` ✅ |
| P3 | Trust Budget (7 giới hạn) + Autonomy Levels + Autonomy Policy + SAFE-STOP | TASK-102 | `done` ✅ |
| P4 | Docs & ADR — INV-038 Autonomy Boundary + Autonomy Constitution | TASK-103 | `done` ✅ |

Dependency order: P0 → P1 → P2 → P3 → (P4 song song cuối)
## ✅ M16 — Harness Ecosystem Integration (DONE ✅) · INTEGRATE

> PLAN.md §M16 (P21): tích hợp dsh làm external oracle (độc lập thực sự) + management console. M16 = INTEGRATE — biến dsh thành independent verification path thực thụ (giải vòng tròn Meta-Harness M13-P2) + tận dụng `dsh-web-app` làm management console, giữ nguyên fail-closed / permission boundary / certified baseline.
> **Trạng thái**: 5/5 task done — full suite **2360 PASS / 0 FAIL** + 16 harness total + 4 invariant track củng cố (FAIL-CLOSED ✅ + INDEPENDENT VERIFICATION ✅ + PERMISSION BOUNDARY ✅ + CERTIFIED BASELINE/ROLLBACK ✅). Nhánh: `feature/ISSUE-8-m14-controlled-self-healing`.

| Phase | Nội dung | Task | Trạng thái |
|-------|----------|------|------------|
| P0 | DSH Bridge — independent verification oracle (map INV-001..038) | TASK-104 | `done` ✅ |
| P1 | Behavioral Conformance Bridge (ACP snapshot / fast-check) | TASK-106 | `done` ✅ |
| P2 | Permission & Sandbox Bridge (remediation apply theo scope) | TASK-107 | `done` ✅ |
| P3 | Management Console (embed/proxy dsh-web-app) | TASK-108 | `done` ✅ |
| P4 | Docs & ADR | TASK-105 | `done` ✅ |

Dependency order: P0 → P1 → P2 → P3 → (P4 song song cuối)

## 📋 M17–M26 — Coding Plane (PLANNED — sau M16) · CODE

> PLAN.md §M17–M26 (P22–P31): biến AIOS từ "OS có Harness rất mạnh" thành "AIOS thực sự có khả năng coding". **Nguyên tắc**: (1) KHÔNG phá Runtime/Orchestrator/Harness (giữ INV-001..038); (2) Coding Plane là **CONSUMER** của Runtime + Harness, không tự tạo hệ thống agent riêng; (3) **AIOS là chính, Harness là lớp Trust/Verification**; (4) ModelProvider là INFRASTRUCTURE, không chứa coding logic; (5) Coder Agent là worker trong Worker Plane, truy cập qua Capability + Runtime.
> **Trạng thái**: `planned` — chi tiết task/spec do user gửi sau (xem LOG 2026-08-18). Nhánh: `docs/coding-plane-plan` (từ `verify`).
> **Milestone chain**: M17 → M18 → M19 → M20 → (M21 ∥ M22) → M23 → M24 → M25 → M26 → M27.

| Phase | Nội dung | Milestone | Trạng thái |
|-------|----------|-----------|------------|
| P22 | Model Provider & Inference Runtime (OpenAI/Anthropic/Local/Compatible/Mock) | M17 | `todo` |
| P23 | Coding Context (repo index, retrieval, symbol graph) | M18 | `todo` |
| P24 | Coder Agent (Goal → inspect → plan → edit → verify → repair) | M19 | `todo` |
| P25 | Sandbox Execution (build/test/lint safe) | M20 | `todo` |
| P26 | Coding Loop (Plan → Code → Test → Fix) | M21 | `todo` |
| P27 | Code Verification (Harness xác minh code) | M22 | `todo` |
| P28 | Adversarial Evaluation & Resilience (verify-the-verifier) | M23 | `todo` |
| P29 | Continuous Quality Governance & Release Gate | M24 | `todo` |
| P30 | Git/Artifact Integration (diff/commit/rollback) | M25 | `todo` |
| P31 | Coding Evaluation (benchmark + regression) | M26 | `todo` |
| P32 | AIOS 2.0 Coding Edition (freeze + certification) | M27 | `todo` |

Dependency order: M17 → M18 → M19 → M20 → (M21 ∥ M22) → M23 → M24 → M25 → M26 → M27

**M17 task breakdown (TASK-109..116 — ID điều chỉnh từ attachment TASK-101..108 đã trùng M15/M16)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-109 | Model Contracts (Request/Response/Error/Metadata/Capability/Usage/Cost/StreamEvent) | `todo` |
| TASK-110 | Provider Registry + lifecycle | `todo` |
| TASK-111 | Model Registry + deterministic Resolver | `todo` |
| TASK-112 | Inference Runtime orchestration | `todo` |
| TASK-113 | Credential + Permission + Policy integration | `todo` |
| TASK-114 | Retry / Timeout / Streaming / cancellation | `todo` |
| TASK-115 | Usage / Cost / Audit / Evidence | `todo` |
| TASK-116 | Provider Conformance + Certification (Harness + Security Check → Registry) | `todo` |

> **INV mới (M17)**: INV-039 Provider Isolation · INV-040 Inference Policy Gate · INV-041 Credential Isolation · INV-042 Provider Conformance · INV-043 Inference Auditability · INV-044 Inference Fail-Closed. (Attachment đề xuất INV-036..041 nhưng đã thuộc M13/M14/M15 → điều chỉnh lên INV-039..044.)
> **M17 KHÔNG làm Coder Agent** — chỉ xây "cognition backend" (Inference Runtime). Ranh giới: sau M17 AIOS gọi được LLM thật qua abstraction NHƯNG chưa tự sửa code (M19 mới có coding capability).

**M18 task breakdown (TASK-117..124 — ID điều chỉnh từ attachment TASK-201..208)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-117 | Repository Scanner (RepositoryManifest, framework detection là plugin) | `todo` |
| TASK-118 | Source/Symbol Index (Symbol: id/name/kind/file/line/parent/refs) | `todo` |
| TASK-119 | Dependency Graph (imports/exports/calls/inherits/references/tests) | `todo` |
| TASK-120 | Semantic + Hybrid Index (Structural > lexical > semantic) | `todo` |
| TASK-121 | Context Retriever (ContextQuery → relevant files/symbols/deps) | `todo` |
| TASK-122 | Context Builder + Budget (ContextPackage + token budget + Manifest) | `todo` |
| TASK-123 | Context Verification + Evidence (ContextVerifier + freshness) | `todo` |
| TASK-124 | Context Harness + Conformance (CTX-001..012, fixture repo) | `todo` |

> **INV mới (M18)**: INV-045 Context Isolation · INV-046 Context Freshness · INV-047 Context Evidence · INV-048 Context Determinism · INV-049 Context Fail-Closed · INV-050 Context Budget. (Attachment đề xuất INV-042..047 nhưng INV-042/043/044 đã thuộc M17 → điều chỉnh lên INV-045..050.)
> **M18 KHÔNG tự code** — chỉ xây "Context Plane": AIOS hiểu repository (scan/index/symbol/dependency/retrieval/verification) để M19 Coder Agent có context chính xác. Output: CodingContext + ContextManifest + Evidence (deterministic, fail-closed).

**M19 task breakdown (TASK-125..134 — ID điều chỉnh từ attachment TASK-301..310)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-125 | Coder Agent Contract + State Machine (RECEIVED→…→COMPLETED/FAILED) | `todo` |
| TASK-126 | Coding Planner + PlanVerifier (KHÔNG edit code) | `todo` |
| TASK-127 | Code Generation Runtime (M17 + structured output + schema validate) | `todo` |
| TASK-128 | Patch Engine (validate/preview/apply/rollback, base_hash → PATCH_STALE) | `todo` |
| TASK-129 | Code Review Agent (PASS/WARN/REJECT, không tự sửa) | `todo` |
| TASK-130 | Coding Artifact + CodingEvidence (hash chain) | `todo` |
| TASK-131 | Coder Conformance Harness + Security (CODER-001..015 + adversarial) | `todo` |
| TASK-132 | Autonomy Level (L0/L1/L2) + Permission integration (M14) | `todo` |
| TASK-133 | Prompt Architecture + PromptBuilder + versioning | `todo` |
| TASK-134 | File Safety Boundary + Scope enforcement (allowed/forbidden paths) | `todo` |

> **INV mới (M19)**: INV-051 Agent/Provider Separation · INV-052 Patch-First Mutation · INV-053 Patch Freshness · INV-054 Scope-Bounded Coding · INV-055 Structured Generation · INV-056 Review Before Apply · INV-057 Coding Evidence · INV-058 Repository Content Is Untrusted. (Attachment đề xuất INV-048..055 nhưng INV-048/049/050 đã thuộc M18 → điều chỉnh lên INV-051..058.)
> **M19 KHÔNG autonomous** — Coder Agent tạo patch có scope/provenance/policy/evidence/artifact rõ ràng NHƯNG chưa tự chạy test / tự sửa lỗi / tự commit (M20/M21). Ranh giới: M19 = "biết cần sửa gì + tạo patch", M20 = "chạy patch an toàn", M21 = "Code→Execute→Observe→Diagnose→Repair".

**M20 task breakdown (TASK-135..144 — ID điều chỉnh từ attachment TASK-401..410)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-135 | Execution Contracts (ExecutionRequest/ExecutionResult + status enum) | `todo` |
| TASK-136 | Sandbox Manager (lifecycle + state machine + cleanup) | `todo` |
| TASK-137 | Workspace / Snapshot Manager (repo snapshot + WorkspaceManifest) | `todo` |
| TASK-138 | Resource + Network + Command Policy (limits / DENY / ALLOW-REQUIRE_APPROVAL) | `todo` |
| TASK-139 | Test Runner (adapter-based, TestResult/TestFailure) | `todo` |
| TASK-140 | Build / Lint Runner (BuildRunner + LintRunner adapter) | `todo` |
| TASK-141 | Output + Artifact Collector (limits + Artifact Manager) | `todo` |
| TASK-142 | Verification Engine (VerificationResult, fail-closed) | `todo` |
| TASK-143 | Security + Replay Harness (SEC/REPLAY-001.. + adversarial escape suite) | `todo` |
| TASK-144 | Execution Evidence + Conformance (hash chain + Scheduler/Cancellation M1) | `todo` |

> **INV mới (M20)**: INV-059 Host Isolation · INV-060 Network Default-Deny · INV-061 Resource Bound · INV-062 Workspace Isolation · INV-063 Command Policy · INV-064 Execution Evidence · INV-065 Execution Fail-Closed · INV-066 Sandbox Cleanup · INV-067 Replay Provenance. (Attachment đề xuất INV-056..064 nhưng INV-056/057/058 đã thuộc M19 → điều chỉnh lên INV-059..067.)
> **M20 KHÔNG tự sửa code** — chỉ chạy + kiểm chứng patch an toàn (sandbox/resource/network/command policy, evidence, replay, security). CHƯA autonomous repair / coding loop / LLM diagnosis / commit (M21+).

**M21 task breakdown (TASK-145..154 — ID điều chỉnh từ attachment TASK-501..510)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-145 | Coding Loop State Machine | `todo` |
| TASK-146 | Execution Observation (structured) | `todo` |
| TASK-147 | Failure Classification | `todo` |
| TASK-148 | Diagnostic Agent (no self-fix) | `todo` |
| TASK-149 | Repair Planner (→ M19 Coder) | `todo` |
| TASK-150 | Progress + Regression Detection | `todo` |
| TASK-151 | Verification Gate (INV-035+INV-062 applied) | `todo` |
| TASK-152 | Context Refresh + Patch Chain | `todo` |
| TASK-153 | Autonomous Safety Controller (Kill Switch/Permission/Trust/Policy) | `todo` |
| TASK-154 | Autonomous Coding Harness (AUT-001..018) | `todo` |

> **INV mới (M21)**: INV-068 Bounded Autonomy · INV-069 Verified Completion · INV-070 No Progress Termination · INV-071 Repair Provenance · INV-072 Regression Protection · INV-073 Autonomous Scope Boundary · INV-074 Kill Switch Dominance · INV-075 Budget Dominance · INV-076 Unknown Completion Prohibition · INV-077 Loop State Integrity. (Attachment đề xuất INV-065..074 nhưng INV-065/066/067 đã thuộc M20 → điều chỉnh lên INV-068..077.)
> **M21 = Controlled Autonomous Coding** — tự hoàn thành coding task nhiều bước CÓ budget/scope/kill-switch/policy/evidence chain. KHÔNG unrestricted agent loop. M22 tiếp theo = Coding Verification/Evaluation/Trust (Verifier ≠ Generator, tận dụng Harness M13–M16).

**M22 task breakdown (TASK-155..164 — ID tự gán, attachment KHÔNG đưa TASK-xxx, nối tiếp M21)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-155 | Verification Contract + Requirement→Evidence Mapping | `todo` |
| TASK-156 | Test Adequacy Analyzer + Mutation Verifier | `todo` |
| TASK-157 | Behavioral Verifier (Behavior > Implementation) | `todo` |
| TASK-158 | Contract Verifier (API/Agent/Capability/... contracts) | `todo` |
| TASK-159 | Regression Verifier | `todo` |
| TASK-160 | Security Verifier (hard failure) | `todo` |
| TASK-161 | Performance Verifier (baseline threshold) | `todo` |
| TASK-162 | Replay & Flaky Detector | `todo` |
| TASK-163 | Evidence Collector + Evidence Integrity | `todo` |
| TASK-164 | Trust Evaluator + CodingCertificate + Verification Harness | `todo` |

> **INV mới (M22)**: INV-078 Independent Verification · INV-079 Evidence-Backed Verification · INV-080 Verification Fail-Closed · INV-081 Immutable Candidate During Verification · INV-082 Hard Failure Dominance · INV-083 Evidence Integrity · INV-084 Reproducible Verification. (Attachment đề xuất INV-036..042 nhưng **TOÀN BỘ range đã bị chiếm**: INV-036/037/038 = M13/M14/M15, INV-039/040/041/042 = M17 → điều chỉnh lên INV-078..084.)
> **M22 = Verification Plane** — lớp độc lập với Coding Plane (Generator ≠ Verifier). Chỉ OBSERVE→VERIFY→EVALUATE→CERTIFY/REJECT. KHÔNG generate/repair code. REJECTED → quay lại M21 repair. Biến Autonomous Coding → **Trustworthy Autonomous Coding**.

**M23 task breakdown (TASK-165..174 — ID tự gán, attachment KHÔNG đưa TASK-xxx, nối tiếp M22)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-165 | Adversarial Evaluation Harness (contract + Red/Blue Team) | `todo` |
| TASK-166 | Evidence Attackers (Tampering/Stale/Missing) | `todo` |
| TASK-167 | Test Weakness Attackers (Weak/Assertion Evasion/Mutation) | `todo` |
| TASK-168 | Requirement/Scope Attackers (Evasion/Scope Violation) | `todo` |
| TASK-169 | Certificate Attackers (Replay/Forgery) | `todo` |
| TASK-170 | Prompt Injection Tester + Untrusted Artifact Isolation | `todo` |
| TASK-171 | Execution Integrity Attackers (Tool/Replay/Flaky) | `todo` |
| TASK-172 | Environment/Dependency Attackers | `todo` |
| TASK-173 | Boundary Attackers (Permission/Sandbox Escape/Verifier Manipulation) | `todo` |
| TASK-174 | Collusion Detector + Resilience Score + Attack Corpus Regression | `todo` |

> **INV mới (M23)**: INV-085 Adversarial Verification · INV-086 False-PASS Resistance · INV-087 Evidence Tamper Detection · INV-088 Certificate Binding · INV-089 Untrusted Artifact Isolation · INV-090 Verifier Boundary Protection · INV-091 Attack Fail-Closed · INV-092 Critical Finding Dominance. (Attachment đề xuất INV-043..050 nhưng **TOÀN BỘ range đã bị chiếm**: INV-043/044 = M17, INV-045..050 = M18 → điều chỉnh lên INV-085..092.)
> **M23 = Adversarial / Resilience Plane** — kẻ tấn công giả lập của AIOS (verify-the-verifier). Chỉ OBSERVE→ATTACK→EVALUATE→RESILIENT/DEGRADED/VULNERABLE/CRITICAL. KHÔNG tạo Coding Plane mới. Success của attack = finding.

**M24 task breakdown (TASK-175..184 — ID tự gán, attachment KHÔNG đưa TASK-xxx, nối tiếp M23)**:
| Task | Nội dung | Trạng thái |
|------|----------|------------|
| TASK-175 | Quality Gate + Gate States (ALLOW/CONDITIONAL/WARN/BLOCK/UNKNOWN) | `todo` |
| TASK-176 | Risk Model + Classification (R0–R4) | `todo` |
| TASK-177 | Policy Engine + Profiles + Precedence | `todo` |
| TASK-178 | Exception Management (scope/expiration/audit) | `todo` |
| TASK-179 | Quality Debt Tracking | `todo` |
| TASK-180 | Release Gate + Decision Explainability | `todo` |
| TASK-181 | Governance Ledger + Provenance Graph | `todo` |
| TASK-182 | Trust Lifecycle + Invalidation + Selective Reverification | `todo` |
| TASK-183 | Approval Workflow + Rollback Recommendation | `todo` |
| TASK-184 | Quality Dashboard + Governance Harness | `todo` |

> **INV mới (M24)**: INV-093 Policy-Driven Gate · INV-094 Hard Gate Dominance · INV-095 Explainable Decision · INV-096 Exception Explicitness · INV-097 Exception Expiration · INV-098 Finding Preservation · INV-099 Trust Invalidation · INV-100 Governance Auditability · INV-101 Security Precedence · INV-102 Unknown Fail-Closed. (Attachment đề xuất INV-051..060 nhưng **TOÀN BỘ range đã bị chiếm**: INV-051..058 = M19, INV-059..067 = M20 → điều chỉnh lên INV-093..102.)
> **M24 = Quality Governance / Trust Gate** — biến Verify(M22)+Attack(M23) thành governance liên tục. KHÔNG tạo Agent mới. Policy decides, score informs. M25 tiếp theo = Git/Artifact Integration (proposed).
## �🚀 M11 — Deterministic Artifact & Interaction Runtime (2026-08-16 — DONE ✅ TRÊN MASTER)

> PLAN.md §M11: **Issue #4** — user duyệt xử lý TOÀN BỘ (P0–P4). Proposal `docs/proposals/m11-creative-engineering.md` (từ `operation/test-A`, review 8.8/10). Giới thiệu **INV-035** (Core Invariant MỚI — không vi phạm INV-001..034).
> **Vòng đời KHÉP KÍN**: PR #5 (feature → verify) MERGED `57345ca` → verify PASS (2052/2052 + conformance READY) → **PR #6** (promotion `release: verify → master (2026-08-16)`) MERGED `3b513c3` → **Issue #4 CLOSED** → nhánh feature đã xóa. master = verify = `3b513c3` (ADR-0005).

| Phase | Nội dung | Nâng cấp | Task | Trạng thái |
|-------|----------|----------|------|------------|
| P0 | Verification Integrity | R2 INV-035 Verification Fail-Closed (+ Verification State Model, conformance visual policy, CI fail-closed gate, retroactive audit) | TASK-078 | `done` ✅ (12/12 AC — 30 unit + conformance 10 areas/6 gates + full suite 1969) |
| P1 | Deterministic Visual Runtime | R3 RenderReplay / DeterministicHarness (record input timeline + seed → replay → assert pixel-stable) | TASK-079 | `done` ✅ (10/10 AC — rendering/ package + 18 tests + full suite 1987) |
| P2+P2b | Visual Observability | R1 VisualEvidence / VisualRegressionProbe + R10 UI State Contract (`UI State → Render → Screenshot`) | TASK-080 | `done` ✅ (10/10 AC — probe bắt state_diff scale 3→2 + missing-ref fail-closed; full suite 2003) |
| P3 | Asset Capability Architecture | R9 AssetPipeline Contract + R4 Registry kind=asset + R11 Discovery/Routing (1 slice) | TASK-081 | `done` ✅ (10/10 AC — registry wire skill agent-sprite-forge thật + matcher offline; full suite 2018) |
| P3b/c/d | Creative + Vendor + Reference | R6 Creative Domain + R8 Vendor Integrity + R12 Reference-Asset Understanding | TASK-082 | `done` ✅ (11/11 AC — pre-route creative 0.85 + 2 workflow creative + vendor_integrity check #12 + ReferenceAssetUnderstanding; full suite 2034) |
| P4a/b | Ecosystem & DX | R5 SkillDistiller + R7 Static Deploy (optional) | TASK-083 | `done` ✅ (11/11 AC — distiller 7 bước deterministic + deploy verify/manifest/dry/apply; full suite 2052 — **M11 HOÀN TẤT 6/6 task**) |

Dependency order: R2 → R3 → (R10 ∥ R1) → R9 → (R4 ∥ R11) → R6 → (R8 ∥ R12) → R5 → R7

## ✅ TASK-077 — Quy trình Issue → Branch → PR → Merge thủ công → verify → master (2026-08-16)

- **Kết quả**: thiết lập **Issue-Driven Development** đầy đủ theo yêu cầu người dùng: (1) 3 GitHub issue templates (`bug-report`/`feature-upgrade`/`idea-proposal` — issue forms chuẩn `about`, không `description`) + `config.yml` (tắt blank issue); (2) PR template bắt buộc link issue / `[bypass]`; (3) action `.github/workflows/pr-validation.yml` (github-script@v7 — luồng quyết định 7 bước: draft skip → `release:` base=master skip body → base=verify → body `[bypass]` → `type/ISSUE-N` + link → `type/bypass-slug` + tag → fail; permissions read-only, concurrency; KHÔNG auto-merge/approve); (4) `docs/workflows/issue-pr-workflow.md` (5 giai đoạn + quy ước nhánh `<type>/ISSUE-N-slug` từ verify + lệnh gh/git PowerShell); (5) `docs/adr/0006-issue-pr-workflow.md` (accepted, extends ADR-0005, **main = master** giữ nguyên); (6) `AGENTS.md` §4.2 bắt buộc + `PLAN.md` cập nhật.
- **Vòng đời đã khép kín (dogfooding 100%)**: hard gate → implement → **PR #2** (feature → verify, merged `30e2a23`) → verify PASS (78/78) → **PR #3** promotion (`release: verify → master (2026-08-16)`, merged `4454c9d`) — **PR Validation chạy thật & PASS trên chính PR #3** (xác nhận điểm C2-05); master = verify = `4454c9d`; nhánh `docs/issue-pr-workflow` đã xóa.
- **Test**: `validate_task077.py` thật — **78 PASS / 0 FAIL** (parse 5/5, schema 30/30, mô phỏng luồng quyết định 20/20 case, docs 23/23). Hard gate đủ 8-file + implementation/.
- Xem chi tiết: `LOG.md` entry 2026-08-16 TASK-077.

## 🔒 Quy tắc branching mới (BẮT BUỘC từ 2026-08-15 — ADR-0005 + ADR-0006)

- `master` = ổn định, CHỈ nhận từ `verify`; `verify` = trạm kiểm tra bắt buộc (test + hard gate + review).
- Nhánh chức năng tạo TỪ `verify` (tiền tố `feature/`, `fix/`, `docs/`, `operation/`, `refactor/`, `test/`...).
- Chuỗi: nhánh chức năng → `verify` (kiểm tra) → `master`. Vi phạm = sai quy trình.
- Ghi chú: các entry bypass trước (tạo nhánh operation/test-A, verify) nằm trên nhánh operation/test-A — chưa gộp về master.

## ✅ TASK-076 — Architecture v3 (Mermaid): AIOS 1.0 Final (2026-08-15)

- **Kết quả**: tạo `docs/architecture-v3.md` — bản **hiện hành** (AIOS 1.0 Final, **Mermaid** — theo yêu cầu người dùng phương án "2 và 3"), 12 khối sơ đồ (10 flowchart + stateDiagram-v2 Safety chain + sequenceDiagram Kill Switch), 7 tầng L1..L7 theo `layer-model.md` **frozen** (Autonomous = L2 — sửa điểm v2 sai; Harness/Enterprise/Ecosystem = L7; M10 = nhóm đảm bảo không phải L8), bảng tasks M10 13/13 done (đúng ánh xạ id PROGRESS), INV-001..034 frozen + 5 release gates + AIOS 1.0 READY/CERTIFIED. `architecture-v2.md` đánh dấu **LỊCH SỬ** (header/§0/§14); README link → v3.
- **Test**: `validate-v3.js` **19/19 PASS**; Mermaid parse thật (mermaid v11 + jsdom tại `aios/tools/mermaid-validate/`, node_modules gitignored) **12/12 khối OK**; AC9 diff v2 chỉ header/§0/§14; AC12 `docs/architecture/*` nguyên vẹn. **13/13 AC — TASK-076 DONE**.
- Xem chi tiết: `LOG.md` entry 2026-08-15 TASK-076.

## ✅ TASK-063 — Vẽ lại hoàn toàn kiến trúc hệ thống (2026-08-15)

- **Kết quả**: tạo `docs/architecture-v2.md` (markdown thuần — bảng + ASCII diagrams, KHÔNG Mermaid theo yêu cầu người dùng) — tài liệu kiến trúc **hiện hành** thay thế file cũ; file cũ `docs/architecture.md` giữ nguyên làm lịch sử.
- **Nội dung**: 14 mục — 7 tầng lõi M0–M5 + 4 lớp M6–M9 (Harness/Enterprise/Ecosystem/Autonomous) + 3 plane + Orchestrator modules + luồng request 12 bước + Runtime Kernel 9 services + Core Intelligence + INV-001..034 + milestones M0–M10 + bảng tasks M1–M9.
- **Test**: script node kiểm tra cấu trúc markdown 21/21 PASS; đối chiếu dữ liệu PROGRESS.md khớp. **7/7 AC — TASK-063 DONE**.
- Xem chi tiết: `LOG.md` entry 2026-08-15 TASK-063.

## M10 — AIOS 1.0 ✅ (2026-08-15 — DONE)

> PLAN.md §M10: `BUILD NOTHING — PROVE EVERYTHING → AIOS 1.0 CERTIFIED`. Freeze Architecture (INV-001..034, vi phạm = release blocker), Contract 1.0, Runtime durable, Autonomous bounded, 5 release gates, Golden Scenarios GS-001..020, `aiagent conformance` → **AIOS 1.0 READY**.
> 13 task (TASK-063..075), 5 phase: **P1 Freeze** (063, 064) → **P2 Harden** (065, 066, 069) → **P3 Secure** (067, 068, 070) → **P4 Productize** (071, 072, 075) → **P5 Certify** (073, 074).
> Kết quả: full suite **1939 pass** + vitest 13/13 + conformance READY + doctor 100/100. Review: `reviews/M10-review.md` (ACCEPTED, không P1).

| Task | Nội dung | Milestone | Trạng thái | Owner |
|------|----------|-----------|------------|-------|
| TASK-063 | F1 Architecture Freeze — Constitution 1.0 (INV-001..034 frozen) + docs/architecture/* (AIOS-1.0, layer-model, control-plane, execution-plane, autonomy) | M10-P1 | `done` ✅ (19/19 PASS; +2 enforcement test INV-008/012) | AIOS Orchestrator |
| TASK-064 | F2 Contract 1.0 — freeze 10 contracts (Agent/Capability/Tool/Workflow/Runtime/Event/Artifact/Plugin/Model/Memory) + semantic versioning + `aiagent contract-check` | M10-P1 | `done` ✅ (20/20 PASS) | AIOS Orchestrator |
| TASK-065 | F3 Runtime Hardening — failure matrix 12 loại (detect→contain→recover→resume) | M10-P2 | `done` ✅ (18/18 PASS — 12 scenario end-to-end) | AIOS Orchestrator |
| TASK-066 | Durable Execution 1.0 — journal + verify-before-resume + idempotency classification (exactly-once/at-least-once) | M10-P2 | `done` ✅ (10/10 PASS) | AIOS Orchestrator |
| TASK-069 | Reliability Engineering — SLO registry + non-averaged gates (policy bypass=0, lost execution=0, ...) | M10-P2 | `done` ✅ (12/12 PASS) | AIOS Orchestrator |
| TASK-067 | F4 Autonomy Safety — Action Proposal → Risk Classifier → Governor → Policy → Permission → Capability → Tool (mandatory, stop-anywhere) | M10-P3 | `done` ✅ (15/15 PASS) | AIOS Orchestrator |
| TASK-068 | Kill Switch — `aiagent stop execution/goal` + `aiagent emergency-stop` | M10-P3 | `done` ✅ (13/13 PASS) | AIOS Orchestrator |
| TASK-070 | Security Baseline 1.0 — 11 items baseline + `aiagent security-check` (9 PASS/2 WARN, SECURE) | M10-P3 | `done` ✅ (8/8 PASS) | AIOS Orchestrator |
| TASK-071 | F7 Developer Experience — command tree thống nhất + `aiagent doctor` first-class (Health 100/100) | M10-P4 | `done` ✅ (10/10 PASS) | AIOS Orchestrator |
| TASK-072 | AIOS Dashboard 1.0 — 11 tabs + Execution Timeline | M10-P4 | `done` ✅ (backend 5/5 + vitest 13/13) | AIOS Orchestrator |
| TASK-075 | Performance & Cost — metrics + Cost/Goal/Workflow/Agent/Tool/Success + model independence | M10-P4 | `done` ✅ (11/11 PASS) | AIOS Orchestrator |
| TASK-073 | F8 Certification Suite — 13 categories + GS-001..020 + `aiagent conformance` + 5 release gates | M10-P5 | `done` ✅ (9/9 PASS — **AIOS 1.0 READY**) | AIOS Orchestrator |
| TASK-074 | Upgrade & Migration 1.0 — migration plan/backup/dry-run/validation/rollback (0.x→1.0, plugin/contract/workflow v0→v1) | M10-P5 | `done` ✅ (13/13 PASS) | AIOS Orchestrator |

## ✅ Review toàn diện M0–M9 (2026-08-15)

- **Kết quả**: M0–M9 ĐẠT — backend 1793 pass + dashboard 12 + extension 19; CLI deliverable chạy thật (doctor/arch-health/run --simulate); **ALL 62 TASK đủ 8-file hard gate**.
- **Đã sửa (process/hồ sơ, không code)**:
  - Bổ sung file hard-gate thiếu cho 24 task: `test.md` (TASK-011/020/021/022), `review.md` (TASK-033/034/046/047/048/049), `evaluation.md` (TASK-045..049), `implementation/README.md` (23 task — pointer tới code thật).
  - PROGRESS.md: 8 header milestone sai `(in-progress)` → `✅` (M1/M2/M4/M5/M6/M7/M8/M9); ghi chú INV-022 lỗi thời → cập nhật theo M7 F3 đã resolve (nhãn canonical `test_inv022..inv029`).
- Xem chi tiết: `LOG.md` entry 2026-08-15 "M0-M9 review+fix".

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `done` ✅ |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `done` ✅ (review độc lập PASS) |
| M2 | Developer Edition (P3–P4: orchestrator v1 + assistants, tools/skills/sandbox) | `done` ✅ (669 tests, 95.51%) |
| M3 | Desktop Edition (P5–P6: dashboard, VS Code extension) | `done` ✅ (689 pytest + 12+19 vitest) — **review độc lập ACCEPTED** (V1–V6,V8 PASS; V7 P2 → đã bổ sung đủ 8-file hard gate TASK-017/018/019) |
| M4 | Platform Edition (P7–P8: upgrade pipeline, observability) | `done` ✅ (809 tests, 94.92%) — **review độc lập + 1 P1 fix (F1 arch-health scanner)** |
| M5 | Core Intelligence (P9–P10: memory/context/model/planning/graph/scheduler) | `done` ✅ (1086 tests, 95.22%) |
| M6 | AIOS Harness (P11: harness kernel, verification, test & simulation, evaluation, benchmark, doctor & readiness) | `done` ✅ (1521 tests, 95.35%) — **review độc lập (self) + 1 P2 fix (F1 harness scanner)** |
| M7 | Enterprise (P12: identity, tenancy, distributed runtime, distributed scheduler, governance, security, operations, dashboard) | `done` ✅ (1560 tests, 95.05%) — **review độc lập ACCEPTED** (V1–V7 PASS; V8 P2→RESOLVED: F1 scanner cover enterprise + F2 implementation/ + F3 INV-022 label) |
| M8 | Ecosystem (P13: Public SDK, Plugin Runtime, Extension Contracts, Registry, Developer Kit, Hub, Certification) | `done` ✅ (1639 tests) — **review độc lập (self) + 1 P2 fix (F1 M8 scanner coverage)** |
| M9 | Autonomous (P14: goal engine, planner, world model, loop, governor, recovery, long-horizon, memory, experimentation, multi-agent, evaluation, stuck, scheduler) | `done` ✅ (**1780 tests @M9, coverage 94.46%; full suite 1793 sau review + M5/M6/M7/M8 review additions**) — **review độc lập ACCEPTED** (V1–V7 PASS; V8 P2→RESOLVED: F1 scanner cover autonomous, F2/F3 không apply — TASK-050..062 đã đủ 8-file, INV-030..034 không collision) |
| M10 | AIOS 1.0 (P15: freeze architecture + contract 1.0 + hardening + durable + autonomy safety + kill switch + security baseline + DX + dashboard + certification + migration + performance) | `done` ✅ (**1939 tests + 13 vitest dashboard** — **review ACCEPTED, không P1; `aiagent conformance` → AIOS 1.0 READY**) |

## Hạ tầng bổ sung (bypass)

| Mục | Nội dung | Trạng thái | Ghi chú |
|-----|----------|------------|---------|
| Secret scan | GitHub Actions Gitleaks — quét secret trên push/PR master + manual trigger | `done` | `.github/workflows/secret-scan.yml` (2026-08-14) |
| Remote | Chuyển origin → repo GitHub mới `mrdanhdanh/aios-python` (PUBLIC) | `done` | commit e42bae4 (2026-08-14) |
| DoD checklist | **Definition of Done — Closing Checklist** (AGENTS.md §3.1 + PLAN.md): bắt buộc cập nhật LOG.md + PROGRESS.md + PLAN.md + STATS.md + task folder + commit sau MỖI task — tránh quên ghi tài liệu | `done` | theo yêu cầu người dùng 2026-08-15 |
| README docs | `[bypass]` — cập nhật `docs/README.md` (GitHub fallback render khi root không có README.md) khớp trạng thái AIOS 1.0: mô tả 7 tầng + CERTIFIED, bảng M0–M10, mục kiểm tra sức khỏe (`aiagent doctor/conformance/arch-health`), link constitution-1.0.md; không tạo README root mới | `done` | theo yêu cầu người dùng 2026-08-15 |


## M0 — Development Foundation ✅

| Bước | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| B0 | git init + docs/PLAN.md + AGENTS.md + .gitignore + commit | `done` | commit e50b715 |
| B1 | Tạo 4 VS Code custom agent (.github/agents/) | `done` | orchestrator + spec-writer + critic + reviewer |
| B2 | Tạo aios/progress/ (PROGRESS, LOG, STATS, TASK-001) | `done` | TASK-001 đủ 8 file, critique ×2 đã resolve |
| B3 | Commit lần cuối M0 | `done` | commit 08f1efa + c2d1032 |
| B4 | Verify M0 (agent picker, hard gate) | `done` | người dùng xác nhận B4.2/B4.3 2026-08-11 |
| B5 | **Milestone review M0** (hồi tố, bằng chứng repo) | `done` | 5/5 mục tiêu + 4/5 verification pass; M0 ĐẠT — xem `reviews/M0-review.md` |
| B6 | **Review brief** (template + bản M0) để đem cho model khác review độc lập | `done` | xem `reviews/REVIEW-BRIEF-TEMPLATE.md` + `reviews/M0-review-brief.md` |
| B7 | **Review brief M1** (điền từ template, 7 tiêu chí AC từ PLAN.md) | `done` | xem `reviews/M1-review-brief.md` |
| B7 | **Fix review findings** (F-001..F-004 P3) — bypass fixes + commit | `done` | commits 92f1321 + 3b7d8b6; working tree clean |

## M1 — Core Runtime ✅ (2026-08-12)

### P0 — Infrastructure (TASK-002) ✅
| Bước | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| 1 | Spec + critique ×2 + tasks + review | `done` | critic ×2 (19 vấn đề resolved), reviewer (8 vấn đề resolved) |
| 2 | Implement: scaffold monorepo + aios_core (config/logging/metadata/healthcheck) | `done` | commits 7a270ff + 486fb9f |
| 3 | Test + Evaluate | `done` | 32 tests pass, coverage 96.14%, 16/16 AC |
| 4 | Commit | `done` | working tree sạch |

### P0.5 — Runtime Kernel (TASK-003 + TASK-004 + TASK-005)

**TASK-003 — Kernel Foundations** ✅ (2026-08-12)
- semver + contracts + DI container + event bus + execution plan — 107 tests, coverage 94.82%, 20/20 AC

**TASK-004 — Kernel Services I** ✅ (2026-08-12)
- Context + EventService (audit SQLite) + ArtifactService (sidecar) + PermissionService + PolicyService
- 162 tests pass, coverage 94.77%, 13/13 AC — commit eb64795

**TASK-005 — Kernel Services II** ✅ (2026-08-12)
- Scheduler + State + Resource + ExecutionService + RuntimeKernel (9 services wiring)
- 207 tests pass, coverage 95.32%, 15/15 AC — commit code M1-P0.5c (`a3426de`; done `57f1896`)

### P1 — Model + Memory + Knowledge

**TASK-006 — Model Contract + Providers** ✅ (2026-08-12)
- ModelContract template-method + Mock/OpenAI/Ollama + ModelRegistry + RuntimeKernel wiring
- 233 tests pass, coverage 94.73%, 13/13 AC

**TASK-007 — Memory 4 loại + Knowledge pipeline** ✅ (2026-08-12)
- Conversation (SQLite) + Session (cache) + Knowledge (chunks+vectors cùng file) + Artifact (TASK-004)
- 270 tests pass, coverage 94.90%, 12/12 AC

### P2 — Workflow + Capability + Catalog

**TASK-008 — Workflow Definition + Compilers + Library** ✅ (2026-08-12)
- Declarative definition + DAG helper + MockCompiler + LangGraph stub + Library + CLI simulate
- **Deliverable M1 đạt: `aiagent run workflow.yaml --simulate` chạy được**
- 300 tests pass, coverage 94.92%, 10/10 AC

**TASK-009 — Capability + Prompt Registry + Catalog + Knowledge Graph** ✅ (2026-08-12)
- CapabilityRegistry + PromptRegistry (str.format v1) + SystemCatalog + KnowledgeGraph + PLAN amend
- **346 tests pass, coverage 95.30% — M1 HOÀN TẤT (9/9 tasks)**

## M1 — Follow-up (P3 remediation) ✅ (2026-08-12)

**TASK-011 — Remediation 9 P3 findings từ M1 v2 independent review** ✅ (2026-08-12)
- F-001 CLI subcommands (doctor / catalog list / workflow validate / contract validate, nested parsers)
- F-002 contract field-evolution regression tests (pydantic dual-class, 4 case direction)
- F-003 Resource FIFO queue (`acquire_slot_wait` blocking + `pending()`), giữ `acquire_slot` non-blocking
- F-004 Context inheritance (PARENT map, `get/get_context/get_all` inherit)
- F-005 Tool/Snapshot events (`SNAPSHOT_SAVED` + `TOOL_STARTED`/`TOOL_FINISHED` emit từ ExecutionService)
- F-006 Catalog `rebuild()` + `_revision` + `is_stale()`
- F-007 CLI dùng `RuntimeKernel.create()` / `SystemCatalog()` (DI đúng chỗ), không còn `ExecutionService(...)` trực tiếp
- F-008 ≥3 ADR (`docs/adr/0001..0003`) + link từ `PLAN.md`
- F-009 Benchmark harness (`tests/test_benchmark.py`, marked skippable)
- **428 tests pass, coverage 95.76%, 9/9 AC — M1 runtime hardening hoàn tất**

## M1 — Core Runtime ✅ (2026-08-12)
**Toàn bộ P0–P2 xong**: 9 services + contracts + DI + event bus + models (Mock/OpenAI/Ollama) + memory 4 loại + knowledge pipeline + workflow (CLI simulate) + capability + prompt + catalog + knowledge graph. Deliverable `aiagent run workflow.yaml --simulate` ✓

## Tasks

| Task ID | Mô tả | Milestone | Trạng thái | Owner |
|---------|-------|-----------|------------|-------|
| TASK-001 | M0 — Development Foundation | M0 | `done` ✅ | AIOS Orchestrator |
| TASK-002 | M1-P0 — Scaffold monorepo + backend core | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-003 | M1-P0.5a — Kernel Foundations | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-004 | M1-P0.5b — Kernel Services I (context, event+audit, artifact, permission, policy) | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-005 | M1-P0.5c — Kernel Services II (scheduler, state, resource, execution) + RuntimeKernel | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-006 | M1-P1a — Model Contract + providers (Mock/OpenAI/Ollama) | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-007 | M1-P1b — Memory 4 loại + Knowledge pipeline | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-008 | M1-P2a — Workflow Definition + compilers + library + CLI | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-009 | M1-P2b — Capability + Prompt Registry + Catalog + Knowledge Graph | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-010 | M2-P3a — AIOS Orchestrator v1: Decision Pipeline 4 tầng (Normalizer, Rule Engine, Workflow Matcher, Planner LLM) | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-012 | M2-P3b — Goal Manager + Task Queue + Permission Broker + Failure Recovery | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-011 | M1/P3 — Remediation 9 P3 findings từ M1 v2 review (CLI subcommands, contract field-evolution test, resource queue, context inheritance, tool/snapshot events, catalog rebuild, CLI DI, ADR, benchmark) | M1 (follow-up) | `done` ✅ | AIOS Orchestrator |
| TASK-016 | M2-ARCH — Architecture Hardening: INV-001..010 + AST tests + reference update (docs/architecture.md, ADR-0004, PLAN.md) | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-013 | M2-P3c — Assistants: General + Coder Pipeline + Doctor Pipeline + Safety Layer + System Doctor (Worker Plane — INV-001/002) | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-014 | M2-P4 — Tools 6 loại (Python/Docker/REST/MCP/Shell/Git) + Tool Registry + capability binding | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-015 | M2-P4 — Skills lifecycle 10 trạng thái + Skill Manager (zip/git/pip) + Sandbox Pool | M2 | `done` ✅ | AIOS Orchestrator |

## M2 — Developer Edition ✅ (2026-08-13)

**TASK-012 — M2-P3b: Goal Manager + Task Queue + Permission Broker + Failure Recovery** ✅ (2026-08-13)- `orchestrator/goals/` package mới: goal.py (GoalManager, state machine, cascade cancel), task_queue.py (dequeue atomic RETURNING, reorder 2 pha, recover stale), permission_broker.py (ask_scopes, default-deny no-approver), failure_recovery.py (retry→fallback→report), errors.py, schema.py (shared DDL), `__init__.py` (build_goal_modules factory)
- Kernel additive: EventType +6 (`goal.*`, `queue.updated`, `recovery.*`), `PolicyDecision.ask_scopes` (5 nhánh), `GoalsSettings` + config.yaml
- Critique ×2: 31 vấn đề resolved (C1-01..C1-16, C2-01..C2-15) — gồm 3 Critical, 6 Major
- **490 tests pass (baseline 428 + 62), coverage 95.96%, 12/12 AC**

**TASK-016 — Architecture Hardening** ✅ (2026-08-13)
- 10 Architecture Invariants (INV-001..010) chốt vào `docs/architecture.md` §7 + ADR-0004 + PLAN.md (link + index + Architecture Health→M4)
- Control/Execution Plane tách bạch; dependency 1 chiều Agent→Capability→Tool→Infra; Evaluation = post-execution observer; KB vs KG; Context vs Memory; Scheduler/Resource/Execution 3 vai; System Knowledge = System Brain
- **12 architecture tests** (`tests/test_architecture.py` + `_arch_scan.py`, AST pure scan — không import runtime): INV-003/004/005(A+B allow-list)/006/007(hard call-site)/009(4 business)/010 + helper; INV-001/002 skip (chờ agents//tools/)
- Critique ×2: 23 vấn đề resolved (1 P1 + 5 P2...); Review: CHANGES REQUESTED → R1 fix (SRC_ROOT parents[1])
- **502 passed + 2 skipped, coverage 95.96%, 10/10 AC**

**TASK-013 — M2-P3c: Assistants (Worker Plane)** ✅ (2026-08-13)
- `agents/` package mới (tuân INV-001/002 — chỉ import models.base/errors + pydantic + stdlib, mọi service qua callable injectable): base.py (template method handle + event sink best-effort), general.py, coder.py (7 steps + Self-Fix loop, repr-escape, exec ns), doctor.py (6 bước + Safety Layer 4 bất biến: disclaimer ok-only, cấm kê đơn trước (d), high→emergency, (d) gate không danger; KB-miss cautious), system_doctor.py (probe + score + FIX_HINTS), registry.py (RLock, resolve_by_intent qua selector)
- **test_architecture.py**: skip condition INV-002 sửa (chỉ agents/); `test_inv_agents_import_allowlist` (2 set, exclude agents*)
- Critique ×2: 25 vấn đề resolved (1 Critical + 5 Major...); Review: CHANGES REQUESTED → R1.1 (extractor union default KB) + R1.2 (allow-list exclude intra)
- **549 passed + 0 skipped, coverage 96.03%, 12/12 AC — INV-001/002 BẬT và PASS**

**TASK-014 — M2-P4: Tools (Execution Plane)** ✅ (2026-08-13)
- `tools/` package mới (allow-list cứng — chỉ metadata + pydantic + stdlib + urllib.parse; KHÔNG kernel/capabilities/agents/orchestrator): base.py (template run 1-6: tool_id → gate fail-closed [None/False/raise] → started → _run(input, context) → finished → output), 6 stub tool (Python ast.parse no-exec / Docker mock / REST validate / MCP registry giả / Shell no-exec scope bắt buộc / Git mock), registry.py (RLock, bind_capabilities qua callable — idempotent)
- **test_architecture.py**: `test_inv_tools_import_allowlist` (2 set + urllib AST module-con check R3)
- Critique ×2: 27 vấn đề resolved (1 P1 + 7 P2...); Review: APPROVED + 3 lưu ý (duration_s error path, gate-raise test, urllib AST)
- **622 passed + 0 skipped, coverage 96.15%, 14/14 AC**

**TASK-015 — M2-P4: Skills + Sandbox Pool** ✅ (2026-08-13)
- `skills/` package: base.py (10 SkillState + bảng transitions T1-T10 — C1-01, manifest validate bằng aios_core.semver), manager.py (lifecycle đầy đủ + optimistic concurrency WHERE state + dependent check rollback/remove + history stack), registry.py (read-through), sources.py (Zip/Git/Pip stub no-syscall), schema.py (CHECK sinh từ hằng số)
- `sandbox/` package: pool.py (SandboxPool — acquire warm reuse + normalize language, execute no-exec, release, evict_idle(now=...), health; RLock; không thread nền)
- **test_architecture.py**: `test_inv_skills_import_allowlist` (metadata + semver) + `test_inv_sandbox_import_allowlist` (empty set)
- Critique ×2: 27 vấn đề resolved (1 Critical + 4 Major...); Review: CHANGES REQUESTED → R1 (dependent check spec body) + R2 (optimistic spec body) + R3 (semver 6 chỗ)
- **669 passed + 0 skipped, coverage 95.51%, 18/18 AC — M2-P4 HOÀN TẤT**

## M3 — Desktop Edition ✅ (2026-08-13)

**TASK-017 — M3-P5: FastAPI REST + WebSocket API** ✅ (commit 16c998f)
- `api/` package: app.py (create_app), wiring.py (build_registries — MockModel registered đầu, catalog populated), serve.py (uvicorn), routers/ 9 router (health score = 1 - weight/2, events REST + WS loop.call_soon_threadsafe, catalog, goals, skills, tools, memory, prompts, chat ChatRequest → orchestrator → assistant resolve theo intent)
- CLI `aiagent serve --host --port` (lazy import)
- **689 passed + 0 skipped, coverage 95.10%** (14 API test + 6 chat/serve test mới)

**TASK-018 — M3-P5: Dashboard SPA (React + Vite + TS)** ✅ (commit 33b6b05)
- `dashboard/`: vite proxy /api → 127.0.0.1:8000 (ws: true), 10 tabs (Chat/Workflow/Events/Tools/Memory/Artifacts/Skills/Models/Prompts/Health), api.ts 3-envelope, ws.ts reconnect 3s + MockWebSocket stub
- **vitest 12/12 pass + vite build OK**

**TASK-019 — M3-P6: VS Code Extension (TS, 9 lệnh)** ✅
- `extension/`: package.json (9 commands + activationEvents + config aios.serverUrl), client.ts (AiosClient.callChat — 3 envelope + 422 array + trim slash), context.ts (editorText qua document.getText — Selection thật không có .text; gitDiff(cwd); buildPrompt 8 template), extension.ts (activate với vscode injected, 9 commands, INTENTS map đúng bảng §4, guard selection warning, editor.edit replace cho fix/generate_test)
- Critic ×2: critique-1 13 vấn đề (1 P1 — Selection.text, 7 P2, 5 P3) + critique-2 3 vấn đề — resolved hết; Review: APPROVED có điều kiện → 3 R2 (gitDiff cwd, intent test 9 case, editor.edit test) + 7 R3 resolved
- **Đủ 8-file hard gate**: spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/ (test.md + implementation/README.md bổ sung 2026-08-15 để đóng F1 review)
- **vitest 19/19 pass + tsc clean + build emit out/extension.js — M3 HOÀN TẤT**

**TASK-017 / TASK-018 — bổ sung hard-gate files (F1 review M3, 2026-08-15)**: TASK-017 thiếu critique-2/tasks/review/test/implementation → đã tạo đủ; TASK-018 thiếu tasks/review/test/implementation → đã tạo đủ. Cả 3 task TASK-017/018/019 nay đủ 8-file hard gate (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/).
## M4 — Platform Edition ✅ (2026-08-13)

### P7 — TASK-020: Upgrade Pipeline ✅ (2026-08-13)
- `upgrade/` package: dependency.py (ComponentSpec/Dependency frozen, DependencyResolver — DFS post-order, sort (name,version), missing/cycle/conflict, deterministic), backup.py (BackupStore SQLite — backup/restore/list, persist cross-instance), migrator.py (Migrator Protocol + DictMigrator + SkillMigrator wrap SkillManager — payload = model_dump JSON), pipeline.py (6 bước: read current → skip check → compatibility → dependencies → backup → migrate → health → complete; dry-run 0→2; rollback best-effort: migrator.rollback ưu tiên, fallback write_current backup; 9 UPGRADE_* events), errors.py (UpgradeError)
- `kernel/events.py`: +8 EventType members (UPGRADE_STARTED..ROLLED_BACK, value "upgrade.<snake>")
- `workflow/cli.py`: subcommand `aiagent upgrade <kind> <id> --version X [--dry-run]` — v1 chỉ wire skill (SkillMigrator + SkillManager từ settings); exit codes chuẩn
- `test_architecture.py`: `test_inv_upgrade_import_allowlist` (internal: contracts/semver/kernel.events/skills.errors; hook-injected — không import skills.manager)
- Critic ×2: 31 vấn đề (9 P1) resolved — **quyết định: chỉ migrate ROOT, dependency chỉ resolve**; Review: CHANGES REQUESTED → 1 R1 + 3 R2 + 6 R3 resolved
- **730 passed + 0 skipped, coverage 95.00%, 10/10 AC — P7 HOÀN TẤT**

### P8 — TASK-021: Observability & Diagnostics ✅ (2026-08-13)
- `observability/` package: metrics.py (MetricsService — subscribe EventBus, category workflow/tool, duration từ Event.timestamp, UPDATE row mới nhất chưa finish, orphan NULL, tool_failures), prompt_history.py (PromptHistory — SQLite sort_keys), profiler.py (Profiler — fake clock, double-start raise), doctor.py (HealthDoctor — worst-wins + diagnostics hooks, tránh trùng agents.SystemDoctor), arch_scan.py (move từ tests/ — 1 engine, SRC_ROOT parents[2]), arch_health.py (ArchitectureHealth — scan(package_dir), layer/contract/policy 3 check), evaluation.py (EvaluationStore — cache STARTED duration, COMPLETED→success / FAILED+CANCELLED→failed, evaluate() feedback)
- `kernel/services/execution.py`: +5 emit (WORKFLOW_FAILED 6 nhánh _run, WORKFLOW_CANCELLED flag + cancel giữa node; resume ×2 + cancel trước execute không emit)
- `api/routers/observability.py`: 5 GET (metrics/prompt-history/doctor/arch-health/evaluations) + POST feedback (404/422); wiring regs["observability"]; config ObservabilitySettings
- CLI: `aiagent metrics` / `doctor` (giữ key kernel) / `arch-health`
- Critic ×2: 36 vấn đề (9 P1) resolved; Review: APPROVED có điều kiện → 3 amendment (duration cache, emit scope, doctor key) + R2-2 + R3×7 resolved
- **779 passed + 0 skipped, coverage 95.11%, 10/10 AC — P8 Phần 1 HOÀN TẤT**

### P8 — TASK-022: Orchestrator v2 ✅ (2026-08-13)
- `orchestrator/advisor.py` — ImprovementAdvisor: 5 rules deterministic (quality thấp, fail nhiều, tool failures, prompt chưa đánh giá, workflow chậm — duration_by_workflow mới) + dedup/sort; suggestion KHÔNG tự áp dụng
- `orchestrator/supervisor.py` — ExecutionSupervisor: track running từ bus (clock float monotonic), stuck detect, FAILED+CANCELLED → recent_failed, queue hook
- `orchestrator/evaluation_collector.py` — EvaluationCollector: evaluator layer trên EvaluationStore, KeyError/error swallow, collect_all aggregate; trigger qua bus wiring
- `orchestrator/goals/reporting.py` — GoalReporter: 5 status, avg_progress, failed=FAILED+CANCELLED, report_goal detail (qua public API — không sửa GoalManager)
- API `/api/v1/orchestrator-v2/` (4 GET); wiring regs["orchestrator_v2"] + TaskQueue wire; CLI `aiagent advisor`/`supervisor`; metrics.py +duration_by_workflow
- Critic ×2: 24 vấn đề (7 P1) resolved; Review: APPROVED có điều kiện → 1 R2 + 3 R3 resolved (+1 bypass fix `_metrics` suffix)
- **809 passed + 0 skipped, coverage 94.92%, 8/8 AC — P8 HOÀN TẤT → M4 HOÀN TẤT**

### M4 — Review độc lập (self-review, 2026-08-15)
- Đọc thực tế code TASK-020/021/022 + spec + chạy test thật + chạy scanner trên cây thật `SRC_ROOT`.
- **F1 (P1)**: `ArchitectureHealth.scan()` bỏ qua TOÀN BỘ layer/contract check trên cây thật — `target = package_dir / sub` với `package_dir = backend/src`, nhưng `agents/` nằm dưới `backend/src/aios_core/agents` → `is_dir()` False → skip silent; chỉ policy check chạy. Thêm nữa: `rel` truyền dot-form vào `collect_imports` (hàm expects slash-form) → relative import phân giải sai. **→ ĐÃ TỰ SỬA**: tính `aios_root = package_dir/"aios_core"` nếu tồn tại; truyền `rel` slash-form; exempt slash-form. Thêm 2 test regresi (nested layout).
- F2 (P3): `orchestrator/__init__.py` không export module M4 mới (inconsistency, không phải bug). F3 (P3): advisor rule 1+5 dedup collapse (đúng spec).
- Kết quả: **M4 ĐẠT** V1–V8 (sau fix F1); full suite `1636 passed, 0 fail`. Xem `reviews/M4-review.md` + `reviews/M4-review-brief.md`.

## M5 — Core Intelligence ✅ (2026-08-15)

> PLAN.md §M5: nâng cấp "bộ não vận hành" — không thêm agent/UI. Trả lời: Memory (nhớ gì?), Context (đưa gì vào?), Model Router (dùng model nào?), Planning (làm bước nào?), Execution Graph (phụ thuộc thế nào?), Scheduler (chạy khi nào/song song?).
> Thứ tự: Phase 1 (023→024) → Phase 2 (025) → Phase 3 (026→027→028). Mỗi task qua hard gate đầy đủ (spec → critique ×2 → tasks → review → implement → test → evaluate).
> DoD M5: Memory không truy cập trực tiếp từ Agent; Context có budget + priority; Model routing theo policy + fallback; Planner tạo task graph; Graph hỗ trợ dependency + parallel; Scheduler không sở hữu Resource/Execution; INV-011..016 enforced bằng AST tests; observability đầy đủ.

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-023 | Memory Coordinator — Retrieve → Filter → Rank → Deduplicate → Compress → Prioritize → Inject; contract MemoryQuery/Candidate/Score/Selection/Context; budget; INV-011 | `done` ✅ | 855 pass, coverage 95.16%, 10/10 AC (2026-08-14) |
| TASK-024 | Context Optimizer — Deduplicate → Compress → Prioritize → Token Budget → Final Context; priority P0–P6; compression 3 cấp; INV-012 | `done` ✅ | 896 pass, coverage 95.21%, 11/11 AC (2026-08-14) |
| TASK-025 | Model Router — ModelSelector/RoutingPolicy/CostEstimator/AvailabilityChecker/FallbackResolver/ModelHealth; metadata model; policy yaml; fallback theo Policy; INV-013 | `done` ✅ | 949 pass, coverage 95.13%, 11/11 AC (2026-08-14) |
| TASK-026 | Planning Engine — Goal Analyzer → Task Decomposer → Dependency Analyzer → Capability Resolver → Risk Analyzer → Execution Planner → Execution Graph; plan validation 8 hạng mục; INV-014 | `done` ✅ | 1003 pass, coverage 95.00%, 11/11 AC (2026-08-15) |
| TASK-027 | Execution Graph — ExecutionGraph/GraphNode/GraphEdge/Dependency/Condition/JoinPolicy/FailurePolicy; graph state 8 trạng thái; INV-015 | `done` ✅ | 1055 pass, coverage 95.09%, 13/13 AC (2026-08-15) |
| TASK-028 | Parallel Scheduler — Graph Scheduler → Resource → Execution → State; không sở hữu Resource/Execution; INV-016 | `done` ✅ | 1086 pass, coverage 95.22%, 12/12 AC (2026-08-15) — **M5 HOÀN TẤT** |

### M5 — Review độc lập (self-review, 2026-08-15)
- Đọc thực tế code TASK-023..028 + spec, chạy test thật (256 M5 test + 17 INV-011..016 arch test PASS), chạy scanner trên cây thật.
- **F1 (P2)**: runtime `ArchitectureHealth.scan()` không cover M5 packages (memory/context/models.router/orchestrator.planning/kernel.graph/kernel.scheduler) — vi phạm PLAN §M5 "observability đầy đủ". **→ ĐÃ TỰ SỬA**: thêm 6 M5 layer rule vào `arch_health.py` + 6 test regresi `test_observability_arch_health.py`; scanner trên `SRC_ROOT` → `healthy=True, 0 violations`.
- **F2 (P3)**: M5 thiếu milestone review doc (M0/M3/M4 có). **→ ĐÃ TỰ SỬA**: viết `reviews/M5-review.md` + `reviews/M5-review-brief.md`.
- Kết quả: **M5 ĐẠT** V1–V8 (sau F1); không P1. Xem `reviews/M5-review.md` + `reviews/M5-review-brief.md`.

## M6 — AIOS Harness ✅ (2026-08-15)

> PLAN.md §M6: subsystem `harness/` giúp AIOS tự kiểm thử/xác minh/quan sát/cải tiến (H1-H5). Không sửa Runtime/Orchestrator — chỉ gọi qua API. INV-017..021.

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-029 | H1 Harness Kernel — contracts chung + lifecycle 8-state + registry + runner + evidence (INV-018); INV-017 isolation | `done` ✅ | 1124 pass, coverage 95.20%, 10/10 AC (2026-08-15) |
| TASK-030 | H2 Execution Verification — Preconditions/Postconditions/Verdict + Evidence Package + Replay; INV-019 | `done` ✅ | 1210 pass, coverage 95.26%, 10/10 AC (2026-08-15) |
| TASK-031 | H3 Test & Simulation — Scenario + Simulation Mode; không side effect | `done` ✅ | 1299 pass, coverage 95.26%, 12/12 AC (2026-08-15) |
| TASK-032 | H4 Evaluation Harness — Evaluation Model + Suite + Trajectory; INV-020 | `done` ✅ | 1387 pass, coverage 95.27%, 12/12 AC (2026-08-15) |
| TASK-033 | H4 Benchmark + Regression Gate — INV-021 | `done` ✅ | 1450 pass, coverage 95.31%, 11/11 AC (2026-08-15) |
| TASK-034 | H5 Doctor & Readiness — Doctor architecture + Readiness Score | `done` ✅ | 1521 pass, coverage 95.35%, 11/11 AC (2026-08-15) — **M6 HOÀN TẤT** |
| INV-011..016 | Enforcement tests (AST) trong `tests/test_architecture.py` + observability metrics M5 | `todo` | tích hợp trong các task |

## M7 — Enterprise ✅ (2026-08-15)

> PLAN.md §M7: đưa AIOS từ single-instance thành nền tảng vận hành an toàn quy mô doanh nghiệp. 7 nhóm (E1–E7), 8 invariant (INV-022..INV-029). Không biến AIOS thành cloud/distributed platform — chỉ định nghĩa contract + governance.
> Dependency: TASK-035 → TASK-036 → ┬ TASK-037 ┐ → TASK-038 → TASK-039 → TASK-041 → TASK-042; └ TASK-040 ┘ song song với TASK-037.
> Approach: gom 8 task thành 1 package `backend/src/aios_core/enterprise/` (offline-first, DI injectable, không God Object), mỗi nhóm = 1 module, facade `EnterpriseManager` trong `runtime_kernel`. Behavioral tests trong `tests/test_enterprise.py`, structural invariant tests trong `tests/test_architecture.py` (m7_*).

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-035 | E1 Identity & Access — Principal (user/agent/service), RBAC + ABAC, delegation + capability attenuation; INV-022 | `done` ✅ | `enterprise/identity.py` + `contracts.py`; 29 enterprise tests pass (chung) |
| TASK-036 | E2 Multi-Tenancy — Tenant model + TenantBoundary (deny-by-default) + MemoryNamespace isolation; INV-023 | `done` ✅ | `enterprise/tenancy.py` |
| TASK-037 | E3 Distributed Runtime — RuntimeNodeInfo + NodeRegistry + RuntimeRouter (tenant/region/capability/capacity/cost/health), tenant_class gate; INV-029 | `done` ✅ | `enterprise/runtime.py` |
| TASK-038 | E4 Distributed Scheduler + Lease — single-active lease (INV-026) + failover/resume snapshot | `done` ✅ | `enterprise/scheduler.py` |
| TASK-039 | E5 Resource Governance — QuotaManager (fairness INV-025) + CostGovernor (budget deny / cheaper route) | `done` ✅ | `enterprise/governance.py` |
| TASK-040 | E6 Security & Data Isolation — CredentialBroker (scoped INV-024) + NetworkPolicy (default-deny) + SandboxBoundary (INV-028) | `done` ✅ | `enterprise/security.py` |
| TASK-041 | E7 Operations — CentralAuditStore (tamper-evident INV-027) + HealthMonitor failover + RecoveryManager | `done` ✅ | `enterprise/operations.py` |
| TASK-042 | Enterprise Operations + Dashboard — EnterpriseDashboard aggregate tenant metrics từ audit | `done` ✅ | `enterprise/dashboard.py` |
| TASK-043 | M8-E1 — Public AIOS SDK | `done` ✅ | 5 SDK tests pass; backend regression có 1 flaky timing failure không liên quan |
| TASK-044 | M8-E2 — Plugin Runtime | `done` ✅ | 1584 tests (baseline 1560 + 24), 1 flaky timing có sẵn |
| INV-022..029 | 8 architecture invariant enforced bằng import allow-list + source-literal tests trong `tests/test_architecture.py` (`test_inv022..inv029_*` — canonical, rename từ `test_m7_*` sau M7 F3) | `done` ✅ | 79 arch tests pass (chung) |

**Deliverable M7 (batch)**: `backend/src/aios_core/enterprise/` 10 file (contracts, identity, tenancy, runtime, scheduler, governance, security, operations, dashboard, __init__) + config (`EnterpriseSettings` trong `config.py` + `config.yaml`) + wiring (`RuntimeKernel.create` register `EnterpriseManager`) + `tests/test_enterprise.py` (29 tests) + `tests/test_architecture.py` (8 m7_* invariant tests).
**1560 passed + 0 skipped, coverage 95.05%, 8/8 AC (E1–E7) — M7 CORE HOÀN TẤT**.

> ✅ Ghi chú đánh số (đã resolve M7 review F3, 2026-08-15): nhãn INV chuẩn hóa — M6 = `test_inv017..inv021` (4 test M6-H5 đã rename khỏi nhãn inv022), M7 = `test_inv022..inv029` (canonical, đã rename từ `test_m7_*`), M9 = `test_inv030..inv034`. Không còn xung đột nhãn.

## M8 — Ecosystem ✅ (2026-08-15)

> PLAN.md §M8: đưa AIOS từ nền tảng vận hành (M7) thành hệ sinh thái mở rộng được bởi bên thứ ba. E1–E4 = Core Ecosystem, E5–E7 = hệ sinh thái bên ngoài. M8 KHÔNG thêm architecture invariant (tập invariant giữ nguyên tại M8).
> Dependency: TASK-043 → ┬ TASK-044 ┐ → TASK-046 Registry → TASK-047 DevKit → TASK-049 Certification → TASK-048 Marketplace; └ TASK-045 ┘
> Approach: SDK độc lập (`sdk/python/`), Plugin Runtime trong `backend/src/aios_core/plugins/` (lifecycle reuse 10-state skills — không state machine thứ hai), plugin là record passive (không chạm Runtime/Registry/DB trực tiếp — import allow-list).

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-043 | E1 Public AIOS SDK — `from aios import Agent, Tool, Capability, Workflow, Client`; transport injection; không import aios_core | `done` ✅ | `sdk/python/`; 5 SDK tests (2026-08-15) |
| TASK-044 | E2 Plugin Runtime — lifecycle 10-state reuse `SkillState`/`assert_transition`; compat aios range (`*`/`2.x`/semver); dependency + dependent check; provides index active-only; events plugin.* | `done` ✅ | `plugins/` 7 file + 4 arch test m8_*; 1584 tests (2026-08-15) |
| TASK-045 | E3 Extension Contracts — Internal/Public/Extension/Experimental API + Compatibility Matrix | `done` ✅ | `extension/` 4 file; 8 tests + 3 arch (2026-08-15) |
| TASK-046 | E4 Ecosystem Registry — Registry v2 + discovery (`aios search`), MCP làm adapter | `done` ✅ | `ecosystem/registry.py` + `contracts.py`; 7 tests + arch (2026-08-15) |
| TASK-047 | E5 Developer Kit — `aios create/dev/test` scaffold | `done` ✅ | `ecosystem/devkit.py` + CLI `aiagent plugin create`; 7 tests + arch (2026-08-15) |
| TASK-048 | E6 Marketplace/Distribution — Trust Model + signature | `done` ✅ | `ecosystem/marketplace.py` + CLI `aiagent marketplace publish`; 12 tests + arch (2026-08-15) |
| TASK-049 | E7 Certification — COMMUNITY→VERIFIED→CERTIFIED, Harness gate | `done` ✅ | `ecosystem/certification.py`; 9 tests + arch (2026-08-15) |

**Deliverable M8 (7/7)**: `sdk/python/src/aios/` (TASK-043) + `plugins/` (TASK-044) + `extension/` (TASK-045: ApiNamespace + matrix) + `ecosystem/` (TASK-046..049: registry/contracts, devkit, certification, marketplace) + config `PluginSettings`/`EcosystemSettings` + `config.yaml` + wiring (`regs["plugins"]`/`regs["plugin_registry"]`/`regs["ecosystem"]`) + CLI `aiagent ecosystem search` / `plugin create` / `marketplace publish` + 4 EventType `PLUGIN_*`.
**1639 passed (baseline 1584 + 55 mới), 7/7 AC (E1–E7) — M8 HOÀN TẤT**.

> M8 KHÔNG thêm architecture invariant (đúng PLAN); arch tests `test_m8_*` (13 tests: 4 plugins + 3 extension + 6 ecosystem) bảo vệ import allow-list + literal gates.

## M9 — Autonomous ✅ (2026-08-15)

> PLAN.md §M9: đưa AIOS từ "nhận task và thực hiện task" thành "tự phát hiện mục tiêu, lập kế hoạch dài hạn, tự thực hiện, tự kiểm chứng, tự phục hồi, tự học trong giới hạn Policy".
> `Autonomous = Goal-driven + Bounded + Observable + Reversible + Evaluated`. Autonomy Layer KHÔNG thay Orchestrator — nó định hướng Orchestrator (Autonomy → Orchestrator → Runtime).
> 13 task (TASK-050..062), 5 invariant mới (INV-030..034). 4 phase: P1 Foundation (050-054) → P2 Long-running (055,056,057,061) → P3 Adaptive (058,060) → P4 Ecosystem (059,062).
> Approach: 1 package `backend/src/aios_core/autonomous/` (Autonomy Layer, offline-first, DI injectable, facade `AutonomyManager`), mỗi task = 1 module; behavioral tests `tests/test_autonomous.py`, invariant tests `tests/test_architecture.py` (test_m9_*).

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-050 | Autonomous Goal Engine — Goal contract (objective/success/constraints/permissions/autonomy) + lifecycle PROPOSED→VALIDATING→APPROVED→PLANNING→EXECUTING→EVALUATING→COMPLETED (+BLOCKED/RECOVERY/REPLANNING/ESCALATED) | `done` ✅ | `autonomous/goal.py` (2026-08-15) |
| TASK-051 | Autonomous Planner — Goal→World→Constraints→Capabilities→History→Plan; assumptions/steps/success_conditions/rollback; dynamic replanning | `done` ✅ | `autonomous/planner.py` (2026-08-15) |
| TASK-052 | World Model — WorldState (System/Runtime/Goals/Tasks/Environment/Constraints/History) + Fact (source/timestamp/confidence/freshness); World ≠ Memory | `done` ✅ | `autonomous/world.py` (2026-08-15) |
| TASK-053 | Autonomous Loop — Observe→Understand→Decide→Plan→Policy→Act→Verify→Learn; mọi action qua Governor (INV-030) | `done` ✅ | `autonomous/loop.py` (2026-08-15) |
| TASK-054 | Autonomy Governor — CONTINUE/PAUSE/ASK_HUMAN/REPLAN/ROLLBACK/STOP + budget (steps/llm/cost/duration/tool/retries/parallel) + risk budget; INV-030/031 | `done` ✅ | `autonomous/governor.py` (2026-08-15) |
| TASK-055 | Autonomous Recovery — Detect→Classify→Diagnose→Strategies→Score→Policy→Execute→Verify; fingerprint + circuit breaker + cooldown + escalation | `done` ✅ | `autonomous/recovery.py` (2026-08-15) |
| TASK-056 | Long-Horizon Execution — ExecutionSession + Checkpoint + context compaction + resume (INV-032) | `done` ✅ | `autonomous/long_horizon.py` (2026-08-15) |
| TASK-057 | Autonomous Memory — Working/Episodic/Semantic/Procedural/Failure/Goal + Learning Loop (candidate→dedup→validate→confidence→promote); INV-034 | `done` ✅ | `autonomous/memory.py` (2026-08-15) |
| TASK-058 | Autonomous Experimentation — Hypothesis→Design→Sandbox→Execute→Evaluate→Compare→Accept/Reject (qua Harness — INV-033) | `done` ✅ | `autonomous/experimentation.py` (2026-08-15) |
| TASK-059 | Multi-Agent Autonomy — mode single/parallel/sequential/hierarchical + delegation (owner/deadline/budget/output contract) | `done` ✅ | `autonomous/multi_agent.py` (2026-08-15) |
| TASK-060 | Autonomous Evaluation — correctness/quality/cost/risk/progress/confidence → decision (continue/retry/replan/stop/ask) + ProgressEstimator | `done` ✅ | `autonomous/evaluation.py` (2026-08-15) |
| TASK-061 | Advanced Stuck Detection — 7 signals (repeated tool/errors, no state change/progress, oscillation, budget burn, contradictory) | `done` ✅ | `autonomous/stuck.py` (2026-08-15) |
| TASK-062 | Autonomous Scheduler — proactive triggers (interval/daily) chạy workflow/goal tự động | `done` ✅ | `autonomous/scheduler.py` (2026-08-15) |
| INV-030..034 | 5 invariant enforced bằng arch tests `test_m9_*` (governor gate, budget, checkpoint/resume, experiment qua harness, memory promote có kiểm chứng) | `done` ✅ | 10 arch tests trong `tests/test_architecture.py` |

**Deliverable M9 (13/13)**: `backend/src/aios_core/autonomous/` 16 file (contracts, errors, goal, planner, world, loop, governor, recovery, long_horizon, memory, stuck, experimentation, evaluation, multi_agent, scheduler, __init__) + config `AutonomousSettings` + `config.yaml` + wiring (`AutonomyManager` trong RuntimeKernel.create) + 10 EventType `autonomy.*` + `tests/test_autonomous.py` (129 tests) + `tests/test_architecture.py` (test_m9_* — 10 arch tests INV-030..034).
**1780 passed (baseline 1639 + 141 mới), coverage 94.46%, 13/13 AC (TASK-050..062) — M9 HOÀN TẤT**.

> Autonomy Layer định hướng Orchestrator (Autonomy → Orchestrator → Runtime); INV-030..034 enforced: governor gate duy nhất (loop gọi check_action), 7 budget limits, checkpoint/resume SQLite, experiment evidence-first, memory promote double gate.

## TASK-063 — Vẽ lại hoàn toàn tài liệu kiến trúc (docs-only) ✅ (2026-08-15)

- Tạo `docs/architecture-v2.md` — tài liệu kiến trúc **hiện hành** (markdown thuần: bảng + danh sách + ASCII diagrams — KHÔNG Mermaid, theo yêu cầu người dùng); phản ánh M0–M9 done + M10 todo + INV-001..034 + bảng tasks M1–M9.
- File cũ `docs/architecture.md` giữ nguyên làm lịch sử (AC6); nguồn dữ liệu: PROGRESS.md/PLAN.md/code thật.
- Hard gate đủ 8-file; test cấu trúc markdown 21/21 PASS; **7/7 AC — TASK-063 DONE**.

| Task ID | Mô tả | Milestone | Trạng thái | Owner |
|---------|-------|-----------|------------|-------|
| TASK-063 | Vẽ lại hoàn toàn tài liệu kiến trúc hệ thống — `docs/architecture-v2.md` (markdown thuần, thay thế file cũ làm bản hiện hành) | Docs | `done` ✅ | AIOS Orchestrator |

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-15 | TASK-044 | implement/test | plugins/: lifecycle reuse 10-state, compat, provides, dependency, events; 1584 collected (baseline 1560 + 24), 10/10 AC — TASK-044 DONE` → done
2. `2026-08-15 | TASK-044 | hard-gate | spec + critique ×2 + tasks + review PASS` → done
3. `2026-08-15 | TASK-043 | evaluate | Public SDK v1 đạt phạm vi; TASK-043 DONE` → done

