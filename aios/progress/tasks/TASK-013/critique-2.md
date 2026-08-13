# Critique vòng 2 — TASK-013 (M2-P3c: Assistants)

> Ngày: 2026-08-13 | Reviewer: critic subagent (vòng 2) | Spec: `spec.md` (đã sửa 14/14 v1)

## Đánh giá chung

**3/5 — chưa sẵn sàng implement.** 12/14 resolution v1 đúng, 2 thiếu (C1-06, C1-09). 11 vấn đề mới (3 P1 + 4 P2 + 4 P3) — 3 P1 đều là AC không thể pass với chính nội dung spec (mâu thuẫn nội tại).

## Mục A — Verify 14 resolutions v1

12/14 đúng; C1-06 thiếu (KB-miss dead code + need_more_info không có chỗ chứa → C2-03/C2-05); C1-09 thiếu (issues không có field → C2-07).

## Mục B — Vấn đề mới (11) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C2-01 | P1 | Danger keyword không phải symptom ("bất tỉnh"/"co giật" không trong KB) → nhánh (d) từ chối thay vì emergency; AC8(c) fail + nguy hiểm an toàn | **Gate (d) thêm điều kiện "VÀ không có danger keyword trong text"**; danger-only → risk=high + recommendation="emergency" + danger keyword đưa vào `symptoms` (template hiển thị) |
| C2-02 | P1 | AC8(b) input "uống paracetamol được không" KHÔNG match pattern nào → (b) không trigger → test fail | **Đổi input AC8(b) thành "tôi đau đầu, nên uống thuốc gì"** (match "thuốc" + "uống gì"); giữ input "uống thuốc gì" (không symptom) cho nhánh (b)∩(d) |
| C2-03 | P1 | Symptom Extractor keyword nguồn không xác định → "KB inject → extractor theo KB" → KB-miss là dead code, AC9 không test được | **Extractor dùng keyword = union(KB keys, DANGER_KEYWORDS)**; KB-miss xảy ra khi keyword match (VD "tê tay" trong text) không có trong KB đang dùng → nhánh C1-06 kích hoạt được; ghi rõ trong 5.4 bước 1 |
| C2-04 | P2 | unit_test exec + gọi main() thiếu namespace contract | Ghi rõ: `ns: dict = {}; exec(code, ns); main = ns.get("main")`; thiếu main → passed=False "no main function"; main() raise → passed=False + detail; syntax fail → passed=False |
| C2-05 | P2 | `need_more_info` không có chỗ chứa (metadata + DoctorAssessment) | Thêm `need_more_info: bool = False` vào DoctorAssessment + metadata line thêm `"need_more_info": bool` — 1 key thống nhất 3 nhánh: (d), (b)∩(d), KB-miss |
| C2-06 | P2 | Allow-list test copy rule B chỉ check aios_mods → external (openai/requests...) lọt lưới | Test check CẢ 2: `aios_mods ⊆ {models.base, models.errors}` VÀ `external_top_level ⊆ {pydantic} ∪ stdlib_allowed` |
| C2-07 | P2 | CoderResult không có field issues — C1-09 "phản ánh qua metadata" không có nơi đựng | Thêm `issues: list[str] = Field(default_factory=list)` vào CoderResult (copy từ `state["static_analysis"].get("issues", [])` vòng cuối) |
| C2-08 | P3 | stdlib list thiếu threading/collections → allow-list test fail nhầm | Liệt kê đầy đủ cho test: `{pydantic, typing, collections, abc, re, logging, ast, dataclasses, enum, threading, functools}` |
| C2-09 | P3 | Feedback embed docstring chưa nói escape | Docstring feedback cũng qua `repr()` — test assert substring feedback raw (repr giữ nguyên) |
| C2-10 | P3 | Comment/reason skipif test_inv002 còn nói TASK-013/014 | Cập nhật comment + reason thành "agents/ chưa tồn tại (TASK-013)" |

## Kết luận

- [x] **Cần sửa trước khi implement** — 3 P1 (mâu thuẫn nội tại spec) + 4 P2 + 4 P3 (cùng đợt).
- **Trạng thái: RESOLVED 11/11** (spec.md đã cập nhật).
