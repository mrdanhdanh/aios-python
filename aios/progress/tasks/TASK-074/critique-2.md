# TASK-074 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P2) — Backup: tái dùng BackupStore M4 hay tạo mới?
→ **Resolve**: Tái dùng `upgrade/backup.py::BackupStore` (SQLite backup/restore) — apply() tạo backup trước steps; rollback dùng backup nếu step không có rollback_fn (fallback).

### C2-02 (P3) — Journal persist giữa lần chạy
→ **Resolve**: MigrationJournal SQLite (db_path từ settings.upgrade? mặc định "aios/data/migrations.db") — ghi từng step done + status cuối.

### C2-03 (P3) — Idempotent: apply 2 lần cùng plan?
→ **Resolve**: Journal có status=completed → apply từ chối (MigrationError "already applied") — tránh double migration.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
