# TASK-081 — Critique vòng 1 (spec)

> **Critic**: AIOS Orchestrator (vòng phản biện độc lập)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved

## P1 — Phải sửa

### C1-01. `AssetCapability` chưa định nghĩa schema — registry register cái gì?
→ **Resolve**: `AssetCapability` (pydantic extra=forbid): `id: str`, `name: str`,
`description: str`, `kinds: list[str]`, `pipeline: AssetPipeline` (Protocol — duck-typed),
`version: str = "1.0"`, `source: str = ""` (path skill/repo). Registry lưu `AssetCapability`
object (không serialize pipeline).

### C1-02. `CreativeMatcher.match` scoring thế nào — deterministic ra sao?
→ **Resolve**: scoring deterministic không LLM: `score = kind_match*10 (request kind ∈
capability kinds) + keyword_hit (mỗi từ request xuất hiện trong description/name = 1) +
name_prefix_hit (request bắt đầu bằng tên capability = 3)`. Trả sorted giảm dần + `reason`
giải thích. Không dùng model/ngẫu nhiên.

### C1-03. Registry "wire" skill sprite-forge — đọc từ đâu khi repo không có file manifest?
→ **Resolve**: `default_asset_capabilities()` — khảo sát `skills/` trong repo lúc khởi tạo;
nếu `skills/agent-sprite-forge/` tồn tại (check path) → register capability
`agent-sprite-forge` (kinds: sprite, animation); nếu không → bỏ qua (registry vẫn hoạt động
với capabilities thủ công). Không hard-fail khi skill thiếu.

## P2 — Nên sửa

### C2-01. `produce` fail-closed: spec sai kind → error gì?
→ **Resolve**: `AssetError` (RuntimeError con) — pipeline không hỗ trợ kind → raise AssetError;
caller bắt → outcome ERROR (không PASS). Ghi rõ.

### C2-02. Matcher trả gì khi không match?
→ **Resolve**: list rỗng + `suggested: []` — không raise; CLI in "no match".

### C2-03. Registry có cần persist (SQLite)?
→ **Resolve**: P3 in-memory (singleton) — persist để P4/R5 SkillDistiller khi cần đăng ký nhiều.
Ghi vào tasks.md.

## P3 — Ghi nhận

### C3-01. Mirror M1 CapabilityRegistry?
→ Resolve: tách riêng (kind=asset chuyên biệt) nhưng tái dùng tư duy — không import M1 (tránh
ràng buộc). Ghi chú evaluation.

### C3-02. Có cần arch allow-list test cho rendering/asset.py?
→ Resolve: có — thêm vào test_rendering import allow-list (asset/registry/matcher không import
agents/enterprise).

## Kết luận
Spec khả thi sau resolve C1-01..03 + C2-01..03 → chuyển vòng 2.
