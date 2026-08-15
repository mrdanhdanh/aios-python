# TASK-047 — Evaluation

> Bổ sung hồi tố 2026-08-15 khi đóng hard gate (evaluation ban đầu ghi trong LOG.md).

## Đối chiếu acceptance criteria
1. **Đạt** — `create_scaffold` tạo đúng 5 file cho plugin.
2. **Đạt** — Manifest YAML hợp lệ (id, version, aios range, provides, permissions).
3. **Đạt** — Stub plugin.py import được (compile).
4. **Đạt** — Kind không hợp lệ → lỗi rõ.
5. **Đạt** — Overwrite file tồn tại → lỗi (refusing to overwrite).
6. **Đạt** — Deterministic (cùng input → cùng output bytes).
7. **Đạt** — Test scaffold structure + compile + deterministic + kind validation (`tests/test_ecosystem_devkit.py`).

## Kết luận
TASK-047 đạt phạm vi Developer Kit (E5): developer bên ngoài có thể `aios create plugin/agent/capability/tool/workflow` với scaffold deterministic, stub dùng SDK public — nền cho trải nghiệm "không cần sửa AIOS Core".
