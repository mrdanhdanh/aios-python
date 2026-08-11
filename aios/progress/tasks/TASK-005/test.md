# Test — TASK-005

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Kết quả | **207 passed** (45 mới) |
| Coverage | **95.32%** (ngưỡng 80%) |
| Git sạch sau test | ✅ |

Test file mới: test_scheduler (10), test_state (8), test_resource (7), test_execution (15), test_runtime_kernel (5).

## Lỗi phát hiện khi implement + fix (5)
1. **`from __future__ import annotations` → string annotations → Container không resolve** — fix: `get_type_hints` trong `_instantiate` (container.py)
2. **Runner exception trong timeout-thread bị nuốt → trả None (success sai)** — fix: box capture error + re-raise
3. **Cancel trước execute phải đăng ký flag** — fix: cancel() tạo flag set nếu chưa có
4. **`_safe_deepcopy` fallback repr cả dict → string** — fix: deepcopy per-value (dict/list/tuple/leaf)
5. **ExecutionService.__init__ thiếu type hints** — fix: thêm annotations (DI bắt buộc)

## Đối chiếu AC (15 AC)
**15/15 PASS** — chi tiết: AC1 scheduler (7 case), AC2 state (deepcopy + fallback), AC3 resource (clamp), AC4 topo, AC5 retry + fail-fast, AC6 timeout retryable + 0, AC7 cancel (event + trước execute), AC8 resume + mismatch, AC9 policy (deny/approval/sandbox), AC10 release baseline, AC11 events, AC12 kernel resolve 10 interfaces + e2e, AC13 imports, AC14 git sạch, AC15 resources settings + reason non-empty.

## Kết luận
- [x] **TẤT CẢ PASS (15/15 AC)** — sẵn sàng đánh giá cuối.
