# TASK-020 — tasks.md (breakdown checklist)

> Chuỗi hard gate: spec → critique ×2 → tasks → review → implement → test → evaluate → commit

## Checklist

| # | Bước | Trạng thái | Ghi chú |
|---|------|-----------|---------|
| 1 | Spec v1 | done | — |
| 2 | Critique ×1 (critic) | done | 15 vấn đề (5 P1) — RESOLVED → v2 |
| 3 | Critique ×2 (critic) | done | 16 vấn đề (4 P1: dry-run, validate hook, dep target, health) — RESOLVED → v3 |
| 4 | tasks.md | done | file này |
| 5 | Review (reviewer subagent) | todo | — |
| 6 | Implement: kernel/events.py — thêm 8 EventType members | todo | UPGRADE_STARTED..ROLLED_BACK (tái dùng UPGRADE_COMPLETED) |
| 7 | Implement: upgrade/dependency.py — Dependency, ComponentSpec, Resolution, DependencyResolver | todo | DFS post-order, sort (name, version), cycle/missing/conflict |
| 8 | Implement: upgrade/backup.py — BackupRecord, BackupStore | todo | SQLite pattern chuẩn |
| 9 | Implement: upgrade/migrator.py — Migrator Protocol, DictMigrator, SkillMigrator | todo | rollback NotImplementedError fallback |
| 10 | Implement: upgrade/pipeline.py — UpgradePipeline, UpgradeResult, 6 bước + dry-run + rollback + events | todo | chỉ migrate root |
| 11 | Implement: workflow/cli.py — subcommand upgrade (lazy import, wire skill) | todo | exit codes |
| 12 | Test: test_upgrade_dependency.py | todo | topo/cycle/missing/conflict/deterministic |
| 13 | Test: test_upgrade_backup.py | todo | persist 2 instance |
| 14 | Test: test_upgrade_pipeline.py | todo | ok/4 fail/skip/dry-run/rollback |
| 15 | Test: test_upgrade_skill.py | todo | SkillMigrator thật |
| 16 | Test: test_upgrade_cli.py | todo | exit codes + not wired |
| 17 | Test: test_architecture.py allow-list upgrade/ | todo | full dotted path |
| 18 | Evaluation + PROGRESS/LOG + commit | todo | — |
