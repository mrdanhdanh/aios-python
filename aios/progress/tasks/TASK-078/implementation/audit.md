# Retroactive Audit — INV-035 Verification Fail-Closed (TASK-078, M11-P0)

> Mục đích: áp dụng INV-035 cho code/visual đã merge trước M11 — ghi nhận
> vi phạm tiềm năng (chỉ ghi nhận, KHÔNG sửa code game — theo spec AC11).
> Ngày: 2026-08-16 | Nguồn: `git log --all -- "games/*" "skills/*"`

## Phạm vi & phương pháp

Rà soát các commit webgame/visual đã merge, đối chiếu với tiêu chuẩn INV-035:
- Có cơ chế verification nào trả `PASS` dù state non-terminal (SKIPPED/UNKNOWN/MISSING_EVIDENCE) không?
- Có test nào "báo PASS" nhưng thực chất không chạy assert thật không?

## Findings (đã merge trước M11)

| # | Commit | Nội dung | Đánh giá INV-035 |
|---|--------|----------|------------------|
| F1 | `c1a33ce` TASK-077 | Webgame 2D pixel 'Yuniebel' — 86 tests PASS | ⚠️ Tiềm năng: "86 tests PASS" chưa có bằng chứng visual (screenshot ref) — nếu screenshot bị skip thì báo PASS sai |
| F2 | `da3600b` TASK-078 | Redo game — brief-accurate, 17 screenshot comparisons | ⚠️ Tiềm năng: 17 screenshot comparisons — nếu thiếu ảnh ref → `toHaveScreenshot` skip → false-positive "17/17 PASS" (đúng ví dụ trong proposal M11) |
| F3 | `4b65e69` + `867d49f` TASK-079 | Fix cat biến mất (scale mismatch 160×90 vs ×3) + refresh 17 screenshots | ✅ Sau fix: bug CHỈ bị bắt bởi visual test — minh chứng cần fail-closed; screenshots đã refresh nhưng không có bằng chứng "không skip" |
| F4 | `1933d5f`/`8823380` fix(game) | Garden fence continuous row + refresh screenshots | ⚠️ Screenshot refresh thủ công — không có cơ chế chặn "ảnh cũ dùng lại" |
| F5 | `2eefc97` TASK-080 | Game-dev skills (agent-sprite-forge + pixel-game-dev) + catalog | ✅ Không verification visual — ghi nhận nền cho R11 (Capability Discovery) |
| F6 | `f247860` TASK-081 | Scaffold Phaser 4 (Vite) — migrate scene/dialogue | ⚠️ Verify thủ công SHA256 vendor bundle (byte-identical) — chính là gap R8 (Vendor Integrity) |
| F7 | `9575402` TASK-082 | Phaser 4 upgrade — sprite sheet PNG + fx + parallax + transition (88/88, 23/23 AC) | ⚠️ 88/88 test — worker tự viết PNG encoder + seeded PRNG + vendor-hash baseline (reimplement primitive) — gap R4/R9/R11 |

## Kết luận

- **Không có vi phạm INV-035 nghiêm trọng nào trong code backend đã merge** — nhưng toàn bộ
  nguồn rủi ro nằm ở **visual verification layer** (screenshot/golden-master):
  - Không có cơ chế fail-closed khi `toHaveScreenshot` skip (thiếu ref)
  - Không có "missing reference detection" ở tầng hệ thống
  - Worker tự reimplement primitive (PNG encoder, PRNG seeded, vendor-hash) thay vì
    dùng capability có sẵn → chính là gap mà R4/R9/R11 (P3) và R8 (P3c) giải quyết
- **M11-P0 (task này) đã vá phần lõi**: Verification Kernel INV-035 + conformance area/gate
  + normalize security/contract/harness → từ nay mọi verification mechanism báo PASS
  phải có state thật = PASS; skipped/error → INCONCLUSIVE (không PASS).
- Các phase sau (P1–P4) sẽ vá phần visual: R3 DeterministicHarness (P1), R1/R10 (P2),
  R9/R4/R11 (P3), R8 vendor integrity (P3c).

## Đề xuất (ngoài scope — ghi nhận)

1. CI fail-closed gate cho visual test (R2 mở rộng) — chặn `toHaveScreenshot` skip → đề xuất P4/R7 static deploy CI
2. Missing-reference detector trong test framework (P2/R1 VisualRegressionProbe)
3. Vendor bundle hash → `aiagent security-check` (P3c/R8 — đã có trong roadmap M11)
