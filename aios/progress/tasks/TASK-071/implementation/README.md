# TASK-071 — Implementation + Evaluation

## Implementation
| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/cli/doctor.py` | DoctorFirstClass (18 hạng mục: runtime/contracts/registry/models/memory/knowledge/filesystem/sandbox/tools/plugins/policies/permissions/db/events/scheduler/autonomy/harness/enterprise) + format (Health: N/100) |
| `backend/src/aios_core/cli/system.py` | system_status (version + services + emergency) |
| `backend/src/aios_core/cli/__init__.py` | exports |
| `backend/src/aios_core/workflow/cli.py` | +`health`, `system status`, `goal list`, `execution list`, `skill list`, `capability list` |
| `backend/tests/test_cli_m10.py` | 10 tests |

## Evaluation — 9/9 AC ĐẠT
Command tree mở rộng đủ PLAN §M10-27; `aiagent health` → 100/100. Doctor cũ (JSON) giữ nguyên — tương thích.

## Bài học
- First-class doctor = 18 checks thật — nền cho `aiagent conformance` (TASK-073) và Dashboard Overview (TASK-072).
