# TASK-058 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Sandbox execute thế nào (INV-033: "qua Sandbox")?
→ **Resolve**: `sandbox_fn: Callable[[dict], Any]` injectable (tên rõ ràng — sandbox); execute qua sandbox_fn KHÔNG chạy trực tiếp. Mặc định noop (trả params) — test truyền fake.

## C2-02 (P2) — Evidence format?
→ **Resolve**: evidence = dict từ evaluate_fn — bắt buộc có key "metric_value" hoặc "result"; rỗng/thiếu → INCONCLUSIVE (C1-05).

## C2-03 (P3) — Nhận hypothesis + params riêng?
→ **Resolve**: `run(hypothesis, params)` — params dict (VD {"retry": 5}); experiment row lưu cả hai.

## Kết luận
Resolve xong — spec đủ chặt.
