# Review — TASK-091 (M13-P2: Meta-Harness) — Pre-implementation Review

> Reviewer: reviewer agent (độc lập). Ngày: 2026-08-17.
> Đối tượng: spec v3 + critique-1 (resolved) + critique-2 (resolved) + tasks.md.

## 1. Đánh giá spec v3

Spec v3 đã tích hợp ĐẦY ĐỦ resolution của cả 2 vòng critique:
- **critique-1** (2 P1 + 5 P2 + 3 P3): BROKEN_VERIFIER semantics đảo ngược, danh sách test cập nhật, oracle độc lập + AC16, sha256 check, replay build, case 8 VERIFY_SKIPPED, make_registry.
- **critique-2** (1 P1 + 4 P2 + 5 P3): **P1-1 (quan trọng nhất)** — round-1 P1-1 chưa áp dụng đúng trong v2 (Meta không bao giờ PASS). V3 đã sửa: `fail_closed` = "Meta đạt mục tiêu adversarial", BROKEN_VERIFIER + VERIFY_SKIPPED → `fail_closed=True` (scenario a), scenario (b) đẩy vào AC16 negative test. Đây là sửa đúng và đủ để AC13/AC15 reachable.

## 2. Rủi ro còn lại (đã được spec xử lý)

| Điểm | Trạng thái |
|------|-----------|
| `MetaHarness` thiếu `name` (P2-3) | ✅ đã thêm `name="meta-harness"` |
| `state_service` route vào engine (P2-2) | ✅ `__init__` route vào `MetaHarnessEngine(state_service)` |
| `expected_state` vocabulary lộn xộn (P2-4) | ✅ chuẩn hóa `MetaOracle` enum |
| `metrics` undefined (P3-3) | ✅ `{total, fail_closed, by_case}` |
| `test_components_7_exclude_self` sập (P2-1) | ✅ rename `test_components_8_exclude_self` (total==8) |
| monkeypatch module-level (P3-4) | ✅ AC16 hướng module-level import |
| gọi `has_critical_evidence` trước `compute_verdict` (P3-5) | ✅ engine gọi đúng thứ tự |

## 3. Kiến trúc / Invariant

- KHÔNG sửa Runtime/Orchestrator (INV-017..021 giữ nguyên) — Meta chỉ test qua public API (`compute_verdict`/`replay_verdict`/`has_critical_evidence`/`CheckResult.effectively_passed`).
- KHÔNG thêm invariant (INV-001..035 frozen).
- Tái dùng `HarnessRunner` lifecycle + fail-closed (INV-035).
- 4 invariant track (FAIL-CLOSED + INDEPENDENT VERIFICATION + PERMISSION BOUNDARY + CERTIFIED BASELINE) không bị vi phạm — Meta là independent verification path (oracle hardcode).

## 4. Phê duyệt

**APPROVED** — spec v3 đạt 5/5 sẵn sàng, hard gate đủ (spec + critique×2 resolved + tasks + review). Được phép implement.

### Điều kiện nhỏ (non-blocking)
- R1: engine thuần, không import sqlite3/httpx/socket/requests/os (R4 spec).
- R2: `hashlib` đã trong allow-list (TASK-089) — CORRUPTED_ARTIFACT dùng sha256 tự viết.
- R3: ghi nhận residual circularity (oracle cùng nguồn spec) — M16/dsh là path độc lập thật (P3-3).
