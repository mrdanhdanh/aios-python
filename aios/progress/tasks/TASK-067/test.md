# TASK-067 — Test + Evaluation (Autonomy Safety 1.0)

## Test — `tests/test_autonomy_safety.py` **15/15 pass**
- Risk bảng deterministic (AC2) + target nhạy cảm +1
- Chain đủ thứ tự Risk→Governor→Policy→Permission; gate fail dừng ngay (AC1)
- Risk critical → STOP; high → ASK_HUMAN; critical + approval → đi tiếp (AC4/AC5)
- Policy ask → ASK_HUMAN không tự ALLOW (AC5)
- ToolGuard: deny → tool._run KHÔNG gọi (đếm = 0) (AC6); hợp lệ pass (AC7); post-check write fail (AC6); emergency hook (TASK-068 hợp nhất)
- Evidence đủ 4 gate kể cả deny sớm (R2)

## Full suite: **1891 passed** (AC8).

## Evaluation — 9/9 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 chain + dừng ngay | ✅ |
| AC2 risk bảng | ✅ |
| AC3 decision + evidence | ✅ |
| AC4 STOP | ✅ |
| AC5 ASK_HUMAN | ✅ |
| AC6 ToolGuard pre/post + đếm | ✅ |
| AC7 tool hợp lệ | ✅ |
| AC8 regression | ✅ |
| AC9 DoD | ✅ |

## Bài học
1. Chain enforce phải injectable (không import governor/policy) — giữ INV-030, dễ test.
2. "Chặn trước khi chạy" phải đo bằng counter trong tool._run, không chỉ assert decision.
3. Risk HIGH (deploy/network) không được tự ALLOW — ASK_HUMAN là mặc định an toàn.
