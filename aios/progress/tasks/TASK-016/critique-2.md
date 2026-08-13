# Critique vòng 2 — TASK-016 (Architecture Hardening)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 2) | Spec: `spec.md` (đã sửa sau vòng 1)

## Đánh giá chung

**3.5/5 — cần sửa trước khi implement (nhẹ hơn vòng 1).** Verify v1: 10/13 đúng, 3/13 thiếu (C1-02, C1-05, C1-10), 0 sai hoàn toàn. Phát hiện 1 lỗ hổng enforcement P1: `models/__init__.py` re-export `OpenAIModel`/`OllamaModel` → rule B có thể bị bypass bằng `from aios_core.models import OpenAIModel`.

## Mục A — Verify 13 resolutions v1

10/13 đúng (kèm bằng chứng code), 3 thiếu: C1-02 (INV-007 cần assert call-site), C1-05 (section 4 còn text cũ liệt kê file lẻ), C1-10 (nhãn INV-002↔INV-004 lẫn + premise test thiếu).

## Mục B — Vấn đề mới (10) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C2-01 | P1 | Rule B bypass: `from aios_core.models import OpenAIModel` (re-export qua `__init__`) không khớp prefix nào; startswith trần chặn nhầm | **Allow-list cho planner**: chỉ được import `aios_core.models.base` + `aios_core.models.errors`; mọi module khác dưới `models` (kể cả `models` trần vì __init__ re-export) đều cấm; semantics **dot-boundary** (`mod == target OR mod.startswith(target + ".")`); thêm test vi phạm `from aios_core.models import OpenAIModel` → fail |
| C2-02 | P2 | INV-009: events.py là chính hạ tầng event (không phải business emit) — đếm 5/9 thổi phồng; state có lifecycle thật (snapshot do execution emit) | Tách: events.py = infrastructure (loại khỏi phép đếm); hard test = 4 business services (execution/artifacts/permissions/policy); 4 future giữ (context/state/resource/scheduler) + ghi chú snapshot do execution emit; bảng "4/8 business + infra events; 4 future" |
| C2-03 | P2 | INV-002/INV-004 lẫn nhãn 3 chỗ; premise test thiếu | (1) In #2 sửa nhãn → INV-004 (capabilities/ không chứa aios_core.tools); (2) section 4 sửa INV-002 = "agents/ không import aios_core.tools trực tiếp"; (3) thêm `test_inv004_capability_no_tools_premise` (chạy ngay, không skip) |
| C2-04 | P2 | INV-007 mơ hồ import vs call-site; text "warning" còn sót | Test assert **call-site** `self._policy.evaluate(` trong execution.py (AST Attribute); xóa cụm "test warning nếu không" |
| C2-05 | P2 | Section 4 liệt kê file lẻ, không đồng bộ dir-scan | Thống nhất cú pháp: `workflow/**` (dir scan kể cả `__init__.py`) cho INV-003/004/005/010 |
| C2-06 | P2 | 12 điểm user không được map → không kiểm chứng được | Thêm **bảng map 12 điểm → file/đoạn sửa → AC**; bổ sung AC riêng: Execution Plane tách khỏi Control Plane (sơ đồ + text), Evaluation là post-execution observer; 12 điểm: #1 Orchestrator≠God, #2 Agent→Cap→Tool enforced, #3 10 INV, #4 dependency 1 chiều, #5 Evaluation observer, #6 KB vs KG, #7 Context vs Memory, #8 Scheduler/Resource/Execution, #9 System Brain, #10 Architecture Health M4, #11 Execution Plane, #12 kiến trúc cuối tham chiếu |
| C2-07 | P3 | PLAN.md ADR index (dòng 231-232) không cập nhật | AC5 thêm: cập nhật danh sách ADR thêm 0004 |
| C2-08 | P3 | architecture.md bảng tiến độ stale (428 tests, TASK-012 "đang test") | Cập nhật bảng trạng thái: 490 tests, 95.96%, TASK-012 done |
| C2-09 | P3 | ADR-0004 copy nội dung architecture.md tạo 2 nguồn sự thật; overclaim sandbox | ADR-0004 tham chiếu (không copy) + ghi gap: `sandbox_required` chưa enforce v1 (execution.py chỉ logger.warning) |
| C2-10 | P3 | SRC_ROOT chưa định nghĩa; evil.py cần absolute import | `SRC_ROOT = Path(__file__).resolve().parents[2] / "src"` (từ tests/); evil.py dùng `import aios_core.models` (absolute) |

## Kết luận

- [x] **Cần sửa trước khi implement**: C2-01 (P1) + C2-02..06 (P2) + P3 cùng đợt.
- Các claim INV-003/004/007/010/006 đã verify pass thật trên code — phần khả thi vững.

**Trạng thái: RESOLVED 10/10** (spec.md đã cập nhật).
