# TASK-069 — Evaluation

## Đối chiếu AC — 9/9 ĐẠT
Xem test.md. Mấu chốt: non-averaged gates (1 lần vi phạm = FAIL), SKIPPED không chặn release, metrics thật từ runtime không crash khi DB rỗng.

## Giá trị
- `aiagent slo` là công cụ vận hành đầu tiên trả verdict release — nền cho Gate D/E (TASK-073).
- Bổ sung `counts_by_outcome()` + workflow ok vào MetricsService — dữ liệu mới phục vụ TASK-075 (Performance & Cost).

## Bài học
1. Nguồn dữ liệu SLO phải mapping rõ từng metric (metrics/audit/arch-health/contract) — nếu không có nguồn thì SKIPPED, không bịa số.
2. Zero-gate "canary" (policy_bypass mặc định 0) ghi chú rõ là đo gián tiếp — TASK-070 Security Baseline sẽ củng cố nguồn.

## Đề xuất (P3)
- Đưa `slo.release_ready` vào `aiagent conformance` (TASK-073) làm Gate D/E input.
