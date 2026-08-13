# Critique vòng 2 — TASK-015 (Skills + Sandbox)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 2) | Spec: `spec.md` (đã sửa v1)

## Đánh giá chung

**2.5/5 — chưa đạt, cần sửa trước khi implement.** 5/19 resolution v1 chưa áp vào spec (C1-03 optimistic, C1-04 semver một phần, C1-05 dependent check, C1-08, C1-13) + 7 áp một phần. 8 vấn đề mới (1 P2 + 7 P3). Bảng transitions T4/T5 (C1-01) đã sửa ĐÚNG.

## Mục A — Verify 19 resolutions v1

7 ĐÚNG (C1-01/02/07/14/17/18/19) · 7 THIẾU · 5 SAI (C1-03, C1-04, C1-05, C1-08, C1-13).

## Mục B — Vấn đề mới (8) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C2-01 | P2 | `from aios_core import semver` trần → scan trả "aios_core" ∉ allow-set → FAIL | Quy ước "chỉ dotted import: `from ..semver import compare`; CẤM `from aios_core import <mod>` trần" |
| C2-02 | P3 | AC3 gộp nhầm upgraded→rollback (hợp lệ T9) | Bỏ khỏi AC3 invalid cases (AC9 cover "no history") |
| C2-03 | P3 | upgrade new_version invalid → ValueError trần | Wrap → `SkillError("invalid new version")` + test |
| C2-04 | P3 | release không ownership-scoped | Ghi giới hạn v1: acquire→execute→release cùng thread; không token |
| C2-05 | P3 | Sandbox.warm comment lệch semantic | Sửa comment "True = tái sử dụng từ pool; set khi acquire — monotonic" |
| C2-06 | P3 | Constraint `id@>=X` grammar chưa đóng | Chốt: v1 chỉ `>=`; parse fail → `SkillError("invalid dependency constraint")` |
| C2-07 | P3 | Fixtures metadata datetime → determinism xuyên run | Fixtures không metadata (hoặc cố định) — resolve trả instance lưu sẵn |
| C2-08 | P3 | SKILLS_DIR/SANDBOX_DIR chưa tồn tại trong test_architecture.py | Thêm 2 hằng số + chuyển bullets test plan sang mục "Cập nhật test_architecture.py" |

## Kết luận

- [x] **Cần sửa trước khi implement**: C1-04 (P1 — dọn mâu thuẫn semver toàn spec), C1-05 (P1 — dependent check), C1-03 (P2 — optimistic), C1-08/C1-13/C1-12/C1-11 (P3) + C2-01..08.
- **Trạng thái: RESOLVED 27/27** (spec.md đã cập nhật — xem commit kèm).
