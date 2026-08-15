# TASK-058 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Compare "≥ target" với hướng nào?
Metric có thể improvement = tăng (quality) hoặc giảm (cost/latency). So sánh một chiều là sai.
→ **Resolve**: Hypothesis có `direction: "higher" | "lower"` — ACCEPTED nếu direction=higher và value ≥ target; direction=lower và value ≤ target. Mặc định higher.

## C1-02 (P2) — evaluate_fn mặc định REJECTED vì thiếu evidence — có quá khắc?
Nếu không wire harness, mọi experiment reject → không test được accept path.
→ **Resolve**: evaluate_fn injectable BẮT BUỘC qua constructor (không default reject); test truyền fake. Nhưng arch test INV-033 đảm bảo source chứa literal harness/evaluation API — experiment phải GỌI evaluate_fn (evidence-first) và verdict chỉ từ evidence. Constructor yêu cầu evaluate_fn (required param) — fail-fast nếu quên wire.

## C1-03 (P2) — deploy() làm gì cụ thể?
→ **Resolve**: deploy() = đánh dấu `deployed=True` + `canary=True` trên Experiment row (persist); KHÔNG tự sửa production. Chỉ khi verdict=ACCEPTED. Human/operator thực thi thật.

## C1-04 (P3) — Persist lịch sử ở đâu?
→ **Resolve**: SQLite `autonomous_experiments` (autonomous.db chung) — id, hypothesis_json, params_json, result, verdict, evidence_json, deployed, at.

## C1-05 (P3) — INCONCLUSIVE khi nào?
→ **Resolve**: value không so sánh được (None) hoặc evidence rỗng → INCONCLUSIVE (không ACCEPT/REJECT bừa).

## Kết luận
Resolve xong. Vòng 2 kiểm tra.
