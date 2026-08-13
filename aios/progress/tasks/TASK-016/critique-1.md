# Critique vòng 1 — TASK-016 (Architecture Hardening: Invariants + Reference)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 1) | Spec: `spec.md`

## Đánh giá chung

**3/5 — cần sửa trước khi implement.** Phần khả thi (AST scan, pytest collection, AC8) đã verify đúng hướng; 4 invariant INV-003/004/005/010 hiện pass thật trên code. Nhưng có 1 claim sai sự thật làm test không thể pass (INV-009), 1 rationale sai làm giảm giá trị enforcement (INV-007), thiếu chốt semantic scanner (conditional import).

## Vấn đề (13) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C1-01 | Critical | INV-009 claim "có sẵn" sai: chỉ 5/9 service emit events (execution, artifacts, permissions, policy, events); context/state/resource/scheduler KHÔNG tham chiếu EventType → test fail hoặc vô nghĩa | Hard test cho 5 service đã emit ("lifecycle quan trọng"); warning/future cho 4 service còn lại; bảng ghi "test một phần ⚠️" |
| C1-02 | Major | INV-007 rationale sai: `execution.py` ĐÃ import + gọi `self._policy.evaluate()` (dòng 138) → policy-first đã enforce | Đổi thành **hard test** (assert PolicyService trong execution.py — pass); bỏ cơ chế warning mơ hồ |
| C1-03 | Major | Rule INV-005 thiếu: không chặn `orchestrator/**` import provider cụ thể (openai/ollama) kể cả planner | Thêm rule B: `orchestrator/**` (KỂ CẢ planner) không import `openai`, `ollama`, `aios_core.models.openai_provider`, `aios_core.models.ollama_provider`; rule A giữ nguyên (models trừ planner); ghi rõ AST chỉ check direct imports |
| C1-04 | Major | Conditional import/TYPE_CHECKING chưa chốt semantic — có thể tạo lỗ hổng enforcement | **Mọi Import node đều tính** (top-level, trong function, try/except, TYPE_CHECKING) — đều tạo coupling thật; test assert PHÁT HIỆN import lậu trong try/except (không phải "không crash") |
| C1-05 | Major | Rules liệt kê module lẻ bỏ sót `__init__.py` | Chuyển **directory scan**: quét mọi `*.py` trong thư mục (kể cả `__init__.py`) trừ exclude list tường minh; INV-005 scan toàn `orchestrator/` kể cả `goals/` |
| C1-06 | Major | Architecture Health (M4, đề xuất #10) không có mục In/AC → dễ bị drop | Thêm vào In (PLAN.md): ghi chú Architecture Health → M4 + mở rộng AC5 |
| C1-07 | Minor | INV-010 test trùng subset INV-005 → "test ✅" gây hiểu lầm | Mở rộng INV-010: thêm `catalog/`, `knowledge_graph/`, `prompts/` (verify: hiện sạch) — deterministic-first phủ rộng hơn |
| C1-08 | Minor | `skipif not exists` cần định nghĩa hằng số | `AGENTS_DIR = SRC_ROOT/"aios_core"/"agents"`, `TOOLS_DIR = SRC_ROOT/"aios_core"/"tools"` + comment TASK-013/014 tạo đúng tên |
| C1-09 | Minor | `collect_imports` return type không đủ; không nên dùng sys.path | Trả 2 tập: `external_top_level: set[str]` + `aios_core_modules: set[str]` (resolve thuần từ relative); CẤM sys.path |
| C1-10 | Minor | INV-002 test hiện là placeholder (tools/ chưa tồn tại) | Ghi rõ: enforcement thật khi agents/+tools/ tồn tại (TASK-013/014); test hiện tại là tiền đề (capabilities/ không chứa aios_core.tools) |
| C1-11 | Minor | Coverage/collection: test mới không được import aios_core runtime | Ghi ràng buộc: `_arch_scan.py` + `test_architecture.py` KHÔNG import aios_core runtime (chỉ ast.parse); không thêm `tests/__init__.py` |
| C1-12 | Minor | INV-006 Contract First trống | Thêm 1 AST purity check: `contracts/` không import `kernel.services`/`kernel.events` (contract thuần) — ghi "manual review + purity check" |
| C1-13 | Minor | AC8 cần chi tiết temp package | Chốt: AC8 dùng `tmp_path` + file đơn (`evil.py`) — helper resolve thuần đường dẫn; không cần `__init__.py` |

## Kết luận

- [x] **Cần sửa trước khi implement** — 1 Critical + 5 Major + 7 Minor (resolve cùng đợt).
- **Trạng thái: RESOLVED 13/13** (spec.md đã cập nhật).
