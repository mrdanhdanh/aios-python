# TASK-049 — Pre-implementation Review

> File bổ sung hồi tố 2026-08-15 khi đóng hard gate (review ban đầu ghi trong LOG.md).

## Kết luận
**APPROVED có điều kiện** để implement Certification (M8-E7).

## Kiểm tra
- Phạm vi đúng M8-E7: CertLevel 4 + 6 check groups + evidence + security hard-block.
- Harness là gate của Ecosystem (M6): `check_fn` injectable cho phép test harness gate thật.
- Security fail → hard-block (không cho "đạt" dù điểm khác cao).

## Điều kiện bắt buộc khi implement
1. CertLevel 4 giá trị đúng PLAN (COMMUNITY/VERIFIED/CERTIFIED/ENTERPRISE_CERTIFIED).
2. `certify()` chạy checks; mọi fail → level COMMUNITY + report FAIL.
3. VERIFIED khi toàn bộ basic checks pass; CERTIFIED khi threshold đạt + security pass; ENTERPRISE_CERTIFIED khi enterprise evidence pass.
4. `check_fn` injectable (test harness gate).
5. Import allow-list ecosystem.

## Kết quả sau implement
- 1639 passed (batch M8) — các điều kiện 1–5 đều thỏa (xem `test.md` + `evaluation.md`).
