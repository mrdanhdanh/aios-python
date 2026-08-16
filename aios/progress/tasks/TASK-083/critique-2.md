# TASK-083 — Critique vòng 2 (spec)

> **Critic**: AIOS Orchestrator | **Ngày**: 2026-08-16 | **Trạng thái**: resolved

## P1 — Phải sửa

### C2-01. Distiller ghi file ra out_dir — nếu out_dir đã có file cũ (no-overwrite)?
→ **Resolve**: deterministic no-overwrite (giống M8 devkit): nếu `SKILL.md`/`manifest.json` đã tồn tại → `SkillDistillError` (fail-closed, không ghi đè). Test.

### C2-02. R7 verify "artifact non-empty" — chuẩn gì cho dir không phải static site?
→ **Resolve**: chuẩn: dir tồn tại + ≥1 file + (index.html HOẶC total_bytes > 0); không đòi index.html cứng (artifact dir cũng hợp lệ). Fail-closed: dir thiếu/rỗng → BLOCKED.

### C2-03. R5 fetch stub tree — manifest.json trong tree có thể thiếu; synthesis phải tự sinh
→ **Resolve**: tree stub chỉ có SKILL.md + src/ + tests/ (KHÔNG có manifest.json sẵn) — synthesis chịu trách nhiệm sinh manifest đủ field. Kiểm chứng pipeline 7 bước thật.

## P2 — Nên sửa

### C2-04. Capability keywords — nguồn deterministic nào?
→ **Resolve**: quét nội dung SKILL.md stub (đã có từ tree) cho keywords `sprite|pixel|game|canvas|audio|animation|map|tileset` (mirror CREATIVE_TRIGGERS R6) — trả sorted list.

### C2-05. `deploy --apply` có cần verify trước không?
→ **Resolve**: có — deploy luôn chạy verify trước (fail-closed): verify fail → không apply, trả BLOCKED.

## P3 — Ghi nhận

### C2-06. Có cần `aiagent deploy` hiển thị hint CI (pages.yml)?
→ Resolve: ghi nhận — report thêm `hint: str` (GitHub Pages deploy suggestion) — DX nhẹ, không bắt buộc.

## Kết luận
Spec v2 sau resolve → **APPROVED — được phép implement** (đủ 2 vòng).
