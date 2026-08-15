# TASK-053 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Verify → Learn: verdict thế nào thì "học"?
Loop phải biết pass/fail để quyết định vòng sau. Thiếu contract cho verifier output.
→ **Resolve**: verifier trả `VerificationResult(success: bool, evidence: dict, score: float)`; learner nhận result này; loop dừng khi success=True (hoặc goal complete theo AC9).

## C1-02 (P2) — Policy deny: dừng hẳn hay hỏi human?
Spec AC3 nói "dừng + ghi ASK_HUMAN/STOP" — mơ hồ 2 lựa chọn.
→ **Resolve**: policy deny → governor trả ASK_HUMAN (nếu action risk=approval) hoặc STOP (nếu deny cứng). Loop chỉ dừng khi decision ∈ {STOP, ASK_HUMAN} — ASK_HUMAN dừng loop chờ human (v1: loop trả về với final_state="awaiting_human").

## C1-03 (P2) — Act có qua capability/tool không?
Loop.act injectable — spec không nói act làm gì.
→ **Resolve**: act = callable nhận (plan_step, context) → kết quả; M9 v1 không chạm Tool trực tiếp (INV-002 — autonomous/ không import tools/); act thật sẽ qua Orchestrator (wiring sau). Ghi rõ trong spec.

## C1-04 (P3) — Event payload loop_step
→ **Resolve**: {goal_id, iteration, decision, step_id} — đủ để dashboard theo dõi.

## C1-05 (P3) — LoopResult.final_state là gì?
→ **Resolve**: enum `LoopFinalState`: COMPLETED / STOPPED / AWAITING_HUMAN / ERROR / BUDGET_EXCEEDED.

## Kết luận
P1-P2 resolve; P3 ghi rõ. Vòng 2 kiểm tra.
