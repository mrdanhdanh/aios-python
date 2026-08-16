# Critique vòng 1 — TASK-081 (spec)

> Ngày: 2026-08-15 · Bởi: critic agent · Trạng thái: **RESOLVED toàn bộ** (owner AIOS Orchestrator)
> Spec version phản biện: draft v1. Sau resolve: spec v2.

## Kết luận critic

Cần sửa trước khi implement: **P1-1, P1-2** bắt buộc; **P2-1..P2-8** nên chốt; **P3-1..P3-14** ghi nhận.

## Resolution theo từng vấn đề

### P1-1 — Pre-render bg "1 lần" mâu thuẫn state/time dependency → **RESOLVED**
- **Vấn đề**: drawGarden vẽ owner chỉ khi G_INIT+dialogue, đèn hiên theo darkness, drawHaunted ẩn ghost khi H_INIT+dialogue, drawKitchen highlight K_CHOICE, darkness ramp 5s — pre-render 1 lần sẽ mất các hiệu ứng.
- **Quyết định**: **Phương án A — re-render bg texture mỗi frame** (như vanilla đã chứng minh). Sửa spec §3: bỏ "pre-render 1 lần", thay bằng "re-render mỗi frame vào CanvasTexture (960×270 hoặc 480×270) rồi refresh()" — fidelity 100%, cost tương đương vanilla. Title/END cũng re-render mỗi frame (rẻ, P2-6). Ghi nhận tối ưu cache-by-key (phase/darkness/scareActive) cho vòng sau.

### P1-2 — AC-7 pixel probe không chạy được trên WebGL → **RESOLVED**
- **Vấn đề**: `getImageData` trên canvas WebGL trả rỗng/null (vanilla dùng được vì 2D context).
- **Quyết định**: AC-7 kiểm chứng bằng **expose `camX()` qua `window.__yuniebel`** (debug hook giữ nguyên + thêm getter) → e2e assert camX tăng khi player.x > 77. Ảnh chụp dùng `page.screenshot()` (compositor — hoạt động với WebGL). Bỏ mọi getImageData.

### P2-1 — Smoke test "Phaser boot trong jsdom" → **RESOLVED**
- **Quyết định**: Chốt AC-3 = (1) 3 file vendor load trong vitest jsdom (không throw), (2) gọi thử `Sprites.drawGarden` vào mock 2D ctx (tái dùng mockCtx vanilla) không throw, (3) object config `Phaser.Game` hợp lệ (không khởi tạo). **Boot thật = Playwright e2e/visual**.

### P2-2 — UMD vendor + Vite/vitest cơ chế → **RESOLVED**
- **Quyết định**: vitest `environment: 'jsdom'` cho core.test + smoke.test (jsdom có `self` → UMD gán `window.AiosCore/Sprites/AudioFX` đúng). Không sửa file vendor. Test viết lại khung vitest, **giữ nguyên 27 assertion** (P3-14).

### P2-3 — Texture sprite 48×48 không đủ + anchor 0.5 sai + setFlipX → **RESOLVED**
- **Quyết định**: Texture sprite động ≥ **96×96** (32 logical) với offset trái ≥12 logical; **anchor (0,0)**; position `(p.x*3 − offset*3, p.y*3)`; **KHÔNG dùng setFlipX** (drawCat tự flip nội bộ, không đối xứng). Ràng buộc 4 sửa theo.

### P2-4 — AC-13 chưa đủ + thiếu AC vendor → **RESOLVED**
- **Quyết định**: AC-13 đổi thành `git diff --quiet HEAD -- games/yuniebel` (chỉ tracked — test-results/ untracked không tính). **Thêm AC-16**: `diff --no-index` 3 file vendor vs vanilla = **byte-identical sạch** (adapter chỉ ở file riêng `src/vendor/loader.js` nếu cần).

### P2-5 — CI artifact phình node_modules → **RESOLVED**
- **Quyết định**: pages.yml thêm step `rm -rf games/yuniebel-phaser/node_modules` TRƯỚC `upload-pages-artifact` (hoặc rm trong cùng step build). Ghi vào AC-14.

### P2-6 — Title màn đóng băng → **RESOLVED**
- **Quyết định**: Phương án A (re-render mỗi frame) phủ luôn — title có mây trôi + gợn nước + mèo vẫy đuôi. Nến/sparkle BIRTHDAY/END cũng re-render mỗi frame (miễn phí, texture 480×270).

### P2-7 — Visual test freeze + cơ chế "!" marks → **RESOLVED**
- **Quyết định**: (a) Mọi shot visual dùng `debug.freeze(true)` (port R1 test vanilla) + chụp 2 lần cách 500ms so khớp. (b) "!"/"!!"/"!!!"/"!?" = **Phaser Text game object**, position `(p.x − camX + 4)*3, p.y*3 − 4`, font monospace bold 10-14px, ẩn/hiện theo scareActive.

### P2-8 — Vite preview port + build trước preview → **RESOLVED**
- **Quyết định**: playwright.config `webServer: { command: 'npm run build && npm run preview -- --port 4174 --strictPort', url: 'http://localhost:4174', reuseExistingServer: !process.env.CI }`. Dev port vite: **5175 strictPort** (tránh dashboard 5173) — P3-12.

### P3-1 — 1 GameScene vs 3 scene → **RESOLVED**
- **Quyết định**: **1 GameScene duy nhất** xử lý theo `state.scene` (như drawScene vanilla). Bỏ TitleScene/EndScene riêng — scene switch Phaser không cần thiết với state machine đã có. Sửa spec §3.

### P3-2 — Fade/footstep/ambient → **RESOLVED**
- Port vào GameScene/update: fadeT 0.35s (rectangle overlay alpha), footstep timer 0.28s, ambient bird/clockTick theo scene (giữ parity vanilla).

### P3-3 — Input window listener → **RESOLVED**
- Giữ nguyên **window keydown/keyup listener** vanilla (đã ổn định qua e2e) — không dùng Phaser keyboard cho movement. Phaser chỉ nhận click nếu cần.

### P3-4 — canvas#game mount → **RESOLVED**
- Phaser config `canvas: document.getElementById('game')` — giữ selector `#game` + kích thước canvas 480×270 cho e2e `locator('#game').screenshot()`.

### P3-5 — AC-4 "45s" cứng nhắc → **RESOLVED**
- Ghi "≤120s (timeout config), tương đương vanilla playthrough 40–90s".

### P3-6 — AC-7 threshold sai → **RESOLVED**
- camX bắt đầu trượt từ **x > 77** (không phải 160). Sửa AC-7.

### P3-7 — Ràng buộc 4 diễn đạt → **RESOLVED**
- "Logical grid 160×90; Phaser pixel 480×270 = logical ×3 (GX=3); GARDEN/HALLWAY 320×90 → 960×270".

### P3-8 — Autoplay policy → **RESOLVED**
- Giữ `--autoplay-policy=no-user-gesture-required` trong playwright.config mới.

### P3-9 — e2e "không hook" định nghĩa → **RESOLVED**
- Quy ước: e2e được phép ĐỌC state qua `?test=1` (`window.__yuniebel.getState()`), KHÔNG gọi debug setter (setPhase/setPlayer...). Visual mới dùng setter + freeze.

### P3-10 — baseimg copy vào test/brief → **RESOLVED**
- Copy 6 ảnh baseimg → `games/yuniebel-phaser/test/brief/refs/1..6.png` (đối chiếu thủ công dễ). Ghi nguồn gốc trong README.

### P3-11 — Verify Phaser API → **RESOLVED**
- Bước 0 tasks.md: cài phaser@4.2.1 + verify API (`textures.createCanvas`, `texture.refresh()`, `add.image`, `cameras.main.setScroll`, `add.text`) qua snippet thật trước khi viết scene.

### P3-12 — Dev port → **RESOLVED** (P2-8: 5175 strictPort).

### P3-13 — PROGRESS/LOG cập nhật → **RESOLVED**
- Cập nhật PROGRESS.md (TASK-081 in-progress) + LOG.md ngay khi spec approve (bước này).

### P3-14 — Test viết lại khung → **RESOLVED**
- Vendor byte-identical; test viết lại khung vitest giữ 27 assertion (core) + smoke jsdom.

## Trạng thái

- [x] Tất cả P1/P2/P3 **RESOLVED** (theo khuyến nghị critic — không còn blocker).
- Spec v2 sẽ phản ánh đầy đủ các resolution trên.
