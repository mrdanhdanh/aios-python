# TASK-083 — Evaluation (M11-P4a/b: R5 + R7)

> **Ngày**: 2026-08-16 | **Trạng thái**: **DONE** — 11/11 AC đạt

## Đối chiếu AC

| # | AC | Kết quả | Bằng chứng |
|---|----|---------|------------|
| AC1 | R5: distill → report (SKILL.md + manifest.json) + capabilities | ✅ | test_r5_distill_report |
| AC2 | R5: license thiếu → WARN; MIT → OK | ✅ | test_r5_license_ok_when_mit + license_warn_when_missing |
| AC3 | R5: fetch fail/tree rỗng → SkillDistillError (fail-closed, no-overwrite) | ✅ | test_r5_fetch_fail_fail_closed + empty_tree + no_overwrite |
| AC4 | R5: manifest sinh hợp lệ (contract validation) | ✅ | test_r5_manifest_valid |
| AC5 | R5: capability extraction deterministic | ✅ | test_r5_capability_extraction_deterministic + stub_deterministic + different_url |
| AC6 | CLI `skill distill` thật | ✅ | chạy thật (stub fetch) |
| AC7 | R7: verify — hợp lệ PASS; thiếu/rỗng BLOCKED | ✅ | test_r7_verify_ok + missing_dir + empty_dir |
| AC8 | R7: manifest SHA256 deterministic | ✅ | test_r7_manifest_deterministic |
| AC9 | R7: dry_run không tạo file; apply → marker; merge không ghi đè; verify fail → không apply | ✅ | 4 tests deploy |
| AC10 | CLI `deploy --static` thật | ✅ | chạy thật (dry + apply) |
| AC11 | Full suite xanh | ✅ | **2052 passed / 0 failed** |

## Deliverables

- `ecosystem/distiller.py` — `SkillDistillError` + `SkillDistillReport` + `GitHubFetchStub` (hash URL → seed → tree) + `SkillDistiller` pipeline 7 bước (fetch → license → structure → capability extraction → synthesis → contract validation → report); fail-closed + no-overwrite
- `ecosystem/deploy.py` — `DeployReport` + `StaticDeploy` (verify fail-closed → manifest SHA256 → deploy dry-run/apply; marker `.aios/deploy.json` merge không ghi đè; exclude `.aios` khỏi manifest)
- `workflow/cli.py` — `aiagent skill distill <url> --out` + `aiagent deploy --static <dir> [--apply]`
- `tests/test_m11_p4.py` (18 tests)

## Bài học

1. **Allow-list M8 ecosystem chỉ cho semver/metadata** — import `skills.base` bị arch scanner chặn (test_m5_real_src_healthy bắt). Fix: mirror validation qua `semver.parse_version` + field checks — KHÔNG phá allow-list frozen. Đây là bằng chứng giá trị của arch-health (bắt vi phạm ngay).
2. **Deploy marker không tự đếm vào manifest** — `.aios/deploy.json` phải exclude khỏi `rglob` (nếu không manifest thay đổi sau mỗi apply → không deterministic).
3. **R7 optional đúng nghĩa**: dry-run mặc định, apply chỉ ghi marker (không push thật) — giữ scope P4 nhỏ như proposal.
4. **GitHubFetchStub hash URL → seed** — cùng URL cùng tree, khác URL khác skill (deterministic + meaningful, không cần network).

## Ghi nhận

- R5 không auto-install vào SkillManager — user chạy `skill resolve/install` sau (đúng spec — distiller là Ecosystem Extension)
- R7 push thật (GitHub Pages/S3/Netlify) ngoài scope — marker + hint CI đã đủ cho P4 optional
