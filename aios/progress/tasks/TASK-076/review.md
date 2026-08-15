# TASK-076 — Review (pre-implementation)

> Ngày: 2026-08-15 · Reviewer: subagent `reviewer` · Giai đoạn: trước implement (hard gate)

## Kết luận

**APPROVED** — không có P1/P2 blocking. Spec v3 sau 2 vòng critique đã đủ rõ, thứ tự tasks hợp lý (context → hard gate → v3 → v2 → test → DoD).

## Xác minh dữ liệu (reviewer đối chiếu nguồn sự thật)

- ✅ AC4 ánh xạ id↔module M10: khớp 100% PROGRESS.md (`063,064,065,066,069,067,068,070,071,072,075,073,074`)
- ✅ Số liệu M10: 1939 pass, vitest 13/13, conformance READY, doctor 100/100, review ACCEPTED, coverage M10 = N/A
- ✅ Module path M10: có trong LOG.md (`autonomous/safety.py`, `kernel/kill_switch.py`, `kernel/{hardening,durability}.py`, `observability/slo.py`, `harness/certification/*`, `upgrade/migration.py`, `api/routers/m10.py`, `contracts/{catalog,check}.py`)
- ✅ 7 tầng L1..L7 khớp layer-model.md frozen; premise "v2 sai" chính xác
- ✅ 4 plane có nguồn từ control-plane.md + execution-plane.md + autonomy.md (frozen)
- ✅ 12 bước + từ khóa AC11 đủ trong v2 §4; INV-001..034 + Gate A–E đủ trong v2 §12/§15.3
- ✅ AC12: `docs/architecture/` đúng 6 file; `.gitignore` đã có `node_modules/` → AC8 không ô nhiễm git

## AC kiểm tra được

- AC8 (mermaid+jsdom pure JS trên Windows) ✅ — `aios/tools/` chưa tồn tại, phải tạo (không blocking)
- AC11 (grep theo khối) ✅ — tách fence rồi check từng khối, hết false-positive
- AC13 ✅ — lưu ý §11.1 v2 có dòng range `TASK-035..042`/`TASK-045..049`/`TASK-050..062` + dòng đặc biệt (`669+`, `1780 @M9`) → v3 giữ nguyên văn; script normalize whitespace + trim

## Ghi nhận P3 (cải thiện, không chặn done — implementer phải xử lý)

- **P3-1** — AC11 chỉ phủ 5/10 khối; stateDiagram (Safety chain) + sequenceDiagram (Kill Switch) không có AC keyword riêng → phủ gián tiếp qua parse + AC6; post-implement test phải đọc kỹ 2 khối này
- **P3-2** — AC13 chỉ phủ bảng tasks M1–M9, không phủ bảng milestones M0–M9 (428/669/689/809/1086/1521/1560/1639/1780) → spot-check thêm 3–5 dòng bảng milestones trong test
- **P3-3** — tasks.md Bước 1 nên đọc thêm `docs/architecture/AIOS-1.0.md` + `control-plane.md` + `execution-plane.md` (nguồn sơ đồ 4 plane + INV-030/005)
- **P3-4** — luồng request bước 12: theo v2 §4.2 (bước 12 = Observability) — KHÔNG vẽ 13 bước
- **P3-5** — AC2 "≥ 8 khối" vs tasks 10 sơ đồ: không mâu thuẫn; test script không hardcode đúng 8

→ Tất cả P3 đã đưa vào tasks.md/test plan trước khi implement.
