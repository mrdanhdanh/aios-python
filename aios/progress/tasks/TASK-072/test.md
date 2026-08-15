# TASK-072 — Test + Evaluation (Dashboard 1.0)

## Backend — `tests/test_api_m10.py` **5/5 pass**
- /m10/overview shape (health_score, slo_release_ready, security_blocking, contract_breaking) + giá trị hợp lệ
- /m10/timeline DB rỗng → [] + có data (plan/result steps, sort seq) + limit

## Dashboard — vitest **13/13 pass** (12 cũ + 1 mới)
- 11 tab labels đúng tên PLAN (Overview/Operations/Autonomy/Agents/Workflows/Knowledge/Memory/Harness/Enterprise/Ecosystem/System)
- Overview render (slo READY + contract clean) + ExecutionTimeline render 2 steps
- ChatView/HealthView/no-data cũ vẫn pass (view cũ giữ nguyên)

## tsc --noEmit: clean.

## Full suite backend: **1917 passed** (AC7).

## Evaluation — 8/8 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 11 tabs | ✅ |
| AC2 ExecutionTimeline | ✅ |
| AC3 Overview | ✅ |
| AC4 /m10/overview | ✅ |
| AC5 /m10/timeline | ✅ |
| AC6 vitest cũ pass | ✅ |
| AC7 backend regression | ✅ |
| AC8 DoD | ✅ |

## Bài học
1. **Response body chỉ consume 1 lần** — mock fetch phải tạo Response mới mỗi call (mockImplementation), nếu không test thứ 2 fail "invalid JSON".
2. Timeline steps sort theo seq (ts rỗng làm sort hỗn loạn).
3. Tabs mới nhóm view cũ (giữ nguyên component) — không xóa UI M3.
