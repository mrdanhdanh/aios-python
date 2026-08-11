# Review — TASK-004 (Pre-Implementation)

## Tổng quan
2 vòng critique resolve triệt để, 13/13 AC phủ checklist. **Không R1** — 5 R2 vá nhẹ spec (không đổi kiến trúc/AC).

## Vấn đề + Resolution

- **R2-1** (mâu thuẫn pending lifecycle): bỏ cụm "đăng ký pending (dù có callback)" sót trong Phạm vi — thống nhất "pending CHỈ cho ASK".
- **R2-2** (fake clock trap): **chọn bỏ `init=False`** — service tạo `Context(..., _created_mono=self.clock())` → mọi fake clock hoạt động; AC1 test dùng fake clock đếm tăng.
- **R2-3** (sandbox_required chưa có rule): **defer** giống max_concurrent — PolicyService chở giá trị, TASK-005 Execution enforce; ghi rõ.
- **R2-4** (default Policy): `allow_scopes=[filesystem]`, `deny_scopes=[]`, `require_approval=False`, `sandbox_required=False`, `allow_internet=False`, `max_tokens=None`, `version="0.1.0"`.
- **R2-5** (on_ask trả ALLOW/DENY): callback trả ALLOW/DENY → xóa pending + emit GRANTED/DENIED ngay; trả ASK → giữ pending + emit PERMISSION_REQUESTED; không double emit.

### R3 (xử lý trong implement, ghi LOG)
1. `ttl_s=None` → không hết hạn
2. `list()` dùng rglob; base_dir chưa tồn tại → trả []
3. `store()` mutate in-place contract caller + trả contract đã cập nhật
4. PolicyService payload PERMISSION_REQUESTED tự sinh request_id (uuid)
5. tasks.md thêm E0 Review cho task sau (ghi chú)
6. `query_audit` tái dựng EventType lạ → log warning + skip

## Kết luận
- [x] **Resolve toàn bộ (5 R2 + 6 R3)** — spec vá xong, sẵn sàng implement.
