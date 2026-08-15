# TASK-067 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-067.

## Các vấn đề

### C1-01 (P1) — "Governor" là governor nào? Phải định nghĩa callable contract
AutonomousGovernor có check_action(proposal) hay method khác?
→ **Resolve**: SafetyEnforcer nhận 3 callable injectable với contract rõ: `governor_fn(proposal) -> str` (continue/pause/ask_human/replan/rollback/stop — theo INV-030), `policy_fn(proposal) -> PolicyDecision-like (approved/requires_approval)`, `permission_fn(proposal) -> bool`. Enforcer không import governor/policy trực tiếp (duck-typed, không God Object). Test dùng fake functions.

### C1-02 (P2) — Risk Classifier 5 mức: mức nào chặn?
→ **Resolve**: Bảng deterministic: action read/edit = risk 1–2; commit/deploy/network = 3–4; delete/destructive = 5. Rule: risk ≥ 4 → ASK_HUMAN; risk = 5 → STOP (trừ khi proposal khai báo approval đã có). Test từng action.

### C1-03 (P2) — Evidence chain phải ghi đủ 4 gate
→ **Resolve**: SafetyDecision.evidence = list[str] luôn đủ 4 phần tử (risk/governor/policy/permission) — dù fail giữa chừng vẫn ghi "denied at policy" kèm lý do.

### C1-04 (P3) — ToolGuard post-check cần nói rõ
→ **Resolve**: post-check = verify output.ok + (nếu proposal là write) artifact/result tồn tại; guard raise SafetyError nếu post-check fail (side effect bất hợp lệ).

## Kết luận
Resolve vào spec v2.
