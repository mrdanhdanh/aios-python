# Critique vòng 1 — TASK-013 (M2-P3c: Assistants + Safety Layer + System Doctor)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 1) | Spec: `spec.md`

## Đánh giá chung

**4/5 — đạt chất lượng cao, nhưng cần sửa trước khi implement.** 12 AC test được, kế thừa đúng bài học TASK-010/012/016. 1 mâu thuẫn Critical với code thật (INV-002 skip condition), 5 lỗ hổng Major trong thiết kế Coder/Doctor.

## Vấn đề (14) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C1-01 | Critical | `test_inv002` skip condition đòi CẢ agents/ VÀ tools/; tools/ = TASK-014 (out-of-scope) → "0 skip" bất khả thi | **Sửa skip condition `test_inv002_worker_no_direct_tool` thành chỉ `not AGENTS_DIR.is_dir()`** (forbidden target không cần tồn tại) — nằm trong In mục 8; INV-002 bật sớm đúng tinh thần |
| C1-02 | Major | `handle()` bắt exception → response error KHÔNG có disclaimer — vi phạm invariant (a) "mọi response" | Thu hẹp bất biến: "(a) mọi response **ok** của Doctor có disclaimer"; error path thuộc contract chung `handle()` (AC2) — ghi rõ |
| C1-03 | Major | Step contract Coder: unit_test/integration_test cùng key `passed`/`detail` → merge đè nhau, `state["passed"]` không kiểm chứng được | **Mỗi step ghi key riêng theo tên** (`state["unit_test"] = {...}`, `state["integration_test"] = {...}`); `state["passed"]` do pipeline aggregate (`unit.passed and integration.passed`) |
| C1-04 | Major | Default generator nhét requirement raw vào string literal → quote/backslash làm syntax-invalid | **Escape bằng `repr(requirement)`** (hoặc json.dumps) trước khi vào literal; thêm test edge: input chứa dấu nháy → `ast.parse` pass |
| C1-05 | Major | (b) cấm thuốc ∩ (d) không symptom chưa định nghĩa thứ tự; AC8(b) input không có symptom → test nhầm nhánh | **(b) kiểm tra TRƯỚC (d), áp dụng mọi response**; khi cả hai → text = refusal thuốc + câu hỏi thêm + disclaimer, metadata `{"need_more_info": True, "medication_refused": True}`; AC8(b) đổi input "tôi đau đầu, uống paracetamol được không" (có symptom + thuốc) |
| C1-06 | Major | Symptom match nhưng KB-miss → risk=low + self_care = nghịch lý an toàn | **Có symptom nhưng KHÔNG có condition trong KB → `recommendation="see_doctor"` + `need_more_info=True`** (thận trọng); AC9 bổ sung assert risk/recommendation |
| C1-07 | Minor | `dir_imports` không hỗ trợ allow-list toàn package | Loop `AGENTS_DIR.rglob("*.py")` + `collect_imports` + set-diff (không cần sửa `_arch_scan.py`) — ghi rõ mục 8 |
| C1-08 | Minor | `except (ModelError, Exception)` redundant | `except ModelError` trước, `except Exception` sau (phân biệt) |
| C1-09 | Minor | `passed` chỉ phản ánh test, static issues không rõ tác động | Ghi rõ: `passed = unit_test.passed AND integration_test.passed`; static issues là advisory qua metadata |
| C1-10 | Minor | AC6 wording ngược | Viết lại: "step raise → `handle()` bắt → status=error + metadata[error] + finished error; exception không propagate" |
| C1-11 | Minor | `DoctorAssessment.recommendation: str = ""` comment không phải type | Ghi rõ: giá trị ∈ {self_care, see_doctor, emergency}, rỗng khi (d) trigger |
| C1-12 | Minor | SystemDoctor: degraded bị coi fail mất thông tin | Ghi rõ "degraded → coi fail (worst-wins)"; FIX_HINTS generic fallback là chuẩn |
| C1-13 | Minor | Test concurrent registry cần áp dụng bài học #23 | Mỗi thread dùng prefix riêng (`worker-a-{i}` / `worker-b-{i}`) |
| C1-14 | Minor | Đếm bước Coder không nhất quán "8 bước" vs "7 step + loop" | Thống nhất chú thích "7 steps + 1 Self-Fix loop = 8 mục theo PLAN" |

## Kết luận

- [x] **Cần sửa trước khi implement** — 1 Critical + 5 Major + 8 Minor (resolve cùng đợt).
- **Trạng thái: RESOLVED 14/14** (spec.md đã cập nhật).
