# TASK-049 — Evaluation

> Bổ sung hồi tố 2026-08-15 khi đóng hard gate (evaluation ban đầu ghi trong LOG.md).

## Đối chiếu acceptance criteria
1. **Đạt** — CertLevel 4 giá trị đúng PLAN.
2. **Đạt** — `certify()` chạy checks; mọi fail → level COMMUNITY + report FAIL.
3. **Đạt** — VERIFIED khi toàn bộ basic checks pass.
4. **Đạt** — CERTIFIED khi threshold đạt + security pass.
5. **Đạt** — ENTERPRISE_CERTIFIED khi enterprise evidence pass.
6. **Đạt** — `check_fn` injectable (test harness gate).
7. **Đạt** — Import allow-list ecosystem.
8. **Đạt** — Test levels, threshold, fail → COMMUNITY, injectable (`tests/test_ecosystem_certification.py`).

## Kết luận
TASK-049 đạt phạm vi Certification (E7): hệ thống trust 4 cấp cho plugin, Harness là gate (M6), security hard-block — sức mạnh hệ sinh thái: Ecosystem càng mở, guardrails càng chặt.
