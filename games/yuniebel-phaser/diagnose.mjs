/* diagnose.mjs — chẩn đoán nhanh: load game qua preview, bắt console/pageerror/crash */
import { chromium } from "@playwright/test";

const browser = await chromium.launch({
  headless: true,
  args: ["--autoplay-policy=no-user-gesture-required"]
});
const page = await browser.newPage({ viewport: { width: 480, height: 270 } });

page.on("console", (msg) => console.log("[console." + msg.type() + "]", msg.text().slice(0, 300)));
page.on("pageerror", (err) => console.log("[pageerror]", err.message.slice(0, 500)));
page.on("crash", () => console.log("[CRASH] page crashed!"));
page.on("requestfailed", (req) => console.log("[requestfailed]", req.url(), req.failure()?.errorText));

try {
  await page.goto("http://localhost:4174/?test=1", { waitUntil: "load", timeout: 30000 });
  await page.waitForTimeout(3000);
  const info = await page.evaluate(() => ({
    hasYuniebel: !!window.__yuniebel,
    hasCore: !!window.AiosCore,
    hasSprites: !!window.Sprites,
    hasPhaser: !!window.__phaserGame,
    phase: window.__yuniebel ? window.__yuniebel.getState().phase : null,
    canvas: { w: document.getElementById("game")?.width, h: document.getElementById("game")?.height }
  }));
  console.log("[info]", JSON.stringify(info));
  // click START
  await page.click("#btn-start").catch((e) => console.log("[click-start fail]", e.message));
  await page.waitForTimeout(2000);
  const info2 = await page.evaluate(() => ({
    phase: window.__yuniebel ? window.__yuniebel.getState().phase : null,
    scene: window.__yuniebel ? window.__yuniebel.getState().scene : null
  }));
  console.log("[after-start]", JSON.stringify(info2));
} catch (e) {
  console.log("[goto fail]", e.message.slice(0, 500));
}

await browser.close();
