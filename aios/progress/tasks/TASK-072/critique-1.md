# TASK-072 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-072.

## Các vấn đề

### C1-01 (P1) — Timeline "goal→plan→agent→capability→tool→result→evaluation" dữ liệu từ đâu cụ thể?
→ **Resolve**: Mỗi step có `{seq, type (goal/plan/agent/capability/tool/result/evaluation), label, ts}`; nguồn: metrics table (workflow rows: execution_id, name, started/finished), events (TOOL_STARTED/TOOL_FINISHED, ARTIFACT_CREATED, GOAL_*, EVALUATION). API `/m10/timeline?limit=50` trả `[{execution_id, steps: [...]}]` — DB rỗng → [].

### C1-02 (P2) — Overview shape phải khớp backend endpoints có sẵn
→ **Resolve**: Dùng: HealthDoctor.report (health_score), SloEngine.check (release_ready), SecurityChecker (blocking), ContractChecker (breaking_count) — backend gom vào 1 endpoint `/m10/overview`.

### C1-03 (P3) — 11 tabs: giữ tab cũ hay thay?
→ **Resolve**: Giữ đủ view cũ (Chat/Events/Tools/Memory/Artifacts/Skills/Models/Prompts/Health/Workflow) — thêm Overview + Autonomy + Agents + Knowledge + Harness + Enterprise + Ecosystem + System = tổng 11 tabs nhóm (một số view cũ nằm trong nhóm Operations). App.tsx giữ các view cũ trong nhóm — không xóa.

## Kết luận
Resolve vào spec v2.
