# Milestone Review Brief — M8 (Ecosystem)

> **Mục đích**: tài liệu tự chứa để đem cho model/người review ĐỘC LẬP đánh giá M8.
> **Cách dùng**: copy file này sang model review. Model tự đọc repo + chạy test, trả báo cáo theo mục 7 của REVIEW-BRIEF-TEMPLATE.md. KHÔNG sửa file.
> **Lưu ý reviewer**: M8 đã có 1 self-fix (F1) ghi trong `reviews/M8-review.md` — reviewer độc lập đánh giá lại từ code thực tế, không bị ảnh hưởng bởi kết luận đó.

---

## 1. Bối cảnh dự án

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M10). Quy trình hard gate cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate.

Đọc bắt buộc:
- `docs/PLAN.md` — master plan, **đặc biệt mục "M8 – Ecosystem (P13)"** + "Architecture Invariants" (INV-022..029 — Enterprise, được M8 tái dụng làm ecosystem boundary).
- `AGENTS.md` — quy tắc vận hành.
- `docs/adr/0004-architecture-invariants.md` + `docs/architecture.md` §7.

## 2. Nhiệm vụ

Review milestone **M8** — Ecosystem: Public SDK, Plugin Runtime, Extension Contracts, Ecosystem Registry, Developer Kit, Marketplace/Hub, Certification (TASK-043..049, E1–E7). Tái dụng INV-022..029 làm guardrails.
Đánh giá độc lập 4 khía cạnh: (1) đúng phạm vi, (2) đúng quy trình 8-file hard gate, (3) hồ sơ nhất quán, (4) kiến trúc & runtime correctness.

## 3. Deliverable cần kiểm tra

**Code (đọc thực tế):**
- `backend/sdk/python/` (TASK-043 — Public AIOS SDK: DTO, Agent/Tool/Capability/Workflow, Client/Transport, metadata)
- `backend/src/aios_core/plugins/` (TASK-044 — Plugin Runtime: contracts, errors, compat, manager, registry, __init__)
- `backend/src/aios_core/extension/` (TASK-045 — Extension Contracts: contracts, matrix, errors)
- `backend/src/aios_core/ecosystem/` (TASK-046..049 — registry, devkit, marketplace, certification, contracts, errors, __init__)
- `backend/src/aios_core/observability/arch_health.py` (F1 self-fix: 3 M8 layer rule plugins/extension/ecosystem)

**Tests (chạy thật):**
- `backend/tests/test_plugins.py`, `test_extension_contracts.py`, `test_ecosystem_registry.py`, `test_ecosystem_marketplace.py`, `test_ecosystem_devkit.py`, `test_ecosystem_certification.py` (62 functional)
- `backend/tests/test_architecture.py` (`test_m8_plugins_*` / `test_m8_extension_*` / `test_m8_ecosystem_*` + `test_inv022_..test_inv029_*`)
- `backend/tests/test_observability_arch_health.py` (test_m8_* — F1 self-fix, 4 test mới)

**Hồ sơ quy trình (mỗi task đủ 8 file):**
- `aios/progress/tasks/TASK-043/`..`TASK-049/` (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)

## 4. Architecture & Runtime Deep Review (TRỌNG TÂM)

Áp dụng mục 4.1–4.12 của template. Đặc biệt chú ý:
- **Plugin boundary (E2)**: `plugins/` chỉ import `skills.base`/`skills.errors`/`semver`/`metadata` (allow-list `test_m8_plugins_import_allowlist`); PluginState = SkillState (không state machine thứ hai); compat fail-fast; provides chỉ active.
- **Extension Contracts (E3)**: `extension/` chỉ import `semver` + pydantic/stdlib (pure namespace + matrix); 4 namespace + `assert_namespace_allowed` fail-closed; missing runtime contract → error.
- **Ecosystem isolation (E4–E7)**: `ecosystem/` chỉ import `semver`/`metadata` (+ `hmac`) — độc lập kernel/plugins/extension/harness; registry chỉ index/search (không nhúng certification/marketplace); certification = Harness gate (M6) — fail check → COMMUNITY, security fail hard-block; marketplace 9-step trust chain + raw key không serialize (chỉ fingerprint).
- **Control Plane Isolation (INV-029)**: ecosystem/extension/plugins KHÔNG chạm `kernel.services.*` / `orchestrator` / `models` / `memory` / `knowledge` — boundary bảo vệ Core.
- **4.12 Anti Fake Test**: đọc body test, không chỉ đếm pass. Đặc biệt `test_observability_arch_health.py::test_m8_*` — chạy scanner trên cây thật (`SRC_ROOT`) và confirm M8 rule thực sự FIRE (không dead rule) và không false-positive.

## 5. Tiêu chí chấp nhận (nguồn: PLAN.md §M8 DoD)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|-----------------|---------------------|
| V1 | Public SDK ổn định, isolated API (E1) | `test_*` SDK + đọc `sdk/python/` | SDK chỉ DTO/Client/Transport |
| V2 | Plugin Runtime reuse SkillState + isolation (E2) | `test_m8_plugins_*` + `test_plugins.py` | PluginState = SkillState; allow-list |
| V3 | Extension Contracts namespace + matrix fail-closed (E3) | `test_m8_extension_*` | assert_namespace_allowed + fail-closed |
| V4 | Ecosystem Registry pure index (E4) | `test_m8_ecosystem_registry_pure_index` | class EcosystemRegistry, không import cert/marketplace |
| V5 | Developer Kit deterministic no-overwrite (E5) | `test_m8_ecosystem_devkit_deterministic_no_overwrite` | "refusing to overwrite" + name regex |
| V6 | Marketplace trust chain + HMAC (E6) | `test_m8_ecosystem_marketplace_trust_chain` | 9 bước + signing_key không serialize |
| V7 | Certification = Harness gate (E7) | `test_m8_ecosystem_certification_harness_gate` | CertLevel + security_failed + evidence |
| V8 | Observability đầy đủ (§M8 DoD) | scanner trên `SRC_ROOT` + `test_m8_real_src_healthy` | M8 packages scan xanh (F1 self-fix) |

## 6. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file mục 3 — không tin mô tả, phải thấy bằng chứng trong file.
2. Với mỗi tiêu chí mục 5: tìm bằng chứng → kết luận PASS/FAIL/INCONCLUSIVE kèm trích dẫn `file:đường dẫn`.
3. Áp dụng Architecture & Runtime Deep Review (mục 4.1–4.12) — mỗi mục có kết luận rõ.
4. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline`.
5. Tìm lỗ hổng chủ động: file thiếu, stub không logic, mâu thuẫn, claim không bằng chứng, **test pass nhưng không test đúng** (mục 4.12).
6. Với mỗi task: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/).
7. Phân mức findings: **P1** (sai mục tiêu/tiêu chí), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ).

## 7. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review M8 — bởi <tên model / reviewer>

## 1. Bảng đối chiếu tiêu chí
| # | Tiêu chí | Kết quả (PASS/FAIL/INCONCLUSIVE) | Bằng chứng (file + trích dẫn) |

## 2. Architecture Compliance
(đối chiếu mục 4.1–4.12: Runtime-first / Contract-first / Plugin-first / Engine-independent /
Capability-first / Policy-first / DI / Event-driven / Dependency / Wiring / Security /
Performance / Event Bus / Anti-fake-test — mỗi nguyên tắc ghi PASS/FAIL/INCONCLUSIVE + trích dẫn)

## 3. Findings
| ID | Mức (P1/P2/P3) | Mô tả | File liên quan | Đề xuất |

## 4. Kết luận
- ĐẠT / CHƯA ĐẠT (kèm điều kiện nếu có)
- Lý do ngắn gọn

## 5. Điểm mạnh (nếu có)
## 6. Gợi ý cải thiện (không bắt buộc)
```

## 8. Final Gate

Milestone chỉ được ACCEPTED khi: tất cả tiêu chí mục 5 = PASS; không có P1; không INCONCLUSIVE; test bắt buộc chạy thành công.

> Nếu có INCONCLUSIVE → không ACCEPTED cho đến khi nâng lên PASS hoặc FAIL.
