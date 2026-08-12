# Critique vòng 1 — TASK-010

## Đánh giá chung
Khung tốt, DI-friendly, stats cho verification M2. Nhưng 3 P1 (false positive substring; matcher có thể không bao giờ chạy — mâu thuẫn rule-vs-matcher; llm_calls/AC6 không kiểm chứng được) + 9 P2 + 8 P3. **Sẵn sàng: 3/5.**

## Vấn đề + Resolution

### P1-1 — Keyword substring false positive ("system" khớp "file system")
- **Resolution**: match theo **word-boundary regex** (`re.search(rf"\b{pattern}\b", text.lower())`); **longest pattern wins** (cùng intent); bỏ negative_patterns v1 (token đủ); ghi vào Yêu cầu 2.

### P1-2 — Matcher có thể không bao giờ chạy (rule có agent → dừng cứng) + default_rules() không định nghĩa
- **Resolution**: 
  - **Bảng `default_rules()` đầy đủ trong spec** (8 rule: generate api/coding→coder; medical|doctor→doctor; system status→system_doctor; install skill→skill(agent=None); upgrade→upgrade(None); diagnose→diagnose(None); chat|hello→chat(None); crud→workflow(None))
  - Ngữ nghĩa: rule có agent KHÔNG dừng cứng — **matcher vẫn chạy; template macro khớp → gắn thêm workflow_name** (response có cả 2); rule agent=None → resolved_by="workflow" nếu matcher khớp
  - Rule "crud" agent=None đảm bảo đường tới matcher tồn tại

### P1-3 — llm_calls + AC6 không kiểm chứng được
- **Resolution**: `llm_calls` = số lần `model.chat` thực (PlannerStub không tăng); AC6 dùng **Planner thật + MockModel (TASK-006) đếm calls**; stats thêm `total_requests`; test `reset()`; `stats()` trả bản copy (thread-safe, lock chỉ bao counter không bao LLM call).

### P2 — (áp)
1. **7 intents** (sửa khắp spec): chat, coding, medical, system, skill, upgrade, diagnose
2. **Intent canonical "medical"** (alias "khám bệnh"/"doctor"/"medical" → medical); selector medical→doctor
3. **AgentSelector nối luồng**: `agent = rule.agent or selector.select(intent)`; skill/upgrade/diagnose → agent None → matcher/planner → fallback general
4. **Normalizer schema**: `normalize(text: str, source: str = "cli")` hoặc dict `{"text", "source", "params"}`; regex params `(\w+)=([^\s]+)` (ghi chú giới hạn); thứ tự: params strip → alias → macro
5. **`!skill` v1**: → intent="skill", params={"skill": name}, dừng pipeline (ghi chú M2 Skill Manager)
6. **Planner**: `plan(request, model, library)` — inject library; catch **ModelError** (gồm ModelTimeoutError); check is_available trước
7. **AC1 6 case liệt kê**: CLI params, alias merge, @workflow, # chat, lowercase/strip, dict input
8. **system_doctor**: Out TASK-012 bổ sung system_doctor (ghi chú)
9. **`#` prefix**: chỉ khi BẮT ĐẦU câu (regex `^#`) — tránh "fix #123"

### P3 — (áp)
1. `resolved_by="normalizer"` khi `#` prefix (chat direct)
2. WorkflowMatcher: first match (library.search insertion order)
3. Đổi field response `stats` → `request_stats` (tránh nhầm với Orchestrator.stats cumulative)
4. `#` chặt (P2-9)
5. AC9 coverage: dùng addopts sẵn có (pyproject) — ghi rõ
6. AC10 "git sạch" → chuyển yêu cầu quy trình (ghi chú)
7. SystemKnowledge: test tiếng Anh; dùng `graph.neighbors(kind="capability", id=...)` (API thật ✓)
8. Matcher phải tách keyword trước search (library.search là substring cả câu — query toàn văn trượt): matcher tách từng token → search từng token

## Kết luận
- [x] **Resolve toàn bộ (3 P1 + 9 P2 + 8 P3)** — cập nhật spec, chuyển critique vòng 2.
