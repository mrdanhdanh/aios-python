# TASK-047 — Developer Kit (M8-E5)

## Mục tiêu
Developer tạo plugin/agent/capability mới bằng scaffold: `aiagent plugin create <kind> <name>` sinh `aios.plugin.yaml` + `src/<name>/plugin.py` + `tests/` + `README.md` + `pyproject.toml`.

## Phạm vi
- `ecosystem/devkit.py`: `DevKit.create_scaffold(kind, name, out_dir)` — kinds: plugin (integration), agent, capability, tool, workflow.
- Template nhỏ deterministic (không dependency bên ngoài).
- Không chạy dev server (M8 v1: chỉ scaffold — `aios dev` để M10/CLI wiring sau).

## Input/Output
- Input: kind, name, out_dir.
- Output: cây thư mục + manifest yaml + module python stub + README.

## Tiêu chí chấp nhận
1. create_scaffold tạo đúng 5 file cho plugin.
2. Manifest YAML hợp lệ (id, version, aios range, provides, permissions).
3. Stub plugin.py import được (compile).
4. Kind không hợp lệ → lỗi rõ.
5. Overwrite file tồn tại → lỗi (không ghi đè).
6. Deterministic (cùng input → cùng output bytes).
7. Test: scaffold structure + compile + deterministic + kind validation.
