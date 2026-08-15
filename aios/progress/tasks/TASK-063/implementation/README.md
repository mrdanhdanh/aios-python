# TASK-063 — Implementation (M10-F1)

> v1 (docs redraw) artifact: `docs/architecture-v2.md` (bản hiện hành — đã hoàn thành). v2 (M10-F1) artifact dưới đây.

| Artifact | Nội dung |
|----------|----------|
| `docs/architecture/AIOS-1.0.md` | Kiến trúc 1.0 tổng thể + cam kết 10 năng lực + release gates (planned TASK-073) |
| `docs/architecture/layer-model.md` | 7 tầng L1..L7 + bảng package + luồng request + quy tắc tầng |
| `docs/architecture/control-plane.md` | Orchestrator + registries + governance + INV liên quan |
| `docs/architecture/execution-plane.md` | Runtime kernel + workers + tools + sandbox + distributed (M7) |
| `docs/architecture/autonomy.md` | Autonomy Layer + Governor gate + budget/risk + levels |
| `docs/architecture/constitution-1.0.md` | **Constitution 1.0**: 15 core principle + INV-001..034 + freeze + hệ quả |
| `docs/architecture-v2.md` | Cập nhật section 15 (M10) + link tới docs/architecture/ |
| `backend/tests/test_architecture.py` | +2 enforcement test: `test_inv008_artifact_first`, `test_inv012_context_budget` |
| `aios/progress/tasks/TASK-063/check_m10.py` | Script test 19 mục (AC1–AC7) |
