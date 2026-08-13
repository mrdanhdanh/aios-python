# TASK-013 — Tasks Breakdown (Assistants)

> Ngày: 2026-08-13 | Spec: `spec.md` (approved — critique ×2 resolved 25 vấn đề: 14 + 11)

## Checklist

### T1 — Update test_architecture.py (trước khi tạo agents/)
- [ ] T1.1 Sửa skip condition `test_inv002_worker_no_direct_tool` → chỉ `not AGENTS_DIR.is_dir()` + cập nhật comment/reason "agents/ chưa tồn tại (TASK-013)" (C1-01/C2-10)
- [ ] T1.2 Thêm `test_inv_agents_import_allowlist`: rglob agents/ + collect_imports gộp set + **loại trừ `aios_core.agents*` (intra-package — R1.2)** + check CẢ 2 (aios_mods ⊆ {models.base, models.errors}; external ⊆ {pydantic} ∪ stdlib_allowed) (C1-07/C2-06/C2-08/R1.2)

### T2 — `agents/` package (Worker Plane — allow-list cứng)
- [ ] T2.1 `base.py`: AssistantRequest/AssistantResponse/Assistant (template method handle: empty text → error; started/finished; except Exception → status=error; event_sink best-effort)
- [ ] T2.2 `general.py`: GeneralAssistant (deterministic template + knowledge bullets; model optional — except ModelError trước, Exception sau; fallback)
- [ ] T2.3 `coder.py`: CoderAssistant + CoderResult (code, test_reports, **issues C2-07**, iterations, passed, history) + 7 default steps (step contract state[step_name] C1-03; generator repr-escape C1-04/C2-09; unit_test exec ns C2-04; passed = unit AND integration C1-09) + Self-Fix loop (max_fix_rounds=2, feedback)
- [ ] T2.4 `doctor.py`: DoctorAssistant + DoctorAssessment (**need_more_info C2-05**) + DOCTOR_KNOWLEDGE + Safety Layer 4 invariants (a ok-only; b trước d; c high→emergency; d gate thêm "không danger" C2-01; KB-miss → see_doctor + need_more_info C1-06; extractor union(KB, danger) C2-03)
- [ ] T2.5 `system_doctor.py`: SystemDoctor (probe normalize — degraded→fail C1-12; score; FIX_HINTS + generic)
- [ ] T2.6 `registry.py`: AssistantRegistry (RLock; register/get/list/resolve_by_intent qua selector callable; duplicate → ValueError)
- [ ] T2.7 `__init__.py` exports + `aios_core/__init__.py` + test_import.py cập nhật

### T3 — Test (5 file mới)
- [ ] T3.1 `test_agents_base.py` — handle contract: empty text, started/finished events, event_sink raise best-effort, _process raise → status=error, session_id (AC1-2)
- [ ] T3.2 `test_coder_assistant.py` — happy path (ast.parse, test_reports, history 7 bước, issues), self-fix (feedback truyền, max_rounds), error path (AC4-6)
- [ ] T3.3 `test_doctor_assistant.py` — pipeline + safety layer invariants (a/b/c/d + b∩d + danger-only C2-01) + KB inject/validate/deterministic (AC7-9)
- [ ] T3.4 `test_system_doctor.py` — score 2/3, fail hint, invalid probe, raise, None, deterministic (AC10)
- [ ] T3.5 `test_assistant_registry.py` — register/get/list/duplicate/unknown + resolve_by_intent (selector stub/None/unknown) + concurrent (prefix riêng C1-13) + tích hợp AgentSelector thật (AC11-12)

### T4 — Chạy + đánh giá
- [ ] T4.1 `pytest -q` toàn bộ pass (502 baseline + mới, **0 skip**)
- [ ] T4.2 Coverage agents/ ≥ 80%
- [ ] T4.3 `evaluation.md` đối chiếu 12 AC
- [ ] T4.4 PROGRESS.md / LOG.md / STATS.md + commit
