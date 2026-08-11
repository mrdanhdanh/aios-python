# Critique vòng 2 — TASK-005

## Đánh giá chung
3 P1 + 10 P2 + 8/9 P3 vòng 1 áp đúng. Nhưng 1 P1 mới (runner contract không định nghĩa) + 3 P2 (ResourcesSettings wiring, ContextService không DI-safe, stale cancel flag) + 10 P3. **Sẵn sàng: 3.5/5 — sửa trước khi implement.**

## Vấn đề + Resolution

### P1 — Runner interface không định nghĩa
- **Resolution**: pin runner contract: `runner: dict[str, Callable[[PlanNode, dict[str, Any]], Any]]` — map node_id → `fn(node, results_so_far)` (results_so_far = {node_id: result} các node completed); kết quả node = giá trị trả về → lưu node_results; runner raise → node failed; **runner không có entry → node failed reason "no runner for node X" (không crash toàn bộ)**; runner gọi đúng 1 lần mỗi attempt (retry/timeout/resume cùng path). AC12 dùng fake runner dict 1–2 node.

### P2-A — ResourcesSettings không wiring qua register
- **Resolution**: RuntimeKernel.create dùng `register_instance(ResourcesSettings, ResourcesSettings(max_tokens=..., max_concurrent=...))` từ settings.resources; ctor ResourceService nhận `limits: ResourcesSettings` (type đơn, DI-safe).

### P2-B — ContextService không DI-safe (clock Callable → ContainerError ngầm; container.start() nuốt lỗi)
- **Resolution**: RuntimeKernel.create dùng `register_instance(ContextService, ContextService())`; AC12 bổ sung: resolve lần lượt CẢ 9 interface không raise (không chỉ has).

### P2-C — Re-execute cùng plan.id: stale cancel flag + state cũ
- **Resolution**: `execution_id = plan.id` (v1); `execute()` **reset toàn bộ state + cancel flag** cho execution_id trước khi chạy; `cancel(execution_id không tồn tại)` → no-op; cancel trước execute → CANCELLED ngay.

### P3 — (áp vào spec)
- A: contract change — thêm case `timeout_s: 0.5` float + giữ negative test (test cũ int vẫn pass)
- B: AC6 timing ghi rõ: sleep 0.2s + timeout 0.1s + retries=1 → ~0.2-0.3s; test timeout_s=0 dùng runner nhanh
- C: reason paths: deny → decision.reason + policy_version; resource fail → "resource unavailable"
- D: workflow events payload tối thiểu: `execution_id`, `plan_id`, `reason` (khi có)
- E: emit qua **EventService.emit** (có audit) — RuntimeKernel wiring
- F: cancel trước execute → CANCELLED ngay không chạy node
- G: AC1 interval test assert ≥ N lần + margin rộng (interval 0.02-0.05s, cửa sổ 0.3-0.5s) tránh flaky
- H: AC12 BẮT BUỘC dùng Settings với tmp_path paths (tránh tạo aios/data trong repo)
- I: AC12 plan end-to-end dùng required_permissions=["filesystem"] (default policy allow) hoặc Policy riêng
- J: cập nhật `__all__` kernel/__init__ + services/__init__ (4 service + RuntimeKernel + WORKFLOW_CANCELLED)

## Kết luận
- [x] **Resolve toàn bộ (1 P1 + 3 P2 + 10 P3)** — cập nhật spec, sẵn sàng tasks.md + review.
