# TASK-042 — Enterprise Dashboard (M7)

## Mục tiêu
`EnterpriseDashboard` aggregate tenant metrics từ audit store: executions, success_rate, denied, policy_violations, agents, workflows. Không compute business logic mới — chỉ tổng hợp.

## Phạm vi
- `EnterpriseDashboard.tenant_summary(tenant_id)` + `overview()`
- Đọc từ `CentralAuditStore` (injectable)
- Dimension aggregate: executions, success/failed, denied, policy_violations, agents, workflows

## Input/Output
- In: audit store; Out: summary dict per tenant / global overview

## Tiêu chí chấp nhận (AC)
1. `tenant_summary` trả về metric đúng tenant
2. `overview` aggregate toàn bộ
3. success_rate = success/(success+failed)
4. Không duplicate logic governance (chỉ read)
5. Contract `extra=forbid` (nếu có model)
6. Test aggregate đúng
7. Test empty audit → zero metrics
