# TASK-073 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-073 (task lớn nhất M10 — đặc biệt chú ý).

## Các vấn đề

### C1-01 (P1) — 20 Golden Scenario "chạy được" nghĩa là gì? Đừng check giả
Mỗi GS phải kiểm tra MỘT hành vi cụ thể bằng component thật.
→ **Resolve**: Mỗi GS có check_fn(ctx) thao tác component thật + assert kết quả:
- GS-001 chat: Orchestrator/assistant handle intent chat → response ok
- GS-002 coding: CoderAssistant pipeline → code output
- GS-003 workflow: ExecutionService chạy plan 2 node → completed
- GS-004 tool fail: tool _run raise → output.ok=False (không crash)
- GS-005 agent fail: assistant _process raise → status error
- GS-006 policy deny: plan required_permissions bị policy deny → FAILED
- GS-007 human approval: policy requires_approval → FAILED "approval required"
- GS-008 checkpoint-resume: execute crash → resume → completed (node done không chạy lại)
- GS-009 autonomous goal: GoalEngine lifecycle → APPROVED→EXECUTING
- GS-010 long-horizon: JournaledExecutor checkpoint/resume 4 node
- GS-011 multi-agent: MultiAgentOrchestrator sequential 2 agent
- GS-012 plugin install: PluginManager install valid manifest
- GS-013 incompat: PluginManifest aios range không match → fail-fast
- GS-014 upgrade: upgrade pipeline dry-run → compatibility ok
- GS-015 rollback: upgrade fail → rollback best-effort
- GS-016 security violation: CredentialBroker scope deny → denied
- GS-017 arch violation: scanner phát hiện import xấu (dùng fixture) → violation
- GS-018 memory learning: LearningLoop candidate → validate → promote
- GS-019 self-improvement: Experimentation ACCEPTED qua evidence (INV-033)
- GS-020 emergency stop: KillSwitch.emergency_stop → preflight False

### C1-02 (P1) — Gate B: "critical=0, high=0" nghĩa là gì với security-check?
SecurityChecker blocking chỉ critical. High=0 → mọi FAIL severity high cũng chặn.
→ **Resolve**: Gate B = SecurityChecker report: không FAIL severity critical VÀ không FAIL severity high (warn cho phép). Test 2 nhánh.

### C1-03 (P2) — Gate D "critical scenario failures = 0"
→ **Resolve**: Gate D = mọi GoldenScenario PASS (20/20) + SLO release_ready. Test.

### C1-04 (P2) — Gate A dùng gì?
→ **Resolve**: Gate A = ArchitectureHealth.scan() (runtime scanner thật) healthy + test_architecture.py chạy pass (qua pytest --no-cov subset? Không — conformance dùng scanner + DoctorFirstClass.architecture). Ghi chú: full arch tests chạy trong CI/pytest, conformance dùng scanner.

### C1-05 (P3) — Conformance chạy lâu?
→ **Resolve**: Golden scenarios deterministic nhanh (<2s); conformance total <5s.

## Kết luận
Resolve vào spec v2 (bảng 20 GS cụ thể, Gate B 2 nhánh, Gate D qua GS+SLO).
