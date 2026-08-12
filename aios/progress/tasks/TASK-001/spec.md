# TASK-001 — M0: Development Foundation

## Mục tiêu
Thiết lập nền tảng phát triển dự án AIOS: repo git có master plan, VS Code custom agent "AIOS Orchestrator" làm Development Control Plane, và hệ thống progress/log bắt buộc (`aios/progress/`) để mọi công việc tiếp theo đều có kế hoạch, có dấu vết, đánh giá được — không phụ thuộc bộ nhớ phiên chat.

## Phạm vi
- **In**:
  1. git repo khởi tạo + `docs/PLAN.md` (plan v6) + `AGENTS.md` + `.gitignore` + commit đầu tiên
  2. 4 VS Code custom agent: `aios-orchestrator` (user-invocable), `spec-writer`, `critic`, `reviewer` (subagent)
  3. Hệ thống progress: `PROGRESS.md`, `LOG.md`, `STATS.md`, template `tasks/TASK-xxx/` (8 file)
- **Out (không làm)**: M1+ (backend Python, contracts, kernel...) — chỉ nền tảng phát triển

## Yêu cầu chi tiết
1. Master plan v6 đầy đủ nằm tại `docs/PLAN.md`, git-tracked
2. `AGENTS.md` bắt buộc mọi agent: đọc repo trước, ghi repo sau, hard gate 8 bước, bypass chỉ cho fix nhỏ
3. Agent AIOS Orchestrator: chọn được trong agent picker, có đủ 8 luật hard gate + decision pipeline + quy tắc subagent
4. Subagent: spec-writer (template spec), critic (2 vòng, P1/P2/P3 + resolution), reviewer (AC đối chiếu + APPROVED/CHANGES REQUESTED)
5. `aios/progress/`: PROGRESS.md (chỉ mục trạng thái), LOG.md (entry mới nhất đầu bảng), STATS.md (chỉ số)
6. TASK-001 tự nó trải qua đủ 8 bước hard gate — dogfooding

## Input / Output
- Input: plan v6 (từ phiên thiết kế), quyết định vận hành (Start Implementation cho M0, repo = nguồn sự thật)
- Output: cấu trúc repo như M0 mô tả + commit history rõ ràng

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: `git log` có commit đầu tiên chứa PLAN.md + AGENTS.md + .gitignore
- [ ] AC2: Tồn tại 4 file `.github/agents/*.agent.md` với frontmatter hợp lệ (description quoted, name, tools, user-invocable đúng)
- [ ] AC3: Trong agent picker VS Code xuất hiện "AIOS Orchestrator" và chọn được
- [ ] AC4: Hard gate hoạt động — yêu cầu implement task không có spec+critique → orchestrator từ chối và nêu lý do
- [ ] AC5: TASK-001 có đủ 8 file: spec, critique-1, critique-2, tasks, review, implementation, test, evaluation
- [ ] AC6: PROGRESS.md/LOG.md phản ánh đúng trạng thái thực tế (B0–B2 done, B3–B4 tương ứng)
- [ ] AC7: Mọi thay đổi M0 đã commit

## Phụ thuộc
- Git đã cài (kiểm tra: `git --version` → 2.55.0 — ok)
- VS Code Insiders hỗ trợ AGENTS.md + custom agents (có từ 1.99+)

## Rủi ro
- R1: AGENTS.md không được agent đọc tự động ở một số phiên bản → giảm thiểu: kiểm tra lúc verify (B4), fallback thêm `.github/copilot-instructions.md` trỏ sang AGENTS.md
- R2: Git identity chưa có global → đã set local (AIAGENT Dev); user có thể đổi sau
- R3: Bảng LOG.md khó đọc khi entry dài → chấp nhận cho M0 (ít entry), chuyển list format khi cần

## Constraints
- Phải tuân thủ AGENTS.md: đọc repo trước, ghi repo sau, hard gate 8 bước, bypass chỉ cho fix nhỏ
- TASK-001 tự đi qua đủ 8 bước hard gate (dogfooding)
- Mọi artifact phải git-tracked, không chỉ nằm trong chat session
- Code/commit: tiếng Anh; Tài liệu progress/log: tiếng Việt

## Expected Artifacts
- `docs/PLAN.md` — master plan v6
- `AGENTS.md` — quy tắc bắt buộc mọi agent
- `.gitignore` — bỏ qua file build/temp, KHÔNG ignore `.vscode/`, `.github/agents/`, `aios/progress/`, `docs/`
- `.github/agents/aios-orchestrator.agent.md` — VS Code custom agent (user-invocable)
- `.github/agents/spec-writer.agent.md` — subagent viết spec
- `.github/agents/critic.agent.md` — subagent phản biện 2 vòng
- `.github/agents/reviewer.agent.md` — subagent review code
- `aios/progress/PROGRESS.md` — chỉ mục tiến độ
- `aios/progress/LOG.md` — nhật ký hành động
- `aios/progress/STATS.md` — thống kê milestone
- `aios/progress/tasks/TASK-001/` — 8 file: spec, critique-1, critique-2, tasks, review, implementation, test, evaluation
