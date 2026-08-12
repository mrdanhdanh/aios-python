# Critique vòng 1 — TASK-009

## Đánh giá chung
Khung tốt, 4 module phù hợp gộp 1 task. Nhưng 4 P1 (Prompt regex/{{}} không nhất quán; duplicate overwrite phá versioning; evaluate write-only; mâu thuẫn PLAN persistence/populate) + 7 P2 + 7 P3. **Sẵn sàng: 3/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — Regex `\{(\w+)\}` không nhất quán str.format (false positive `{{name}}`, miss format spec, positional)
- **Resolution**: subset nghiêm ngặt v1: chỉ `{identifier}` thuần; regex extract `(?<!\{)\{([A-Za-z_]\w*)\}(?!\})`; **validate lúc register**: mọi `{`/`}` không thuộc field/escape `{{`/`}}` → PromptError (bắt `{score:.2f}`, `{}`, `{0}`, brace lệch); render bọc KeyError/ValueError → PromptError kèm tên biến; AC ghi rõ output template có `{{`/`}}`.

### P1-2 — Duplicate register → overwrite phá versioning
- **Resolution**: overwrite CHỈ khi trùng `(id, version)`; version khác → thêm entry; "mới nhất" = max theo `semver.compare()` (TASK-003); unknown id VÀ unknown version → PromptError (2 AC test riêng).

### P1-3 — evaluate write-only
- **Resolution**: thêm `evaluations(id, version=None) -> list[PromptEvaluation(version, score, note, timestamp)]` — append history (không overwrite); AC: evaluate 2 lần → 2 entry.

### P1-4 — Mâu thuẫn PLAN (SQLite graph + populate registry)
- **Resolution**: **AMEND `docs/PLAN.md`** (cập nhật note): graph v1 in-memory + populate thủ công; SQLite persist + auto-sync/auto-build → M4/M2 (ghi rõ quyết định vào PLAN + PROGRESS — không lệch plan âm thầm).

### P2 — (đặc tả)
1. **Catalog search**: đệ quy dict/list, so `str(value).lower()` scalar (key KHÔNG search); kind filter = exact; kết quả sorted (kind, id); query rỗng → trả toàn bộ
2. **neighbors**: dedup (set, giữ thứ tự ổn định); reverse lookup trả (relation gốc, đầu kia); AC test 2 chiều
3. **add_edge missing node → GraphError** (không auto-create node ma); AC riêng
4. **find**: property tầng 1 (nested → Out); property_value=None → bỏ qua value (trả node có key); so sánh `==` đúng kiểu
5. **agents_using**: giữ — pin: register_agent_use capability unknown → CapabilityError; trùng (agent, capability) → idempotent set; **ghi chú: M2 graph populate đọc từ registry (registry là nguồn chính)**
6. **bind_tool**: tool_id string tự do (chưa có Tool Registry — ghi chú); Out thêm "auto-discovery từ ToolContract scan → M2"
7. **Graph version**: quy ước properties chứa key "version" (không bắt buộc, ghi chú)

### P3 — (áp)
1. Capability.get() trả object — document (caller không mutate)
2. bind_tool trùng → idempotent; tools_for unknown → CapabilityError; variables dedup giữ thứ tự; variables tự extract lúc construct (model_validator)
3. AC2 thêm edge case extract ({{}}, format spec); AC3 render assert cụ thể (escape literal, thiếu biến, thừa biến)
4. AC8 chốt: dùng WorkflowLibrary thật (TASK-008) → index/add thủ công → 2-3 query kỳ vọng
5. AC5 tách dedup + missing node thành AC riêng
6. Đồng bộ từ ngữ escape {{ }} (R1 vs Yêu cầu #2)
7. Ghi chú phân biệt knowledge_graph/ vs knowledge/

## Kết luận
- [x] **Resolve toàn bộ (4 P1 + 7 P2 + 7 P3)** — cập nhật spec + amend PLAN.md, chuyển critique vòng 2.
