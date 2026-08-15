# TASK-074 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-074.

## Các vấn đề

### C1-01 (P1) — "Rollback tự động sau fail" phải định nghĩa rõ thứ tự
→ **Resolve**: apply() catch exception → journal FAILED → gọi rollback ngược từ step cuối đã apply (mỗi step có rollback_fn; thiếu rollback_fn → step không rollback được nhưng không crash — best-effort, ghi chú). Kết quả rollback trả trong journal.

### C1-02 (P2) — MigrationFormats "rename field" config phải có ví dụ thật
→ **Resolve**: Config v0→v1: `autonomous.budget.max_duration_s` (v0) → `autonomous.budget.max_duration_seconds` (v1) — format fn nhận dict YAML → dict mới. Workflow: `depends_on` list (v0) → giữ nguyên + thêm `timeout_s` default (v1). Plugin: `aios: {min, max}` → `aios: {min, max, compatible: [semver]}` (v1).

### C1-03 (P2) — Dry-run không side effect đo thế nào?
→ **Resolve**: Test: dry_run với step fn có counter → counter = 0 sau dry_run (fn không gọi). Journal không tạo.

### C1-04 (P3) — CLI migrate args
→ **Resolve**: `aiagent migrate <kind> <from> <to> --dry-run|--apply|--rollback` — từ/to semver validate.

## Kết luận
Resolve vào spec v2.
