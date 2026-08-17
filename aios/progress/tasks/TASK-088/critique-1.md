# Critique vòng 1 — TASK-088 (M12-P4: Docs & ADR C5)

> Đối chiếu code thật TASK-084..087 (vừa implement) + docs hiện trạng: `docs/adr/` (0001–0006), `docs/guides/` (chưa tồn tại), `docs/PLAN.md` §M12 (còn nguyên, TASK-088 `todo`; §M13/M14/M15 PLANNED từ session khác), `docs/README.md` (chưa có link guide).

## Đánh giá chung

Spec nền tốt nhưng 4 điểm cần làm chính xác: version policy mapping, guide phải nói rõ stub vs `--input`, idempotent per component, PLAN cập nhật không đụng M13/M14. Mức sẵn sàng v1: 3/5.

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C1-01 | P1 | ADR mục "Version policy" thiếu chính xác: `check_upgrade("0.1.0","1.1.0")` = breaking (Rule 4 — 0.x), đường hỗ trợ CHỈ `1.0.0→1.1.0`; `__version__` hiện tại = "1.1.0" | **RESOLVED** — ADR ghi rõ 3 cột: dev `0.1.0` (lịch sử, không thuộc đường nâng cấp) / release `1.0.0` (M10) / hiện tại `1.1.0` (M12); đường hỗ trợ chính thức `1.0.0 → 1.1.0` minor backward-compatible |
| C1-02 | P1 | Guide bước apply mơ hồ: CLI `migrate <kind> 1.0.0 1.1.0 --apply` dùng stub MẶC ĐỊNH (plugin demo/workflow demo_flow/contract agent) — người dùng dữ liệu thật phải `--input file.json`; nếu không sẽ migrate nhầm stub | **RESOLVED** — Guide: bước 3 ghi rõ stub default + cảnh báo "dữ liệu thật phải dùng --input" + ví dụ lệnh đầy đủ |
| C1-03 | P1 | Guide thiếu: journal idempotent per component (apply lần 2 cùng component → "đã applied" lỗi); backup path (`--journal` đổi → backup db đổi theo); config SKIP matrix (không cần version) | **RESOLVED** — Guide thêm mục "Lưu ý" 3 điểm này |
| C1-04 | P2 | PLAN §M12 cập nhật có thể đụng §M13/M14 (session khác vừa thêm PLANNED) | **RESOLVED** — Chỉ sửa trong §M12: header IN-PROGRESS→DONE + bảng 5 task done; KHÔNG chạm §M13/M14/M15 |
| C1-05 | P2 | README chưa có mục link docs — guide mới cần link được | **RESOLVED** — README: thêm link `docs/guides/migration-1.0-to-1.1.md` + ADR-0007 vào mục phù hợp (nếu có danh sách ADR) |

**Kết quả: 5/5 RESOLVED — spec nâng v2.**

# Critique vòng 2 — TASK-088

> Vòng 2 sau resolve vòng 1 — đối chiếu thêm: `format_conformance` (header/result 1.1), `compat verify` (fail-closed exit 1), `migrate` (matrix pre/post, backup_id), `AiosRange.compatible` (parse-only).

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C2-01 | P2 | ADR/guide phải dùng "AIOS 1.1 READY" (conformance TASK-087 đổi format — không còn "AIOS 1.0 READY"); gate_g là release blocker | **RESOLVED** — Ghi đúng: conformance → 11 areas + 20 GS + 7 gates → "AIOS 1.1 READY"; gate_g_compatibility vi phạm = release blocker |
| C2-02 | P2 | ADR mục "parse-only mở rộng" cần ví dụ chính xác: `AiosRange.compatible` — check min/max KHÔNG đổi (verify bằng `check_compatibility`) | **RESOLVED** — ADR ghi đúng precedent TASK-086 + khẳng định behavior min/max giữ nguyên |
| C2-03 | P3 | Guide bước 1 (compat verify) nên nói rõ fail-closed: bất kỳ check fail → exit 1 → KHÔNG nâng cấp | **RESOLVED** — Guide: "verify fail-closed — 1 check fail = exit 1, dừng lại" |
| C2-04 | P3 | Guide lưu ý: `migrate plugin` thêm `aios.compatible` vào manifest (dữ liệu thay đổi); `migrate config` chỉ thêm marker `migration` | **RESOLVED** — Guide mục "Điều gì thay đổi trên dữ liệu" per kind |

**Kết quả: 4/4 RESOLVED — spec nâng v3 (bổ sung câu chữ). Đủ điều kiện tasks.md + review.**
