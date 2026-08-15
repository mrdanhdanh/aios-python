# TASK-071 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-071.

## Các vấn đề

### C1-01 (P1) — Doctor 18 hạng mục phải kiểm tra THẬT, không hard-code PASS
Nếu chỉ trả "ok" cho mọi thứ → vô nghĩa.
→ **Resolve**: Mỗi hạng mục có check cụ thể: Runtime (RuntimeKernel.create + start/stop), Contracts (ContractChecker matrix — TASK-064), Registry (model/agent/capability list), Models (ModelRegistry default), Memory (ConversationMemory connect), Knowledge (KnowledgeMemory connect), Filesystem (artifact dir writable — tempfile), Sandbox (pool init), Tools (registry list), Plugins (PluginRegistry db), Policies (PolicyService), Permissions (PermissionService), DB (audit db connect), Events (EventBus publish/subscribe), Scheduler (SchedulerService), Autonomy (AutonomyManager present), Harness (harness_registry 6), Enterprise (EnterpriseManager present).

### C1-02 (P2) — Health score công thức
→ **Resolve**: score = round(100 * pass/total) với total = pass+warn+fail (SKIPPED không có); FAIL trừ điểm tương đương.

### C1-03 (P3) — execution list đọc từ đâu?
→ **Resolve**: MetricsService.recent(limit) (đã có) + status field từ events — DB rỗng → `<empty>`.

## Kết luận
Resolve vào spec v2.
