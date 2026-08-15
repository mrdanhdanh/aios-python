# TASK-071 — M10-F7: Developer Experience 1.0 (command tree + doctor first-class)

## Mục tiêu
PLAN §M10-27/28: gom CLI thành command tree thống nhất; `aiagent doctor` first-class kiểm tra 18 hạng mục (Runtime/Contracts/Registry/Models/Memory/Knowledge/Filesystem/Sandbox/Tools/Plugins/Policies/Permissions/DB/Events/Scheduler/Autonomy/Harness/Enterprise) → output `✓/⚠/✗ + Health: 94/100`.

## Phạm vi
- `cli/` package (backend/src/aios_core/cli/): `doctor.py` (DoctorFirstClass — 18 hạng mục, mỗi hạng mục PASS/WARN/FAIL + score /100), `system.py` (system status: version, services, health)
- Mở rộng `workflow/cli.py` (additive): `aiagent doctor` (nâng cấp output first-class), `aiagent health` (alias), `aiagent system status`, `aiagent goal list`, `aiagent execution list`, `aiagent skill list`, `aiagent capability list`
- `execution list`: đọc metrics/state → danh sách execution gần đây

## Ngoài phạm vi
- Không đổi lệnh hiện có (chỉ thêm + nâng cấp doctor output giữ JSON cũ cho tương thích test)

## Input
- `observability/doctor.py` (HealthDoctor), `workflow/cli.py` hiện có, `config.py`

## Output
- `backend/src/aios_core/cli/{__init__,doctor,system}.py` + CLI mở rộng + `tests/test_cli_m10.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | DoctorFirstClass có ĐỦ 18 hạng mục (đúng tên PLAN §M10-28) | Test set compare |
| AC2 | Mỗi hạng mục PASS/WARN/FAIL + không crash khi thiếu component (tự dựng tối thiểu) | Test kernel thật |
| AC3 | Health score = round(100 * pass/(pass+warn+fail)) — ổn định | Test |
| AC4 | `aiagent doctor` in bảng 18 hạng mục + `Health: N/100`; JSON cũ vẫn chạy (tương thích) | CLI thật + test cũ pass |
| AC5 | `aiagent health` = alias doctor | Test |
| AC6 | `aiagent system status` in version + services + emergency flag | CLI thật |
| AC7 | `aiagent goal list` + `skill list` + `capability list` + `execution list` chạy được (DB rỗng → hợp lệ) | CLI thật |
| AC8 | Regression full suite | pytest |
| AC9 | Đóng DoD | checklist |

## Ghi chú
- Doctor first-class tái dùng HealthDoctor + registry thật; "không crash" = mỗi hạng mục bọc try/except → FAIL kèm lý do.
