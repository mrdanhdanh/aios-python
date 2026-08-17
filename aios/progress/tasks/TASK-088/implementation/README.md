# TASK-088 — Implementation artifacts

## Deliverables

| File | Nội dung |
|------|----------|
| `docs/adr/0007-compatibility-migration-policy.md` | **MỚI** — ADR-0007: version policy (0.1.0 dev/1.0.0 release/1.1.0 hiện tại; đường nâng cấp chính thức 1.0.0→1.1.0), Compatibility Matrix fail-closed, Migration per component (idempotent), Backward Suite, Conformance 11 areas/7 gates → AIOS 1.1 READY, parse-only precedent (AiosRange.compatible) |
| `docs/guides/migration-1.0-to-1.1.md` | **MỚI** — Migration guide 5 bước (compat verify → dry-run → apply → rollback → conformance) + bảng "điều gì thay đổi" per kind + cảnh báo stub vs --input + lưu ý idempotent/backup path/config skip |
| `docs/PLAN.md` §M12 | Header DONE + 5 task done ✅ (chỉ trong §M12) |
| `docs/README.md` | Link guide + ADR-0007 + conformance 11 areas/7 gates + compat verify |
| `aios/progress/tasks/TASK-088/implementation/validate_task088.py` | Script validate cấu trúc docs (PASS 0 failures) |

## Kết quả

- Validate: PASS — 0 failures (ADR headers + nội dung đúng code + guide 5 bước + PLAN tasks + README links)
- CLI thật (mọi lệnh trong guide): compat verify 9/9 + migrate config/plugin/contract exit 0 + conformance → AIOS 1.1 READY
- Full suite: **2118 PASS / 0 FAIL** (0 regression)
