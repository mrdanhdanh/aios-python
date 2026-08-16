# TASK-082 — M11-P3b/c/d: R6 Creative Domain + R8 Vendor Integrity + R12 Reference-Asset

> **Milestone**: M11-P3b/c/d (Issue #4)
> **Ngày**: 2026-08-16 | **Owner**: AIOS Orchestrator
> **Tham chiếu**: proposal M11 §R6 + §R8 + §R12 + §7 (P3b/c/d), PLAN.md §M11

## 1. Mục tiêu

- **R6**: Thêm domain `creative`/`frontend` vào Decision Pipeline (Workflow Matcher) —
  route offline-first "build a game"/"generate pixel art" tới workflow/capability creative.
- **R8**: Vendor Integrity — thêm vào `aiagent security-check`: verify hash pinned vendor
  bundles (byte-identical); độc lập Security Baseline.
- **R12**: Reference-Asset Understanding — ingest reference image → structured description
  (scene/object/style/palette) → feed AssetPipeline (mở rộng R6).

## 2. Phạm vi (IN)

### R6 — Creative Domain (P3b)
1. `orchestrator/workflow_matcher.py`: thêm 1 bước **creative pre-route** (bước 0 — TRƯỚC template macro):
   - Thứ tự match: **(0) creative pre-route → (1) macro → (2) full → (3) token**
   - Constructor: `creative_matcher: Any | None = None` — None → bỏ qua pre-route (hành vi cũ 100%)
   - Từ khóa trigger (lower): `creative, game, sprite, pixel art, tileset, map, audio,
     animation, ui asset, phaser, canvas` → gọi `CreativeMatcher.suggest(request)`
   - Nếu matcher trả kết quả → `WorkflowMatch("creative:asset:<cap_id>", "creative", 0.85)`
     (workflow_name mang prefix `creative:` — không đụng library)
   - Không match → fallthrough các bước cũ (không đổi hành vi hiện có)
2. Workflow library: thêm 2 workflow creative mặc định (v1 — definition đơn giản, MockCompiler pass):
   `creative/game_scaffold` + `creative/sprite_generate` (đăng ký qua `WorkflowLibrary.register`)

### R8 — Vendor Integrity (P3c)
3. `security/checks.py`: thêm check thứ 12 `vendor_integrity`:
   - `VendorIntegrity` contract: `{bundle: str (path), pinned_sha256: str}` — verify
     byte-identical (đọc file + SHA256 so sánh)
   - Default: không có config → PASS (không có vendor bundle pinned — không fail oan)
   - Có config + mismatch → FAIL (severity HIGH); file thiếu → FAIL
   - CLI `aiagent security-check` hiển thị check mới
4. Config: `SecuritySettings` (extra=forbid, `vendor_bundles: dict[str, str] = {}` — path → pinned sha256)
   + `security: SecuritySettings` vào `Settings` + `security:` vào `config.yaml` (rỗng) —
   đồng bộ cả 2 nơi (extra=forbid + `_yaml_extra_keys_guard` sẽ fail nếu thiếu)

### R12 — Reference-Asset Understanding (P3d)
5. `rendering/reference.py` — `ReferenceAssetUnderstanding`:
   - `ingest(image_path: str) -> ReferenceDescription` — **vision model injectable**
     (default: `MockVisionAnalyzer` — seed từ sha256(file) → structured description
     deterministic, cùng ảnh → cùng kết quả)
   - `ReferenceDescription` (pydantic extra=forbid): `scene: str`, `objects: list[str]`
     (dedup + sort), `style: str`, `palette: list[str]` (hex lowercase), `raw_text: str = ""`
   - Output → `AssetSpec` params: `params = {**existing, "reference": desc.model_dump()}`
     (merge an toàn, không ghi đè params có sẵn)
   - Fail-closed: ảnh không tồn tại/không đọc được → `AssetError` (ERROR, không PASS — INV-035)
6. CLI `aiagent reference describe <image>` — mock analyzer → description

## 3. OUT of scope

- Vision model thật (OpenAI/CLIP) — analyzer injectable, default mock
- R5 SkillDistiller (P4), R7 Static Deploy (P4)
- Sửa game code

## 4. Input / Output

- **Input**: request creative (R6), vendor config (R8), reference image path (R12)
- **Output**: workflow matcher creative pre-route + 2 workflow creative + vendor check +
  ReferenceAssetUnderstanding + CLI + tests

## 5. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm tra |
|---|----|---------------|
| AC1 | R6: `WorkflowMatcher.match("build a game")` → WorkflowMatch `creative:*` (confidence 0.85) | unit test |
| AC2 | R6: request backend thường (`run workflow`) KHÔNG đổi hành vi (không creative match) | unit test regression |
| AC3 | R6: 2 workflow creative đăng ký trong library (`creative/game_scaffold`, `creative/sprite_generate`) | unit test |
| AC4 | R8: `VendorIntegrity.verify()` — hash khớp → PASS; mismatch → FAIL; file thiếu → FAIL | unit test |
| AC5 | R8: SecurityChecks thêm check `vendor_integrity` (12 checks); không config → PASS (không fail oan) | unit test + CLI |
| AC6 | R8: config `vendor_bundles` sai hash → FAIL (HIGH) + `aiagent security-check` hiển thị | unit test + CLI |
| AC7 | R12: `ReferenceAssetUnderstanding.ingest()` → `ReferenceDescription` đủ scene/objects/style/palette | unit test |
| AC8 | R12: mock analyzer deterministic (cùng ảnh → cùng description); output feed được AssetSpec params | unit test |
| AC9 | R12: ảnh không đọc được → AssetError (fail-closed) | unit test |
| AC10 | CLI `aiagent reference describe` chạy thật (mock) | chạy CLI |
| AC11 | Full suite xanh | pytest |

## 6. Nguồn tham khảo

- Proposal M11 §R6/R8/R12 + §7 (P3b/c/d) + §1b (bằng chứng: vendor-hash reimplement trong test — gap R8; 8 reference images vision model — gap R12)
- TASK-081 `rendering/matcher.py` (CreativeMatcher), `rendering/asset.py` (AssetSpec)
- M10 `security/checks.py` (11 checks), `orchestrator/workflow_matcher.py`
