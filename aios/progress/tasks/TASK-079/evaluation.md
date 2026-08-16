# TASK-079 — Evaluation (M11-P1: R3 RenderReplay / DeterministicHarness)

> Ngày: 2026-08-16 | Task: TASK-079 | Milestone: M11-P1 (Issue #4)

## Đối chiếu tiêu chí chấp nhận

| AC | Mô tả | Kết quả | Bằng chứng |
|----|-------|---------|------------|
| AC1 | InputEvent + RenderFrame contract (extra=forbid) | ✅ | `test_input_event_contract` + `test_render_frame_contract` |
| AC2 | RenderTimeline record + timestamp tăng | ✅ | `test_timeline_record_order` + `test_timeline_rejects_decreasing_timestamp` |
| AC3 | Replay cùng seed → cùng hash | ✅ | `test_replay_same_seed_same_hash` |
| AC4 | Đổi seed/input → hash khác | ✅ | 2 tests (seed + input) |
| AC5 | SeededPrng deterministic + vector | ✅ | 3 tests (deterministic, KNOWN_VECTOR, next_int) |
| AC6 | Harness stable/unstable | ✅ | 2 tests |
| AC7 | render_fn raise → BLOCKED (INV-035) | ✅ | 2 tests (raise + wrong buffer size) |
| AC8 | AssetIdempotencyClassifier fail-closed | ✅ | 2 tests |
| AC9 | CLI render-replay thật | ✅ | stable=True, exit=0 |
| AC10 | Full suite xanh | ✅ | **1987 passed / 0 failed** |

**10/10 AC — TASK-079 DONE** ✅

## Đánh giá hệ thống (sau P1)

- **Nền tảng deterministic visual đã có**: render = pure function (state, time, seed) +
  pixel_hash SHA256 → AIOS giờ có thể "replay đúng ảnh" — đúng định nghĩa M11-P1.
- **Fail-closed xuyên suốt**: harness dùng VerificationOutcome (INV-035) — render không chạy
  → BLOCKED, không bao giờ PASS. Đây là khác biệt cốt lõi so với "17/17 PASS nhưng bị skip".
- **Freeze policy 3 mức** (none/fixed/paused) phủ đúng tình huống thực tế proposal §1b
  (đóng băng thời gian render, particles PRNG seeded).
- **AssetIdempotencyClassifier** tái dùng pattern M10 (fail-closed) — sẵn sàng cho P3/R9
  (AssetPipeline Contract).

## Bài học

1. **Test vector cho PRNG phải lấy từ implementation đã verify** — vector tự bịa dẫn tới
   fix sai hướng; sau khi sửa đúng chuẩn mulberry32, vector thật mới có ý nghĩa.
2. **Timing trong test deterministic cần tính toán kỹ** — frame rate × số frame quyết định
   event nào được áp dụng; dùng num_frames đủ dài.
3. **RenderFn pure phải thực sự pure** — mock render phải dùng đủ (state, time, seed),
   nếu không test "input thay đổi → pixel khác" không bao giờ phát hiện được.

## Đề xuất (ghi nhận)

1. P2/R1 sẽ dùng DeterministicHarness làm engine cho VisualRegressionProbe (screenshot thật qua driver)
2. P2b/R10 UIState Contract sẽ cung cấp state_hash chuẩn (không phải hash nội bộ timeline)
3. Journal/replay persist cho visual — P2/R1 (VisualEvidence artifact)

## Checklist đóng

- [x] spec + critique-1 (resolved) + critique-2 (resolved) + tasks + review (APPROVED)
- [x] implementation/ (rendering/ package + CLI + 18 tests)
- [x] test.md + evaluation.md
- [x] LOG.md + PROGRESS.md + commit
