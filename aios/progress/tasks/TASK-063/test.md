# TASK-063 — Test (M10-F1)

> Phần v1 (docs redraw): script node 21/21 PASS (xem lịch sử cuối file). Phần v2 (M10-F1) test bên dưới.

## Test v2 (M10-F1) — 2026-08-15

Script `check_m10.py` (python thuần) kiểm tra AC1–AC7:

| # | Kiểm tra | Kết quả |
|---|----------|---------|
| AC1 | 6 file `docs/architecture/*` tồn tại | ✅ 6/6 |
| AC2 | layer-model.md đủ 7 tầng L1..L7 đúng thứ tự | ✅ 7/7 |
| AC3 | constitution-1.0.md chứa INV-001..INV-034 (34 invariant) | ✅ 34/34 |
| AC4 | Mọi INV có enforcement test trong test_architecture.py | ✅ (bổ sung `test_inv008_artifact_first` + `test_inv012_context_budget` — 2 invariant trước đó chỉ enforce gián tiếp) |
| AC5 | Freeze declaration + renumber deferred (AIOS 2.0) | ✅ |
| AC6 | Không block ```mermaid trong 7 file | ✅ |
| AC7 | architecture-v2.md có section 15 (M10) + link docs/architecture/ | ✅ |

**Kết quả: 19/19 PASS** (lần đầu 18/19 — 2 INV thiếu enforce test → bổ sung 2 test, chạy riêng 2/2 pass).

## Regression
- `test_architecture.py` thêm 2 test: `test_inv008_artifact_first` + `test_inv012_context_budget` — **2/2 pass**.
- Full suite: **1815 passed** (baseline 1793 + 22 mới).

## Lịch sử v1 (docs redraw) — 2026-08-15

Script node `check-markdown.js`: không còn ```mermaid, code fence cân bằng, heading duy nhất, đủ 15 mục, bảng hợp lệ, đủ INV-001..034, đủ M0..M10 — **21/21 PASS**; đối chiếu PROGRESS.md khớp.
| M0–M9 `done`, M10 `todo` | ✅ khớp PROGRESS.md 2026-08-15 |
| Số liệu tests M1..M9 (428/669/689+12+19/809/1086/1521/1560/1639/1780) | ✅ khớp bảng milestone + tasks |
| Coverage (95.76/95.51/94.92/95.22/95.35/95.05/94.46) | ✅ khớp |
| INV-001..034: M2=001-010, M5=011-016, M6=017-021, M7=022-029, M9=030-034 | ✅ khớp nhãn canonical (PROGRESS.md §M7 note) |
| Task id M1–M9 (TASK-002..062) + số tests từng task | ✅ khớp PROGRESS.md |

## 3. Kiểm tra tham chiếu file cũ (AC6)

- `docs/architecture.md` KHÔNG bị sửa (git status chỉ thấy file mới + aios/progress/).

## Kết luận

**PASS 21/21** — đủ điều kiện đánh giá.
