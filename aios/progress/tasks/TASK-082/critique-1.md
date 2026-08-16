# TASK-082 — Critique vòng 1 (spec)

> **Critic**: AIOS Orchestrator | **Ngày**: 2026-08-16 | **Trạng thái**: resolved

## P1 — Phải sửa

### C1-01. R6 creative pre-route đặt ở đâu trong `match()`? Thứ tự so với template macro?
Spec nói "TRƯỚC template macro" nhưng nếu đặt trước, các workflow creative đăng ký trong library sẽ bị template macro match trước (vì library.list() bao gồm cả creative) → pre-route không bao giờ chạy với confidence 0.85.
→ **Resolve**: pre-route đặt TRƯỚC bước 1 (template macro) như spec nói — đúng, vì pre-route chạy ĐẦU TIÊN. Nhưng phải guard: chỉ gọi CreativeMatcher khi có từ khóa creative (đã có trigger list). Khi matcher trả kết quả → return ngay; không → fallthrough. Ghi rõ thứ tự: (0) creative pre-route → (1) macro → (2) full → (3) token.

### C1-02. R6 cần inject CreativeMatcher vào WorkflowMatcher — constructor đổi, ai gọi?
`WorkflowMatcher.__init__(library)` — thêm param optional `creative_matcher=None` (lazy import nếu None). Không phá caller cũ.
→ **Resolve**: `creative_matcher: Any | None = None` — nếu None, không pre-route (hành vi cũ giữ nguyên 100%). Normalizer/Orchestrator cũ không cần sửa.

### C1-03. R8 `vendor_integrity` — `SecurityChecks` nhận `SecurityContext(settings)`, settings chưa có security section
Settings extra="forbid" + `_yaml_extra_keys_guard` — thêm `security` phải thêm cả Settings field + config.yaml. Nếu không, mọi Settings() load fail.
→ **Resolve**: thêm `SecuritySettings(BaseModel)` (extra=forbid, `vendor_bundles: dict[str,str] = {}`) + `security: SecuritySettings` vào Settings + `security:` vào config.yaml (rỗng). SecurityContext đọc `settings.security.vendor_bundles`.

## P2 — Nên sửa

### C2-01. R12 `ReferenceDescription` palette — chuẩn hex lowercase; objects list dedup
→ Resolve: validator lowercase + dedup, sort objects (deterministic).

### C2-02. R12 fail-closed: `ingest` với ảnh không tồn tại → AssetError (đã có) — nhưng MockVisionAnalyzer cần check file tồn tại trước
→ Resolve: `ReferenceAssetUnderstanding.ingest` check `os.path.exists` trước → raise AssetError("reference image not found: ..."). Mock analyzer giả định file tồn tại.

### C2-03. R6 2 workflow creative cần test compile được (MockCompiler) — workflow library register cần definition hợp lệ
→ Resolve: dùng `WorkflowDefinition` từ YAML dict — test `MockCompiler().compile` pass cho cả 2.

## P3 — Ghi nhận

### C3-01. R8 severity HIGH cho vendor mismatch — đồng bộ Gate B (critical/high fail → fail security area)
→ Resolve: đúng — check HIGH sẽ làm Gate B fail khi có mismatch (fail-closed). Ghi nhận, không sửa gì thêm.

## Kết luận
Spec khả thi sau resolve C1-01..03 + C2-01..03 → vòng 2.
