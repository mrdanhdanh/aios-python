# TASK-039 — E5 Resource Governance (M7)

## Mục tiêu
`QuotaManager` (fairness INV-025) + `CostGovernor` (budget deny / cheaper route). Đảm bảo resource fairness giữa tenants/executions.

## Phạm vi
- `Quota` contract (concurrent, cpu, memory, tokens, storage, tool_calls, sandbox_seconds)
- `QuotaManager.set_quota/get_quota/usage/can_start/check_fairness` raise `QuotaExceeded`
- `CostGovernor.set_budget/estimate/check_budget` raise `BudgetExceeded` / `cheaper_alternative`

## Input/Output
- In: tenant/execution + request; Out: allow/deny + cost estimate

## Tiêu chí chấp nhận (AC)
1. INV-025: `check_fairness` deny vượt quota → `QuotaExceeded` (trừ override)
2. `can_start` theo concurrency
3. `CostGovernor` deny vượt budget → `BudgetExceeded`
4. `cheaper_alternative` suggest route rẻ hơn
5. Contract `extra=forbid`
6. Test quota gate
7. Test budget gate
