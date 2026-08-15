# TASK-070 — M10-F6: Security Baseline 1.0

## Mục tiêu
PLAN §M10-23: Security baseline 1.0 — 11 items: `Identity · Authentication · Authorization · Secrets · Encryption · Audit · Plugin signing · Supply chain · Sandbox · Network policy · Data boundary`. `aiagent security-check` → PASS/WARN/FAIL per item + tổng kết.

## Phạm vi
- `security/` package (backend/src/aios_core/security/):
  - `contracts.py`: `SecurityItem` (id, name, category, status: PASS/WARN/FAIL, evidence, recommendation, extra=forbid) + `SecurityReport` (items + summary + blocking)
  - `checks.py`: 11 `SecurityCheck` — mỗi check nhận `SecurityContext` (kernel/container) trả SecurityItem; deterministic, không network
    - identity: EnterpriseSettings.identity enabled (INV-022)
    - authentication: principal required flag
    - authorization: RBAC/ABAC present (enterprise identity module)
    - secrets: CredentialBroker scoped (INV-024) present
    - encryption: artifact checksum/sidecar (INV-008) present
    - audit: CentralAuditStore tamper-evident (INV-027) present
    - plugin_signing: marketplace HMAC signature (M8) present
    - supply_chain: trust chain verify (M8) present
    - sandbox: policy sandbox_required + SandboxBoundary (INV-028) present
    - network_policy: NetworkPolicy default-deny (M7) present
    - data_boundary: TenantBoundary deny-by-default (INV-023) present
  - `checker.py`: `SecurityChecker.run(ctx)` → SecurityReport (blocking = FAIL nào critical?)
- CLI: `aiagent security-check`
- Wiring: SecurityChecker optional trong RuntimeKernel (không bắt buộc DI)

## Ngoài phạm vi
- Không implement cơ chế bảo mật mới (chỉ baseline check các cơ chế M1–M9 đã có)
- Không sửa enterprise/security hiện có

## Input
- `enterprise/` (identity, security, tenancy, operations), `ecosystem/marketplace.py`, `plugins/compat.py`, `config.py` (EnterpriseSettings/PluginSettings/EcosystemSettings)

## Output
- `backend/src/aios_core/security/{__init__,contracts,checks,checker}.py` + CLI + `tests/test_security.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | Đủ 11 SecurityItem (id theo PLAN §M10-23) | Test set compare |
| AC2 | Mỗi check deterministic, không network, không crash khi thiếu config | Test với kernel thật |
| AC3 | Check dựa trên cơ chế THẬT (module import được + cấu hình) — không "check giả" | Test import + assert evidence |
| AC4 | SecurityReport: PASS/WARN/FAIL per item + blocking (FAIL critical → block) | Test |
| AC5 | `aiagent security-check` in bảng + verdict | CLI thật |
| AC6 | Regression full suite | pytest |
| AC7 | Đóng DoD | checklist |

## Ghi chú
- Baseline = kiểm tra "cơ chế tồn tại + được bật" (deterministic) — không phải penetration test.
- Evidence: mỗi item ghi module/flag kiểm tra (vd "CredentialBroker.scoped present in enterprise/security.py").
