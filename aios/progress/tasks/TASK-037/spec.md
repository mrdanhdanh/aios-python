# TASK-037 — E3 Distributed Runtime (M7)

## Mục tiêu
`RuntimeRouter` chọn node theo health → tenant_class → region → capability → capacity → cost → id. Node có `tenant_classes` (empty = serve all). INV-029 Control Plane Isolation: control plane không chạy user execution.

## Phạm vi
- `RuntimeNodeInfo` (id, region, capacity, capabilities, health, version, tenant_classes)
- `NodeRegistry` (register/deregister/get/list/healthy)
- `RuntimeRouter.select(criteria)` + `check_isolation(node, tenant_class)`

## Input/Output
- In: `RoutingCriteria` (tenant_id, region, capability, tenant_class); Out: selected `RuntimeNodeInfo`

## Tiêu chí chấp nhận (AC)
1. INV-029: node chỉ nhận tenant_class nằm trong `tenant_classes` (empty = all)
2. Select ưu tiên healthy > tenant_class match > region > capability > capacity
3. Node registry thread-safe
4. No node match → raise `NodeNotFoundError`
5. `check_isolation` enforce control-plane boundary
6. Contract `extra=forbid`
7. Test deny unmatched tenant_class
