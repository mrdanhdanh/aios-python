# Proposal: M11 — Deterministic Artifact & Interaction Runtime

> **Status**: refined (post-review — user score 8.8/10, chuẩn bị thành milestone)
> **Date**: 2026-08-16 (review adjustments cùng ngày)
> **Source**: thực tế từ việc xây dựng webgame **Yuniebel's Cat** (vanilla canvas → Phaser 4 Vite) + game-dev skills (agent-sprite-forge, pixel-game-dev) trong repo — phân tích các commit liên quan.
> **Author**: AIOS Orchestrator (analysis pass) + user review/adjustment
> **Related**: M10 AIOS 1.0 CERTIFIED; ADR-0005 branching model

---

## TL;DR

Việc xây dựng webgame **Yuniebel's Cat** (vanilla → Phaser 4) + game-dev skills là nguyên liệu thực tế.
Phân tích các commit liên quan cho thấy AIOS 1.0 xử lý backend/runtime xuất sắc, nhưng **mù với
output phi-deterministic** (render/UI/asset) và **không điều phối được skill/capability creative**.

**M11 không phải "creative expansion" cho vui** — đó là bước tiến kiến trúc:

```
M10: AIOS can reliably execute logic.
M11: AIOS can reliably execute AND verify logic + state + render + asset + interaction.
```

Đề xuất **M11** gồm 10 nâng cấp (R1–R10) mở rộng trực tiếp M10, không phá vỡ INV-001..034.
**Cụm cốt lõi (R2 → R3 → R1)**: Verification Policy → Deterministic Harness → Visual Evidence,
mở đường cho CAD, diagram, document rendering, image/video/3D generation — mọi workflow có artifact phi-text.

**Ưu tiên số 1: R2 (INV-035 Verification Fail-Closed)** — vì thực tế chứng minh false-positive đã xảy ra thật
(visual test báo "17/17 PASS" nhưng thực chất `toHaveScreenshot` bị skip do thiếu ảnh ref). Đây là **Core Invariant**, không chỉ rule visual test.

> User review: **8.8/10** — "M11 không phải thêm feature creative cho vui, mà xuất phát từ một failure mode thực tế của AIOS 1.0."

---

## 1. Tín hiệu từ thực tế phát triển (dữ liệu thực tế)

| Chỉ số | Giá trị | Ý nghĩa |
|--------|---------|---------|
| Tổng thay đổi | 158 files, **+13,527 / −1** | Gần như toàn thêm mới (game + skills) |
| Ảnh PNG commit | **47 file** (screenshots + sprite outputs + brief refs + baseimg) | QA phụ thuộc hoàn toàn vào visual/golden-master |
| Webgame vanilla | 46 files, 7479+ (vanilla, 0 deps) | Scaffold thủ công, canvas primitives by hand |
| Game redo (brief) | 64 files, 3119+ / 1334− (làm lại + 17 screenshots) | Chụp ảnh so brief + 5 ảnh tham khảo |
| Fix cat biến mất | 19 files, 2517+ (logical grid) + 17 PNG refresh | Fix cat biến mất do scale mismatch |
| Game-dev skills | 35 files, 1061+ (skills từ repo ngoài) | Distill thủ công 2 skill package |
| Phaser 4 scaffold | Phaser 4 Vite, vendor byte-identical SHA256 (AC-16), 56/56 test | Verify thủ công third-party bundle |
| CI | `pages.yml` sửa tay (Node 20 + build + `rm node_modules`) | Không có deploy capability |

**Sự kiện then chốt (từ LOG.md)**:
- Review của webgame phát hiện "17/17 khớp brief" thực chất **bị skip** — brief không có ảnh ref nên
  `toHaveScreenshot` không chạy → **false-positive**.
- Bug "cat biến mất sau START" (scale mismatch sprite 160×90 vs world ×3) **chỉ bị bắt bởi visual
  test**; core 27/27 vẫn xanh. Đây là blind spot của test backend-thuần.

**3 nhóm tín hiệu cốt lõi**:
1. **Observability mù với output phi-deterministic** (render/UI/asset) — AIOS 1.0 đo latency/SLO/
   event bus nhưng không có khái niệm "render state" hay "pixel diff delta".
2. **Capability/Skill không được Orchestrator điều phối** — `generate2dsprite.py` và skill packages
   tồn tại ngoài Capability Registry; "generate sprite" không route được offline-first.
3. **Test framework thiếu fail-closed cho golden-master** — nguyên tắc "policy bypass=0" (M10 SLO)
   chưa áp dụng cho visual test.

---

## 1b. Tín hiệu bổ sung — nâng cấp game Phaser 4 (sprite/fx/parallax/transition)

Một đợt nâng cấp tiếp theo của cùng webgame (hướng E = sprite sheet PNG + fx + parallax + transition,
88/88 test / 23/23 AC, thực hiện autonomous) cung cấp bằng chứng bổ sung rất mạnh cho M11 — và cho thấy
các primitive M11 đề xuất **chưa tồn tại ở tầng hệ thống**, buộc worker phải tự implement lại:

- **Asset-generation viết tay từ đầu** — worker tạo script encoder PNG riêng (CRC32 + zlib, palette vendor)
  thay vì dùng skill `agent-sprite-forge` đã có. → Củng cố **R4/R9**: AssetPipeline contract + Capability
  Registry chưa discoverable/routable; worker không route được "generate sprite" tới skill sẵn có.
  *(Sub-gap mới **R4a** — capability discovery gap: skill tồn tại nhưng worker không tìm/thấy dùng được.)*
- **Determinism bolt-on từng layer** — mọi layer mới phải tự respect freeze (`rtime` đóng băng, particle
  dùng PRNG seeded mulberry32, `anims.pauseAll()` khi frozen). → Củng cố **R3** cực mạnh: cần
  `RenderReplay`/`DeterministicHarness` ở tầng runtime, không phải tự implement mỗi lần.
  *(Sub-gap mới **R3a** — determinism là per-layer duct-tape, không phải guarantee của runtime.)*
- **Vendor-hash re-implement trong test** — `vendor-hashes.json` (SHA256 baseline) tự viết trong test
  (C2-11/C3-06) thay vì capability hệ thống. → Củng cố **R8** (Vendor Integrity) — nên là `aiagent
  security-check`, không phải test tự làm.
- **Fail-closed tự vá ở test** — worker phải thêm cơ chế "non-empty + byte-compare frozen" vào visual
  regression (C2-09) trực tiếp vì bài học false-positive. → Bằng chứng thực tế **R2** cần là invariant
  hệ thống, không phải duct-tape mỗi task.
- **Render là pure function của (state, time, seed)** — worker định nghĩa rõ "frozen state" và render
  thuần hàm. → Củng cố **R10** (UI State Contract): UI State → Render → Screenshot.
- **Reference-asset hiểu bằng vision model** — worker dùng `imagedata.md` (mô tả ảnh từ vision model) làm
  cầu nối giữa brief ảnh và code. AIOS không có capability first-class để ingest/structure reference
  visual asset. → **Candidate R11**: "Reference-Asset Understanding" (xem §8 — có thể gộp R6 hoặc R10,
  hoặc đứng riêng).
- **Autonomous worker tái implement primitive** — task chạy autonomous nhưng worker KHÔNG có AIOS
  capability cho asset-gen/determinism/vendor-integrity → tự viết lại. Đây chính là gap M11 đóng: worker
  nên gọi capability có sẵn, không reimplement.

---

## 2. Gap Analysis — AIOS 1.0 thiếu gì cho creative/asset/UI

| Thành phần AIOS 1.0 | Trạng thái hiện tại | Thiếu cho domain creative |
|---------------------|---------------------|---------------------------|
| Observability (SLO registry) | Ratio + zero-gate backend | Không có tín hiệu render/pixel |
| Durable Execution | Journal + replay backend workflow | Không có replay cho UI/input timeline |
| Security Baseline | 11 items, không cover bundle hash | Không verify third-party vendor hash |
| Contract 1.0 | 10 contract (Agent/Capability/.../Memory) | Không có AssetPipeline contract |
| Ecosystem (M8) | Plugin Runtime/Registry | Không có SkillDistiller tự động |
| Orchestrator 4 tầng | Normalizer→Rule→Matcher→Planner (backend) | Không có domain `creative` |
| Developer Experience | `doctor`/`conformance` first-class | Không có `deploy --static` |

---

## 3. Đề xuất nâng cấp (R1–R10, đã điều chỉnh theo review)

> Dependency order (architecture): **R2 → R3 → R1 → R9 → R4 → R8 → R6 → R5 → R7**
> (R3 nền tảng trước R1; R4+R9 gộp thành Asset Capability Architecture; R5 rớt xuống Ecosystem Extension; R7 trì hoãn P4)

### R2 — INV-035: Verification Fail-Closed (CORE INVARIANT)
- **Evidence**: Kết quả visual test báo "17/17 PASS" thực chất skip vì thiếu ảnh ref.
- **Gap**: `aiagent conformance` không enforce verification fail-closed.
- **Proposal**: Thăng cấp thành **Core Invariant INV-035** — wording rộng:
  > *Không một verification mechanism nào được phép chuyển trạng thái `UNKNOWN / NOT EXECUTED / MISSING EVIDENCE` thành `PASS`.*
  Bắt: missing screenshot reference, test skipped, browser failed to launch, renderer unavailable,
  reference unreadable, artifact missing, dependency unavailable, assertion not executed.
  Trạng thái hợp lệ: `PASS | FAIL | ERROR | BLOCKED` — **KHÔNG** `SKIP → vô tình PASS`.
- **Maps-to**: M10-P3 (security-check) + M10-P5 (conformance) + Constitution 1.0.
- **Priority**: 🔴 CAO NHẤT.

### R3 — RenderReplay / DeterministicHarness (FOUNDATION, trước R1)
- **Evidence**: playtest thật 45s (title→birthday) / 22s (title→gameover); bug do non-determinism (scale).
- **Gap**: Durable Execution 1.0 chỉ cho backend workflow.
- **Proposal**: `RenderReplay` — record input timeline + seed → replay → assert pixel-stable.
  Là nền tảng cho R1: không có deterministic replay thì VisualRegressionProbe dễ thành
  "ảnh hôm nay khác ảnh hôm qua" nhưng không biết tại sao. Mượn idempotency classification (exactly-once) cho asset.
- **Maps-to**: M10-P2 (Durable Execution).

### R1 — VisualEvidence / VisualRegressionProbe (KHÔNG chỉ pixel-diff metric)
- **Evidence**: 47 PNG golden-master; bug (cat biến mất sau START) chỉ bắt bằng visual test.
- **Gap**: SLO registry chỉ có metric backend.
- **Proposal**: Thiết kế `VisualEvidence` TRƯỚC khi có metric:
  ```
  VisualRegressionProbe
        ├── Screenshot
        ├── DOM Snapshot
        ├── Render State
        ├── Input Timeline
        ├── Browser/OS metadata
        ├── Seed
        └── Pixel Diff
  ```
  `VisualEvidence` → `VisualRegressionProbe` → Observability → SLO/Evaluation.
  Pixel-diff KHÔNG tự nói tốt/xấu (anti-aliasing, font, GPU, device scale factor tạo diff lớn)
  → chỉ là 1 trường trong evidence, không phải SLO chính sớm.
- **Maps-to**: M10-P2 (SLO registry).

### R9 + R4 — Asset Capability Architecture (GỘP)
- **Evidence**: `generate2dsprite.py` script rời; agent-sprite-forge chroma #FF00FF chưa chuẩn.
- **Gap**: Capability Registry chỉ backend tools; không có AssetPipeline contract.
- **Proposal**: Gộp thành một kiến trúc lớn:
  ```
  AssetPipeline Contract        (R9)
       ├── Sprite / Tileset / Map / Audio / Animation / UI Asset
       ↓
  Capability Manifest
       ↓
  Asset Capability Registry     (R4, kind=asset)
       ↓
  Creative Matcher
       ↓
  Runtime / Orchestrator
  ```
  Biến M11 từ "AIOS hỗ trợ game" → **"AIOS hiểu và điều phối artifact creative"**.
- **Maps-to**: M1 (Capability Registry) + M10-P1 (Contract 1.0).

### R6 — Creative/Game domain trong Decision Pipeline
- **Evidence**: "build a game" / "generate pixel art" không có workflow; scaffold ad-hoc.
- **Gap**: 4 tầng Orchestrator建模 backend, không có domain `creative`.
- **Proposal**: Thêm workflow domain `creative`/`frontend` vào Workflow Matcher → route offline-first,
  giảm lệ thuộc Planner LLM.
- **Maps-to**: Orchestrator Decision Pipeline (PLAN.md §AIOS Orchestrator).

### R8 — Vendor Integrity verification
- **Evidence**: Scaffold Phaser 4 (Vite): AC-16 verify thủ công SHA256 vendor bundle byte-identical.
- **Gap**: `security-check` (M10) chưa cover third-party bundle hash.
- **Proposal**: Thêm `VendorIntegrity` vào `aiagent security-check` — tự verify hash pinned bundles; freeze invariant.
- **Maps-to**: M10-P3 (Security Baseline).

### R10 — UI State Contract (MỚI)
- **Evidence**: Trường hợp cat biến mất — logical state đúng nhưng render transform sai → screenshot khác, nhưng AIOS không biết "tại sao".
- **Gap**: Proposal cũ tập trung pixel/asset/render/replay, chưa chuẩn hóa UI state.
- **Proposal**: `UIState` contract — chuẩn hóa state có thể reason:
  ```json
  {
    "screen": "game",
    "player": { "x": 160, "y": 90, "scale": 3 },
    "input": { "left": false, "right": true }
  }
  ```
  `UI State → Render → Screenshot`. Giúp AIOS **debug UI bằng reasoning**, không chỉ screenshot comparison.
- **Maps-to**: M10-P1 (Contract 1.0) + Observability.

### R5 — SkillDistiller (Ecosystem Extension, KHÔNG core M11)
- **Evidence**: Game-dev skill package được distill thủ công từ repo ngoài.
- **Gap**: Ecosystem (M8) không có tool tự distill.
- **Proposal**: Xếp thành `M11 Ecosystem Extension` (P4), không core. Scope lớn
  (repo → license → structure → capability extraction → synthesis → manifest → contract validation → critique×2 → registry)
  — gần như Meta-Evolution Engine; làm sớm sẽ phình M11 mất trọng tâm.
- **Maps-to**: M8 (Ecosystem / Registry / DevKit).

### R7 — Static-site / Artifact Deploy (TRÌ HOÃN → P4 / optional)
- **Evidence**: `pages.yml` sửa tay (Node 20 + build + `rm node_modules`).
- **Gap**: CLI không có deploy; nhưng thực tế không chứng minh correctness bị phá vỡ.
- **Proposal**: `aiagent deploy --static <dir>` → P4 / optional. R2/R3/R9 là correctness primitives quan trọng hơn.
- **Maps-to**: M3 (Dashboard/Extension) + M10-P4 (DX).

---

## 4. Asset Capability Architecture (R9 + R4 gộp)

```
AssetPipeline Contract
       │
       ├── Sprite
       ├── Tileset
       ├── Map
       ├── Audio
       ├── Animation
       └── UI Asset
              ↓
      Capability Manifest
              ↓
      Capability Registry (kind=asset)
              ↓
       Creative Matcher
              ↓
          Runtime
```

## 5. M11 Roadmap — 5 tầng (P0–P4)

```
M11 — Deterministic Artifact & Interaction Runtime

P0 — Verification Integrity
 └── R2  INV-035 Fail-closed Verification

P1 — Deterministic Visual Runtime
 └── R3  RenderReplay / DeterministicHarness

P2 — Visual Observability
 └── R1  VisualEvidence / VisualRegressionProbe

P3 — Asset & Creative Architecture
 ├── R9  AssetPipeline Contract
 ├── R4  Asset Capability
 ├── R6  Creative Domain
 └── R8  Vendor Integrity

P4 — Ecosystem & DX
 ├── R5  SkillDistiller (Ecosystem Extension)
 └── R7  Static Deploy (optional)
```

**Dependency graph**:
```
Verification (R2)
     ↓
Determinism (R3)
     ↓
Observation (R1)
     ↓
Contract (R9)
     ↓
Capability (R4)
     ↓
Decision (R6)
     ↓
Ecosystem (R5) + DX (R7)
```

**Core capability cluster (R2 → R3 → R1)**:
```
┌──────────────────────┐
│ Verification Policy  │  INV-035
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ DeterministicHarness │  RenderReplay
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│    VisualEvidence    │  Regression Probe
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ AIOS Evaluation /    │  Observability
│ Observability        │
└──────────────────────┘
```
> Nếu xây đúng cụm này, M11 mở đường cho CAD, diagram, document rendering, image generation, video, 3D và mọi workflow có artifact phi-text.

## 6. Architectural Goal / Progression

```
M10: AIOS can reliably execute logic.
M11: AIOS can reliably execute AND verify logic + state + render + asset + interaction.
```
M11 = **Deterministic Artifact & Interaction Runtime** (không phải "Creative expansion").

## 7. TASK breakdown (refined — M11-P0 thu nhỏ)

```
M11-P0 — Verification Integrity
  Scope:
  ├── INV-035 (Verification Fail-Closed)
  ├── conformance visual policy
  ├── skip/error normalization
  ├── missing reference detection
  ├── CI fail-closed gate
  ├── regression tests
  └── retroactive audit các commit webgame/visual đã merge

M11-P1  → RenderReplay (R3)
M11-P2  → VisualEvidence (R1)
M11-P2b → UI State Contract (R10)
M11-P3a → AssetPipeline Contract (R9)
M11-P3b → Asset Capability (R4)
M11-P3c → Creative Domain (R6)
M11-P3d → Vendor Integrity (R8)
M11-P4a → SkillDistiller (R5, Ecosystem)
M11-P4b → Static Deploy (R7, optional)
```

## 8. Open Questions (cập nhật)

1. **R2 retroactive**: user duyệt — M11-P0 bao gồm *retroactive audit các commit webgame/visual đã merge* (áp dụng INV-035 cho code hiện tại). ✅ resolved.
2. R1 pixel-diff threshold: chưa tham số hóa thành SLO sớm (theo feedback R1 → VisualEvidence trước, metric sau). Để phase M11-P2 quyết.
3. R5 SkillDistiller form: CLI `aiagent skill distill <url>` hay `agent` tool? → phase M11-P4a.
4. R7 deploy hosts: GitHub Pages only hay S3/Netlify? → phase M11-P4b.
5. R10 UIState schema: định hình chuẩn JSON trong phase M11-P2b.
6. **R11 candidate — Reference-Asset Understanding**: từ nâng cấp game Phaser 4, worker dùng `imagedata.md`
   (vision-model description) làm cầu nối brief ảnh → code. Có nên thành capability riêng (R11) hay gộp
   vào R6 (Creative Domain) / R10 (UI State)? → chờ quyết định trước M11-P3.

## 9. Ghi chú tuân thủ

- **Không vi phạm INV-001..034** — toàn bộ additive lên M10; INV-035 là invariant MỚI (M11).
- Trạng thái: proposal đã qua review user (8.8/10), sẵn sàng tạo task M11-P0 theo hard-gate chuẩn.
- Khi duyệt → tạo task M11-P0 (thu nhỏ, chỉ P0) trước; các phase P1–P4 theo tiến độ.
- **Nguồn evidence**: (1) đợt xây dựng webgame đầu (vanilla → Phaser 4) + game-dev skills; (2) đợt nâng cấp
  game Phaser 4 tiếp theo (sprite/fx/parallax/transition, autonomous, 88/88 test) — cả hai cùng chỉ ra
  các primitive M11 chưa tồn tại ở tầng hệ thống.
- Tài liệu này **branch-independent**: không gắn với PR/nhánh cụ thể, dùng làm tham khảo kiến trúc M11 trên bất kỳ nhánh nào.
