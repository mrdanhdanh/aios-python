# Test — TASK-004

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Lệnh chạy | `backend/.venv/Scripts/python -m pytest` |
| Kết quả | **162 passed** (55 mới) |
| Coverage | **94.77%** (ngưỡng 80%) |
| Git sạch sau test (AC11) | ✅ — chỉ file dự kiến trong git status |

Test file mới: test_context (10), test_events (7), test_artifacts (16), test_permissions (12), test_policy (10) + test_config +2, test_import +1.

## Lỗi phát hiện khi implement + fix
1. Import path sai `..logging` → `...logging` trong services/events.py
2. Gọi `EventBus.publish` sai signature (payload/source trực tiếp) → phải tạo `Event` object — fix 3 service (artifacts/permissions/policy)

## Đối chiếu AC (13 AC)
**13/13 PASS** — AC1 Context (fake clock), AC2-3 EventService audit, AC4-6 Artifact (sidecar, mkdir, path guard 4 case), AC7 Permission defaults, AC8 Policy 6 case, AC9 semver, AC10 imports, AC11 git sạch, AC12 Settings keys, AC13 pending lifecycle + on_ask fallback.

## Kết luận
- [x] **TẤT CẢ PASS (13/13 AC)** — sẵn sàng đánh giá cuối.
