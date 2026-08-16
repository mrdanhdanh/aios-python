# TASK-080 — M11-P2/P2b: R1 VisualEvidence + R10 UI State Contract

> **Milestone**: M11-P2+P2b (Issue #4) — Visual Observability
> **Ngày**: 2026-08-16 | **Owner**: AIOS Orchestrator
> **Tham chiếu**: proposal M11 §R1 + §R10 + §7 (M11-P2/P2b), PLAN.md §M11

## 1. Mục tiêu

- **R10 (P2b, nền)**: `UIState` contract — chuẩn hóa state có thể reason:
  `UI State → Render → Screenshot`. AIOS debug UI bằng reasoning, không chỉ pixel compare.
- **R1 (P2)**: `VisualEvidence` / `VisualRegressionProbe` — Screenshot + DOM Snapshot +
  Render State + Input Timeline + Seed + Pixel Diff; **pixel-diff chỉ là 1 trường evidence,
  KHÔNG thành SLO sớm** (anti-aliasing/font/GPU gây diff).

## 2. Phạm vi (IN)

1. **Package mở rộng `backend/src/aios_core/rendering/`**:
   - `ui_state.py` — `UIState` contract (pydantic extra=forbid): `version: str = "1.0"`,
     `screen: str`, `entities: dict[str, dict]` (player {x, y, scale}...), `input: dict[str, Any]`,
     `t: float`, `seed: int`; canonical JSON = `json.dumps(sort_keys=True, separators=(",", ":"))`;
     `state_hash()` = SHA256(canonical) — deterministic
   - `evidence.py` — `VisualEvidence` (pydantic): `version: str = "1.0"`,
     `screenshot: str` (**base64 data URI** `data:image/png;base64,...` — self-contained),
     `dom_snapshot: dict` (`{"tag", "text", "attrs", "children"}` recursive),
     `render_state: UIState` (**required** — R10 nền R1),
     `input_timeline: list[InputEvent]` (P1 contract — không duplicate),
     `seed: int`, `browser_meta: dict` (`browser/os/viewport/device_scale_factor`),
     `pixel_diff: float = -1.0` (**-1 = thiếu ref, 0 = giống, >0 = % khác**)
   - `probe.py` — `VisualRegressionProbe` (config `pixel_threshold: int = 30`): so sánh
     ref vs current → diff summary (pixel_diff %, dom diff path/before/after, state diff);
     dùng DeterministicHarness (P1) khi cần replay; outcome VerificationOutcome (INV-035):
     **state mapping: thiếu ref → MISSING_EVIDENCE; probe không gọi → NOT_EXECUTED;
     collector lỗi → ERROR; cả 3 KHÔNG PASS; 2 bên thiếu ref → vẫn MISSING_EVIDENCE**
2. **Observability tích hợp**:
   - `observability/metrics.py` (MetricsRegistry có sẵn M4): register idempotent counters
     `visual_probe_count`, `visual_fail_closed_violations` + gauge `visual_pixel_diff_max`
     — không phải SLO pixel (metric sau evidence)
3. **CLI `aiagent visual-probe`** — demo: mock evidence (--dump-ref/--dump-current ghi JSON file,
   --ref/--current đọc JSON, --threshold, --missing-ref mô phỏng thiếu ref) → diff + outcome
   (exit theo outcome)

## 3. OUT of scope

- R9/R4/R11 Asset Capability (P3 — TASK-081)
- Screenshot thật (browser driver) — probe nhận evidence injectable; test dùng mock
- Pixel-diff thành SLO — ghi nhận (proposal: metric sau evidence)
- Sửa game code

## 4. Input / Output

- **Input**: UIState (render state), evidence từ probe/collector
- **Output**: UIState contract + VisualEvidence + VisualRegressionProbe + CLI + observability metrics + tests

## 5. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm tra |
|---|----|---------------|
| AC1 | `UIState` contract: canonical JSON + state_hash deterministic (cùng state → cùng hash) | unit test |
| AC2 | UIState extra=forbid + validate entities/input là dict | unit test |
| AC3 | `VisualEvidence` đủ 7 trường (screenshot/dom_snapshot/render_state/input_timeline/seed/browser_meta/pixel_diff) | unit test |
| AC4 | `VisualRegressionProbe.compare()`: 2 evidence giống → diff nhỏ (pixel_diff=0.0, dom/state khớp) → outcome PASS | unit test |
| AC5 | Probe: evidence khác state → phát hiện state_diff (reasoning — R10) | unit test |
| AC6 | Probe: **thiếu screenshot ref → MISSING_EVIDENCE → outcome KHÔNG PASS** (INV-035 — chống false-positive "17/17 PASS") | unit test |
| AC7 | Probe: screenshot khác (pixel_diff > 0) → FAIL nhưng vẫn kèm evidence đầy đủ (không kết luận thiếu) | unit test |
| AC8 | Observability: metrics visual_probe_count/visual_fail_closed_violations đăng ký | unit test |
| AC9 | CLI `aiagent visual-probe` chạy thật (mock evidence) → diff + outcome, exit theo outcome | chạy CLI |
| AC10 | Full suite xanh | pytest |

## 6. Nguồn tham khảo

- Proposal M11 §R1 (VisualEvidence tree) + §R10 (UIState JSON example) + §7 (P2/P2b)
- TASK-079 `rendering/` (DeterministicHarness, InputEvent, RenderTimeline)
- TASK-078 `verification/` (VerificationOutcome, VerificationState — MISSING_EVIDENCE)
