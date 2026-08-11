# TASK-001 — Breakdown checklist

> Quy ước: `[x]` = đã làm XONG VÀ đã verify (chạy được / kiểm chứng thấy kết quả), không chỉ viết xong.

## B0 — Nền móng repo
- [x] B0.1 git init + git config local (user.name/email)
- [x] B0.2 `docs/PLAN.md` — plan v6 đầy đủ (sao chép từ session, git-tracked)
- [x] B0.3 `AGENTS.md` — quy tắc bắt buộc mọi agent (nguồn sự thật, hard gate, log/commit)
- [x] B0.4 `.gitignore` (chỉ ignore `.vscode/settings.json` cá nhân, KHÔNG ignore cả `.vscode/`)
- [x] B0.5 commit đầu tiên (e50b715)

## B1 — VS Code custom agents
- [x] B1.1 `aios-orchestrator.agent.md` — persona + decision pipeline + hard gate + bypass + subagent rules
- [x] B1.2 `spec-writer.agent.md` — template spec.md chuẩn
- [x] B1.3 `critic.agent.md` — 2 vòng phản biện, P1/P2/P3 + resolution
- [x] B1.4 `reviewer.agent.md` — đối chiếu AC + APPROVED/CHANGES REQUESTED

## B2 — Progress system
- [x] B2.1 `PROGRESS.md` — chỉ mục milestones/tasks/trạng thái
- [x] B2.2 `LOG.md` — nhật ký (entry mới nhất đầu bảng)
- [x] B2.3 `STATS.md` — chỉ số + mục Bài học
- [x] B2.4 `tasks/TASK-001/` — 8 file hoàn chỉnh (spec, critique-1/2, tasks, review, implementation, test, evaluation)

## B3 — Commit M0
- [ ] B3.1 Commit toàn bộ thay đổi M0 (agent files + progress + fixes từ critique)

## B4 — Verify M0
- [ ] B4.1 Git: `git log` có đủ commit, working tree sạch
- [ ] B4.2 Agent picker: chọn được "AIOS Orchestrator" + 3 subagent hiển thị
- [ ] B4.3 Hard gate: yêu cầu implement không có spec/critique → từ chối + nêu lý do
- [ ] B4.4 Frontmatter: đủ 4 file, description quoted, không lỗi YAML
- [ ] B4.5 PROGRESS.md/LOG.md khớp trạng thái thực tế
