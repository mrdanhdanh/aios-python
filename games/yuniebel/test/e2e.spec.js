/* e2e.spec.js — TASK-078 — npx playwright test
 * AC-14: 2 test CHƠI THẬT không hook (title→sinh nhật, title→game over).
 *   "không hook" = không gọi debug setter; ĐƯỢC PHÉP đọc state (C2-14) → URL ?test=1
 *   để có window.__yuniebel đọc state nhưng KHÔNG gọi debug setter trong 2 test chơi thật.
 * AC-3/AC-4: assert mood + SFX stats qua window.__yuniebel.audio.
 */
const { test, expect } = require("@playwright/test");

const URL = "file://" + __dirname.replace(/\\/g, "/") + "/../index.html?test=1";

async function gotoGame(page) {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForFunction(() => window.__yuniebel && window.__yuniebel.getState().phase === "G_INIT");
}

async function getState(page) {
  return page.evaluate(() => window.__yuniebel.getState());
}

// Điều khiển mèo bằng phím
async function hold(page, key, ms) {
  await page.keyboard.down(key);
  await page.waitForTimeout(ms);
  await page.keyboard.up(key);
}

// Di chuyển mèo tới (tx, ty) — ưu tiên trục Y trước (tránh kẹt wall ngang thân nhà/sofa)
async function moveTo(page, tx, ty, maxSteps) {
  maxSteps = maxSteps || 60;
  const startPhase = (await getState(page)).phase;
  for (let i = 0; i < maxSteps; i++) {
    const st = await getState(page);
    if (st.phase !== startPhase) break; // phase đổi → đã chạm zone mục tiêu, dừng
    const p = st.player;
    const dx = tx - p.x, dy = ty - p.y;
    if (Math.abs(dx) < 10 && Math.abs(dy) < 10) break;
    // ưu tiên y trước (thay đổi nhỏ, tránh kẹt wall ngang)
    if (Math.abs(dy) > 12) await hold(page, dy > 0 ? "s" : "w", 120);
    else await hold(page, dx > 0 ? "d" : "a", 120);
  }
}

// Đuổi bướm — bấm hướng bướm LIÊN TỤC (không dừng): mèo 120px/s đuổi kịp 60px/s → chạm → catch
async function chaseButterfly(page, maxSteps) {
  maxSteps = maxSteps || 100;
  for (let i = 0; i < maxSteps; i++) {
    const st = await getState(page);
    if (["G_DARK", "G_DOOR"].includes(st.phase)) return true;
    if (!st.butterfly) { await page.waitForTimeout(100); continue; }
    const p = st.player, b = st.butterfly;
    const dx = b.x - p.x, dy = b.y - p.y;
    if (Math.abs(dx) > Math.abs(dy)) await hold(page, dx > 0 ? "d" : "a", 120);
    else await hold(page, dy > 0 ? "s" : "w", 120);
  }
  return false;
}

test("AC-14a: chơi thật title → sinh nhật (D_END) — không hook", async ({ page }) => {
  await gotoGame(page);

  // ===== S1 Sân vườn =====
  await page.keyboard.press("Space"); // advance câu 1
  await page.keyboard.press("Space"); // advance câu 2
  // mèo tiến gần cửa (x>780) → bướm xuất hiện
  await moveTo(page, 800, 210);
  let st = await getState(page);
  expect(st.butterfly).toBeTruthy();
  // đuổi bướm đến khi bắt được
  const caught = await chaseButterfly(page);
  expect(caught).toBeTruthy();
  st = await getState(page);
  expect(["G_DARK", "G_DOOR"].includes(st.phase)).toBeTruthy();
  // chờ trời tối xong → G_DOOR (hoặc đã vào nhà)
  await page.waitForFunction(() => ["G_DOOR", "L_SEARCH"].includes(window.__yuniebel.getState().phase), null, { timeout: 15000 });
  st = await getState(page);
  if (st.phase !== "L_SEARCH") {
    await moveTo(page, 865, 178); // cửa mở dưới y=172 — mèo phải đi thấp
    st = await getState(page);
  }
  expect(st.phase).toBe("L_SEARCH");

  // ===== S2 Phòng khách → S3 bếp =====
  await page.keyboard.press("Space");
  await moveTo(page, 20, 110);
  st = await getState(page);
  expect(["K_INIT", "K_BLOOD", "K_CHOICE"].includes(st.phase)).toBeTruthy();

  // ===== S3 Bếp: chạm vết máu → K_BLOOD → K_CHOICE =====
  st = await getState(page);
  expect(["K_INIT", "K_BLOOD", "K_CHOICE"].includes(st.phase)).toBeTruthy();
  await page.keyboard.press("Space");
  if ((await getState(page)).phase !== "K_CHOICE") {
    await moveTo(page, 60, 60); // vùng tối → K_CHOICE
  }
  st = await getState(page);
  expect(st.phase).toBe("K_CHOICE");

  // ===== Chọn 1 "Bỏ chạy" → H_INIT (ma ám) =====
  await page.keyboard.press("1");
  await page.waitForFunction(() => window.__yuniebel.getState().phase === "H_INIT");
  await page.keyboard.press("Space");
  await page.waitForTimeout(150);
  await page.keyboard.press("Space");
  await page.waitForFunction(() => ["H_BLOCK", "H_EXIT"].includes(window.__yuniebel.getState().phase));
  st = await getState(page);
  // thử ra cửa chính → bị đẩy (task đổi "Phải đi qua phòng khác!")
  await moveTo(page, 440, 150);
  st = await getState(page);
  expect(st.ghostBlocked).toBeTruthy();
  // đi qua cửa phụ trái → W_INIT
  await moveTo(page, 10, 110);
  await page.waitForFunction(() => ["W_INIT", "W_WALK", "W_DONE"].includes(window.__yuniebel.getState().phase));

  // ===== S5 Hành lang: 5 scare =====
  st = await getState(page);
  if (st.phase === "W_INIT") {
    await page.keyboard.press("Space");
    await page.waitForFunction(() => window.__yuniebel.getState().phase === "W_WALK");
  }
  // đi hết hành lang (qua 5 scare zone)
  await moveTo(page, 930, 135, 60);
  st = await getState(page);
  expect(st.scareCount).toBe(5);
  expect(["W_DONE", "D_END"].includes(st.phase)).toBeTruthy();
  // vào phòng ăn → D_END (sinh nhật)
  if (st.phase === "W_DONE") {
    await moveTo(page, 935, 135, 20);
    st = await getState(page);
  }
  expect(st.phase).toBe("D_END");
  // nhiệm vụ đúng
  const task = await page.evaluate(() => document.getElementById("task-text").textContent);
  expect(task).toBe("Hoàn thành nhiệm vụ: Tìm chủ nhân.");
});

test("AC-14b: chơi thật title → game over (chọn 2) — không hook", async ({ page }) => {
  await gotoGame(page);
  await page.keyboard.press("Space");
  await page.keyboard.press("Space");
  await moveTo(page, 800, 210);
  await chaseButterfly(page);
  await page.waitForFunction(() => ["G_DOOR", "L_SEARCH"].includes(window.__yuniebel.getState().phase), null, { timeout: 15000 });
  let st = await getState(page);
  if (st.phase !== "L_SEARCH") { await moveTo(page, 865, 178); } // cửa mở dưới y=172
  await page.keyboard.press("Space");
  await moveTo(page, 20, 110);
  await page.waitForFunction(() => ["K_INIT", "K_BLOOD", "K_CHOICE"].includes(window.__yuniebel.getState().phase));
  await page.keyboard.press("Space");
  st = await getState(page);
  if (!["K_BLOOD", "K_CHOICE"].includes(st.phase)) {
    await moveTo(page, 60, 60);
  }
  st = await getState(page);
  if (st.phase !== "K_CHOICE") { await moveTo(page, 60, 60); }
  st = await getState(page);
  expect(st.phase).toBe("K_CHOICE");
  // chọn 2 → GAME OVER
  await page.keyboard.press("2");
  await page.waitForFunction(() => window.__yuniebel.getState().phase === "GAME_OVER");
  const overVisible = await page.locator("#gameover-screen").isVisible();
  expect(overVisible).toBeTruthy();
});

test("AC-3/AC-4: mood đổi đúng phase + SFX đếm được (audio.getMood/getStats)", async ({ page }) => {
  await page.goto(URL);
  const getMood = () => page.evaluate(() => window.__yuniebel.audio.getMood());
  const getStats = () => page.evaluate(() => window.__yuniebel.audio.getStats());
  // title → calm-happy
  expect(await getMood()).toBe("calm-happy");
  await page.click("#btn-start");
  await page.waitForFunction(() => window.__yuniebel.getState().phase === "G_INIT");
  await page.waitForTimeout(700); // chờ setMood áp dụng
  expect(await getMood()).toBe("garden-calm");
  // đủ loại SFX API tồn tại + counter là number
  const names = ["ting", "flutter", "meow", "happyMeow", "scaredMeow", "painMeow",
    "footstepGrass", "footstepEcho", "wind", "bird", "clockTick", "drip",
    "whisper", "whisperFar", "rush", "swoosh", "whoosh", "creak",
    "jumpscare", "candle", "bell", "sparkle"];
  const stats = await getStats();
  for (const n of names) {
    expect(typeof stats[n]).toBe("number");
  }
});

test("AC-13: debug API setPhase hoạt động (kiểm tra hook riêng)", async ({ page }) => {
  await page.goto(URL);
  await page.click("#btn-start");
  await page.waitForTimeout(500); // chờ fade hết
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("K_CHOICE");
    d.freeze(true);
  });
  await page.waitForFunction(() => window.__yuniebel.getState().phase === "K_CHOICE");
  const choiceVisible = await page.locator("#choice-box").isVisible();
  expect(choiceVisible).toBeTruthy();
  // freeze determinism: 2 frame render giống nhau
  const shot1 = await page.locator("#game").screenshot();
  await page.waitForTimeout(500);
  const shot2 = await page.locator("#game").screenshot();
  expect(Buffer.compare(shot1, shot2)).toBe(0);
});
