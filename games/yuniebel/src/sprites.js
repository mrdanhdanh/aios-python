/* sprites.js — Yuniebel's Cat (TASK-078) — vẽ lại hoàn toàn theo 5 ảnh tham khảo
 * Canvas primitives (fillRect) trên pixel grid 3px. 100% static, 0 asset.
 * MỌI animation nhận tham số time (dựa state.time — R1: freeze deterministic).
 */
(function (root) {
  "use strict";

  // ===== Palette (brief-visuals.md — Tổng hợp palette chính) =====
  var C = {
    skyDayTop: "#2f7de0", skyDayBot: "#a8dcff", skyDuskTop: "#ff9a3c", skyDuskBot: "#b04fd6",
    skyNightTop: "#0b1d4d", skyNightBot: "#1d3a8a", star: "#ffffff",
    sun: "#ffd93b", sunGlow: "#fff3b0",
    cloud: "#ffffff", cloudShade: "#dce9f7",
    grass: "#3fae4a", grassDark: "#2a6b33", grassLight: "#58c95f",
    dirt: "#8a5a33", wood: "#7a5230", woodDark: "#5a3a24", woodLight: "#9a6b42",
    wallCream: "#e8d9b8", wallCreamDark: "#d9c49a", roofRed: "#c0392b", roofDark: "#8e2b1f",
    fence: "#f2ede2", fenceShade: "#d4cbb8",
    sofaRed: "#c0483a", sofaRedDark: "#9c3629", cushion: "#e07b54",
    rug: "#d9b98a", rugStripe: "#c49b62",
    plant: "#2e8b57", pot: "#8b5a2b",
    blood: "#d92626", bloodDark: "#8f1010",
    cabWhite: "#e8e8ea", cabShade: "#c2c2c8", handle: "#3a3a44",
    oven: "#b8bcc4", fridge: "#d9dce2",
    ghostBlue: "#8ec9ff", ghostBlueDark: "#5f9ad1", skull: "#f4f6f8", skullDark: "#b8c0c8",
    ghostWhite: "#e8ecf2", ghostWhiteDark: "#c3ccd8",
    eyeYellow: "#ffd93b",
    catBody: "#f5a623", catWhite: "#ffffff", catDark: "#d98f1d", catPink: "#ffb6c1",
    ownerShirt: "#2e86de", ownerHair: "#7a4a21", ownerSkin: "#ffc9a3",
    cake: "#fff6e0", cakeFrost: "#ffc4e3", candle: "#ff6b3d", flame: "#ffd93b",
    fire: "#ff7b1c", fireHot: "#ffd93b",
    darkOverlay: "rgba(8,10,30,", // + alpha
    textYellow: "#ffd93b", boxBlack: "#101018", boxBorder: "#ffd93b"
  };

  // Pixel grid: vẽ logical 160×90, scale 3 → 480×270
  var GX = 3, GW = 160, GH = 90;

  function toRgb(h) {
    if (h[0] === "r") { // "rgb(r,g,b)" từ mix trước
      var m = h.match(/(\d+)/g);
      return [+m[0], +m[1], +m[2]];
    }
    var n = parseInt(h.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function mix(a, b, t) {
    var ca = toRgb(a), cb = toRgb(b);
    return "rgb(" + Math.round(ca[0] + (cb[0] - ca[0]) * t) + "," +
      Math.round(ca[1] + (cb[1] - ca[1]) * t) + "," +
      Math.round(ca[2] + (cb[2] - ca[2]) * t) + ")";
  }

  // ===== Helpers =====
  function R(ctx, x, y, w, h, col) { ctx.fillStyle = col; ctx.fillRect(x * GX, y * GX, w * GX, h * GX); }
  function P(ctx, x, y, col) { R(ctx, x, y, 1, 1, col); }

  // ===== 1. TITLE — trời xanh gradient + dithering, mặt trời, mây, đồi, nước, nút START =====
  function drawTitle(ctx, time) {
    // sky gradient (dithering 3 bands)
    var bands = 12;
    for (var i = 0; i < bands; i++) {
      var t = i / bands;
      R(ctx, 0, i * 5, GW, 5, mix(C.skyDayTop, C.skyDayBot, t));
    }
    // dithering chấm
    for (var y = 20; y < 55; y += 2) {
      for (var x = (y % 4) / 2; x < GW; x += 4) {
        P(ctx, x, y, "rgba(255,255,255,0.14)");
      }
    }
    // mặt trời + hào quang (phải trên)
    var sg = 10 + Math.sin(time * 1.2) * 0.8;
    R(ctx, 128, 6, 20, 20, C.sunGlow);
    R(ctx, 134, 8, 14, 14, "rgba(255,243,176,0.55)");
    R(ctx, 137, 10, 8, 8, C.sun);
    // mây trắng trôi
    var cdx = Math.sin(time * 0.35) * 3;
    cloud(ctx, 14 + cdx, 12, 26, 8);
    cloud(ctx, 66 - cdx * 0.6, 22, 18, 6);
    cloud(ctx, 100 + cdx * 0.8, 8, 14, 5);
    // đồi xanh lam xa
    R(ctx, 0, 56, GW, 6, "#7fb3d9");
    R(ctx, 0, 60, GW, 5, "#6ba3c9");
    hill(ctx, 0, 62, 40, 10, "#5f97c4");
    hill(ctx, 55, 62, 55, 10, "#5f97c4");
    hill(ctx, 120, 62, 40, 10, "#5f97c4");
    // bụi cây xanh đậm
    R(ctx, 0, 72, GW, 5, "#2e6b3a");
    bush(ctx, 8, 74, 22, 6, "#1f4f2a");
    bush(ctx, 60, 74, 18, 6, "#1f4f2a");
    bush(ctx, 118, 74, 24, 6, "#1f4f2a");
    // mặt nước
    for (i = 0; i < 13; i++) R(ctx, 0, 77 + i, GW, 1, mix("#1d4e89", "#163a63", i / 13));
    // gợn nước
    for (i = 0; i < 4; i++) {
      var wx = ((time * 12 + i * 37) % 160);
      R(ctx, wx, 80 + i * 3, 10, 1, "rgba(255,255,255,0.18)");
    }
    // mèo Yuniebel đứng cạnh nút START (brief ảnh 1)
    drawCat(ctx, 66, 60, 1, Math.floor(time * 4) % 2, time);
  }

  // ===== 2. GARDEN — nhà hiên, hàng rào, cây, bụi, hoa; trời ĐỘNG ngày→hoàng hôn→đêm =====
  // w: width map (160 cho scene 1 màn, 320 cho GARDEN/HALLWAY) — nền trải theo w
  function sky(ctx, darkness, time, w) {
    w = w || GW;
    // darkness 0..0.5: day→dusk; 0.5..1: dusk→night — luôn mix 2 HEX gốc (tránh NaN)
    var t1 = Math.min(darkness / 0.5, 1);
    var t2 = Math.max((darkness - 0.5) / 0.5, 0);
    var top, bot;
    if (darkness < 0.5) {
      top = mix(C.skyDayTop, C.skyDuskTop, t1);
      bot = mix(C.skyDayBot, C.skyDuskBot, t1);
    } else {
      top = mix(C.skyDuskTop, C.skyNightTop, t2);
      bot = mix(C.skyDuskBot, C.skyNightBot, t2);
    }
    for (var i = 0; i < 9; i++) {
      R(ctx, 0, i * 6, w, 6, mix(top, bot, i / 9));
    }
    // mặt trời lặn dần về phía chân trời (hoàng hôn)
    var sy = 4 + t1 * 22;
    if (t1 < 0.9) {
      R(ctx, 126, sy, 12, 12, C.sunGlow);
      R(ctx, 130, sy + 2, 8, 8, mix(C.sun, "#ff7b3c", t1));
    }
    // sao khi đêm
    if (t2 > 0.3) {
      for (i = 0; i < 18; i++) {
        var sx = (i * 37 + 13) % (w - 10);
        var sxx = (i * 53) % (w - 100) + 100;
        var tw = Math.sin(time * 2 + i) > 0.6 ? 1 : 0;
        if (tw) P(ctx, sx, 2 + (i * 7) % 20, C.star);
        if (tw && t2 > 0.6) P(ctx, sxx, 3 + (i * 11) % 16, "rgba(255,255,255,0.6)");
      }
    }
    // mây
    cloud(ctx, 20 + Math.sin(time * 0.3) * 3, 8, 20, 6, "rgba(255,255,255," + (0.9 - t1 * 0.5) + ")");
    cloud(ctx, 90 - Math.sin(time * 0.25) * 3, 16, 16, 5, "rgba(255,255,255," + (0.85 - t1 * 0.5) + ")");
    if (w > 200) { // mây phụ cho map 320
      cloud(ctx, 180 + Math.sin(time * 0.28) * 3, 10, 18, 6, "rgba(255,255,255," + (0.88 - t1 * 0.5) + ")");
      cloud(ctx, 250 - Math.sin(time * 0.2) * 3, 18, 16, 5, "rgba(255,255,255," + (0.82 - t1 * 0.5) + ")");
    }
  }

  function cloud(ctx, x, y, w, h, col) {
    col = col || C.cloud;
    R(ctx, x, y + 2, w, h - 2, col);
    R(ctx, x + 3, y, w - 6, 3, col);
    R(ctx, x + Math.floor(w * 0.6), y - 1, Math.floor(w * 0.3), 2, col);
  }

  function hill(ctx, x, y, w, h, col) {
    R(ctx, x, y, w, h, col);
    P(ctx, x + Math.floor(w * 0.3), y, col); P(ctx, x + Math.floor(w * 0.6), y, col);
  }
  function bush(ctx, x, y, w, h, col) {
    R(ctx, x, y + 1, w, h - 1, col);
    R(ctx, x + 2, y, w - 4, 2, col);
  }

  // ===== 2. GARDEN — map 320×90 logical (2 màn hình, camera scroll) =====
  function drawGarden(ctx, state, time, cx) {
    cx = cx || 0;
    var d = state.darkness || 0;
    var i;
    ctx.save();
    ctx.translate(-cx * GX, 0); // C2-P1-2: bọc translate — không restore → transform rò rỉ
    sky(ctx, d, time, 320);
    // cỏ
    R(ctx, 0, 66, 320, 24, mix(C.grass, C.grassDark, Math.min(d * 1.2, 1)));
    // vệt cỏ sáng
    for (i = 0; i < 16; i++) P(ctx, (i * 23 + 5) % 320, 70 + (i % 5) * 3, C.grassLight);
    // đường mòn đất
    R(ctx, 40, 76, 180, 2, mix(C.dirt, "#4a2f16", d));
    R(ctx, 60, 78, 120, 2, mix(C.dirt, "#4a2f16", d));
    // hàng rào trắng (trải 0..320)
    for (i = 0; i < 16; i++) {
      var fx = 8 + i * 18;
      R(ctx, fx, 62, 2, 10, mix(C.fence, "#9a9386", d));
      R(ctx, fx - 2, 63, 6, 2, mix(C.fence, "#9a9386", d));
      R(ctx, fx - 2, 69, 6, 2, mix(C.fence, "#9a9386", d));
    }
    // bụi cây + hoa (khớp 4 wall GARDEN)
    bush(ctx, 67, 62, 8, 5, mix("#2e8b57", "#14402a", d));
    bush(ctx, 117, 33, 7, 5, mix("#2e8b57", "#14402a", d));
    bush(ctx, 207, 85, 9, 4, mix("#2e8b57", "#14402a", d));
    bush(ctx, 13, 50, 7, 4, mix("#2e8b57", "#14402a", d));
    R(ctx, 72, 66, 2, 2, "#ff6b9d"); R(ctx, 121, 36, 2, 2, "#ff6b9d");
    R(ctx, 210, 87, 2, 2, "#ffd93b"); R(ctx, 42, 74, 2, 2, "#ffd93b");
    // quả bóng đỏ
    R(ctx, 56, 72, 4, 4, "#e03030"); R(ctx, 57, 73, 1, 1, "rgba(255,255,255,0.5)");
    // cây lớn (230,13 — khớp wall cây)
    R(ctx, 230, 36, 3, 24, C.woodDark);
    R(ctx, 223, 24, 17, 16, mix("#2e8b57", "#0f3020", d));
    R(ctx, 226, 12, 11, 14, mix("#3aa05f", "#155030", d));
    // ===== NGÔI NHÀ (x 267..320 — khớp wall nhà (267,7,53,43)) =====
    // thân nhà (tường be)
    R(ctx, 267, 26, 53, 24, mix(C.wallCream, "#8a7a58", d));
    // mái đỏ 3 lớp
    R(ctx, 265, 22, 57, 5, mix(C.roofRed, "#5e1c13", d));
    R(ctx, 268, 19, 51, 4, mix(C.roofRed, "#5e1c13", d));
    R(ctx, 271, 16, 45, 4, mix(C.roofRed, "#5e1c13", d));
    // cửa gỗ (khớp door zone 284,48)
    R(ctx, 285, 42, 9, 8, mix(C.wood, "#3c2716", d));
    R(ctx, 286, 43, 7, 6, mix(C.woodDark, "#2a1a0e", d));
    // cửa sổ
    R(ctx, 271, 32, 5, 5, mix("#bfe8ff", "#20304a", d));
    R(ctx, 300, 32, 5, 5, mix("#bfe8ff", "#20304a", d));
    R(ctx, 273, 34, 1, 3, C.woodDark); R(ctx, 302, 34, 1, 3, C.woodDark);
    // hiên nhà
    R(ctx, 265, 49, 55, 2, mix(C.wood, "#3c2716", d));
    R(ctx, 265, 48, 55, 1, mix(C.woodLight, "#5a3a24", d));
    // đèn hiên khi darkness>0.15 (hoàng hôn, ảnh B panel 2)
    if (d > 0.15) {
      R(ctx, 287, 38, 2, 2, "#ffd93b");
      R(ctx, 285, 39, 6, 1, "rgba(255,217,59,0.35)");
    }
    // chủ nhân đứng ở cửa khi G_INIT (gọi mèo)
    if (state.phase === "G_INIT" && state.dialogue) {
      drawOwner(ctx, 288, 44, 0, 1);
    }
    ctx.restore();
  }

  // ===== 3. LIVING — phòng khách ấm áp (ảnh C trái) =====
  function drawLiving(ctx, time) {
    var i;
    // tường kem sọc mờ
    R(ctx, 0, 0, GW, 62, C.wallCream);
    for (i = 0; i < 10; i++) R(ctx, (i * 16 + 6) % GW, 0, 2, 62, "rgba(190,170,130,0.35)");
    // sàn gỗ
    for (i = 0; i < 8; i++) R(ctx, 0, 62 + i * 4, GW, 4, mix(C.wood, "#6a4526", i / 8));
    // viền chân tường
    R(ctx, 0, 62, GW, 2, C.woodDark);
    // sofa đỏ cam + gối (khớp wall (10,53,30,15))
    R(ctx, 10, 52, 30, 12, C.sofaRedDark);
    R(ctx, 8, 50, 32, 5, C.sofaRed);
    R(ctx, 12, 48, 10, 4, C.cushion);   // gối tựa
    R(ctx, 24, 48, 8, 4, C.cushion);
    R(ctx, 10, 64, 4, 4, C.sofaRedDark); // chân
    R(ctx, 36, 64, 4, 4, C.sofaRedDark);
    // thảm trải (giữa sofa và bàn trà)
    R(ctx, 44, 73, 20, 2, C.rug);
    for (i = 0; i < 6; i++) R(ctx, 44 + i * 4, 73, 2, 2, C.rugStripe);
    // bàn trà gỗ (khớp wall (63,67,23,4))
    R(ctx, 63, 66, 23, 2, C.woodLight);
    R(ctx, 65, 68, 19, 4, C.wood);
    R(ctx, 63, 72, 2, 2, C.woodDark); R(ctx, 82, 72, 2, 2, C.woodDark);
    // đèn tường sconce
    R(ctx, 12, 12, 2, 6, C.woodDark); R(ctx, 10, 10, 6, 3, "#ffd93b");
    R(ctx, 10, 13, 6, 1, "rgba(255,217,59,0.3)");
    R(ctx, 142, 12, 2, 6, C.woodDark); R(ctx, 138, 10, 6, 3, "#ffd93b");
    // tranh treo tường
    R(ctx, 40, 18, 14, 10, "#f4f0e6"); R(ctx, 42, 20, 10, 6, "#8ec9ff");
    R(ctx, 42, 24, 10, 2, "#3fae4a");
    R(ctx, 62, 18, 10, 10, "#f4f0e6"); R(ctx, 64, 20, 6, 6, "#ffc4a3");
    // đồng hồ tròn
    R(ctx, 82, 16, 10, 10, C.woodLight);
    R(ctx, 84, 18, 6, 6, "#ffffff");
    R(ctx, 86, 20, 1, 2, C.woodDark); R(ctx, 87, 21, 2, 1, C.woodDark);
    // kệ đứng + chậu cây (phải — khớp wall kệ (127,70,10,17))
    R(ctx, 126, 62, 12, 24, C.wood);
    R(ctx, 127, 64, 4, 6, "#b04a3c"); R(ctx, 133, 64, 4, 6, "#b04a3c");
    R(ctx, 127, 72, 4, 6, "#3a6e4a"); R(ctx, 133, 72, 4, 6, "#3a6e4a");
    R(ctx, 127, 80, 4, 4, "#b04a3c"); R(ctx, 133, 80, 4, 4, "#b04a3c");
    R(ctx, 138, 56, 6, 8, C.pot);
    R(ctx, 139, 52, 4, 6, C.plant); R(ctx, 140, 50, 2, 3, C.plant);
    // cửa tối hậu cảnh (bếp)
    R(ctx, 96, 34, 12, 26, "#0a0a14");
    R(ctx, 96, 34, 2, 26, C.woodDark); R(ctx, 106, 34, 2, 26, C.woodDark);
    // cửa ra phòng khách — bên trái (đi tới bếp) + mũi tên (khớp door_kitchen (3,30,11,20))
    R(ctx, 0, 36, 4, 24, "#1a1a24");
    arrow(ctx, 3, 46, 1);
  }

  // ===== 4. KITCHEN — bếp tối: tủ trắng, lò, tủ lạnh, vết máu LỚN, mắt sáng (ảnh C phải) =====
  function drawKitchen(ctx, state, time) {
    var i, x, y;
    R(ctx, 0, 0, GW, 60, mix("#4a4a52", "#22222a", 0.25));
    // sàn gạch nâu tối
    for (y = 60; y < 90; y += 6) {
      for (x = 0; x < GW; x += 8) {
        R(ctx, x, y, 8, 6, ((x / 8 + y / 6) % 2 === 0) ? "#5a4530" : "#4e3c28");
      }
    }
    // tủ bếp trắng trên (giữ nguyên — C2-P3-6: mèo vẽ đè, chấp nhận)
    R(ctx, 0, 10, 80, 22, C.cabWhite);
    R(ctx, 0, 10, 80, 3, C.cabShade);
    for (i = 0; i < 5; i++) {
      R(ctx, 4 + i * 16, 16, 10, 12, "#f4f4f6");
      R(ctx, 11 + i * 16, 20, 2, 3, C.handle);
    }
    // lò + nồi
    R(ctx, 82, 24, 22, 20, C.oven);
    R(ctx, 84, 26, 8, 6, "#2a2a32");
    R(ctx, 84, 36, 8, 6, "#2a2a32");
    R(ctx, 96, 28, 4, 4, C.handle);
    // tủ lạnh (khớp wall tủ (127,7,33,43))
    R(ctx, 128, 12, 16, 30, C.fridge);
    R(ctx, 130, 14, 12, 2, "#c0c4cc");
    P(ctx, 138, 26, "#8a8f98"); P(ctx, 136, 24, "#8a8f98"); P(ctx, 138, 24, "#8a8f98"); P(ctx, 136, 26, "#8a8f98");
    // bàn bếp (khớp wall (100,47,30,15))
    R(ctx, 100, 47, 30, 3, C.woodLight);
    R(ctx, 102, 50, 2, 12, C.woodDark); R(ctx, 126, 50, 2, 12, C.woodDark);
    // cửa sổ
    R(ctx, 60, 2, 16, 8, "#0d1526");
    R(ctx, 62, 4, 12, 6, "#1a2a4a");
    R(ctx, 68, 3, 1, 7, C.woodDark); R(ctx, 62, 6, 12, 1, C.woodDark);
    // VẾT MÁU LỚN (khớp blood zone (50,78,40,8), ảnh C)
    R(ctx, 50, 78, 40, 8, C.blood);
    R(ctx, 54, 86, 26, 3, C.blood);
    R(ctx, 66, 86, 6, 2, C.bloodDark);
    R(ctx, 52, 80, 6, 3, C.bloodDark); R(ctx, 84, 81, 5, 3, C.bloodDark);
    // giọt máu anim (drip)
    var drippy = Math.floor(time * 1.2) % 2 === 0;
    if (drippy) P(ctx, 76, 89, C.bloodDark);
    // VÙNG TỐI + 2 MẮT TRẮNG SÁNG (khớp DARK_RECT (7,7,31,33))
    R(ctx, 7, 7, 31, 33, "#05050c");
    if (Math.floor(time * 2) % 2 === 0) {
      R(ctx, 17, 19, 3, 2, "#ffffff"); R(ctx, 25, 19, 3, 2, "#ffffff");
    }
    // cửa ra (phải — quay về phòng khách ma ám, khớp door_out (149,43,11,20))
    R(ctx, 149, 40, 4, 20, "#0a0a14");
    // nếu đang K_CHOICE: highlight vết máu
    if (state.phase === "K_CHOICE") {
      R(ctx, 50, 78, 40, 8, "rgba(255,255,255,0.25)");
    }
  }

  // ===== 5. HAUNTED — phòng khách ma ám: tối xanh đen, ma XANH đầu lâu chặn cửa (ảnh D) =====
  function drawHaunted(ctx, state, time) {
    var i;
    // tường tối
    R(ctx, 0, 0, GW, 60, mix("#23203d", "#10101f", 0.4));
    // dầm gỗ trần
    R(ctx, 0, 4, GW, 3, "#0c0c18");
    R(ctx, 20, 0, 3, 8, "#0c0c18"); R(ctx, 80, 0, 3, 8, "#0c0c18"); R(ctx, 140, 0, 3, 8, "#0c0c18");
    // mạng nhện
    R(ctx, 4, 8, 3, 1, "rgba(200,200,220,0.3)"); R(ctx, 8, 4, 1, 3, "rgba(200,200,220,0.3)");
    R(ctx, 5, 5, 1, 1, "rgba(200,200,220,0.3)"); R(ctx, 6, 6, 1, 1, "rgba(200,200,220,0.3)");
    // sàn gỗ tối
    for (i = 0; i < 8; i++) R(ctx, 0, 62 + i * 4, GW, 4, mix("#2a2038", "#171020", i / 8));
    // sofa cũ (khớp wall (10,53,30,15))
    R(ctx, 10, 52, 28, 12, "#5c2430");
    R(ctx, 8, 50, 30, 4, "#6e2a38");
    // bàn nhỏ + chân nến (khớp wall (67,68,20,4))
    R(ctx, 67, 66, 20, 3, "#3c2a20");
    R(ctx, 76, 62, 2, 4, "#7a5a2b"); R(ctx, 77, 60, 1, 2, "#ffd93b");
    if (Math.floor(time * 3) % 2 === 0) P(ctx, 77, 59, "#ff8c1c");
    // đồng hồ quả lắc (grandfather clock)
    R(ctx, 120, 16, 10, 34, C.woodDark);
    R(ctx, 122, 18, 6, 6, "#0c0c18"); R(ctx, 123, 20, 4, 3, "#8ec9ff");
    R(ctx, 122, 26, 6, 16, "#1c1226"); R(ctx, 123, 28, 4, 12, "#0c0c18");
    var pend = Math.sin(time * 2) * 2;
    R(ctx, 125, 28 + Math.floor(pend), 1, 10, "#c8c8d0");
    // ảnh treo nghiêng
    ctx.save(); ctx.translate(60 * GX, 20 * GX); ctx.rotate(0.12);
    R(ctx, -8, -6, 16, 12, "#3a2a20"); R(ctx, -6, -4, 12, 8, "#1a1020");
    ctx.restore();
    // CỬA CHÍNH + MA XANH ĐẦU LÂU LỚN chặn (khớp door_front (143,33,15,33), ảnh D)
    R(ctx, 143, 20, 12, 40, "#0a0a16");
    R(ctx, 143, 20, 2, 40, "#3c2a4a"); R(ctx, 153, 20, 2, 40, "#3c2a4a");
    if (state.phase !== "H_INIT" || !state.dialogue) {
      drawGhostSkull(ctx, 139, 16, time, state);
    }
    // cửa phụ trái (khớp door_side (2,30,11,20))
    R(ctx, 0, 36, 4, 24, "#0a0a16");
    arrow(ctx, 2, 46, 1);
    // glow xanh quanh ma
    R(ctx, 143, 34, 12, 20, "rgba(142,201,255,0.08)");
  }

  // ===== 6. HALLWAY — hành lang gỗ tối + 5 jump scare (map 320×90, camera scroll) =====
  function drawHallway(ctx, state, time, cx) {
    cx = cx || 0;
    var i;
    ctx.save();
    ctx.translate(-cx * GX, 0); // C2-P1-2
    // tường tối + sàn ván (trải 320)
    R(ctx, 0, 0, 320, 54, "#17131f");
    for (i = 0; i < 6; i++) R(ctx, 0, 62 + i * 4, 320, 4, mix("#241a30", "#161020", i / 6));
    R(ctx, 0, 60, 320, 2, "#0c0814");
    // ván sàn
    for (i = 0; i < 40; i++) P(ctx, i * 8, 64, "#2e2038");
    for (i = 0; i < 40; i++) P(ctx, i * 8 + 4, 70, "#2e2038");
    // nến/đuốc tường (11 cái trải 0..320)
    for (i = 0; i < 11; i++) {
      var tx = 8 + i * 29;
      R(ctx, tx, 12, 2, 8, "#3c2a20");
      R(ctx, tx - 1, 10, 4, 3, "#ffd93b");
      if (Math.floor(time * 4 + i) % 2 === 0) P(ctx, tx, 9, "#ff8c1c");
      R(ctx, tx - 3, 12, 8, 1, "rgba(255,150,60,0.12)");
    }
    // cửa hai đầu (khớp wall trái (0,33,9,23) + door_dining (302,33,14,20))
    R(ctx, 0, 36, 4, 24, "#0a0a14");
    R(ctx, 316, 36, 4, 24, "#0a0a14");
    // 5 kiểu hù (mapping §6.2) — vị trí tuyệt đối trong map, luôn trong viewport khi kích hoạt
    var sa = state.scareActive;
    if (sa === 1) drawScareGhost(ctx, 130, 30, time);          // ma trắng ga
    if (sa === 2) drawScarePortrait(ctx, 160, 12, time);        // chân dung hét
    if (sa === 3) drawScareHands(ctx, 210, 34, time);           // tay zombie
    if (sa === 4) drawScareShadow(ctx, 260, 20, time);          // bóng mắt vàng
    if (sa === 5) drawScareSkull(ctx, 300, 26, time);           // mặt xương
    ctx.restore();
  }

  // ===== 7. BIRTHDAY — sinh nhật: lò sưởi, bánh kem 4 nến, chủ, sparkle =====
  function drawBirthday(ctx, state, time) {
    // phòng ấm
    R(ctx, 0, 0, GW, 60, "#f2d9b0");
    for (var i = 0; i < 10; i++) R(ctx, (i * 16 + 6) % GW, 0, 2, 60, "rgba(220,190,140,0.4)");
    for (i = 0; i < 8; i++) R(ctx, 0, 62 + i * 4, GW, 4, mix(C.wood, "#6a4526", i / 8));
    R(ctx, 0, 62, GW, 2, C.woodDark);
    // băng rôn "HAPPY BIRTHDAY"
    R(ctx, 20, 8, 60, 6, "#e0709a");
    R(ctx, 24, 10, 52, 3, "#ffffff");
    ctx.fillStyle = "#e0709a"; ctx.font = "bold " + 3 * 3 + "px monospace";
    ctx.fillText("HAPPY BIRTHDAY", 22 * 3, 12 * 3);
    // lò sưởi (trái)
    R(ctx, 8, 40, 26, 22, "#8a4a2e");
    R(ctx, 10, 42, 22, 14, "#2a160c");
    var fl = Math.floor(time * 6) % 3;
    R(ctx, 13, 48 + fl * 0, 6, 4, C.fireHot);
    R(ctx, 17, 46 + (fl % 2), 4, 4, C.fire);
    R(ctx, 21, 48, 4, 3, C.fire);
    R(ctx, 8, 62, 26, 2, "#5c2f1c");
    // bánh kem 4 nến (giữa)
    R(ctx, 70, 48, 20, 6, C.cake);
    R(ctx, 72, 46, 16, 3, C.cakeFrost);
    R(ctx, 76, 50, 8, 2, "#ff9db8");
    for (i = 0; i < 4; i++) {
      R(ctx, 74 + i * 4, 42, 1, 5, "#ff6b9d");
      R(ctx, 74 + i * 4, 40, 1, 2, (Math.floor(time * 5 + i) % 2 === 0) ? C.flame : "#ff8c1c");
    }
    // chủ nhân đứng cạnh bánh
    drawOwner(ctx, 96, 42, Math.floor(time * 4) % 2 === 0 ? 0 : 1, 1);
    // sparkle
    for (i = 0; i < 8; i++) {
      var sx = (i * 29 + 10) % 150, sy = (i * 17) % 30;
      if (Math.sin(time * 3 + i * 1.7) > 0.5) P(ctx, sx, sy + 34, "#ffd93b");
    }
    // text lớn "Chúc Mừng Sinh Nhật!" (canvas — C2-12 không emoji)
    ctx.fillStyle = "#c0392b";
    ctx.font = "bold " + 4 * 3 + "px monospace";
    ctx.fillText("Chuc Mung Sinh Nhat!", 30 * 3, 40 * 3);
  }

  // ===== 8. GAME OVER / END =====
  function drawGameOver(ctx) {
    R(ctx, 0, 0, GW, GH, "#1a0508");
    R(ctx, 0, 0, GW, GH, "rgba(120,10,20,0.25)");
    ctx.fillStyle = "#ff3b3b";
    ctx.font = "bold " + 8 * 3 + "px monospace";
    ctx.fillText("GAME OVER", 36 * 3, 40 * 3);
    ctx.fillStyle = "#d9c9a3";
    ctx.font = 4 * 3 + "px monospace";
    ctx.fillText("Yuniebel da di vao bong toi...", 20 * 3, 50 * 3);
  }
  function drawEnd(ctx, time) {
    R(ctx, 0, 0, GW, GH, "#f2d9b0");
    for (var i = 0; i < 8; i++) {
      var sx = (i * 31 + 8) % 155, sy = (i * 23) % 80;
      if (Math.sin(time * 3 + i) > 0.3) P(ctx, sx, sy, "#ffd93b");
    }
    R(ctx, 62, 44, 36, 8, C.cake);
    R(ctx, 64, 41, 32, 4, C.cakeFrost);
    for (i = 0; i < 4; i++) { R(ctx, 68 + i * 8, 38, 1, 4, "#ff6b9d"); R(ctx, 68 + i * 8, 36, 1, 2, C.flame); }
    ctx.fillStyle = "#8a4a2e";
    ctx.font = "bold " + 6 * 3 + "px monospace";
    ctx.fillText("Chuc Mung Sinh Nhat", 16 * 3, 30 * 3);
    ctx.fillText("Yuniebel!", 48 * 3, 38 * 3);
  }

  // ===== SPRITES =====
  // Mèo cam-trắng (16×16 logical, 3×)
  function drawCat(ctx, x, y, dir, frame, time) {
    x = Math.round(x); y = Math.round(y);
    var lx = dir >= 0 ? x : x + 16;
    ctx.save();
    if (dir < 0) { ctx.translate((x + 8) * GX, 0); ctx.scale(-1, 1); ctx.translate(-(x + 8) * GX, 0); }
    // đuôi
    var tw = Math.sin(time * 6) * 1.5;
    R(ctx, lx + 12, y + 8 + Math.floor(tw), 3, 2, C.catDark);
    // thân (trắng bụng)
    R(ctx, lx + 3, y + 7, 9, 7, C.catBody);
    R(ctx, lx + 5, y + 10, 5, 3, C.catWhite);
    // chân (anim chạy)
    var f = frame % 2;
    R(ctx, lx + 3, y + 13, 2, 3, f === 0 ? C.catBody : C.catWhite);
    R(ctx, lx + 9, y + 13, 2, 3, f === 1 ? C.catBody : C.catWhite);
    // đầu
    R(ctx, lx + 2, y + 1, 11, 7, C.catBody);
    R(ctx, lx + 4, y + 3, 6, 3, C.catWhite); // mặt trắng
    // tai
    R(ctx, lx + 2, y - 1, 3, 3, C.catBody); R(ctx, lx + 10, y - 1, 3, 3, C.catBody);
    R(ctx, lx + 3, y - 1, 2, 2, C.catPink); R(ctx, lx + 11, y - 1, 2, 2, C.catPink);
    // mắt
    R(ctx, lx + 4, y + 3, 2, 2, "#1a1a2e"); R(ctx, lx + 9, y + 3, 2, 2, "#1a1a2e");
    P(ctx, lx + 4, y + 3, "#ffffff"); P(ctx, lx + 9, y + 3, "#ffffff");
    // mũi
    P(ctx, lx + 7, y + 5, C.catPink);
    // ria
    P(ctx, lx + 1, y + 4, "#ffffff"); P(ctx, lx, y + 5, "#ffffff");
    P(ctx, lx + 13, y + 4, "#ffffff"); P(ctx, lx + 14, y + 5, "#ffffff");
    ctx.restore();
  }

  // Chủ nhân (cậu bé: tóc nâu, áo xanh)
  function drawOwner(ctx, x, y, frame, dir) {
    R(ctx, x + 3, y, 5, 3, C.ownerHair);
    R(ctx, x + 2, y + 2, 7, 3, C.ownerHair);
    R(ctx, x + 4, y + 2, 4, 4, C.ownerSkin);
    P(ctx, x + 5, y + 3, "#1a1a2e"); P(ctx, x + 7, y + 3, "#1a1a2e");
    P(ctx, x + 6, y + 5, "#ff6b9d");
    // áo xanh
    R(ctx, x + 3, y + 6, 6, 5, C.ownerShirt);
    if (frame === 1) { R(ctx, x + 1, y + 7, 3, 3, C.ownerShirt); R(ctx, x + 8, y + 7, 3, 3, C.ownerShirt); }
    else { R(ctx, x + 3, y + 7, 2, 3, C.ownerShirt); R(ctx, x + 7, y + 7, 2, 3, C.ownerShirt); }
    // quần + chân
    R(ctx, x + 3, y + 11, 6, 3, "#3d5a80");
    R(ctx, x + 3, y + 14, 2, 2, "#3c2716"); R(ctx, x + 7, y + 14, 2, 2, "#3c2716");
  }

  // Bướm vàng (8×6 logical)
  function drawButterfly(ctx, x, y, time) {
    var fr = Math.floor(time * 8) % 2 === 0 ? 0 : 3;
    R(ctx, x - 2 - fr, y - 2, 3, 3, "#e8c93a");
    R(ctx, x + 2, y - 2, 3 + fr, 3, "#e8c93a");
    R(ctx, x - 1, y + 1, 2, 2, "#d4a61e");
    R(ctx, x + 2, y + 1, 2, 2, "#d4a61e");
    P(ctx, x, y, "#3c2a10");
  }

  // Ma xanh đầu lâu LỚN (ảnh D) — 12×20 logical
  function drawGhostSkull(ctx, x, y, time, state) {
    var bob = Math.sin(time * 2) * 1;
    var a = state && state.darkness > 0.5 ? 0.85 : 1;
    var g = "rgba(142,201,255," + a + ")";
    R(ctx, x + 1, y + 2 + Math.floor(bob), 10, 14, g);
    R(ctx, x, y + 4 + Math.floor(bob), 12, 8, g);
    R(ctx, x + 2, y + 16 + Math.floor(bob), 8, 3, g);
    // đuôi ma lượn
    var w1 = Math.floor(Math.sin(time * 3) * 1);
    R(ctx, x + 2, y + 19 + Math.floor(bob), 3 - w1, 2, g);
    R(ctx, x + 7, y + 19 + Math.floor(bob), 3 + w1, 2, g);
    // hộp sọ trắng
    R(ctx, x + 2, y + 4 + Math.floor(bob), 8, 6, C.skull);
    R(ctx, x + 3, y + 3 + Math.floor(bob), 2, 2, C.skull);
    R(ctx, x + 7, y + 3 + Math.floor(bob), 2, 2, C.skull);
    P(ctx, x + 3, y + 6 + Math.floor(bob), "#0a0a14"); P(ctx, x + 8, y + 6 + Math.floor(bob), "#0a0a14");
    P(ctx, x + 4, y + 8 + Math.floor(bob), "#0a0a14"); P(ctx, x + 7, y + 8 + Math.floor(bob), "#0a0a14");
  }

  // ===== 5 KIỂU HÙ (ảnh E) =====
  // 1. Ma trắng ga
  function drawScareGhost(ctx, x, y, time) {
    var bob = Math.sin(time * 4) * 1;
    var g = "rgba(232,236,242,0.9)";
    R(ctx, x, y + 2 + bob, 10, 12, g);
    R(ctx, x + 1, y + 14 + bob, 8, 3, g);
    R(ctx, x + 2, y + 17 + bob, 2, 2, g); R(ctx, x + 6, y + 17 + bob, 2, 2, g);
    R(ctx, x + 2, y + 4 + bob, 2, 2, "#0a0a14"); R(ctx, x + 6, y + 4 + bob, 2, 2, "#0a0a14");
    R(ctx, x + 3, y + 7 + bob, 4, 2, "#0a0a14");
  }
  // 2. Chân dung hét (tay vươn khỏi khung)
  function drawScarePortrait(ctx, x, y, time) {
    R(ctx, x, y, 14, 12, "#4a3a2a");
    R(ctx, x + 1, y + 1, 12, 10, "#1a1020");
    R(ctx, x + 3, y + 3, 8, 6, "#c9a38a");
    R(ctx, x + 4, y + 2, 2, 2, "#5a3a20"); R(ctx, x + 8, y + 2, 2, 2, "#5a3a20");
    // miệng hét
    R(ctx, x + 5, y + 7, 4, 3, "#3a0a0a");
    // tay vươn
    var ext = Math.floor(time * 4) % 2 === 0 ? 2 : 0;
    R(ctx, x - 3 - ext, y + 4, 3 + ext, 2, "#c9a38a");
    R(ctx, x + 13, y + 4, 3 + ext, 2, "#c9a38a");
  }
  // 3. Tay zombie từ bóng tối
  function drawScareHands(ctx, x, y, time) {
    R(ctx, x - 4, y - 6, 14, 14, "#05050c");
    var r1 = Math.floor(time * 3) % 2 === 0 ? 0 : 1;
    R(ctx, x + 0, y + 2 + r1, 3, 5, "#cfd4dc");
    R(ctx, x + 5, y + 4 - r1, 3, 5, "#cfd4dc");
    R(ctx, x + 9, y + 1 + r1, 3, 5, "#cfd4dc");
    P(ctx, x + 1, y + 5, "#8a8f98"); P(ctx, x + 6, y + 6, "#8a8f98"); P(ctx, x + 10, y + 5, "#8a8f98");
  }
  // 4. Bóng đen mắt vàng
  function drawScareShadow(ctx, x, y, time) {
    R(ctx, x, y + 4, 14, 18, "#05050c");
    R(ctx, x + 1, y + 2, 12, 16, "#05050c");
    R(ctx, x + 3, y, 8, 14, "#05050c");
    if (Math.floor(time * 2) % 2 === 0) {
      R(ctx, x + 4, y + 6, 3, 2, C.eyeYellow); R(ctx, x + 9, y + 6, 3, 2, C.eyeYellow);
    }
  }
  // 5. Mặt xương sọ lớn
  function drawScareSkull(ctx, x, y, time) {
    var s = Math.floor(time * 5) % 2 === 0 ? 1 : 0;
    R(ctx, x, y, 12, 11, C.skull);
    R(ctx, x + 1, y - 1 + s, 10, 4, C.skullDark);
    R(ctx, x + 2, y + 2, 3, 4, "#0a0a14"); R(ctx, x + 7, y + 2, 3, 4, "#0a0a14");
    R(ctx, x + 3, y + 8, 6, 2, "#0a0a14");
    P(ctx, x + 1, y + 4, C.skullDark); P(ctx, x + 10, y + 4, C.skullDark);
  }

  // Vết máu (bếp)
  function drawBlood(ctx, x, y, time) {
    R(ctx, x, y, 24, 5, C.blood);
    R(ctx, x + 4, y + 5, 16, 3, C.blood);
    R(ctx, x + 8, y + 8, 8, 2, C.bloodDark);
    R(ctx, x - 2, y + 3, 4, 3, C.bloodDark); R(ctx, x + 22, y + 4, 4, 2, C.bloodDark);
    if (Math.floor(time * 1.5) % 2 === 0) P(ctx, x + 12, y + 10, C.bloodDark);
  }

  // Bánh kem (cảnh 6 + END)
  function drawCake(ctx, x, y, time) {
    R(ctx, x, y, 16, 5, C.cake);
    R(ctx, x + 1, y - 2, 14, 3, C.cakeFrost);
    R(ctx, x + 2, y + 1, 12, 2, "#ff9db8");
    for (var i = 0; i < 4; i++) {
      R(ctx, x + 3 + i * 4, y - 6, 1, 4, "#ff6b9d");
      R(ctx, x + 3 + i * 4, y - 8, 1, 2, (Math.floor(time * 5 + i) % 2 === 0) ? C.flame : "#ff8c1c");
    }
  }

  // Mũi tên chỉ đường
  function arrow(ctx, x, y, dir) {
    if (dir === 1) { R(ctx, x, y + 1, 4, 1, C.textYellow); R(ctx, x + 1, y, 2, 1, C.textYellow); R(ctx, x + 1, y + 3, 2, 1, C.textYellow); }
    else { R(ctx, x, y + 1, 4, 1, C.textYellow); R(ctx, x + 1, y, 2, 1, C.textYellow); R(ctx, x + 1, y + 3, 2, 1, C.textYellow); }
  }

  // ===== Public =====
  root.Sprites = {
    GX: GX, GW: GW, GH: GH, C: C,
    drawTitle: drawTitle,
    drawGarden: drawGarden,
    drawLiving: drawLiving,
    drawKitchen: drawKitchen,
    drawHaunted: drawHaunted,
    drawHallway: drawHallway,
    drawBirthday: drawBirthday,
    drawGameOver: drawGameOver,
    drawEnd: drawEnd,
    drawCat: drawCat,
    drawOwner: drawOwner,
    drawButterfly: drawButterfly,
    drawGhostSkull: drawGhostSkull,
    drawScareGhost: drawScareGhost,
    drawScarePortrait: drawScarePortrait,
    drawScareHands: drawScareHands,
    drawScareShadow: drawScareShadow,
    drawScareSkull: drawScareSkull,
    drawBlood: drawBlood,
    drawCake: drawCake,
    arrow: arrow
  };
})(typeof self !== "undefined" ? self : this);
