/* debug-zoom.spec.js — debug tạm (xoá sau) — in zoom theo thời gian sau setScareZone(5) */
import { test } from "@playwright/test";

test("debug zoom timeline", async ({ page }) => {
  await page.goto("/?test=1");
  await page.click("#btn-start");
  await page.waitForTimeout(700);
  await page.evaluate(() => {
    const d = window.__yuniebel.debug;
    d.setPhase("W_WALK");
    d.setPlayer(263, 45);
    d.setScareZone(5);
  });
  // kiểm tra scene state + gọi update thủ công
  const base = await page.evaluate(() => {
    const g = window.__phaserGame;
    return {
      paused: g.scene.isPaused("Game"),
      active: g.scene.isActive("Game"),
      visible: g.scene.isVisible("Game"),
      camVisible: g.scene.getScene("Game").cameras.main.visible
    };
  });
  console.log("scene state:", JSON.stringify(base));
  await page.waitForTimeout(100);
  const manual = await page.evaluate(() => {
    const cam = window.__phaserGame.scene.getScene("Game").cameras.main;
    cam.zoomEffect.update(performance.now(), 100);
    cam.shakeEffect.update(performance.now(), 100);
    return {
      zoom: cam.zoom,
      zoomElapsed: cam.zoomEffect._elapsed,
      zoomProgress: cam.zoomEffect.progress,
      shakeElapsed: cam.shakeEffect._elapsed
    };
  });
  console.log("sau update thủ công 100ms:", JSON.stringify(manual));
  await page.waitForTimeout(300);
  const later = await page.evaluate(() => {
    const cam = window.__phaserGame.scene.getScene("Game").cameras.main;
    return { zoom: cam.zoom, zoomElapsed: cam.zoomEffect._elapsed, shakeElapsed: cam.shakeEffect._elapsed };
  });
  console.log("sau 300ms nữa (tự nhiên):", JSON.stringify(later));
});
