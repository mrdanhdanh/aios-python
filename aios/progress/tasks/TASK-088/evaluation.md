# TASK-088 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-16 | Task: M12-P4 C5 Docs & ADR (Issue #7)

## Đối chiếu 10 AC

| AC | Tiêu chí | Kết quả | Bằng chứng |
|----|----------|---------|-----------|
| AC1 | ADR-0007 tồn tại, format khớp ADR-0006 | ✅ | `docs/adr/0007-compatibility-migration-policy.md` + validate (6 headers) |
| AC2 | ADR đúng code: matrix fail-closed, migration per component, verify 9/9, gate_g blocker, AIOS 1.1 READY, AiosRange parse-only | ✅ | validate 11 từ khóa + nội dung viết từ code thật TASK-084..087 |
| AC3 | Guide 5 bước + lệnh thật + lưu ý stub/--input/idempotent/backup/config skip | ✅ | `docs/guides/migration-1.0-to-1.1.md` + validate |
| AC4 | MỌI lệnh CLI trong guide exit 0 | ✅ | CLI thật: verify 9/9 + migrate config/plugin/contract + conformance READY |
| AC5 | PLAN §M12 header DONE + 5 task done; M13/M14 KHÔNG đổi | ✅ | PLAN §M12 updated; §M13/M14/M15 untouched (chỉ sửa trong §M12) |
| AC6 | README link guide + ADR-0007 | ✅ | README ghi chú nâng cấp + link |
| AC7 | Docs khác nguyên vẹn | ✅ | architecture-v3 + ADR 0001-0006 + validate |
| AC8 | Validate cấu trúc script | ✅ | `validate_task088.py` PASS — 0 failures |
| AC9 | Full suite ≥ 2118, 0 regression | ✅ | **2118 PASS / 0 FAIL** |
| AC10 | Commit sạch; không push | ✅ | commit + working tree clean (chưa push) |

**10/10 AC ĐẠT** ✅

## Chất lượng

- ADR-0007 là nguồn chính thức cho: version policy (0.1.0/1.0.0/1.1.0 + đường nâng cấp), matrix fail-closed, migration per component, backward suite, conformance 11/7, parse-only precedent — mọi chi tiết khớp code thật
- Guide thực dụng: 5 bước + bảng "điều gì thay đổi trên dữ liệu" + cảnh báo stub vs --input (quan trọng — tránh migrate nhầm dữ liệu mẫu)
- PLAN §M12 đóng gọn: DONE + 5/5 task (không đụng M13/M14/M15 của session khác)

## Bài học

1. Docs task vẫn cần đối chiếu code thật từng câu chữ — ADR sai 1 chi tiết = policy sai.
2. Cảnh báo stub vs `--input` trong guide là bắt buộc (CLI migrate mặc định dùng dữ liệu mẫu).
3. Giới hạn sửa trong phạm vi section (PLAN §M12) tránh xung đột với planning song song.

## Kết luận

**TASK-088 DONE — 10/10 AC — M12 HOÀN TẤT 5/5 TASK (TASK-084..088)** — AIOS 1.1 Compatibility đầy đủ: version 1.1.0 + matrix + migration + backward suite + conformance 11 areas/7 gates + docs/ADR. Chờ user: push + merge PR #8 → verify → promotion master.
