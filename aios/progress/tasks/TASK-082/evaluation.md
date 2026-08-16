# TASK-082 — Evaluation (M11-P3b/c/d: R6 + R8 + R12)

> **Ngày**: 2026-08-16 | **Trạng thái**: **DONE** — 11/11 AC đạt

## Đối chiếu AC

| # | AC | Kết quả | Bằng chứng |
|---|----|---------|------------|
| AC1 | R6: `WorkflowMatcher.match("build a game")` → `creative:*` confidence 0.85 | ✅ | test_r6_creative_pre_route_build_game |
| AC2 | R6: request backend thường không đổi hành vi | ✅ | test_r6_no_creative_matcher_falls_through + backend_request_unchanged |
| AC3 | R6: 2 workflow creative đăng ký + compile | ✅ | test_r6_workflows_registered_and_compile (MockCompiler pass) |
| AC4 | R8: hash khớp → PASS; mismatch/thiếu → FAIL | ✅ | test_r8_vendor_* (3 tests) |
| AC5 | R8: check thứ 12 + không config → PASS | ✅ | test_r8_twelve_checks_total + security-check CLI |
| AC6 | R8: config sai hash → FAIL HIGH + CLI hiển thị | ✅ | test_r8_vendor_integrity_hash_mismatch_fail + `aiagent security-check` |
| AC7 | R12: ingest → description đủ trường | ✅ | test_r12_ingest_full_description |
| AC8 | R12: deterministic + merge params an toàn | ✅ | test_r12_mock_deterministic + merge_params_no_overwrite |
| AC9 | R12: ảnh thiếu → AssetError fail-closed | ✅ | test_r12_missing_image_fail_closed + CLI exit 1 |
| AC10 | CLI `aiagent reference describe` thật | ✅ | chạy thật (mock vision) |
| AC11 | Full suite xanh | ✅ | **2034 passed / 0 failed** |

## Deliverables

- `orchestrator/workflow_matcher.py` — creative pre-route (bước 0) + CREATIVE_TRIGGERS + CREATIVE_CONFIDENCE 0.85; `creative_matcher=None` → hành vi cũ
- `rendering/workflows.py` — 2 workflow creative (`creative/game_scaffold`, `creative/sprite_generate`) + `register_creative_workflows()`
- `config.py` + `config.yaml` — `SecuritySettings.vendor_bundles` (đồng bộ 2 nơi — extra=forbid)
- `security/checks.py` — check thứ 12 `vendor_integrity` (SHA256 byte-identical, fail-closed)
- `rendering/reference.py` — `ReferenceDescription` + `MockVisionAnalyzer` (seed sha256 file) + `ReferenceAssetUnderstanding` (fail-closed AssetError)
- `workflow/cli.py` — `aiagent reference describe <image>`
- `tests/test_m11_p3bcd.py` (16 tests) + fix `test_security.py` (11→12 items)

## Bài học

1. **Pre-route phải optional** — `creative_matcher=None` giữ 100% hành vi cũ; test fallthrough xác nhận creative workflow vẫn match qua token-search (không chặn).
2. **`suggest()` trả list** (top-3 MatchResult) — pre-route phải lấy `suggestions[0]`, không phải 1 object (bug tiềm ẩn đã bắt khi đọc API).
3. **Settings extra=forbid** — thêm section mới phải đồng bộ `config.py` + `config.yaml`; thiếu 1 trong 2 → load fail toàn bộ.
4. **Test cũ đếm số lượng** (11 items) fail có chủ đích khi thêm check mới — cập nhật test, không né tránh.
5. **Mock vision deterministic qua sha256(file)** — cùng ảnh → cùng description (R12), đủ để test offline mà vẫn meaningful.

## Ghi nhận

- R8 severity HIGH → Gate B (security) fail khi mismatch (fail-closed) — đúng thiết kế, ghi nhận.
- Vision model thật (OpenAI/CLIP) để phase sau — analyzer injectable đã sẵn.
