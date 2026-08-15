# TASK-041 — E7 Operations (M7)

## Mục tiêu
`CentralAuditStore` (tamper-evident INV-027) + `HealthMonitor` failover + `RecoveryManager`. Mọi execution bắt đầu = audit event.

## Phạm vi
- `AuditEvent` contract (previous_hash/hash chain)
- `CentralAuditStore.record` append + chain hash; `verify_integrity` recompute
- `HealthMonitor.heartbeat/mark_draining/is_stale/failover_target`
- `RecoveryManager.snapshot/restore/has_snapshot`

## Input/Output
- In: event/state; Out: stored record / failover target / snapshot

## Tiêu chí chấp nhận (AC)
1. INV-027: audit chain hash tamper-evident (verify phát hiện sửa)
2. `record` gắn previous_hash + hash
3. `verify_integrity` return False nếu bị sửa
4. HealthMonitor stale detection
5. Recovery snapshot/restore
6. Contract `extra=forbid`
7. Test chain integrity
