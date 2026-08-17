# TASK-088 — M12-P4: Docs & ADR (C5) — SPEC v3

> Milestone: M12 AIOS 1.1 Compatibility (Issue #7, nhánh `feature/ISSUE-7-aios-1-1-compatibility`)
> Nâng cấp: C5 — ADR-0007 (compatibility policy) + migration guide 1.0→1.1 + PLAN §M12 docs
> Dependency: C1–C4 (TASK-084..087 ✅) → C5
> v3 = tích hợp resolution critique-1 (5/5) + critique-2 (4/4)

## 1. Mục tiêu

1. **ADR-0007 — Compatibility & Migration Policy** (format chuẩn ADR-0006): version policy, matrix, migration, backward suite, conformance gate — phản ánh ĐÚNG code TASK-084..087.
2. **Migration Guide 1.0→1.1**: hướng dẫn nâng cấp thật — 5 bước + lệnh CLI thật + lưu ý (stub vs --input, idempotent, backup, config skip matrix).
3. **Cập nhật PLAN.md §M12** (tasks done) + README link — KHÔNG đụng §M13/M14/M15 (session khác).

## 2. Phạm vi

**In:**
- `docs/adr/0007-compatibility-migration-policy.md` (tạo mới — format ADR-0006)
- `docs/guides/migration-1.0-to-1.1.md` (tạo thư mục `docs/guides/`)
- `docs/PLAN.md` §M12 — header DONE + bảng 5 task done (chỉ trong §M12 — C1-04)
- `docs/README.md` — link guide + ADR-0007 (C1-05)

**Out:** không

## 3. Thiết kế (nội dung chi tiết đã chốt trong critique-1/2)

### 3.1 ADR-0007 — các mục chính (RESOLVED C1-01, C2-01, C2-02)

- Status accepted / Date 2026-08-16 / Extends ADR-0005, ADR-0006
- **Version policy**: semver; `0.1.0` = dev (lịch sử — KHÔNG thuộc đường nâng cấp, `check_upgrade("0.1.0","1.1.0")` breaking theo Rule 4); `1.0.0` = mốc release M10; `1.1.0` = M12 (hiện tại); đường hỗ trợ chính thức `1.0.0 → 1.1.0` (minor, backward-compatible)
- **Compatibility Matrix** (`upgrade/compatibility.py`): registry min/max per component; fail-closed (kind/id lạ → error; version rác → error; ngoài range → error; version lệch entry → warning)
- **Migration** (`upgrade/migration_110.py`): plan chuẩn per component (migration_id gồm component_id — idempotent per component); backup trước apply; journal; matrix pre/post; rollback guard; config SKIP matrix (không version)
- **Backward Suite** (`upgrade/backward_compat.py`): 9 check cũ→mới, fail-closed bắt BaseException
- **Conformance**: area `compatibility` + `gate_g_compatibility` → 11 areas/20 GS/7 gates → **"AIOS 1.1 READY"**; gate_g vi phạm = release blocker (C2-01)
- **Parse-only mở rộng**: precedent `AiosRange.compatible` (TASK-086) — behavior check min/max KHÔNG đổi (C2-02)
- Consequences: CLI map + quy trình bump version tương lai

### 3.2 Migration Guide — 5 bước (RESOLVED C1-02, C1-03, C2-03, C2-04)

1. Kiểm tra tương thích: `aiagent compat verify` (9/9 — fail-closed: 1 fail = exit 1, dừng) + `aiagent compat list`
2. Dry-run: `aiagent migrate <kind> 1.0.0 1.1.0 --dry-run --journal <path>` (không side effect)
3. Apply: `aiagent migrate <kind> 1.0.0 1.1.0 --apply --journal <path>` — **cảnh báo: mặc định dùng STUB (demo/demo_flow/agent) — dữ liệu thật phải `--input file.json`** (C1-02)
4. Rollback (nếu cần): backup_id từ output; journal status; rollback qua migration_110 (ghi chú)
5. Verify: `aiagent conformance` → "AIOS 1.1 READY" (11 areas/7 gates)
- **Lưu ý** (C1-03): idempotent per component (apply lần 2 cùng component → "đã applied"); `--journal` đổi → backup db đổi theo (`<journal>.replace("migrations.db","backups.db")`); config SKIP matrix
- **Điều gì thay đổi trên dữ liệu** (C2-04): plugin → thêm `aios.compatible` (append "1.1.0"); workflow/contract → bump version 1.1.0; config → thêm marker `migration`

### 3.3 PLAN.md §M12 — chỉ sửa trong §M12 (C1-04): header + bảng 5 task done ✅

### 3.4 README — link guide + ADR-0007 (C1-05)

## 4. Input / Output

Docs mới + cập nhật — không API/CLI mới.

## 5. Tiêu chí chấp nhận (AC)

- [ ] AC1: `docs/adr/0007-compatibility-migration-policy.md` tồn tại, format khớp ADR-0006 (Status/Date/Extends/Context/Decision/Consequences)
- [ ] AC2: ADR phản ánh ĐÚNG code: matrix fail-closed, migration_id per component, verify 9/9 fail-closed, gate_g release blocker, "AIOS 1.1 READY", AiosRange.compatible parse-only (C2-01/02)
- [ ] AC3: Guide tồn tại — 5 bước + lệnh CLI thật + lưu ý stub vs --input + idempotent + backup path + config skip matrix
- [ ] AC4: MỌI lệnh CLI trong guide chạy thật exit 0 (compat verify / migrate dry-run+apply / conformance — journal tmp)
- [ ] AC5: PLAN.md §M12: header DONE + 5 task done ✅; §M13/M14/M15 KHÔNG đổi
- [ ] AC6: README link guide + ADR-0007
- [ ] AC7: docs khác nguyên vẹn (architecture-v3, ADR 0001..0006, PLAN §M10/M11)
- [ ] AC8: validate cấu trúc: script kiểm tra ADR headers + file guide tồn tại + link PLAN
- [ ] AC9: full suite pytest ≥ 2118 PASS / 0 FAIL (không regression)
- [ ] AC10: commit sạch; KHÔNG push

## 6. Rủi ro & giả định

| Rủi ro | Cách xử lý |
|--------|-----------|
| ADR format lệch chuẩn | Bám sát ADR-0006 (đọc trước khi viết) |
| Lệnh CLI guide sai | Chạy thử từng lệnh thật trước khi ghi (AC4) |
| PLAN §M12 bị session khác sửa | Chỉ sửa trong §M12; diff trước commit |

## 7. Ghi chú triển khai

1. Đọc ADR-0006 (format) + PLAN §M12 hiện trạng.
2. Viết ADR-0007 + `docs/guides/migration-1.0-to-1.1.md`.
3. Cập nhật PLAN §M12 (header + tasks done) + README.
4. Chạy thử từng lệnh CLI trong guide (journal tmp).
5. Validate cấu trúc + full suite.
6. Đóng 8-file hard gate; LOG/PROGRESS; commit — KHÔNG push.
