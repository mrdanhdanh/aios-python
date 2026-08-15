# Review M7 — Enterprise (template nâng cấp v2)

> **⚠️ SNAPSHOT @M7 (2026-08-15)** — brief này chụp trạng thái M7. Số liệu test ghi trong này (1560 pytest @M7) ĐÚNG TẠI THỜI ĐIỂM M7. Khi review độc lập, model PHẢI chạy thật để lấy con số hiện tại, không dùng số trong brief làm kết luận cuối.
> **Bản điền sẵn từ** `REVIEW-BRIEF-TEMPLATE.md` — đem cho model khác review độc lập.
> Copy TOÀN BỘ file này sang model review. Model tự đọc repo, tự kết luận — không xem bản review nội bộ nào trước đó.
>
> **Lưu ý cho reviewer:** Template v2.1 (hard-gate review framework) chuyển trọng tâm từ *existence review* sang **runtime correctness & architecture review**. Bắt buộc áp dụng các mục 4–22 + Acceptance Traceability (22A) + Final Gate (26) trước khi kết luận.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M10). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "M7 – Enterprise (P12)" + mục "Architecture Invariants (INV-022..INV-029)"** (tiêu chuẩn nghiệm thu M7)
- `AGENTS.md` — quy tắc vận hành dự án
- `docs/architecture.md` — tài liệu kiến trúc + Architecture Invariants
- `docs/adr/` — Architecture Decision Records

## 2. Nhiệm vụ

Review milestone **M7** — Enterprise (P12): đưa AIOS từ single-instance thành vận hành an toàn trong môi trường doanh nghiệp.
7 nhóm (E1–E7) + 8 invariant (INV-022..INV-029):
- **E1 Identity & Access** (TASK-035): Principal user/agent/service + RBAC/ABAC + delegation/attenuation — INV-022
- **E2 Multi-Tenancy** (TASK-036): Organization→Tenant→Project→Workspace; memory/credential/workflow isolation — INV-023
- **E3 Distributed Runtime** (TASK-037): Runtime Node/Registry/Router — INV-029
- **E4 Distributed Scheduler + Lease** (TASK-038): single-active lease, failover — INV-026
- **E5 Resource Governance** (TASK-039): quota/cost/rate-limit/fairness — INV-025
- **E6 Security & Data Isolation** (TASK-040): Credential Broker/Network/Sandbox — INV-024/028
- **E7 Operations** (TASK-041 + TASK-042): HA/Audit/Recovery + Dashboard — INV-027

Đánh giá độc lập 4 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho M7 (7 nhóm E1–E7 + 8 invariant)
2. **Đúng quy trình**: hard gate có được tuân thủ cho TASK-035..042 không (8-file: spec/critique-1/critique-2/tasks/review/test/evaluation/implementation/)
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế ↔ kết quả test có khớp không
4. **Đúng kiến trúc & runtime correctness**: `enterprise/` tuân thủ INV-022..029; Control Plane tự-contained (chỉ import intra-package + pydantic/stdlib)

## 3. Deliverable cần kiểm tra

### 3.1 Code (backend — package `enterprise` tại `backend/src/aios_core/enterprise/`)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 1 | `enterprise/identity.py` | Principal/RBAC/ABAC/DelegationChain/IdentityEngine; `require()` → `NoPrincipalError` (INV-022) |
| 2 | `enterprise/tenancy.py` | TenantRegistry/TenantBoundary/MemoryNamespace/TenancyManager; `CrossTenantAccessDenied` (INV-023) |
| 3 | `enterprise/runtime.py` | NodeRegistry/RuntimeRouter; tenant_class gate (INV-029) |
| 4 | `enterprise/scheduler.py` | LeaseManager (single-active lease, INV-026) / DistributedScheduler (failover) |
| 5 | `enterprise/governance.py` | QuotaManager (`QuotaExceeded`, INV-025) / CostGovernor |
| 6 | `enterprise/security.py` | CredentialBroker (`_assert_scope`, INV-024) / NetworkPolicyEngine / SandboxBoundary (`SandboxBypassError`, INV-028) |
| 7 | `enterprise/operations.py` | CentralAuditStore (hash chain, INV-027) / HealthMonitor / RecoveryManager |
| 8 | `enterprise/dashboard.py` + `__init__.py` | EnterpriseDashboard + EnterpriseManager facade (compose INV-022..029) |
| 9 | `enterprise/contracts.py` | Contracts `extra="forbid"` (Principal/Tenant/Lease/CredentialRef/...) |

### 3.2 Tests (chạy thật)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 10 | `backend/tests/test_enterprise.py` | ~29 test enterprise (identity/tenancy/runtime/scheduler/governance/security/operations/dashboard) |
| 11 | `backend/tests/test_architecture.py` | 8 INV-022..029 tests (`test_inv022_..test_inv029_*`) + `test_inv022_enterprise_import_allowlist` + `test_m7_enterprise_no_god_object` |
| 12 | `backend/tests/test_observability_arch_health.py` | `test_m7_real_src_healthy` + `test_m7_enterprise_isolation_fires` (scanner cover enterprise) |
| 13 | Toàn bộ backend | `cd backend; .venv/Scripts/python -m pytest` — mong đợi **≥1560 tests pass** (tại M7; sau review F1/F2/F3 thêm vài test) |

### 3.3 Hồ sơ quy trình (hard gate)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 14 | `aios/progress/tasks/TASK-035..042/` | Mỗi folder đủ 8 file: spec, critique-1, critique-2, tasks, review, test, evaluation, **implementation/** |
| 15 | `aios/progress/PROGRESS.md` | Mục M7: TASK-035..042 done; khớp git history + LOG.md |

### 3.4 Architecture scanner

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 16 | `backend/src/aios_core/observability/arch_health.py` | `_LAYER_RULES` phải có rule `("layer", "enterprise", (...))` để scanner cover enterprise (không silent-skip như M5 F1) |
| 17 | runtime verify | `python -c "from aios_core.observability.arch_health import ArchitectureHealth; ArchitectureHealth().scan().healthy"` → `True` |

## 4. Tiêu chí nghiệm thu (V1–V8)

| # | Tiêu chí | Nguồn |
|---|----------|-------|
| V1 | Identity & Access (E1) + INV-022 | PLAN §M7.3 |
| V2 | Multi-Tenancy (E2) + INV-023 | PLAN §M7.4 |
| V3 | Distributed Runtime (E3) + INV-029 | PLAN §M7.5 |
| V4 | Distributed Scheduler + Lease (E4) + INV-026 | PLAN §M7.6 |
| V5 | Resource Governance (E5) + INV-025 | PLAN §M7.7 |
| V6 | Security & Data Isolation (E6) + INV-024/028/027 | PLAN §M7.8 |
| V7 | Operations + Dashboard (E7) + INV-027 | PLAN §M7.9 |
| V8 | Process: 8-file hard gate TASK-035..042 + Arch scanner cover enterprise | AGENTS.md hard gate |

## 5. Kết luận mong đợi

- Nếu V1–V7 PASS + INV-022..029 PASS + V8 PASS → **M7 ACCEPTED**.
- Nếu V8 FAIL do thiếu file process (không phải code bug) → **ACCEPTED with P2 remediation** (thêm `implementation/` + scanner rule).
- P1 code bug → **REJECTED** cho đến khi fix.
