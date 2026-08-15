# TASK-038 — E4 Distributed Scheduler + Lease (M7)

## Mục tiêu
Single-active lease per execution (INV-026). Failover: snapshot execution state → resume trên node khác. `DistributedScheduler` injectable (node_selector/run_on_node/resume_snapshot).

## Phạm vi
- `Lease` contract (execution_id, node_id, acquired_at, expires_at, heartbeat_at)
- `LeaseManager.acquire` raise `LeaseError` nếu execution đã có active lease
- `DistributedScheduler.enqueue/schedule` + failover

## Input/Output
- In: execution_id + node; Out: lease / failover target

## Tiêu chí chấp nhận (AC)
1. INV-026: execution chỉ có 1 active lease → `LeaseError`
2. renew/heartbeat/k_release hoạt động
3. is_expired theo clock injectable
4. failover resume từ snapshot
5. Contract `extra=forbid`
6. Test double-acquire raises
7. Scheduler injectable (testable offline)
