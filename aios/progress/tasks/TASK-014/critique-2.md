# Critique vòng 2 — TASK-014 (M2-P4: Tools)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 2) | Spec: `spec.md` (đã sửa 17/17 v1)

## Đánh giá chung

**4/5 — chất lượng cao, 17/17 vòng 1 sửa đúng hướng (verify code nền: bind_tool idempotent ✅, TOOLS_DIR có sẵn ✅, EventType/PermissionScope khớp ✅).** Nhưng 1 P1 mới do chính quá trình sửa C1-03/C1-15 tạo ra (bước 4 gọi `_run(input)` thiếu context) + 4 P2 (thiếu test plan cho C1-07/C1-14, C1-05 chỉ phủ PythonTool, sequence đánh số lặp).

## Mục A — Verify 17 resolutions v1

12/17 đúng hoàn toàn; 5 đúng ý nhưng tạo vấn đề mới hoặc thiếu test plan (C1-03 → C2-01, C1-05 → C2-05, C1-07 → C2-03, C1-14 → C2-04, C1-15 → C2-02); 0 sai hoàn toàn.

## Mục B — Vấn đề mới (10) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C2-01 | P1 | Bước 4 template gọi `self._run(input)` thiếu context — mâu thuẫn C1-03 → TypeError mọi success path | Sửa thành `self._run(input, context)`; AC2 thêm dòng "success path gọi _run(input, context)" |
| C2-02 | P2 | Sequence đánh số lặp "2" + validate tool_id trùng 2 lần 2 format | Xóa bước trùng; giữ 1 bước duy nhất format `"expected {self.id}, got {input.tool_id}"` trước gate; đánh số lại 1–6 |
| C2-03 | P2 | Global no-syscall test (C1-07) không có trong test plan mục 8 | Thêm `test_no_syscall_all_tools` vào `test_tool_stubs.py` (monkeypatch socket/subprocess/Popen/os.system/urlopen → AssertionError; 6 tool × input hợp lệ → ok=True) |
| C2-04 | P2 | Tool-instance concurrency test (C1-14) không có trong test plan | Thêm `test_tool_concurrent_runs_same_instance` (2 thread × N run cùng instance + input → cùng result; prefix riêng — STATS #23) |
| C2-05 | P2 | C1-05 chỉ phủ PythonTool; 5 tool còn lại không có quy ước "invalid argument" | Mở rộng: MỌI tool validate thiếu key/sai kiểu → `ok=False, error="invalid argument: <key> (expected str)"`; test tham số hóa mỗi tool 1 case |
| C2-06 | P3 | `bind_capabilities` partial state khi raise giữa chừng chưa định nghĩa | Ghi contract "không rollback — caller tự xử lý (fail-fast đủ v1)" |
| C2-07 | P3 | `time.perf_counter` vs `time.monotonic` — 2 chỗ 2 hàm | Chốt `time.perf_counter`; error path → duration_s=0.0 cố ý; bỏ chữ monotonic khỏi C1-12 note |
| C2-08 | P3 | McpTool method list rỗng cho 1 server chưa chốt | Chốt: cho phép list rỗng (server tồn tại nhưng mọi call "unknown method") — ghi 1 dòng |
| C2-09 | P3 | Không có cách tắt constructor sink qua context | Ghi contract: "context sink None → dùng constructor sink (không có cơ chế tắt per-run v1)" |
| C2-10 | P3 | Constructor signature 6 tool chưa thống nhất | Chốt chung: `__init__(self, event_sink=None, available=True, metadata=None, **tool_specific)` áp dụng cả 6 |

## Mục C: Bảng INV ↔ test plan

Nhất quán — mọi invariant có enforcement trong test plan (INV-001/002/004/005/006/007 đều phủ bởi allow-list + AC9 gate).

## Kết luận

- [x] **Cần sửa trước khi implement** — C2-01 (P1) + C2-02..05 (P2) + P3 cùng đợt.
- **Trạng thái: RESOLVED 10/10** (spec.md đã cập nhật).
