# TASK-080 — Test (M11-P2/P2b: R1 VisualEvidence + R10 UIState)

> Ngày: 2026-08-16 | Nhánh: feature/ISSUE-4-m11-deterministic-runtime

## Unit tests

| Suite | Kết quả | Ghi chú |
|-------|---------|---------|
| `tests/test_visual.py` (16 tests) | ✅ **16/16 PASS** | AC1–AC9 + JSON roundtrip |
| `test_architecture.py::test_inv_observability_import_allowlist` | ✅ PASS | +`threading` allow-list (visual.py) |

## CLI thật

| Lệnh | Kết quả | AC |
|------|---------|-----|
| `aiagent visual-probe --dump-ref/--dump-current` | Tạo 2 evidence JSON | — |
| `aiagent visual-probe --ref --current` | Phát hiện **state_diff `entities.player.scale: 3→2`** (đúng bug "cat biến mất" proposal) → fail (reasoning R10); metrics `probe_count=1, violations=1` | AC9 ✓ |
| `aiagent visual-probe --missing-ref` | **missing_evidence (inconclusive) — KHÔNG PASS** (INV-035), exit=1 | AC6 ✓ (CLI) |

## Full suite

- [x] **2003 passed / 0 failed** (sau +threading fix) — baseline 1987 + 16 mới; không regression (AC10)
  (ghi chú: 1 fail đầu tiên là allow-list `threading` — đã fix)

## Ghi chú implement

- `pixel_diff`: -1 = thiếu ref · 0 = giống · >0 = % khác (không mơ hồ)
- Probe phát hiện state diff bằng reasoning (R10) — đúng mục đích "AIOS biết tại sao"
- Metrics: counters + gauge in-memory, idempotent singleton (không sửa RuntimeKernel)
