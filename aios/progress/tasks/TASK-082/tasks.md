# TASK-082 — Tasks breakdown (checklist)

## Khảo sát
- [x] K1. `orchestrator/workflow_matcher.py` — match() 3 bước (macro/full/token), WorkflowMatch dataclass
- [x] K2. `security/checks.py` — SecurityChecks 11 checks + SecurityContext(settings), SecurityChecker.run() fail-closed (TASK-078)
- [x] K3. `config.py` — Settings extra=forbid, chưa có security section; `_yaml_extra_keys_guard`
- [x] K4. TASK-081 `rendering/matcher.py` CreativeMatcher + `rendering/asset.py` AssetSpec

## Implement R6 — Creative Domain
- [ ] I1. `workflow_matcher.py`: thêm `creative_matcher: Any | None = None` param + bước (0) creative pre-route (trigger keywords list, return `WorkflowMatch("creative:asset:<cap_id>", "creative", 0.85)`; None → fallthrough)
- [ ] I2. Workflow library: register 2 workflow creative (`creative/game_scaffold`, `creative/sprite_generate`) — WorkflowDefinition hợp lệ + MockCompiler pass

## Implement R8 — Vendor Integrity
- [ ] I3. `config.py`: `SecuritySettings` (vendor_bundles: dict[str,str] = {}) + `security: SecuritySettings` vào Settings
- [ ] I4. `config.yaml`: thêm `security:` section rỗng
- [ ] I5. `security/checks.py`: `VendorIntegrity` contract + check thứ 12 `vendor_integrity` (đọc file + SHA256 so sánh; không config → PASS; mismatch/file thiếu → FAIL HIGH)

## Implement R12 — Reference-Asset
- [ ] I6. `rendering/reference.py`: `ReferenceDescription` (pydantic — scene/objects/style/palette/raw_text, validator lowercase+dedup) + `MockVisionAnalyzer` (seed từ sha256 file) + `ReferenceAssetUnderstanding.ingest()` (check tồn tại → AssetError fail-closed; merge params an toàn)
- [ ] I7. CLI: `aiagent reference describe <image>` (mock) — kiểm tra không trùng subcommand

## Test
- [ ] T1. AC1/AC2/AC3 R6 (creative match + regression backend + workflow register compile)
- [ ] T2. AC4/AC5/AC6 R8 (hash khớp PASS / mismatch FAIL / thiếu file FAIL / không config PASS + CLI)
- [ ] T3. AC7/AC8/AC9 R12 (description đủ trường / deterministic / fail-closed + merge params)
- [ ] T4. AC10 CLI reference describe thật
- [ ] T5. AC11 full suite — chú ý regression test_workflow* (library +2 workflow — C2-06)

## Evaluate
- [ ] E1. Đối chiếu 11 AC + health check phase P3b/c/d
- [ ] E2. LOG.md + PROGRESS.md + commit
