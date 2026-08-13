# Review — TASK-014 (M2-P4: Tools 6 loại + Tool Registry)

> Ngày: 2026-08-13 | Reviewer: reviewer agent | Giai đoạn: REVIEW TRƯỚC KHI IMPLEMENT
> Spec đã qua critique ×2 (27 vấn đề resolved). Reviewer verify code nền 8/8 điểm chính xác (bind_tool(cap, tool_id) đúng thứ tự + idempotent; make_component_metadata keyword-only; EventType/PermissionScope khớp; __init__.py line 5).

## Kết luận

- [x] **APPROVED — đủ điều kiện implement** (không blocking)

## 3 lưu ý Major khi implement (đã áp dụng)

**R1 — duration_s error path**: template bước 4 ghi `perf_counter() - t0` nhưng C1-12/C2-07 chốt error path → `duration_s=0.0` cố ý. Implement theo C1-12 (success đo thật; deny/mismatch/_run raise → 0.0) + comment code.

**R2 — Gate-raise test**: §8 thiếu tên test gate RAISE → bổ sung `test_permission_gate_raises_fail_closed` (gate lambda raise → ok=False + "(gate error)" + không emit event). tasks.md T3.1 đã ghi.

**R3 — urllib check bằng AST**: `collect_imports` nén external về top-level ("urllib.request" → {"urllib"}) → external check không bắt. C1-04 check thêm PHẢI dùng AST walk (mọi Import node module bắt đầu "urllib" phải == "urllib.parse"; `import urllib` trần cũng tính vi phạm) — tránh false positive substring.

## Ghi chú implement khác

- R4: output tạo TRƯỚC khi emit finished (finished payload lấy ok từ output) — thứ tự: bọc _run → tạo ToolOutput → emit finished → return
- R5: bind_capabilities — collect pairs trong lock, gọi bind_tool ngoài lock (sạch hơn)
- R6: AC12 swap test — tạo tool thứ 7 (clone PythonTool id khác, capabilities=("execute_code",)) register + bind → tools_for cập nhật
- AC14 coverage: chạy riêng `--cov=aios_core.tools` cho module (config chỉ fail-under=80 toàn package)
