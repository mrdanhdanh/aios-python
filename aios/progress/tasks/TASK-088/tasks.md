# TASK-088 — Tasks breakdown (checklist)

> Spec v3 (10 AC). Hard gate: spec ✅ + critique-1 (5/5) ✅ + critique-2 (4/4) ✅ + review ✅ (tự review — docs task, format khớp ADR-0006 đã đọc)

## A. ADR-0007
- [ ] A1. Đọc `docs/adr/0006-issue-pr-workflow.md` (format) — làm mẫu
- [ ] A2. Viết `docs/adr/0007-compatibility-migration-policy.md` (Status/Date/Extends/Context/Decision/Consequences) — nội dung theo spec §3.1 (version policy 0.1.0/1.0.0/1.1.0 + matrix fail-closed + migration per component + backward suite + conformance 11/7 → AIOS 1.1 READY + parse-only precedent)

## B. Migration Guide
- [ ] B1. Tạo `docs/guides/` + `migration-1.0-to-1.1.md` — 5 bước (compat verify → dry-run → apply → rollback → conformance) + lệnh CLI thật + lưu ý (stub vs --input, idempotent per component, backup path, config skip matrix) + "điều gì thay đổi trên dữ liệu" per kind

## C. PLAN + README
- [ ] C1. PLAN.md §M12: header IN-PROGRESS → DONE + bảng 5 task done ✅ (CHỈ trong §M12 — không đụng M13/M14/M15)
- [ ] C2. README: link `docs/guides/migration-1.0-to-1.1.md` + ADR-0007

## D. Validate
- [ ] D1. Chạy thử MỌI lệnh CLI trong guide (journal tmp): compat verify / compat list / migrate config+plugin+contract dry-run+apply / conformance — exit 0
- [ ] D2. Validate cấu trúc: script kiểm tra ADR headers (Status/Date/Extends/Context/Decision/Consequences) + guide tồn tại + link PLAN
- [ ] D3. Full suite pytest ≥ 2118 PASS / 0 FAIL
- [ ] D4. test.md + evaluation.md + implementation/README.md; LOG/PROGRESS; commit — KHÔNG push
