# Proposal: M11 — Deterministic Artifact & Interaction Runtime

> **Status**: refined (post-review — user score 8.8/10, chuẩn bị thành milestone)
> **Date**: 2026-08-16 (review adjustments cùng ngày)
> **Source**: PR #1 (`operation/test-A` → `verify`) — commits TASK-077..081 + 2 bypass fix
> **Author**: AIOS Orchestrator (analysis pass) + user review/adjustment
> **Related**: M10 AIOS 1.0 CERTIFIED; ADR-0005 branching model

---

## TL;DR

PR #1 mang toàn bộ công việc webgame **Yuniebel's Cat** (vanilla → Phaser 4) + game-dev skills.
Phân tích 12 commit thực tế cho thấy AIOS 1.0 xử lý backend/runtime xuất sắc, nhưng **mù với
output phi-deterministic** (render/UI/asset) và **không điều phối được skill/capability creative**.

**M11 không phải "creative expansion" cho vui** — đó là bước tiến kiến trúc:

```
M10: AIOS can reliably execute logic.
M11: AIOS can reliably execute AND verify logic + state + render + asset + interaction.
```

Đề xuất **M11** gồm 10 nâng cấp (R1–R10) mở rộng trực tiếp M10, không phá vỡ INV-001..034.
**Cụm cốt lõi (R2 → R3 → R1)**: Verification Policy → Deterministic Harness → Visual Evidence,
mở đường cho CAD, diagram, document rendering, image/video/3D generation — mọi workflow có artifact phi-text.

**Ưu tiên số 1: R2 (INV-035 Verification Fail-Closed)** — vì PR chứng minh false-positive đã xảy ra thật
(TASK-079: `toHaveScreenshot` skip do thiếu ảnh ref → "17/17 PASS" giả). Đây là **Core Invariant**, không chỉ rule visual test.

> User review: **8.8/10** — "M11 không phải thêm feature creative cho vui, mà xuất phát từ một failure mode thực tế của AIOS 1.0."

---

## 1. Tín hiệu từ PR #1 (dữ liệu thực tế)

| Chỉ số | Giá trị | Ý nghĩa |
|--------|---------|---------|
| Tổng thay đổi | 158 files, **+13,527 / −1** | Gần như toàn thêm mới (game + skills) |
| Ảnh PNG commit | **47 file** (screenshots + sprite outputs + brief refs + baseimg) | QA phụ thuộc hoàn toàn vào visual/golden-master |
| TASK-077 | 46 files, 7479+ (vanilla, 0 deps) | Scaffold thủ công, canvas primitives by hand |
| TASK-078 | 64 files, 3119+ / 1334− (redo + 17 screenshots) | Chụp ảnh so brief |
| TASK-079 | 19 files, 2517+ (logical grid) + 17 PNG refresh | Fix cat biến mất do scale mismatch |
| TASK-080 | 35 files, 1061+ (skills từ repo ngoài) | Distill thủ công |
| TASK-081 | Phaser 4 Vite, vendor byte-identical SHA256 (AC-16), 56/56 test | Verify thủ công third-party bundle |
| CI | `pages.yml` sửa tay (Node 20 + build + `rm node_modules`) | Không có deploy capability |

**Sự kiện then chốt (từ LOG.md)**:
- TASK-079 review phát hiện "17/17 khớp brief" thực chất **bị skip** — brief không có ảnh ref nên
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

## 2. Gap Analysis — AIOS 1.0 thiếu gì cho creative/asset/UI

| Thành phần AIOS 1.0 | Trạng thái hiện tại | Thiếu cho domain creative |
|---------------------|---------------------|---------------------------|
| Observability (TASK-069 SLO) | Ratio + zero-gate backend | Không có tín hiệu render/pixel |
| Durable Execution (TASK-066) | Journal + replay backend workflow | Không có replay cho UI/input timeline |
| Security Baseline (TASK-070) | 11 items, không cover bundle hash | Không verify third-party vendor hash |
| Contract 1.0 (TASK-064) | 10 contract (Agent/Capability/.../Memory) | Không có AssetPipeline contract |
| Ecosystem (M8) | Plugin Runtime/Registry | Không có SkillDistiller tự động |
| Orchestrator 4 tầng | Normalizer→Rule→Matcher→Planner (backend) | Không có domain `creative` |
| Developer Experience (TASK-071) | `doctor`/`conformance` first-class | Không có `deploy --static` |

---

## 3. Đề xuất nâng cấp (R1–R10, đã điều chỉnh theo review)

> Dependency order (architecture): **R2 → R3 → R1 → R9 → R4 → R8 → R6 → R5 → R7**
> (R3 nền tảng trước R1; R4+R9 gộp thành Asset Capability Architecture; R5 rớt xuống Ecosystem Extension; R7 trì hoãn P4)

### R2 — INV-035: Verification Fail-Closed (CORE INVARIANT)
- **Evidence**: TASK-079 "17/17 PASS" thực chất skip vì thiếu ảnh ref.
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
- **Maps-to**: M10-P2 / TASK-066 (Durable Execution).

### R1 — VisualEvidence / VisualRegressionProbe (KHÔNG chỉ pixel-diff metric)
- **Evidence**: 47 PNG golden-master; bug TASK-079 chỉ bắt bằng visual test.
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
- **Maps-to**: M10-P2 / TASK-069 (SLO registry).

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
- **Evidence**: TASK-081 AC-16 verify thủ công SHA256 vendor bundle byte-identical.
- **Gap**: `security-check` (M10) chưa cover third-party bundle hash.
- **Proposal**: Thêm `VendorIntegrity` vào `aiagent security-check` — tự verify hash pinned bundles; freeze invariant.
- **Maps-to**: M10-P3 / TASK-070 (Security Baseline).

### R10 — UI State Contract (MỚI)
- **Evidence**: TASK-079 — logical state đúng nhưng render transform sai → screenshot khác, nhưng AIOS không biết "tại sao".
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
- **Evidence**: TASK-080 distill thủ công từ repo ngoài.
- **Gap**: Ecosystem (M8) không có tool tự distill.
- **Proposal**: Xếp thành `M11 Ecosystem Extension` (P4), không core. Scope lớn
  (repo → license → structure → capability extraction → synthesis → manifest → contract validation → critique×2 → registry)
  — gần như Meta-Evolution Engine; làm sớm sẽ phình M11 mất trọng tâm.
- **Maps-to**: M8 (Ecosystem / Registry / DevKit).

### R7 — Static-site / Artifact Deploy (TRÌ HOÃN → P4 / optional)
- **Evidence**: `pages.yml` sửa tay (Node 20 + build + `rm node_modules`).
- **Gap**: CLI không có deploy; nhưng PR không chứng minh correctness bị phá vỡ.
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

## 7. TASK breakdown (refined — TASK-082 thu nhỏ)

```
TASK-082  M11-P0 — Verification Integrity
  Scope:
  ├── INV-035 (Verification Fail-Closed)
  ├── conformance visual policy
  ├── skip/error normalization
  ├── missing reference detection
  ├── CI fail-closed gate
  ├── regression tests
  └── retroactive audit TASK-077..081

TASK-083 → RenderReplay (R3)
TASK-084 → VisualEvidence (R1)
TASK-085 → AssetPipeline Contract (R9)
TASK-086 → Asset Capability (R4)
TASK-087 → Creative Domain (R6)
TASK-088 → Vendor Integrity (R8)
TASK-089 → UI State Contract (R10)
TASK-090 → SkillDistiller (R5, Ecosystem)
TASK-091 → Static Deploy (R7, optional)
```

## 8. Open Questions (cập nhật)

1. **R2 retroactive**: user duyệt — TASK-082 bao gồm *retroactive audit TASK-077..081* (áp dụng INV-035 cho PR #1 đã merge). ✅ resolved.
2. R1 pixel-diff threshold: chưa tham số hóa thành SLO sớm (theo feedback R1 → VisualEvidence trước, metric sau). Để TASK-084 quyết.
3. R5 SkillDistiller form: CLI `aiagent skill distill <url>` hay `agent` tool? → TASK-090.
4. R7 deploy hosts: GitHub Pages only hay S3/Netlify? → TASK-091.
5. R10 UIState schema: định hình chuẩn JSON trong TASK-089.

## 9. Ghi chú tuân thủ

- **Không vi phạm INV-001..034** — toàn bộ additive lên M10; INV-035 là invariant MỚI (M11).
- Trạng thái: proposal đã qua review user (8.8/10), sẵn sàng tạo `TASK-082` (M11-P0) theo hard-gate chuẩn.
- Khi duyệt → tạo TASK-082 (thu nhỏ, chỉ P0) trước; các TASK-083..091 theo tiến độ phase.
- File này là tài liệu tham khảo; cập nhật LOG.md nhưng CHƯA tạo task (chờ user "tạo TASK-082").
