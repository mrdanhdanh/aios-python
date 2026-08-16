# TASK-079 — Test (M11-P1: R3 RenderReplay / DeterministicHarness)

> Ngày: 2026-08-16 | Nhánh: feature/ISSUE-4-m11-deterministic-runtime

## Unit tests

| Suite | Kết quả | Ghi chú |
|-------|---------|---------|
| `tests/test_rendering.py` (18 tests) | ✅ **18/18 PASS** | AC1–AC8 + arch allow-list |

## CLI thật

| Lệnh | Kết quả | AC |
|------|---------|-----|
| `aiagent render-replay --seed 42 --frames 60 --show-hashes` | `stable: True`, outcome `pass`, exit=0 | AC9 ✓ |

## Full suite

- [x] **1987 passed / 0 failed** (60s) — baseline 1969 + 18 mới; không regression (AC10)

## Bugs phát hiện & fix trong quá trình implement

1. `_mulberry32_next` sai chuẩn JS reference (XOR với t mới thay vì t cũ) — test vector bắt được; fix + cập nhật KNOWN_VECTOR giá trị thật
2. Test timing sai: event 500/600ms không áp dụng trong 20 frames @60fps (0.33s) — tăng num_frames để đủ thời gian
3. Mock render không dùng `state_hash` nên input thay đổi không ảnh hưởng pixel — fix mock (pure function đầy đủ: state, time, seed)
