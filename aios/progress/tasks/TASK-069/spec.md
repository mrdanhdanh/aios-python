# TASK-069 — M10-F5: Reliability Engineering (SLO)

## Mục tiêu
PLAN §M10-20/21: SLO registry (Runtime availability · Execution success · Recovery success · Checkpoint durability · Policy enforcement · Event delivery · API availability) với **non-averaged gates** — những metric KHÔNG được phép trung bình hóa: `Policy bypass = 0 · Lost execution = 0 · Checkpoint corruption = 0 · Unauthorized tool call = 0 · Contract-breaking release = 0`. Health 98% nhưng `Policy bypass = 1` → **Release FAIL**.

## Phạm vi
- `observability/slo.py`:
  - `SloKind`: RATIO (target %, ≥) | ABSOLUTE_ZERO (bắt buộc = 0)
  - `SloDefinition` (id, name, kind, target, window, notes, extra=forbid)
  - `SloRegistry`: 7 SLO + 5 non-averaged gates (12 total)
  - `SloEngine.check(metrics: dict[str, float])` → `SloReport`: per-SLO status (PASS/FAIL) + `release_ready` (mọi gate = 0 + SLO đạt)
  - `report_for_runtime(kernel)` — đọc dữ liệu thật: MetricsService (execution success/failure), audit (policy violations, unauthorized tool), arch-health (architecture violations), contract checker (breaking)
- CLI: `aiagent slo` — in bảng SLO + Release Gate verdict

## Ngoài phạm vi
- Không sửa MetricsService/audit (đọc qua public API)
- Không tự block release (chỉ báo cáo; TASK-073 dùng làm Gate D/E)

## Input
- `observability/metrics.py`, `kernel/services/event.py` (audit), `contracts/check.py` (breaking), `observability/arch_health.py`

## Output
- `backend/src/aios_core/observability/slo.py` + `tests/test_slo.py` + CLI

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | SloRegistry có 12 SLO: 7 ratio + 5 absolute-zero (policy_bypass, lost_execution, checkpoint_corruption, unauthorized_tool, contract_breaking) | Unit test set compare |
| AC2 | RATIO: check target ≥ đạt; < → FAIL | Test biên (đúng/đủ/sai) |
| AC3 | ABSOLUTE_ZERO: value = 0 → PASS; > 0 → FAIL (KHÔNG trung bình hóa — 1 lần cũng fail) | Test |
| AC4 | `SloReport.release_ready` = tất cả PASS (1 gate fail → release_ready False, kể cả SLO khác 99%) | Test |
| AC5 | `report_for_runtime(kernel)`: đọc dữ liệu thật (metrics/audit/arch-health/contract) — không crash khi DB rỗng | Test với kernel thật |
| AC6 | CLI `aiagent slo` in bảng + verdict READY/NOT READY | Chạy CLI thật |
| AC7 | `SloDefinition extra=forbid` + validation (target 0..1 ratio) | Test |
| AC8 | Regression full suite | pytest full |
| AC9 | Đóng DoD | checklist |

## Ghi chú
- Non-averaged = 0 tuyệt đối, không tỷ lệ (1 policy bypass = fail, không "99.99% không bypass").
- Nguồn dữ liệu thật: audit SQLite đếm event type PERMISSION_DENIED/ERROR, metrics table workflow, arch_health scan, contract checker.
