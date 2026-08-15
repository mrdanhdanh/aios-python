# TASK-067 — Implementation + Evaluation

## Implementation
| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/autonomous/safety.py` | RISK_TABLE + SENSITIVE_TARGETS + ActionProposal (extra=forbid) + RiskClassifier + SafetyDecisionResult (evidence 4 gate) + SafetyEnforcer (Risk→Governor→Policy→Permission, dừng ngay) + ToolGuard (pre/post, emergency hook) |
| `backend/tests/test_autonomy_safety.py` | 15 tests |

## Evaluation — 9/9 AC ĐẠT
Chain mandatory đúng PLAN §M10-16; stop-anywhere tại boundary (tool._run không chạy khi deny); ToolGuard hợp nhất preflight_tool của KillSwitch (TASK-068) — một hook duy nhất.

## Bài học
- Safety không được là "lớp trang trí" — mọi side effect phải qua chain; evidence ghi từng gate để audit.
- Risk-based gating: critical → STOP, high → ASK_HUMAN, medium/low → policy/permission quyết định.
