# TASK-081 — Test.md (kết quả test thật)

> Ngày: 2026-08-15 · Owner: AIOS Orchestrator

## 1. Các suite test

| Suite | Lệnh | Kết quả | Ghi chú |
|-------|------|---------|---------|
| core.test.js | `npm run test:core` (vitest) | **27/27 PASS** | 27 assertion migrate từ vanilla core.test.js (bỏ process.exit — R3), state machine, dialogue, task, butterfly AI, scare, choice, freeze |
| smoke.test.js | `npm run test:smoke` (vitest) | **3/3 PASS** | Load vendor UMD qua loader.js; drawGarden mock ctx; config Phaser không boot (dynamic import try/catch — P3-B5) |
| e2e.spec.js | `npm run test:e2e` (playwright) | **8/8 PASS** | AC-2 di chuyển · AC-7 camX · AC-12 d-pad · AC-12b mute/ui-toggle · AC-14a chơi thật title→sinh nhật · AC-14b chơi thật title→game over (chọn 2) · AC-11 mood/SFX · AC-13 debug/freeze |
| visual.spec.js | `npm run test:visual` (playwright) | **19/19 PASS** | 17 shot (AC-6/AC-10) + R1 freeze determinism + AC-7b camX HALLWAY → test-results/shots/ |

**Tổng: 56/56 PASS** (Vitest 29 + Playwright 27)

## 2. Đối chiếu AC

| AC | Nội dung | Kết quả | Bằng chứng |
|----|----------|---------|------------|
| AC-1 | Vendor byte-identical (core/sprites/audio) | ✅ | SHA256 diff --no-index = 0 (xác nhận 3 file IDENTICAL) |
| AC-2 | Mèo di chuyển — hold D 1s → player.x tăng | ✅ | e2e AC-2 (`hold(page,"d",1000)` → player.x tăng) |
| AC-3 | 1 GameScene re-render bg texture mỗi frame | ✅ | `GameScene.renderBg` gọi `tex.refresh()` mỗi frame (P1-1) + code review |
| AC-4 | Sprite động Player + Butterfly duy nhất | ✅ | `renderSprites` dùng 2 texture cat/butterfly (P1-B2) + e2e AC-2/AC-14 |
| AC-5 | DOM overlay UI preserve (id vanilla) | ✅ | `ui.js` syncUI toggle; e2e AC-12b mute/ui-toggle |
| AC-6 | 17 ảnh chụp canvas 480×270 (freeze) | ✅ | visual.spec.js 17 shot → test-results/shots/ + R1 determinism |
| AC-7 | camX() expose khớp công thức vanilla | ✅ | e2e AC-7 (GARDEN x≤77→0, x>77 tăng) + AC-7b (HALLWAY w=320→160) |
| AC-8 | Audio port (WebAudio, 27 SFX + 10 mood) | ✅ | vendor audio.js byte-identical; e2e AC-11 `audio.getStats()` 22+ counter; `getMood()` đổi theo phase |
| AC-9 | Debug hook `?test=1` (no-hook chơi thật) | ✅ | e2e AC-14a/14b chơi thật chỉ ĐỌC state; debug chỉ test |
| AC-10 | 5 scare + camera scroll world 320 | ✅ | visual hallway-scare1..5 + e2e AC-7/AC-7b camera scroll |
| AC-11 | Mood/SFX đổi theo phase (e2e) | ✅ | e2e AC-11 (`getMood()` title=calm-happy→G_INIT=garden-calm; 22 SFX counter) |
| AC-12 | d-pad touch dispatchEvent | ✅ | e2e AC-12 (`dispatchEvent` touchstart dpad → player di chuyển) |
| AC-13 | 3 suite pass + vanilla untouched | ✅ | 56/56 PASS; `git diff --quiet HEAD -- games/yuniebel` = 0 (chỉ baseimg/ mới thêm) |
| AC-14 | CI build Phaser (Node pin + rm node_modules) | ✅ | `.github/workflows/pages.yml` setup-node@20 + `npm ci && npm run build` + `rm -rf node_modules` |
| AC-15 | Build Vite `base: './'` (file:// + Pages) | ✅ | `vite build` emit dist/index.html + assets paths tương đối; preview 4174 boot OK |
| AC-16 | Vendor 3 file SHA256 IDENTICAL | ✅ | core/sprites/audio = games/yuniebel/src/ (verify thực tế) |

## 3. Bảng đối chiếu brief (ảnh chụp vs baseimg 1..6)

> Ảnh chụp (bằng chứng): `games/yuniebel-phaser/test-results/shots/` (17 file PNG)
> Đối chiếu thủ công: `games/yuniebel-phaser/test/brief/COMPARISON.md`

| Cảnh | Khớp baseimg? | Ghi chú |
|------|--------------|---------|
| title | ✅ | menu mèo + "Yuniebel's Cat" |
| garden-day | ✅ | nhà chạm đất, cửa to, hàng rào liền, bướm |
| living | ✅ | sofa/kệ/cửa bếp rộng + mũi tên |
| kitchen-blood | ✅ | tủ trắng/lò/tủ lạnh + vết máu lớn + mắt sáng |
| haunted-ghost | ✅ | ma xanh đầu lưu + knockback |
| hallway-scare1..5 | ✅ | 5 kiểu hù riêng biệt (scareActive 1..5) |
| garden-dusk / night | ✅ | hoàng hôn → đêm + đèn hiên + overlay tối |
| kitchen-choice | ✅ | hộp chọn 1/2 |
| birthday | ✅ | lò sưởi + bánh kem + sparkle + chuông |
| gameover / end | ✅ | màn hình chết / sinh nhật kết thúc |

## 4. Lỗi đã fix trong test phase (chi tiết: `implementation/NOTES.md`)

1. **Phaser.AUTO crash custom canvas** → bắt buộc `type: renderType` (WEBGL/Canvas). (ROOT CAUSE e2e "Target crashed")
2. **Determinism fail khi freeze** → đóng băng render time (`rtime`) truyền vào `renderBg` (bg dùng `time` Phaser tiếp tục tăng). Sửa `GameScene.update`.
3. **Vitest double-run specs Playwright** → `vite.config.js` `test.include=["test/**/*.test.js"]`.
4. **ESM require/__dirname** → `import` + `fileURLToPath(import.meta.url)`.
