# TASK-072 — M10-F7: AIOS Dashboard 1.0 (11 tabs + Execution Timeline)

## Mục tiêu
PLAN §M10-29: Dashboard 1.0 — 11 tabs `Overview · Operations · Autonomy · Agents · Workflows · Knowledge · Memory · Harness · Enterprise · Ecosystem · System` + **Execution Timeline** (Goal→Plan→Agent→Capability→Tool→Result→Evaluation) — tracing là thành phần quan trọng.

## Phạm vi
- `dashboard/src/` (React + Vite + TS — M3): tái cấu trúc tabs → 11 tabs + Execution Timeline view
  - `views/ExecutionTimeline.tsx` — timeline từ `/api/v1/observability/metrics` + `/api/v1/events` (trace: goal→plan→agent→capability→tool→result→evaluation)
  - `views/Overview.tsx` — tổng hợp health + SLO + security + contract (M10 endpoints)
  - Reorganize tabs: Overview · Operations (Events/Tools/Workflows) · Autonomy · Agents · Workflows · Knowledge · Memory · Harness · Enterprise · Ecosystem · System
  - Giữ nguyên api.ts 3-envelope + ws.ts (M3)
- API backend: `api/routers/m10.py` — GET /api/v1/m10/overview (health + slo + security + contract summary) + GET /api/v1/m10/timeline (execution trace từ metrics + events)

## Ngoài phạm vi
- Không đổi các view M3 hiện có (thêm view mới + tabs mới, giữ cũ)
- Không UI mới cho harness/enterprise/ecosystem chi tiết (chỉ tab placeholder + summary)

## Input
- `dashboard/src/App.tsx` + views hiện có, `api/wiring.py`, `observability/slo.py`, `security/`, `contracts/check.py`

## Output
- `dashboard/src/views/{ExecutionTimeline,Overview}.tsx` + App.tsx tabs + `api/routers/m10.py` + `tests/test_api_m10.py` + dashboard vitest

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | App.tsx có 11 tabs đúng tên PLAN | Test vitest (snapshot tabs) |
| AC2 | ExecutionTimeline render trace (goal→plan→agent→capability→tool→result→evaluation) từ data mẫu | Vitest |
| AC3 | Overview hiển thị health + SLO + security + contract summary | Vitest |
| AC4 | API GET /m10/overview trả đúng shape (health_score, slo_release_ready, security_blocking, contract_breaking) | Pytest |
| AC5 | API GET /m10/timeline trả trace từ metrics/events thật (DB rỗng → hợp lệ) | Pytest |
| AC6 | Các view M3 cũ vẫn hoạt động (vitest cũ pass) | Vitest full |
| AC7 | Backend full suite regression | Pytest |
| AC8 | Đóng DoD | checklist |

## Ghi chú
- Timeline trace: từ metrics table (execution_id, started/finished) + events (TOOL_STARTED/ARTIFACT_CREATED/EVALUATION...) — trả list steps theo thời gian.
