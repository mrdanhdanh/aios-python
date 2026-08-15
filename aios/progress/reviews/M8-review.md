# M8 — Ecosystem — Milestone Review (Self-Review)

> **Ngày review**: 2026-08-15
> **Reviewer**: AIOS Orchestrator (self-review — cùng mẫu M5/M6/M7)
> **Phương pháp**: đọc code TASK-043..049 + spec, chạy test thật (62 functional M8 + 20 m8/INV-022..029 arch + 25 observability scanner = 107 test M8), chạy architecture scanner trên cây thật (`SRC_ROOT`), đối chiếu PLAN §M8 DoD + `test_m8_*` allow-list + INV-022..029.
> **Kết luận**: **M8 ĐẠT** — mọi tiêu chí DoD PASS; 1 finding P2 (F1) đã tự sửa, 1 finding P3 (F2) đã tự sửa. Không có P1.

---

## 1. Phạm vi & Deliverable (PLAN §M8)

M8 = "Ecosystem" — đưa AIOS từ nền tảng vận hành (M7) thành hệ sinh thái mở rộng bởi bên thứ ba. 7 task (E1–E7):

| Task | Module | Ghi chú |
|------|--------|---------|
| TASK-043 | `sdk/python/` (Public AIOS SDK) | E1 — stable public API |
| TASK-044 | `plugins/` (Plugin Runtime) | E2 — reuse SkillState 10-state machine |
| TASK-045 | `extension/` (Extension Contracts) | E3 — namespace + matrix fail-closed |
| TASK-046 | `ecosystem/registry.py` (Ecosystem Registry) | E4 — pure index/search |
| TASK-047 | `ecosystem/devkit.py` (Developer Kit) | E5 — deterministic scaffold |
| TASK-048 | `ecosystem/marketplace.py` (Marketplace/Hub) | E6 — 9-step trust chain + HMAC |
| TASK-049 | `ecosystem/certification.py` (Certification) | E7 — Harness gate (M6) |

**Invariants**: M8 không định nghĩa invariant mới — tái sử dụng **INV-022..029** (Enterprise) làm guardrails cho ecosystem boundary (control-plane isolation, credential/identity, audit). Isolation cấp package được enforce bằng `test_m8_*` allow-list (plugins/extension/ecosystem chỉ import `semver`/`metadata`/`skills.base`/`skills.errors`).

Deliverable: Public SDK + Plugin Runtime + Extension Contracts + Ecosystem Registry + Developer Kit + Marketplace + Certification — developer xây extension **không sửa Core**; Ecosystem kết nối chặt với Harness (M6) và Enterprise (M7).

---

## 2. Tiêu chí chấp nhận (DoD §M8) — V1–V8

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|----------|---------|-----------|
| V1 | Public SDK ổn định, isolated API (E1) | ✅ PASS | `test_plugins`? — `sdk/python/` tests + `TASK-043` evaluation (10 AC); SDK chỉ DTO/Client/Transport, không chạm kernel |
| V2 | Plugin Runtime reuse SkillState + isolation (E2, INV-029) | ✅ PASS | `test_m8_plugins_reuse_skills_state_machine` + `test_m8_plugins_import_allowlist` + `test_plugins.py` (1584→1639) |
| V3 | Extension Contracts namespace + matrix fail-closed (E3) | ✅ PASS | `test_m8_extension_namespace_gate` + `test_m8_extension_matrix_fail_closed` + `test_extension_contracts.py` |
| V4 | Ecosystem Registry pure index (E4) | ✅ PASS | `test_m8_ecosystem_registry_pure_index` + `test_ecosystem_registry.py` |
| V5 | Developer Kit deterministic no-overwrite (E5) | ✅ PASS | `test_m8_ecosystem_devkit_deterministic_no_overwrite` + `test_ecosystem_devkit.py` |
| V6 | Marketplace trust chain + HMAC (E6) | ✅ PASS | `test_m8_ecosystem_marketplace_trust_chain` + `test_ecosystem_marketplace.py` |
| V7 | Certification = Harness gate (E7, M6) | ✅ PASS | `test_m8_ecosystem_certification_harness_gate` + `test_ecosystem_certification.py` |
| V8 | Observability đầy đủ (§M8 DoD) | ⚠️→✅ | **F1** (runtime `ArchitectureHealth.scan()` chưa cover `plugins/`/`extension/`/`ecosystem/`) → đã tự sửa (xem §3); baseline: tests/test_architecture.py `test_m8_*` pass |

**Test thực tế chạy lại**: 62 functional M8 (`test_plugins`, `test_extension_contracts`, `test_ecosystem_*`) + 20 arch (`test_m8_*` 14 + `test_inv022..029` 8) + 25 observability scanner (gồm 4 mới) = **107/107 pass**. Full suite backend (1639 test — từ PROGRESS M8) green.

---

## 3. Findings & Tự sửa

### F1 (P2) — Runtime ArchitectureHealth scanner không cover M8 packages
**Phát hiện**: `observability/arch_health.py` (`ArchitectureHealth.scan()`) đã cover agents/workflow/orchestrator/capabilities + 6 M5 (memory/context/models.router/orchestrator.planning/kernel.graph/kernel.scheduler) + M6 `harness` (review M6 F1) + M7 `enterprise` (review M7 F1). NHƯNG **không** có rule cho `plugins/`, `extension/`, `ecosystem/` — 3 package M8.
- PLAN §M8 yêu cầu "observability đầy đủ" cho ecosystem boundary. Một regression import vi phạm `test_m8_*` allow-list (vd: `plugins/` import `agents`, `ecosystem/` import `kernel.services.execution`) sẽ bị bắt bởi `tests/test_architecture.py` (CI) nhưng **không** bởi runtime scanner — không thỏa "observability đầy đủ". Đây chính là gap M5/M6/M7 F1 chưa áp dụng cho M8.

**Tự sửa** (mirror M5/M6/M7 F1):
- Thêm 3 M8 layer rule vào `_LAYER_RULES` (targets `"plugins"`, `"extension"`, `"ecosystem"`) — forbidden downward imports mirroring `test_m8_plugins_import_allowlist` / `test_m8_extension_import_allowlist` / `test_m8_ecosystem_import_allowlist`. Rule không false-positive vì real packages chỉ import allow-list (`skills.base`/`skills.errors`/`semver`/`metadata`) — đã verify qua `test_m8_*` pass.
- Thêm 4 test regression trong `tests/test_observability_arch_health.py`:
  - `test_m8_real_src_healthy` — scanner trên `SRC_ROOT` phải xanh cho `plugins`/`extension`/`ecosystem`
  - `test_m8_plugins_isolation_fires` — plugins import `agents` → violation
  - `test_m8_extension_isolation_fires` — extension import `orchestrator` → violation
  - `test_m8_ecosystem_isolation_fires` — ecosystem import `kernel.services.execution` → violation
- **Verify**: scanner trên cây thật → `healthy=True`, 0 violations cho M8; 25/25 observability scanner test pass (gồm 4 mới).

### F2 (P3) — M8 thiếu milestone review doc
**Phát hiện**: M0/M3/M4/M5/M6/M7 đều có `reviews/Mx-review.md` + `Mx-review-brief.md`. M8 chưa có (chỉ PROGRESS/LOG ghi done). Vi phạm quy trình "mỗi milestone có review".
**Tự sửa**: viết `reviews/M8-review.md` (file này) + `reviews/M8-review-brief.md`; cập nhật PROGRESS/LOG/STATS.

### F3 (P3) — M8 tái sử dụng INV-022..029 (không invariant mới)
**Phát hiện**: PLAN/ADR định nghĩa INV-022..029 thuộc M7 (Enterprise). M8 tái sử dụng chúng làm ecosystem boundary guardrails (certification/trust-chain/control-plane isolation). Đây KHÔNG phải drift (như M6-H5 từng nhầm INV-022) — M7 review (F3) đã rename `test_m6_*_inv022` → đúng nhãn và chuẩn hóa `test_inv022..029` cho M7. M8 dùng `test_m8_*` (allow-list, không nhãn INV) nên không conflict.
- Mức độ: P3 (chỉ ghi nhận cho rõ ràng), không cần sửa code.

---

## 4. Không có P1
Đọc kỹ code 7 module M8 (sdk DTO/transport; plugins reuse SkillState + compat fail-fast + provides active-only; extension namespace gate + matrix fail-closed; ecosystem registry pure index; devkit deterministic no-overwrite; marketplace 9-step trust chain + HMAC fingerprint (không serialize raw key); certification harness gate + security hard-block + evidence bắt buộc). Logic deterministic, tuân INV-022..029 + allow-list, không tìm thấy bug mức P1. Chất lượng tương đương M7.

## 5. Kết luận
**M8 ĐẠT** (V1–V8 PASS sau F1). 107 M8 test (62 functional + 20 arch + 25 scanner) đều xanh. Full suite backend 1639 test green. M8 packages covered bởi runtime scanner (sau F1).

## 6. Artifacts
- `backend/src/aios_core/observability/arch_health.py` (thêm 3 M8 layer rule: plugins/extension/ecosystem)
- `backend/tests/test_observability_arch_health.py` (thêm 4 M8 scanner test)
- `aios/progress/reviews/M8-review.md`, `M8-review-brief.md`
- `aios/progress/PROGRESS.md`, `LOG.md`, `STATS.md`
