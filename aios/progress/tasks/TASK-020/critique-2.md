# Critique ×2 — TASK-020 (critic subagent, vòng 2)

> 2026-08-13 | critic phản biện spec v2 — 4 P1 mới + 5 P2 + 6 P3 → spec v3.

## Vấn đề & Resolution

### P1
- **C2-01 dry-run không tồn tại trong pipeline** (run không có param; result không có plan) → **Resolve**: `run(..., dry_run=False)`; dry-run chạy bước 0→2 dừng trước backup; `plan: tuple[ComponentSpec, ...]` trong UpgradeResult.
- **C2-02 validate hook không có điểm inject** → **Resolve**: tham số constructor `validate: Callable[[str, str, str], str | None] | None = None`.
- **C2-03 target version cho dependency mâu thuẫn SkillManager.upgrade** (migrate mọi component về new_version của root → dep đang cao hơn sẽ raise → rollback giả) → **Resolve (QUYẾT ĐỊNH)**: chỉ migrate ROOT; dependency chỉ resolve/kiểm tra.
- **C2-04 health re-check "check_upgrade lại" không thực thi được** (component đã ở new_version) → **Resolve**: health = read_current version == new_version + validate hook.

### P2
- **C2-05 read_current = get sai type** (Skill là BaseModel) → **Resolve**: `model_dump(mode="json")` trong SkillMigrator.
- **C2-06 write_current không implement được cho SkillMigrator** → **Resolve**: rollback ưu tiên, NotImplementedError → fallback write_current (pipeline try/except).
- **C2-07 allow-list sai format** (thiếu full path + collections/logging) → **Resolve**: full dotted path + external đầy đủ.
- **C2-08 CLI wiring không định nghĩa** → **Resolve**: CLI v1 chỉ wire skill (SkillMigrator + SkillManager từ settings); kind khác → exit 1 "not wired".
- **C2-09 backup-fail không có AC** → **Resolve**: step=backup, status failed, không rollback (chưa migrate), orphan rows chấp nhận.

### P3
- **C2-10** step=rollback giá trị chết → bỏ khỏi enum step.
- **C2-11** version invalid (compare raise) → ValueError propagate; CLI bắt exit 1.
- **C2-12** BackupRecord chưa khai báo → dataclass đầy đủ.
- **C2-13** read_current None → fail "component not found" step=backup.
- **C2-14** Skill state không phù hợp → SkillMigrator map lỗi thành message rõ.
- **C2-15** event 2 luồng (skill.updated + UPGRADE_*) → test test_upgrade_skill.md ghi chú.
- **C2-16** payload event chưa pin hết → payload mỗi event: kind, component_id, version, step, ...

## Trạng thái: RESOLVED 16/16 → spec v3
