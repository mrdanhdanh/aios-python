# Evaluation — TASK-015 (M2-P4: Skills lifecycle + Skill Manager + Sandbox Pool)

> Ngày: 2026-08-13 | Chuỗi: Spec → Critique ×2 (27 vấn đề) → Review (CHANGES REQUESTED → R1/R2/R3) → Implement → Test → **Evaluate**

## Kết quả test

- **669 passed, 0 skipped** (baseline 622 + 47 mới), coverage **95.51%**
- 47 test mới: skills_base 11, skill_manager 16, sandbox_pool 16, arch 2 allow-list mới
- Allow-list `skills/` (metadata + semver) + `sandbox/` (empty) PASS

## Đối chiếu 18 AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | Package + exports + 2 allow-list + INV giữ nguyên | ✅ 0 skip, 2 allow-list pass |
| AC2 | SkillManifest contract (semver validate, extra=forbid) | ✅ 6 test |
| AC3 | State machine 10 trạng thái (bảng T1-T10 tham số hóa) | ✅ `test_transition_table_parameterized` 20 case |
| AC4 | resolve (duplicate → SkillError, loader inject) | ✅ 2 test |
| AC5 | validate (deps + constraint `id@>=X` bằng semver.compare) | ✅ 3 test |
| AC6 | install + event + persist | ✅ lifecycle + persist restart |
| AC7 | Reversible enable↔disable/unload↔reload | ✅ chain test |
| AC8 | upgrade (new > current, invalid → SkillError, không còn active) | ✅ 2 test |
| AC9 | rollback (no history → SkillStateError, dependent check R1) | ✅ 2 test |
| AC10 | remove (terminal soft-delete, dependent active chặn R1) | ✅ 2 test |
| AC11 | CHECK domain-only + persist restart | ✅ `test_check_constraint_domain_only` |
| AC12 | Registry read-through | ✅ 1 test |
| AC13 | Events cross-check EventType | ✅ 1 test |
| AC14 | 3 sources stub + no-syscall | ✅ 6 test |
| AC15 | Warm reuse + normalize language | ✅ 3 test |
| AC16 | Full + evict + health | ✅ 4 test |
| AC17 | Execute no-exec + thread-safe | ✅ 3 test |
| AC18 | Determinism + coverage ≥ 80% | ✅ 669 pass, 95.51% |

**18/18 AC đạt.**

## Xử lý critique ×2 (27) + review (R1-R5)

- C1-01 transitions T4/T5 (bỏ unloaded→enable, thêm upgraded/rolled_back→disable) ✅
- C1-03 optimistic concurrency (UPDATE WHERE state; IntegrityError catch) ✅ `test_optimistic_concurrency_two_instances`
- C1-04 semver allow-list (dọn 6 chỗ mâu thuẫn — R3) ✅
- C1-05 dependent check (rollback constraint vs target; remove chặn active) ✅ 2 test
- C1-02 CHECK domain-only wording ✅; C1-06 upgrade không active ✅; C1-08 message removed ✅; C1-11 normalize ✅; C1-12 stats private ✅; C1-13 bỏ register manager ✅; C1-16 db_path bắt buộc ✅; C1-17 CHECK sinh từ hằng số ✅
- C2-01 dotted import ✅; C2-02 bỏ upgraded→rollback khỏi invalid ✅; C2-03 invalid new version → SkillError ✅; C2-05 warm comment ✅; C2-06 grammar `>=` ✅; C2-07 fixtures không metadata ✅; C2-08 SKILLS_DIR/SANDBOX_DIR ✅

## Bài học mới

1. Evict idle test phải dùng time.monotonic() làm base (không số giả — sandbox tạo bằng monotonic thật)
2. Rollback từ installed bị cấm (T9 không có installed) — test phải enable trước
3. `datetime` cần thêm vào allow-list external khi dùng datetime.now(timezone.utc)
4. Loader callable nhận (source, ref) — fixture lambda phải đúng 2 tham số

## Kết luận

**TASK-015 ĐẠT — 18/18 AC, 669 tests pass, 0 skip (4 allow-list bật), coverage 95.51%, git sạch sau commit.**
