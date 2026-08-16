# TASK-081 — Evaluation (M11-P3: R9 AssetPipeline + R4 Registry + R11 Matcher)

> Ngày: 2026-08-16 | Task: TASK-081 | Milestone: M11-P3 (Issue #4)

## Đối chiếu tiêu chí chấp nhận

| AC | Mô tả | Kết quả | Bằng chứng |
|----|-------|---------|------------|
| AC1 | AssetSpec/Output contract (6 kinds, extra=forbid) | ✅ | 2 tests |
| AC2 | Pipeline produce sha256+size; raise → AssetError | ✅ | 2 tests |
| AC3 | Registry register/discover/list/get | ✅ | 2 tests |
| AC4 | 2 capability cùng kind → discover cả 2 | ✅ | `test_registry_same_kind_multiple` |
| AC5 | Matcher sprite đứng đầu | ✅ | `test_matcher_kind_match_priority` |
| AC6 | suggest gợi ý capability tồn tại | ✅ | `test_matcher_suggest_reuse` |
| AC7 | Registry wire skill thật | ✅ | manifest.json mang từ operation/test-A + CLI list 1 capability |
| AC8 | Produce idempotency fail-closed | ✅ | 2 tests + CLI audio fail |
| AC9 | CLI asset list/discover/match/produce thật | ✅ | chạy thật (list/match/produce OK + audio FAIL) |
| AC10 | Full suite xanh | ✅ | **2018 passed / 0 failed** |

**10/10 AC — TASK-081 DONE** ✅

## Đánh giá hệ thống (sau P3)

- **Asset Capability Architecture đóng gap "reuse vs reimplement"**: `CreativeMatcher` route
  "generate sprite" → `agent-sprite-forge` (score 14, deterministic offline) — worker giờ
  biết capability tồn tại thay vì tự viết PNG encoder (đúng bằng chứng proposal §1b).
- **Registry wire skill thật** (manifest từ operation/test-A): `skills/agent-sprite-forge/`
  là capability kind=asset đầu tiên — đúng kiến trúc `Manifest → Registry → Matcher → Runtime`.
- **Fail-closed giữ vững**: produce kind không hỗ trợ → AssetError → ERROR (không PASS);
  idempotency không khai báo → at-most-once (M10 pattern).
- **Deterministic-first**: spec mang seed; pipeline output sha256 từ spec canonical — cùng
  spec → cùng output (nền cho golden-master P2/R1).

## Bài học

1. **Manifest thực tế ≠ schema giả định**: manifest skill có `capabilities` (không `kinds`) —
  phải map (sprite-generation→sprite). Khảo sát dữ liệu thật trước khi thiết kế parser.
2. **Path resolution dễ sai**: parents index tính từ __file__ phải test với cwd khác nhau
  (bug parents[5] vs parents[4] chỉ lộ khi chạy CLI thật, test tmp_path không bắt được).
3. **Pydantic v2 khác v1**: sort_keys không nằm trong model_dump* — chuyển json.dumps.

## Đề xuất (ghi nhận)

1. P3b (TASK-082): R6 Creative Domain — tích hợp CreativeMatcher vào Orchestrator Workflow Matcher
2. P4 (TASK-083): R5 SkillDistiller — persist registry + quét skills/ tự động
3. Skill scripts thật (generate2dsprite.py) → wire pipeline thật khi merge operation/test-A
   (P4/R5 hoặc đợt riêng)

## Checklist đóng

- [x] spec + critique-1 (resolved) + critique-2 (resolved) + tasks + review (APPROVED)
- [x] implementation/ (asset/registry/matcher + CLI + manifest + 15 tests)
- [x] test.md + evaluation.md
- [x] LOG.md + PROGRESS.md + commit
