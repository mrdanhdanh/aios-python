# TASK-081 — Plan: Scaffold Phaser + Migrate Yuniebel's Cat

> Ngày: 2026-08-15 · Owner: AIOS Orchestrator · Trạng thái: in-progress

## Yêu cầu người dùng

> "Scaffold Phaser cho Yuniebel's Cat và migrate scene/dialogue hiện tại. tham khảo hình ảnh scene tại folder baseimg"

Người dùng đã **duyệt kế hoạch** (2026-08-15): tạo mới `games/yuniebel-phaser/` (Vite + Phaser 4.2.1), **giữ nguyên** bản vanilla `games/yuniebel/` (không phá 28/28 test đang xanh).

## Quyết định đã chốt với người dùng

| # | Vấn đề | Quyết định |
|---|--------|------------|
| 1 | Vị trí | Tạo mới `games/yuniebel-phaser/` — giữ nguyên `games/yuniebel/` |
| 2 | Phaser version | **4.2.1** (latest stable — skill `pixel-game-dev` đã cô đọng API) |
| 3 | Chiến lược render | Tái sử dụng `sprites.js` (đã khớp 5 ảnh ref TASK-078): pre-render nền scene → `CanvasTexture` Phaser + sprite động (mèo/bướm/ma/scare) vẽ texture cập nhật mỗi frame — giữ 100% fidelity baseimg; Phaser lo scene/camera scroll/input/tween |
| 4 | Logic & dialogue | Migrate `core.js` gần như nguyên văn (framework-agnostic, 27 test đang pass) — 13 câu thoại, 17 phase, 9 task text, choice 1/2, 5 scare |
| 5 | UI overlay | Giữ DOM overlay (task box, dialogue, choice 1️⃣/2️⃣, d-pad, mute) như bản hiện tại |
| 6 | Deploy | Sửa `pages.yml`: thêm bước build Vite → URL `/games/yuniebel-phaser/dist/` (không đụng deploy bản cũ) |
| 7 | Test | core.test.js node (nguyên văn) + smoke jsdom + Playwright e2e chơi thật + visual chụp ảnh đối chiếu baseimg (6 ảnh) |

## Baseimg (6 ảnh tham khảo — đã phân tích vision)

| File | Cảnh | Ghi chú |
|------|------|---------|
| 1.png (portrait 1024×1536) | Title screen | Trời gradient + dithering, mặt trời, mây, nút START xanh lá, phong cảnh dưới |
| 2.png (landscape 1536×1024) | Sân vườn (3 panel) | Ngày → hoàng hôn → đêm; nhà gỗ, hàng rào, cậu bé, mèo, bướm vàng, hộp thoại |
| 3.png (landscape) | Phòng khách + Nhà bếp (2 panel) | Living ấm (sofa, bàn trà, kệ, đồng hồ) + Bếp tối (tủ trắng, vết máu LỚN, 2 mắt trắng trong tối) |
| 4.png (landscape) | Phòng khách ma ám | Ma XANH đầu lâu chặn cửa, sofa cũ, đồng hồ quả lắc, mạng nhện, "Phải đi qua phòng khác!" |
| 5.png (landscape) | Hành lang 5 jump scare | Ma trắng / chân dung hét / tay zombie / bóng mắt vàng / mặt xương; mèo + !/!!/!!!/!? |
| 6.png (portrait) | Sinh nhật | Lò sưởi, bánh kem, chủ ôm mèo, "Happy Birthday Yuniebel!" / "Chúc Mừng Sinh Nhật!" |

→ Khớp 100% mô tả chuẩn `TASK-078/implementation/brief-visuals.md` + COMPARISON.md 17/17 (bản vanilla đã render đúng).

## Phạm vi

- **Trong**: `games/yuniebel-phaser/` (mới), `.github/workflows/pages.yml` (thêm build), tài liệu progress.
- **Ngoài**: `games/yuniebel/` (vanilla — giữ nguyên), backend, dashboard, extension, sdk.

## Hard gate

1. Plan ✅ (file này + PROGRESS.md)
2. Spec → `spec.md`
3. Critique ×2 → `critique-1.md` → resolve → `critique-2.md` → resolve
4. Tasks → `tasks.md`
5. Review → `review.md`
6. Implement → code + LOG.md song song
7. Test → `test.md` + chạy test thật
8. Evaluate → `evaluation.md`

## Rủi ro chính

- Phaser 4.2.1 API mới (khác Phaser 3) — giảm thiểu: chỉ dùng API cốt lõi (Game/Scene/camera/texture/keyboard), không dùng filter phức tạp; test thật qua Playwright.
- Vite build cho GitHub Pages subpath — dùng `base: './'` → URL `/games/yuniebel-phaser/dist/`.
- Pre-render fidelity — vì tái dùng đúng hàm sprites.js, fidelity giữ nguyên; visual test chụp ảnh + COMPARISON.md.
