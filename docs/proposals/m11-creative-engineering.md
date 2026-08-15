# Proposal: M11 — AIOS Creative / Asset / UI Engineering

> **Status**: draft / proposal (tham khảo, chưa thành task)
> **Date**: 2026-08-16
> **Source**: PR #1 (`operation/test-A` → `verify`) — commits TASK-077..081 + 2 bypass fix
> **Author**: AIOS Orchestrator (analysis pass)
> **Related**: M10 AIOS 1.0 CERTIFIED; ADR-0005 branching model

---

## TL;DR

PR #1 mang toàn bộ công việc webgame **Yuniebel's Cat** (vanilla → Phaser 4) + game-dev skills.
Phân tích 12 commit thực tế cho thấy AIOS 1.0 xử lý backend/runtime xuất sắc, nhưng **mù với
output phi-deterministic** (render/UI/asset) và **không điều phối được skill/capability creative**.
Đề xuất **M11** gồm 9 nâng cấp (R1–R9) mở rộng trực tiếp các thành phần M10 (observability,
durable execution, security-check, contract 1.0, ecosystem), không phá vỡ INV-001..034.

**Ưu tiên cao nhất: R2** (fail-closed golden-master test policy) — vì PR chứng minh false-positive
đã xảy ra thật (`toHaveScreenshot` skip do thiếu ảnh ref ở TASK-079), vi phạm trực tiếp triết lý
"policy bypass=0" của M10.

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

## 3. Đề xuất nâng cấp (R1–R9)

### R1 — VisualRegressionProbe trong Observability
- **Evidence**: 47 PNG golden-master; bug TASK-079 chỉ bắt bằng visual test.
- **Gap**: SLO registry (M10-P2) chỉ có metric backend.
- **Proposal**: Thêm `VisualRegressionProbe` — biến "pixel-diff delta" thành metric (histogram như
  latency), report qua `aiagent metrics`; mỗi render snapshot → 1 event trên event bus.
- **Maps-to**: M10-P2 / TASK-069 (SLO registry).

### R2 — Fail-closed Golden-Master test policy
- **Evidence**: TASK-079 "17/17 pass" thực chất skip vì thiếu ảnh ref.
- **Gap**: `aiagent conformance` không enforce visual test có reference.
- **Proposal**: `INV-035` — "mọi visual/golden-master test PHẢI fail-closed: thiếu reference =
  ERROR (không skip)". Tích hợp vào `aiagent conformance` + CI gate. Áp dụng trực tiếp "policy
  bypass=0" của M10.
- **Maps-to**: M10-P3 / TASK-070 (security-check) + M10-P5 (conformance).
- **Priority**: 🔴 CAO NHẤT — false-positive đã xảy ra thật.

### R3 — RenderReplay / DeterministicHarness cho UI
- **Evidence**: playtest thật 45s (title→birthday) / 22s (title→gameover); bug do non-determinism.
- **Gap**: Durable Execution 1.0 chỉ cho backend workflow.
- **Proposal**: `RenderReplay` — record input timeline + seed → replay → assert pixel-stable.
  Mượn phân loại idempotency (exactly-once) cho asset generation.
- **Maps-to**: M10-P2 / TASK-066 (Durable Execution).

### R4 — Capability-first cho Asset/Game tooling
- **Evidence**: `generate2dsprite.py` là script rời, không nằm registry; skill tạo tay.
- **Gap**: Capability Registry (M1) chỉ discover tools backend (Python/Docker/REST/MCP/Shell/Git).
- **Proposal**: Thêm `kind=asset` capability type; wrap script sinh sprite/map/audio thành
  `CapabilityManifest` để Orchestrator route offline-first (Rule Engine/Matcher, không rớt Planner).
- **Maps-to**: M1 (Capability Registry).

### R5 — SkillDistiller tool/agent
- **Evidence**: TASK-080 "bring repo ngoài về skill package" làm thủ công (manifest + SKILL.md + catalog).
- **Gap**: Ecosystem (M8) có Plugin Runtime/Registry nhưng không có tool tự distill.
- **Proposal**: `SkillDistiller` — input repo URL + license → tự sinh SkillManifest conform +
  SKILL.md + catalog entry, tự chạy critique×2 gate. Meta-learning cho ecosystem.
- **Maps-to**: M8 (Ecosystem / Registry / DevKit).

### R6 — Creative/Game domain trong Decision Pipeline
- **Evidence**: "build a game" / "generate pixel art" không có workflow; scaffold ad-hoc.
- **Gap**: 4 tầng (Normalizer→Rule→Matcher→Planner)建模 backend/runtime, không có domain creative.
- **Proposal**: Thêm workflow domain `creative`/`frontend` vào Workflow Matcher → route "build game"
  tới chuỗi skill+capability xác định (offline-first), giảm lệ thuộc Planner LLM.
- **Maps-to**: Orchestrator Decision Pipeline (PLAN.md §AIOS Orchestrator).

### R7 — Static-site / Artifact Deploy capability
- **Evidence**: `pages.yml` sửa tay (pin Node 20, build, `rm node_modules` trước upload).
- **Gap**: CLI `aiagent doctor`/`conformance` first-class (M10-P4) nhưng không có deploy.
- **Proposal**: `aiagent deploy --static <dir>` (artifact → GitHub Pages / static host) làm runtime
  service hoặc CLI command tái dùng.
- **Maps-to**: M3 (Dashboard/Extension) + M10-P4 (DX).

### R8 — Vendor Integrity verification
- **Evidence**: TASK-081 AC-16 verify thủ công SHA256 vendor bundle byte-identical.
- **Gap**: `security-check` (M10) chưa cover third-party bundle hash.
- **Proposal**: Thêm `VendorIntegrity` vào `aiagent security-check` — tự verify hash của pinned
  bundles; freeze thành invariant.
- **Maps-to**: M10-P3 / TASK-070 (Security Baseline).

### R9 — AIOS Asset Pipeline Contract
- **Evidence**: agent-sprite-forge dùng chroma #FF00FF, tách layer — nhưng chưa thành chuẩn.
- **Gap**: 10 contract frozen (M10) không có contract cho asset generation.
- **Proposal**: Thêm `AssetPipeline` contract (sprite/map/audio) — output deterministic (RGBA,
  0 magenta), mọi asset skill phải conform; đi cùng `aiagent contract-check`.
- **Maps-to**: M10-P1 / TASK-064 (Contract 1.0).

---

## 4. M11 Roadmap đề xuất

```
M11: AIOS Creative / Asset / UI Engineering
├─ P1 Observability      R1 (VisualRegressionProbe) + R2 (INV-035 fail-closed)
├─ P2 Determinism        R3 (RenderReplay)
├─ P3 Capability/Eco     R4 (asset capability) + R5 (SkillDistiller) + R9 (Asset contract)
└─ P4 Pipeline/DX        R6 (creative domain) + R7 (deploy) + R8 (vendor integrity)
```

**Thứ tự ưu tiên**: R2 → R1 → R8 → R9 → R4 → R3 → R6 → R5 → R7
(Lý do: R2/R1 khắc phụcilable test blind spot ngay; R8/R9 mở rộng contract/security sẵn có;
R4/R3 nền tảng capability/determinism; R6/R5/R7 mở rộng ecosystem/DX.)

---

## 5. Open Questions

1. R2 (INV-035) có nên áp dụng retroactive cho TASK-077..081 đã merge không, hay chỉ cho PR mới?
2. R1 pixel-diff metric: ngưỡng "delta acceptable" bao nhiêu (tham số hóa qua SLO hay cố định)?
3. R5 SkillDistiller có nên chạy qua `agent` tool hay là CLI `aiagent skill distill <url>`?
4. R7 deploy: GitHub Pages only, hay hỗ trợ S3/Netlify/static host khác?

---

## 6. Ghi chú tuân thủ

- Đề xuất này **không vi phạm INV-001..034** — toàn bộ là mở rộng additive lên M10.
- Nếu được chấp nhận → tạo `TASK-082` (M11-P1: R1+R2) theo hard-gate chuẩn
  (plan → spec → critique×2 → tasks → review → implement → test → evaluate).
- Hiện tại file này là **tài liệu tham khảo**, chưa commit vào luồng task.
