# TASK-083 — Tasks breakdown (checklist)

## Khảo sát
- [ ] K1. Đọc `skills/base.py::SkillManifest` fields bắt buộc (id/name/version/description/source/dependencies)
- [ ] K2. Xem `ecosystem/devkit.py` no-overwrite pattern + `workflow/cli.py` skill subcommand

## Implement R5 — SkillDistiller
- [ ] I1. `ecosystem/distiller.py`: `SkillDistillError` + `SkillDistillReport` (pydantic extra=forbid: distilled_files/capabilities/warnings/manifest_path/license_status)
- [ ] I2. `GitHubFetchStub` (hash URL → seed → tree mẫu: SKILL.md + src/ + tests/, KHÔNG manifest sẵn)
- [ ] I3. Pipeline 7 bước: fetch → license (MIT/Apache-2.0 ok, thiếu → WARN) → structure scan → capability extraction (keywords sprite|pixel|game|canvas|audio|animation|map|tileset) → synthesis (SKILL.md + manifest đủ field) → contract validation (SkillManifest) → report
- [ ] I4. Fail-closed: fetch fail/tree rỗng → SkillDistillError; out_dir có file cũ → SkillDistillError (no-overwrite)
- [ ] I5. CLI `skill distill <url> [--out DIR]`

## Implement R7 — Static Deploy
- [ ] I6. `ecosystem/deploy.py`: `DeployReport` (dir/status/files/total_bytes/total_sha256/marker/hint) + `StaticDeploy.verify` (dir tồn tại + ≥1 file + (index.html OR bytes>0); rỗng → BLOCKED) + `manifest` (SHA256 từng file + tổng) + `deploy(dry_run=True)` (verify trước; apply → .aios/deploy.json merge không ghi đè)
- [ ] I7. CLI `deploy --static <dir> [--apply]`

## Test
- [ ] T1. AC1/AC4/AC5 R5 (distill report + manifest validate + deterministic)
- [ ] T2. AC2 R5 (license WARN) + AC3 (fail-closed) + no-overwrite
- [ ] T3. AC6 CLI skill distill thật
- [ ] T4. AC7/AC8/AC9 R7 (verify/manifest/deploy dry+apply)
- [ ] T5. AC10 CLI deploy thật
- [ ] T6. AC11 full suite + health check phase P4

## Evaluate
- [ ] E1. Đối chiếu 11 AC
- [ ] E2. LOG.md + PROGRESS.md + commit
