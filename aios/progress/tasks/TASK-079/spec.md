# TASK-079 — M11-P1: R3 RenderReplay / DeterministicHarness (Foundation)

> **Milestone**: M11-P1 (Issue #4) — Deterministic Visual Runtime
> **Ngày**: 2026-08-16 | **Owner**: AIOS Orchestrator
> **Tham chiếu**: proposal M11 §R3 + §7 (M11-P1), PLAN.md §M11, INV-035 (TASK-078)

## 1. Mục tiêu

Đóng gap "Durable Execution 1.0 chỉ cho backend workflow": xây nền tảng **deterministic visual runtime** —
`RenderReplay` (record input timeline + seed → replay → assert pixel-stable) + `DeterministicHarness`
(chạy render là pure function của (state, time, seed)). Đây là FOUNDATION cho R1 (P2): không có
deterministic replay thì VisualRegressionProbe chỉ so ảnh mà không biết "tại sao" khác.

```
M11-P1: render = pure function (state, time, seed) — AIOS có thể replay đúng ảnh
```

## 2. Phạm vi (IN)

1. **Package `backend/src/aios_core/rendering/`** (mới):
   - `InputEvent` — (type, timestamp, payload) — một sự kiện input trong timeline
   - `RenderFrame` — (frame_index, t, seed, state_hash, pixel_hash)
   - `RenderTimeline` — record ordered input events
   - `RenderReplay` — record → replay(render_fn, seed) → frames; cùng seed+timeline → cùng hash
   - `SeededPrng` (mulberry32, tự implement) — deterministic PRNG: cùng seed → cùng chuỗi
   - `DeterministicHarness` — config (seed, fps, max_frames, freeze_policy, width, height),
     run render_fn 2 lần cùng seed → so sánh pixel_hash → `RenderReplayResult` (stable,
     diff_frames, `outcome: VerificationOutcome` theo INV-035)
   - **RenderFn contract**: `Callable[[RenderFrame], bytes]` — bytes = **raw pixel buffer**
     (W×H×3 RGB, không nén); pixel_hash = SHA256(buffer); render_fn KHÔNG được đọc ngoài
     frame (pure function of state, time, seed)
   - **freeze_policy**: `"none"` (time thật) | `"fixed"` (t = theo timeline) | `"paused"`
     (t = 0 sau frame đầu); harness sinh frame.t theo policy
   - `RenderReplayResult` (pydantic): `frames_a`, `frames_b`, `stable: bool`,
     `diff_frames: list[int]`, `outcome` — harness KHÔNG raise khi unstable
2. **Asset idempotency** (mượn M10 durability): `AssetIdempotencyClassifier` — exactly-once
   (= idempotent write, retry OK) / at-least-once (= read-like, retry OK) / at-most-once
   (= non-idempotent, approve/compensate); fail-closed: không khai báo → at-most-once
3. **Tích hợp Verification Kernel** (TASK-078): kết quả replay → `VerificationOutcome`
   (state PASS/FAIL/BLOCKED; không chạy → NOT_EXECUTED, KHÔNG PASS — INV-035)
4. **CLI `aiagent render-replay`** — demo chạy thật với mock render_fn (sinh pixel theo state+seed)
   → replay 2 lần → assert stable

## 3. OUT of scope

- R1 VisualEvidence / VisualRegressionProbe (P2 — TASK-080)
- R10 UI State Contract (P2b — TASK-080)
- Screenshot thật (browser/Phaser) — render_fn là injectable, test dùng mock
- Sửa game/webgame code

## 4. Input / Output

- **Input**: render_fn injectable (user cung cấp — contract: `(frame: RenderFrame) -> bytes`),
  seed, timeline input events
- **Output**: package `rendering/` + CLI + tests + idempotency classifier

## 5. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm tra |
|---|----|---------------|
| AC1 | `InputEvent` + `RenderFrame` contract (pydantic extra=forbid, field hợp lệ) | unit test |
| AC2 | `RenderTimeline` record đúng thứ tự + timestamp tăng dần | unit test |
| AC3 | `RenderReplay.replay()`: cùng seed + cùng timeline + cùng render_fn → frames có pixel_hash giống hệt | unit test |
| AC4 | Đổi seed hoặc thêm input → pixel_hash khác (detect được) | unit test |
| AC5 | `SeededPrng` (mulberry32): cùng seed → cùng chuỗi 100 số; seed khác → chuỗi khác | unit test |
| AC6 | `DeterministicHarness.run()`: 2 replay cùng config+seed → `stable=True` (pixel-stable PASS); seed khác → stable=False | unit test |
| AC7 | Harness kết quả dùng Verification Kernel: render_fn raise → outcome BLOCKED, không PASS (INV-035); replay không chạy → NOT_EXECUTED | unit test |
| AC8 | `AssetIdempotencyClassifier`: exactly-once/at-least-once/at-most-once đúng; không khai báo → at-most-once (fail-closed) | unit test |
| AC9 | CLI `aiagent render-replay` chạy thật: mock render_fn → stable + exit 0 (--seed/--frames/--width/--height/--show-hashes) | chạy CLI |
| AC10 | Full suite xanh (không regression) | pytest |

## 6. Nguồn tham khảo

- Proposal M11 §R3 + §7 (M11-P1) + §1b (determinism bolt-on từng layer — freeze time, PRNG seeded, anims.pauseAll)
- M10 `kernel/durability.py` (IdempotencyClassifier — fail-closed pattern)
- TASK-078 `verification/` (VerificationOutcome, VerificationState, fail_closed_normalize)
