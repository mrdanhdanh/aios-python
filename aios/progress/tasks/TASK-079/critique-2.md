# TASK-079 — Critique vòng 2 (spec)

> **Critic**: AIOS Orchestrator (vòng 2 — sau resolve vòng 1)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved

## P1 — Phải sửa

### C2-01. `DeterministicHarness.run()` trả gì — verdict hay frames?
→ **Resolve**: `run()` trả `RenderReplayResult` (pydantic): `frames_a`, `frames_b`, `stable: bool`,
`diff_frames: list[int]`, `outcome: VerificationOutcome` (INV-035). Harness KHÔNG tự raise khi unstable
— caller quyết định (fail-closed qua outcome). Ghi rõ.

### C2-02. Seed lấy từ đâu khi replay lần 2?
→ **Resolve**: harness config có `seed` cố định; replay A dùng `seed`, replay B dùng **cùng `seed`**
(đúng mục đích: 2 lần chạy cùng config phải giống). Nếu B dùng seed khác → unstable cố ý (test AC4
dùng trường hợp này).

### C2-03. Input timeline trống thì sao?
→ **Resolve**: replay với timeline rỗng hợp lệ (render thuần theo seed); `stable` vẫn đúng.
Không phải error.

## P2 — Nên sửa

### C2-04. Mulberry32 cần cài từ đâu?
→ **Resolve**: tự implement 1 hàm thuần (~15 dòng, công khai) — không thêm dependency. Test vector
cố định (seed=1 → dãy số cố định) để chứng minh deterministic cross-version.

### C2-05. CLI render-replay có cần --seed/--frames?
→ **Resolve**: có — `--seed` (default 42), `--frames` (default 60), `--width/--height` (default 64×64),
`--show-hashes` (in hash từng frame).

## P3 — Ghi nhận

### C2-06. Performance — replay 300 frames × 2 với mock OK; với render thật (Phaser) thì sao?
→ Resolve: ghi nhận — P1 chỉ mock; render thật qua browser driver ở P2/R1 (VisualRegressionProbe).

### C2-07. Naming: `rendering/` vs `deterministic/`?
→ Resolve: giữ `rendering/` (đúng ngữ nghĩa — RenderReplay; DeterministicHarness là 1 module trong đó).

## Kết luận
Spec v2 sau resolve C2-01..05 → **APPROVED — được phép implement** (đủ 2 vòng critique).
