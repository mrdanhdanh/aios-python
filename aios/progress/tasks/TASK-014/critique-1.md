# Critique vòng 1 — TASK-014 (M2-P4: Tools 6 loại + Tool Registry + capability binding)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 1) | Spec: `spec.md`

## Đánh giá chung

**3.5/5 — chất lượng cao, chưa sẵn sàng implement ngay.** Spec đọc kỹ mã nguồn thực (bind_tool idempotent ✅, EventType tool.started/finished ✅, PermissionScope 8 giá trị ✅, allow-list pattern TASK-013 ✅). 1 P1 (AC3 no-exec assertion ngược — an toàn giả) + 7 P2 + P3.

## Vấn đề (17) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C1-01 | P1 | AC3 no-exec assertion NGƯỢC: "marker KHÔNG tồn tại" = ĐÃ exec → test pass khi tool chạy code (an toàn giả) | Sửa: tạo marker trước → chạy → **marker VẪN tồn tại** (không bị xóa) → chứng minh không exec; assert `marker.exists() is True` |
| C1-02 | P2 | Gate raise → exception propagate, phá contract "run luôn trả ToolOutput" + fail-closed | Bọc gate call trong try/except Exception → `ToolOutput(ok=False, error="permission denied: ... (gate error)")`, không emit event; thêm case AC9 "gate raise → ok=False + không emit" |
| C1-03 | P2 | `_run(self, input)` không nhận context — M4 thật cần context → phải sửa contract sau | **`_run(self, input: ToolInput, context: ToolContext) -> ToolOutput`** — stub bỏ qua context nhưng signature ổn định |
| C1-04 | P2 | Allow-list chỉ check top-level → `urllib.request` (network) lọt | Test scan thêm module con: mọi import `urllib.*` phải == `urllib.parse` (hoặc check raw source không chứa urllib.request/error/robotparser) |
| C1-05 | P2 | Arguments thiếu/sai kiểu → KeyError/TypeError/AttributeError bị bọc message khó hiểu | Mỗi stub `_run` validate arguments: thiếu key/không phải str → `ToolOutput(ok=False, error="invalid argument: code (expected str)")` (ValueError convention) |
| C1-06 | P2 | `required_scopes=()` carve-out mâu thuẫn invariant "side effect ↔ gate" | **Cấm scope rỗng**: `Tool.__init__` raise ValueError nếu required_scopes rỗng (6 tool đều có scope); invariant tuyệt đối |
| C1-07 | P2 | 4 tool (docker/rest/mcp/git) không có bằng chứng no-syscall | Thêm **global no-syscall test**: monkeypatch socket.socket/subprocess.run/Popen/os.system/urllib.request.urlopen → raise AssertionError; chạy 6 tool → vẫn ok |
| C1-08 | P2 | python→filesystem thiếu căn cứ + PermissionService default filesystem=ALLOW → auto-allow exec khi wire M4 | Ghi rõ: P4 real exec phải renegotiate scope (sandbox quyết định); cảnh báo caller không map python→filesystem theo default ALLOW |
| C1-10 | P2 | McpTool "validate dict hợp lệ" chưa định nghĩa | Chốt: `dict[str, list[str]]`, key không rỗng, method str không rỗng, cho phép dict rỗng |
| C1-11 | P2 | `bind_capabilities` return semantics lần 2 chưa chốt | Ghi rõ: trả `int` = số cặp ĐÃ xử lý (luôn = tổng capabilities khai báo, kể cả lần 2); test lần 2 pin kết quả |
| C1-12 | P2 | usage/duration_s khi deny/mismatch chưa chốt | Chốt: deny/mismatch/error → `usage={}` + `duration_s=0.0` (cố ý); success → stub usage + duration ≥ 0 |
| C1-13 | P3 | finished event thiếu capabilities (started có) | Thêm `capabilities` vào payload finished (trace cho M4) |
| C1-14 | P3 | Tool instance shared trong registry — thread-safety chưa khai báo | Contract: `Tool._run` KHÔNG mutate instance state (stateless); test 2 thread chạy cùng PythonTool → kết quả khớp |
| C1-15 | P3 | Gate check trước tool_id check → deny che mismatch | Đổi thứ tự: validate tool_id trước, rồi gate (mismatch không bị che) |
| C1-16 | P3 | Out-of-scope thiếu "KHÔNG nối PermissionService/PermissionBroker thật" | Thêm vào Out: không nối gate với PermissionService/PermissionBroker thật (v1 stub gate độc lập) |
| C1-17 | P3 | AC11 "nhất quán" mơ hồ | Định nghĩa cụ thể: register xong → get/list thấy ngay; count đúng; không exception; không mất update |

## Kết luận

- [x] **Cần sửa trước khi implement** — 1 P1 + 7 P2 + P3 (resolve cùng đợt).
- **Trạng thái: RESOLVED 17/17** (spec.md đã cập nhật).
