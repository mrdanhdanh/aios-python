# Critique vòng 1 — TASK-015 (Skills lifecycle + Skill Manager + Sandbox Pool)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 1) | Spec: `spec.md`

## Đánh giá chung

**3/5 — cần sửa trước khi implement.** Spec chi tiết, 18 AC test được, bài học áp dụng đúng chỗ. Nhưng 1 mâu thuẫn nội bộ NGHIÊM TRỌNG trong bảng transitions (C1-01 — lõi của task) + 4 Major + 14 Minor.

## Vấn đề (19) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C1-01 | Critical | Bảng transitions T4/T5 mâu thuẫn rationale (c)/(d): `unloaded→enable` có trong bảng nhưng (c) cấm; `disable` từ upgraded/rolled_back khai báo nhưng không có trong bảng | Bỏ `unloaded` khỏi T4 (enable); thêm `upgraded, rolled_back` vào T5 (disable); AC3 thêm case `unloaded→enable` → SkillStateError + `upgraded→disable` → disabled |
| C1-02 | Major | "Enforce 2 tầng" phát biểu quá mức: CHECK chỉ enforce domain, không enforce transition | Sửa wording "tầng 2 (CHECK) enforce domain; transition enforce ở code" + test SQL chèn trực tiếp resolved→enabled → DB CHẤP NHẬN (tài liệu hóa giới hạn) |
| C1-03 | Major | TOCTOU race 2 manager cùng DB (check state → UPDATE không nguyên tử) | **Optimistic concurrency: UPDATE WHERE state=expected_old; rowcount==0 → SkillError("state changed concurrently")** |
| C1-04 | Major | Cấm `aios_core.semver` vô nghĩa (semver chỉ import metadata — đã được phép) → ép helper kém chính xác (pre-release) | **Thêm `aios_core.semver` vào allow-list skills/** + dùng `parse_version/compare` chính thức; sandbox/ vẫn empty-set |
| C1-05 | Major | rollback/remove không re-validate dependents → constraint vỡ âm thầm | Trong rollback/remove: quét registry tìm dependent có dep khớp id → nếu constraint fail → **chặn SkillError("dependent broken: ...")** + AC test |
| C1-06 | Minor | upgrade từ enabled → mất active âm thầm | Ghi rõ "upgrade từ enabled/reloaded → state=upgraded, KHÔNG còn active — phải enable lại" + test is_active()==False |
| C1-07 | Minor | AC3 case "upgraded+history rỗng" bất khả thi qua API | Thay: `installed→rollback` invalid + `rolled_back→rollback` khi history rỗng → "no history" |
| C1-08 | Minor | Message "dependency not installed" sai ngữ cảnh khi dep removed | Phân nhánh: removed → "dependency removed: X"; khác → "dependency not installed: X" |
| C1-09 | Minor | Atomicity manifest_json vs cột version + mode serialization | 1 UPDATE statement (state+version+manifest_json+history_json+updated_at) + `model_dump(mode="json")` + test manifest.version == cột version |
| C1-10 | Minor | `Sandbox.warm` monotonic mơ hồ | Ghi rõ "warm=True = tái sử dụng từ pool (không cold-start lần này); set khi acquire, monotonic" |
| C1-11 | Minor | Pool không normalize language → acquire("Python") không reuse | Normalize `language.strip().lower()` đầu acquire/release + test "Python" reuse |
| C1-12 | Minor | `stats()` API chỉ phục vụ test; AC16 wording lủng củng | Bỏ stats() public → `_stats_for_test()`; sửa AC16: 2 idle, 1 cũ → evict 1 |
| C1-13 | Minor | `SkillManager.register ≡ get` trùng nghĩa | Bỏ `register` khỏi manager (registry read-through phục vụ) |
| C1-14 | Minor | Corrupt history_json — tầng nào raise? | Corrupt → SkillError ở MỌI đường đọc (fail-fast); chỉ id không tồn tại → None |
| C1-15 | Minor | Fixtures metadata datetime default → determinism mong manh | Fixtures metadata cố định/None; resolve trả instance lưu sẵn (identity) |
| C1-16 | Minor | `build_skill_manager` db_path mặc định phụ thuộc cwd | Factory KHÔNG có default path — bắt buộc truyền db_path (fail-fast) |
| C1-17 | Minor | CHECK source hardcode | Sinh CHECK từ `_ALL_STATES` + `SkillSource` members (1 hằng số) |
| C1-18 | Minor | validate one-shot chưa nêu rõ | Ghi rõ "validate là one-shot (validated→validated cấm); re-validate → M4" |
| C1-19 | Minor | Error type bất đối xứng 3 sources chưa có rationale | Ghi rationale: ref rỗng = input invalid → ValueError; ref lạ = not found → SkillError |

## Kết luận

- [x] **Cần sửa trước khi implement** — C1-01 (Critical) + 4 Major + 14 Minor (resolve cùng đợt).
- **Trạng thái: RESOLVED 19/19** (spec.md đã cập nhật).
