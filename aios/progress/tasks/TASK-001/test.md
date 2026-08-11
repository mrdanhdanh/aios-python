# Test — TASK-001

> Chạy các bước verify theo checklist B4 của `tasks.md`. Kết quả ghi tại đây.

## B4.1 — Git (tự động)
```bash
git log --oneline          # phải có commit M0
git status                 # working tree sạch sau commit
```
- [x] Pass — 2 commit: e50b715 (Bước 0) + 08f1efa (M0 đầy đủ)
- [x] Pass — working tree sạch

## B4.2 — Agent picker (thủ công, cần người dùng)
- Mở VS Code → chat → agent picker → kiểm tra **"AIOS Orchestrator"** xuất hiện và chọn được
- Chọn AIOS Orchestrator → kiểm tra subagent list có: **spec-writer, critic, reviewer**
- [ ] Pass — "AIOS Orchestrator" chọn được
- [ ] Pass — đủ 3 subagent

## B4.3 — Hard gate (thủ công)
- Gửi yêu cầu "implement X" cho một task CHƯA có spec + critique (VD: tạo task mới bỏ qua spec)
- Mong đợi: agent TỪ CHỐI implement, nêu rõ thiếu bước nào
- Gửi một fix nhỏ (VD: sửa typo trong file) → mong đợi: làm được + LOG.md có entry `[bypass]` kèm lý do
- [ ] Pass — hard gate từ chối đúng
- [ ] Pass — bypass ghi log đúng

## B4.4 — Frontmatter (tự động kiểm tra nội dung)
- [x] Pass — 4 file `.github/agents/` có YAML frontmatter giữa `---`, description có quote, `user-invocable` đúng (orchestrator=true, subagent=false), tools hợp lệ (read/edit/search/execute/todo/agent/web), agents restriction [spec-writer, critic, reviewer]

## B4.5 — Progress khớp thực tế
- [ ] Pass — PROGRESS.md: B0–B2 done, B3/B4 theo trạng thái hiện tại
- [ ] Pass — LOG.md có entry tương ứng từng bước

## Kết luận
- [ ] TẤT CẢ PASS → task được đánh dấu done
- [ ] CÓ FAIL → ghi rõ bước fail + xử lý trước khi done
