# Review — TASK-021 (reviewer subagent)

> 2026-08-13 | reviewer review spec v3: **APPROVED có điều kiện** — 3 amendment bắt buộc (C1/C2/C3) → resolve vào spec v4 → implement → verify.

## Amendments & Resolution
- **C1 (R1-1)**: EvaluationStore không thể tính duration từ finish events (thiếu start timestamp) → **Resolve**: subscribe thêm WORKFLOW_STARTED + cache `{execution_id: started_at}` in-memory, xóa khi finish; restart → NULL.
- **C2 (R1-2 + R2-1)**: claim "mọi nhánh trả FAILED" sai — 2 nhánh `resume()` xảy ra TRƯỚC WORKFLOW_STARTED → **Resolve**: emit FAILED chỉ trong `_run` (6 nhánh); resume ×2 không emit; cancel giữa node (result=="cancelled") → WORKFLOW_CANCELLED.
- **C3 (R2-3)**: test_cli.py sẽ vỡ (doctor output mới mất key "kernel") → **Resolve**: DoctorReport JSON giữ key `"kernel": "ok"`; test_cli vẫn pass (verify full suite).

## R2/R3 khác → Resolve
- R2-2: allow-list exempt self-package `aios_core.observability*`; R2-4 arch_health rglob + collect_imports
- R3-1: `__init__.py` exports; R3-2: regs["observability"]; R3-3: policy check skip khi thiếu file; R3-4: summary total; R3-5: 80% cứng; R3-6: shim import tường minh; R3-7: filter 6 event types

## Verify thực tế (sau implement)
- **pytest full: 779 passed, coverage 95.11%** (trước: 730) — 49 test mới
- observability/: metrics 7, prompt_history 4, profiler 5, doctor 5, arch_health 7, evaluation 8, api 7, execution_failed_events 5, arch allow-list 1
- CLI: `aiagent metrics`/`doctor`/`arch-health` chạy thật OK (JSON đúng)
- arch_scan move: test_architecture.py 19/19 pass qua shim

## Kết luận
**APPROVED** — toàn bộ amendment + findings resolved, verify test thật + CLI thật.
