# TASK-075 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P2) — Model cost estimate cần nguồn tokens rõ
→ **Resolve**: CostEstimator nhận `token_estimates: list[(model_id, tokens_in, tokens_out)]` injectable; mặc định rỗng → cost 0. Test inject [(mock, 1000, 500)] với capability input_cost=1.0/output_cost=2.0 (per 1M) → cost = 1000/1M*1.0 + 500/1M*2.0 = 0.001 + 0.001 = 0.002.

### C2-02 (P3) — Performance CLI gom 1 lệnh hay 2?
→ **Resolve**: 2 lệnh riêng (`cost`, `performance`) đúng PLAN; cả 2 không crash DB rỗng.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
