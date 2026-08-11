# Review — TASK-002 (Pre-Implementation: Spec + Breakdown)

## Tổng quan
Spec đã hấp thụ đầy đủ 2 vòng critique. Breakdown C1→C5 phủ 15/16 AC. **CHANGES REQUESTED**: 1 R1 (blocking) + 3 R2 + 4 R3.

## Đối chiếu AC ↔ checklist
15/16 AC có checklist item; **AC1 (pip install) thiếu bước** → R1.

## Vấn đề + Resolution

### R1 — Thiếu bước tạo venv + pip install (Blocking)
- Vấn đề: AC1 không có checklist; C3.6 không chạy được nếu chưa cài deps.
- **Resolution**: thêm **C2.8**: tạo `backend/.venv` + `pip install -e ".[dev]"` (verify AC1; kiểm tra network theo R4 trước khi cài — nếu offline: báo blocked sớm).

### R2-1 — Spec không miễn trừ `AIOS_CONFIG_PATH` khỏi env validation
- Vấn đề: scan env prefix `AIOS_` so field names → `AIOS_CONFIG_PATH` (không phải field) bị coi là env lạ → AC13/AC14 fail.
- **Resolution**: thêm vào Yêu cầu chi tiết mục 2: "env validator phải **whitelist `AIOS_CONFIG_PATH`** (env điều khiển search order, không phải field)".

### R2-2 — `HealthReport.timestamp: datetime = now` là bẫy import-time
- Vấn đề: default `now()` gọi lúc class definition → mọi report chia sẻ timestamp.
- **Resolution**: spec sửa: `timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))` (aware).

### R2-3 — tasks.md thiếu bước ghi test.md + evaluation.md
- Vấn đề: hard gate cần test.md + evaluation.md; breakdown dừng ở commit.
- **Resolution**: thêm **C3.7** "Ghi `test.md` (kết quả pytest thật: số test, coverage %)" + **C5.3** "Ghi `evaluation.md` + cập nhật PROGRESS.md/LOG.md, commit cuối".

### R3-1 — Lệnh tasks.json lệch spec
- **Resolution**: thống nhất dùng `.venv/Scripts/python -m pytest` (chạy được cả khi chưa activate); docs/README ghi rõ 2 cách + lưu ý activate venv.

### R3-2 — `updated` chưa pin hành vi
- **Resolution**: cả `created`/`updated` dùng `default_factory=now(utc)`; helper override `created` khi truyền vào; test xác nhận `updated >= created`.

### R3-3 — JSON field set + log path CWD-relative
- **Resolution**: JSON formatter ghi field set tối thiểu: `ts`, `level`, `logger`, `message`, `correlation_id` (nếu có) — ổn định cho P8; ghi chú log path CWD-relative vào README + .gitignore thêm `backend/aios/logs/` (chặn chạy tay tạo rác).

### R3-4 — Verify .gitkeep được track
- **Resolution**: C1.1 bổ sung verify: `git status` liệt kê đủ `.gitkeep` (git add tường minh).

## Kết luận
- [x] **Resolve toàn bộ (1 R1 + 3 R2 + 4 R3)** — spec + tasks.md cập nhật theo resolution, sẵn sàng implement.

*(Nội dung review gốc do subagent reviewer sinh ra; resolution bởi AIOS Orchestrator.)*
