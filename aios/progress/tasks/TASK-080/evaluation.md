# TASK-080 — Evaluation (M11-P2/P2b: R1 VisualEvidence + R10 UIState)

> Ngày: 2026-08-16 | Task: TASK-080 | Milestone: M11-P2+P2b (Issue #4)

## Đối chiếu tiêu chí chấp nhận

| AC | Mô tả | Kết quả | Bằng chứng |
|----|-------|---------|------------|
| AC1 | UIState canonical + state_hash deterministic | ✅ | 2 tests |
| AC2 | UIState extra=forbid + validate | ✅ | 2 tests |
| AC3 | VisualEvidence đủ trường | ✅ | 2 tests (fields + required render_state) |
| AC4 | Probe giống → PASS | ✅ | `test_probe_identical_evidence_passes` |
| AC5 | Probe state khác → phát hiện (reasoning R10) | ✅ | `test_probe_detects_state_diff` (scale 3→2) |
| AC6 | Thiếu ref → MISSING_EVIDENCE → không PASS | ✅ | 3 tests (None/không data URI/cả 2 thiếu) |
| AC7 | Pixel diff > 0 → FAIL kèm evidence | ✅ | 2 tests (diff + corrupt base64 → MISSING) |
| AC8 | Observability metrics | ✅ | 2 tests (registry + singleton) |
| AC9 | CLI visual-probe thật | ✅ | dump + compare phát hiện scale bug + missing-ref → exit 1 |
| AC10 | Full suite xanh | ✅ | **2003 passed / 0 failed** |

**10/10 AC — TASK-080 DONE** ✅

## Đánh giá hệ thống (sau P2)

- **Chống false-positive hoàn tất ở tầng visual**: VisualRegressionProbe thiếu ref →
  MISSING_EVIDENCE → KHÔNG PASS. Kịch bản "17/17 PASS nhưng toHaveScreenshot bị skip"
  (proposal §1) giờ bị chặn bởi state model INV-035.
- **R10 hoạt động đúng mục đích**: probe phát hiện `entities.player.scale: 3→2` bằng
  **reasoning** (state diff), không cần pixel compare — đây chính là bug "cat biến mất
  sau START" trong proposal; AIOS giờ biết "tại sao".
- **Pixel diff là evidence, không phải SLO**: gauge `visual_pixel_diff_max` chỉ quan sát;
  đúng tinh thần "metric sau evidence".
- **Observability mở rộng**: visual metrics đăng ký qua singleton idempotent — không chạm
  RuntimeKernel (giữ INV nguyên vẹn).

## Bài học

1. **UI State Contract là chìa khóa reasoning** — cùng bug scale, backend test 27/27 vẫn xanh
   nhưng UIState diff bắt được ngay; đây là lợi ích cốt lõi R10.
2. **Evidence phải self-contained** (base64 data URI) — chạy được trong CI, không phụ thuộc file.
3. **Allow-list arch test bắt được mọi import mới** — thêm module vào observability/ phải
   update allow-list (threading) — quy trình chuẩn M5–M9.

## Đề xuất (ghi nhận)

1. P3/R9 sẽ thêm UIState version vào Contract 1.0 (AssetPipeline contract)
2. Pixel-diff metric thành SLO chỉ sau khi có đủ dữ liệu thực tế (proposal: chưa sớm)
3. VisualEvidence artifact persist → P3/R4 (Asset Capability Registry) dùng làm golden-master

## Checklist đóng

- [x] spec + critique-1 (resolved) + critique-2 (resolved) + tasks + review (APPROVED)
- [x] implementation/ (ui_state/evidence/probe + observability/visual.py + CLI + 16 tests)
- [x] test.md + evaluation.md
- [x] LOG.md + PROGRESS.md + commit
