# TASK-065 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-065.

## Các vấn đề

### C1-01 (P1) — 8/12 scenario "chạy được" chưa đủ mạnh — phải định nghĩa chính xác detect/contain/recover/resume từng loại
Mỗi FailureKind khác nhau về cách inject + assert. Nếu chỉ "PASS/FAIL" chung chung → test vô nghĩa.
→ **Resolve**: Mỗi scenario khai báo rõ 4 hook (fault/detect/contain/recover) + resume assert (ví dụ: sau recover, execution trạng thái RUNNING tiếp tục từ node đã checkpoint, snapshot count không tăng). Bảng 12 loại trong spec: inject gì, assert gì.

### C1-02 (P2) — Không phá production code: cần cơ chế inject an toàn
Inject fault vào ModelRegistry/ToolRegistry... nếu viết vào code production → ô nhiễm.
→ **Resolve**: Chỉ dùng test double/hook: mọi fault inject qua tham số của runner (fn đóng gói component thật), KHÔNG sửa file service. Với service SQLite: dùng db_path tạm rồi xóa file giữa chừng.

### C1-03 (P2) — "Resume không chạy lại" cần đo bằng checkpoint count
Assert mơ hồ dễ pass giả.
→ **Resolve**: Scenario process_chết/checkpoint: ghi `state.snapshot_saved` event count trước → fault → recover → resume; assert count tăng đúng 1 lần cho phần mới, không chạy lại toàn bộ.

### C1-04 (P3) — Event consumer chết: contain nghĩa là gì?
Consumer chết → event không xử lý — contain = không crash bus; recover = re-subscribe.
→ **Resolve**: Dùng EventBus subscribe handler raise → bus không crash (handler lỗi bị catch — đã có cơ chế), recover = subscribe lại + event phát lại.

## Kết luận
Resolve vào spec v2 (bảng 12 loại + hook an toàn + đo checkpoint count + consumer semantics).
