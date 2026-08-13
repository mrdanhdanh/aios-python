# TASK-015 — Tasks Breakdown (Skills lifecycle + Sandbox Pool)

> Ngày: 2026-08-13 | Spec: `spec.md` (approved — critique ×2 resolved 27 vấn đề: 19 + 8)

## Checklist

### T1 — test_architecture.py (trước khi tạo package)
- [ ] T1.1 Thêm `SKILLS_DIR = AIOS / "skills"` + `SANDBOX_DIR = AIOS / "sandbox"` (C2-08)
- [ ] T1.2 Thêm `test_inv_skills_import_allowlist`: aios_mods ⊆ {metadata, semver}; external ⊆ {pydantic} ∪ stdlib; exclude aios_core.skills* (C1-04/C2-01 — chỉ dotted import)
- [ ] T1.3 Thêm `test_inv_sandbox_import_allowlist`: aios_mods ⊆ {}; external ⊆ {pydantic} ∪ stdlib_sandbox

### T2 — `skills/` package
- [ ] T2.1 `errors.py`: SkillError, SkillStateError (kế thừa Exception — skills/ không import orchestrator)
- [ ] T2.2 `base.py`: SkillState (10), SkillSource (zip/git/pip), SkillManifest (pydantic extra=forbid; version validate bằng aios_core.semver), Skill (view), `_TRANSITIONS` map (bảng T1-T10 — C1-01), assert_transition
- [ ] T2.3 `schema.py`: SKILLS_SCHEMA_SQL (10 cột; CHECK state + source sinh từ hằng số — C1-17; connection-per-call pattern)
- [ ] T2.4 `manager.py`: SkillManager — resolve (id trùng → SkillError) / validate (deps + constraint `id@>=X` bằng semver.compare; C2-06 grammar; C1-08 message phân nhánh; C1-18 one-shot) / install (+skill.installed event) / enable/disable/unload/reload / upgrade (new > current; invalid → SkillError C2-03; push history; KHÔNG còn active — C1-06) / rollback (history rỗng → no history; C1-05 dependent check) / remove (soft-delete terminal; C1-05 dependent check) — **optimistic concurrency UPDATE WHERE state=old (C1-03)**; event_sink best-effort; **KHÔNG có register (C1-13)**
- [ ] T2.5 `registry.py`: SkillRegistry read-through DB (get → None nếu không tồn tại; corrupt JSON → SkillError C1-14; list/list_by_state/list_by_capability)
- [ ] T2.6 `sources.py`: ZipSource/GitSource/PipSource stub (fixtures metadata cố định C2-07; ref rỗng → ValueError, ref lạ → SkillError C1-19); no-syscall
- [ ] T2.7 `__init__.py`: exports + build_skill_manager(db_path BẮT BUỘC — C1-16); aios_core/__init__.py + test_import.py

### T3 — `sandbox/` package
- [ ] T3.1 `errors.py`: SandboxPoolError
- [ ] T3.2 `pool.py`: SandboxState (idle/busy/destroyed), Sandbox (warm comment C2-05), SandboxResult, SandboxPool — acquire (normalize language C1-11; idle warm → cold → evict khi full → error) / execute (no-exec) / release (giới hạn cùng thread C2-04) / health / evict_idle(now=...) / _stats_for_test (C1-12); RLock; không thread nền
- [ ] T3.3 `__init__.py`: exports + build_sandbox_pool; aios_core/__init__.py

### T4 — Test (4 file)
- [ ] T4.1 `test_skills_base.py` — manifest contract, transitions tham số hóa (AC2-3), events cross-check EventType (AC13)
- [ ] T4.2 `test_skill_manager.py` — lifecycle chain 10 trạng thái (AC4-10), persist restart (AC11), optimistic 2 manager (C1-03), dependent check (C1-05)
- [ ] T4.3 `test_sandbox_pool.py` — warm reuse (AC15), evict (AC16), no-exec + thread-safe (AC17), "Python" normalize (C1-11)
- [ ] T4.4 `test_skill_sources.py` — 3 sources no-syscall (AC14) + determinism (AC18)

### T5 — Chạy + đánh giá
- [ ] T5.1 `pytest -q` toàn bộ pass (622 baseline + mới, 0 skip)
- [ ] T5.2 Coverage skills/ + sandbox/ ≥ 80%
- [ ] T5.3 `evaluation.md` đối chiếu 18 AC
- [ ] T5.4 PROGRESS.md / LOG.md / STATS.md + commit
