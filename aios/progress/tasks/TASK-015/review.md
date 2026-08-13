# Review — TASK-015 (Skills + Sandbox Pool)

> Ngày: 2026-08-13 | Reviewer: reviewer agent | Giai đoạn: REVIEW TRƯỚC KHI IMPLEMENT
> Spec qua critique ×2 (27 vấn đề). Reviewer verify: baseline 622 passed/0 skipped, semver API đúng, allow-list pattern khớp, SQLite pattern khớp.

## Kết luận

- [x] **CHANGES REQUESTED** — 2 blocking + 1 Major + 2 Minor (đã sửa vào spec):

**R1 (Blocking) — C1-05 dependent check không có trong spec body**: grep "dependent" = 0. Semantics chưa chốt. **Fix (đã ghi spec 5.2.2)**: rollback — quét registry, dependent khai `id@>=X` có constraint fail vs version mục tiêu → chặn `SkillError("dependent broken: <dep_id> (need >=X.Y.Z, have A.B.C)")`; remove — chặn nếu còn dependent ACTIVE (enabled/reloaded) khai báo dep này (kể cả plain "id"); thêm AC9/AC10 + test.

**R2 (Blocking) — C1-03 optimistic concurrency không có trong spec body**: RLock chỉ serialize 1 instance. **Fix (đã ghi spec 5.2.1)**: mọi mutation `UPDATE ... WHERE id=? AND state=<expected>`; rowcount==0 → phân biệt not found / "state changed concurrently"; resolve dùng INSERT + catch IntegrityError (chống TOCTOU).

**R3 (Major) — semver còn 6 chỗ ghi cấm (đặc biệt AC1)**: đã dọn toàn spec → thống nhất `aios_mods ⊆ {"aios_core.metadata", "aios_core.semver"}`.

**R4 (Minor) — AC3 còn case `upgraded→rollback`**: đã bỏ khỏi invalid cases (AC9 cover "no history").

**R5 (Minor) — file layout**: chốt theo spec — errors.py + schema.py tách riêng (không phá allow-list — rglob quét mọi *.py).

## Phần 1: AC ↔ test

18/18 AC có test tương ứng (bảng chi tiết trong review); 2 AC (9, 10) bổ sung dependent check tests.

## Phần 2: Rủi ro top 3

1. R1 dependent check semantics (active-only for remove; constraint vs version target for rollback)
2. R2 optimistic concurrency — WHERE state + IntegrityError catch
3. R3 semver mâu thuẫn AC1 → test fail

## Phần 3: Ràng buộc

- Baseline 622 passed / 0 skipped — verify thật
- Coverage skills/ + sandbox/ ≥ 80% (đo thực tế T5.2)
- Offline-first: 0 network/git/pip/docker thật — no-syscall tests
