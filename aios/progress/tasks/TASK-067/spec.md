# TASK-067 — M10-F4: Autonomy Safety 1.0 (mandatory enforcement)

## Mục tiêu
PLAN §M10-16/17: M9 có Governor/Budget/Risk/Policy → M10 biến thành **mandatory runtime enforcement**: `Autonomous Agent → Action Proposal → Risk Classifier → Autonomy Governor → Policy Engine → Permission Broker → Capability → Tool` (không shortcut). **Stop Anywhere**: mọi autonomous side effect bị chặn tại boundary trước khi thực thi — guardrails cấp tool (pre/post mỗi invocation).

## Phạm vi
- `autonomous/safety.py`:
  - `ActionProposal` (action, target, tool_id, risk_class, op_class, reason, extra=forbid)
  - `RiskClassifier` (5 mức risk từ action + target sensitivity; deterministic)
  - `SafetyEnforcer`: `evaluate(proposal, governor, policy_fn, permission_fn)` → `SafetyDecision` (ALLOW/DENY/ASK_HUMAN/STOP + reason + evidence chain) — CHUỖI BẮT BUỘC, mỗi gate fail → dừng ngay
  - `ToolGuard`: wrapper quanh Tool.run — pre-check (proposal hợp lệ + governor/policy/permission) TRƯỚC khi chạy; post-check sau khi chạy (side effect hợp lệ) — chặn tại boundary (INV-030)
- Tests: chain đầy đủ, mỗi gate chặn, stop-anywhere, tool guard pre/post

## Ngoài phạm vi
- Không sửa governor/policy hiện có (SafetyEnforcer gọi qua callable inject)
- Không sửa tools (ToolGuard là wrapper opt-in)

## Input
- `autonomous/governor.py` (Governor.check_action), `kernel/services/policy.py`, `orchestrator/goals/permission_broker.py`, `tools/base.py`

## Output
- `backend/src/aios_core/autonomous/safety.py` + `tests/test_autonomy_safety.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | Chuỗi enforce đúng thứ tự: Risk → Governor → Policy → Permission; gate fail → dừng ngay (deny, không chạy tiếp) | Unit test từng gate fail |
| AC2 | RiskClassifier deterministic: action/target → 5 mức risk (bảng cố định) | Test bảng |
| AC3 | SafetyDecision: ALLOW/DENY/ASK_HUMAN/STOP + reason + evidence chain (ghi từng gate qua) | Test |
| AC4 | STOP: governor hoặc risk cao → STOP (chặn mọi thực thi) | Test |
| AC5 | ASK_HUMAN: policy ask/permission ask → không tự ALLOW | Test |
| AC6 | ToolGuard: pre-check chặn TRƯỚC khi tool chạy (tool không được gọi) + post-check sau khi chạy | Test đếm tool calls |
| AC7 | ToolGuard không phá tool hợp lệ (chain ALLOW → tool chạy bình thường) | Test |
| AC8 | Regression full suite | pytest |
| AC9 | Đóng DoD | checklist |

## Ghi chú
- SafetyEnforcer KHÔNG sở hữu governor/policy — nhận callable (không God Object, INV-030).
- Evidence chain = list[str] mỗi bước (risk_class, governor_decision, policy_decision, permission_decision) — audit được.
