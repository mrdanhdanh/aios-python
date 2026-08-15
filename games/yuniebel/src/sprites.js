/* sprites.js — Pixel art "Yuniebel" (canvas primitives → cache offscreen)
 * Browser only. Vẽ chi tiết từng sprite bằng fillRect/arc → cache 1 lần.
 */
(function (root) {
  "use strict";
  var CACHE = {};
  function C(w, h) { var c = document.createElement("canvas"); c.width = w; c.height = h; return c.getContext("2d"); }
  function R(g, x, y, w, h, c) { g.fillStyle = c; g.fillRect(x, y, w, h); }
  function P(g, x, y, c) { R(g, x, y, 1, 1, c); }
  function flip(s, w, h) { var c = C(w, h); c.scale(-1, 1); c.drawImage(s, -w, 0); return c.canvas; }

  /* ===== MÈO (14×16) ===== */
  function cat(frame, dir) {
    var g = C(14, 16);
    R(g,4,0,2,3,"#d97735"); R(g,8,0,2,3,"#d97735"); // ears
    R(g,4,1,2,1,"#ff6fb5"); R(g,8,1,2,1,"#ff6fb5"); // inner ear
    R(g,3,3,8,6,"#e8893a"); R(g,4,3,6,1,"#c96d28"); // head
    R(g,5,5,2,2,"#fff"); R(g,7,5,2,2,"#fff");        // eye whites
    P(g,6,5,"#1a1a2e"); P(g,8,5,"#1a1a2e");           // pupils
    P(g,6,4,"#c96d28"); P(g,8,4,"#c96d28");           // brows
    P(g,6,7,"#ff6fb5");                                // nose
    P(g,5,8,"#c96d28"); P(g,7,8,"#c96d28");           // mouth
    P(g,2,6,"#fff"); P(g,1,5,"#fff");                  // whisker L
    P(g,11,6,"#fff"); P(g,12,5,"#fff");                // whisker R
    R(g,3,9,8,5,"#e8893a"); R(g,4,10,6,3,"#f5c49a");  // body+belly
    if (frame===0) { R(g,4,14,2,2,"#d97735"); R(g,8,14,2,2,"#d97735"); }
    else if (frame===1) { R(g,3,14,2,2,"#d97735"); R(g,9,13,2,3,"#d97735"); }
    else { R(g,9,14,2,2,"#d97735"); R(g,3,13,2,3,"#d97735"); }
    R(g,11,10,2,1,"#d97735"); P(g,12,11,"#d97735");   // tail
    R(g,7,0,3,2,"#ff6fb5"); P(g,9,2,"#ff6fb5");       // hair ribbon
    var cv = g.canvas;
    return dir < 0 ? flip(cv, 14, 16) : cv;
  }

  /* ===== BƯỚM (8×6) ===== */
  function butterfly(fr) {
    var g = C(8, 6);
    R(g,1,0,2,2,"#9b7bff"); R(g,5,0,2,2,"#9b7bff");
    R(g,0,1,3,2,"#c4a8ff"); R(g,5,1,3,2,"#c4a8ff");
    if (fr===0) { R(g,1,2,2,1,"#d4c5ff"); R(g,5,2,2,1,"#d4c5ff"); }
    P(g,3,2,"#1a1a2e"); P(g,4,2,"#1a1a2e");
    R(g,3,3,2,3,"#1a1a2e");
    return g.canvas;
  }

  /* ===== CHỦ (12×18) ===== */
  function owner(fr) {
    var g = C(12, 18);
    R(g,3,0,6,3,"#5a3520"); R(g,2,2,8,4,"#6b4226"); // hair
    R(g,4,3,4,4,"#ffb28a");                           // face
    P(g,5,4,"#1a1a2e"); P(g,7,4,"#1a1a2e");           // eyes
    P(g,6,5,"#ff6fb5"); P(g,5,6,"#c96d28"); P(g,6,6,"#c96d28");
    if (fr===0) {
      R(g,3,7,6,6,"#7ec8ff"); R(g,4,7,4,5,"#8fd8ff"); // shirt
      R(g,3,13,6,3,"#3d5a80");                         // pants
      R(g,4,16,2,2,"#5a3520"); R(g,7,16,2,2,"#5a3520");
    } else {
      R(g,1,8,3,3,"#7ec8ff"); R(g,8,8,3,3,"#7ec8ff"); // arms
      P(g,0,10,"#ffb28a"); P(g,11,10,"#ffb28a");       // hands
      R(g,3,7,6,6,"#7ec8ff"); R(g,4,7,4,5,"#8fd8ff");
      R(g,3,13,6,3,"#3d5a80");
      R(g,4,16,2,2,"#5a3520"); R(g,7,16,2,2,"#5a3520");
    }
    return g.canvas;
  }

  /* ===== CHỦ NGỒI (12×14) ===== */
  function ownerSit() {
    var g = C(12, 14);
    R(g,3,0,6,3,"#5a3520"); R(g,2,2,8,3,"#6b4226");
    R(g,4,2,4,4,"#ffb28a");
    P(g,5,3,"#1a1a2e"); P(g,7,3,"#1a1a2e");
    P(g,6,4,"#ff6fb5"); P(g,5,5,"#c96d28"); P(g,6,5,"#c96d28");
    R(g,3,6,6,4,"#7ec8ff"); R(g,4,6,4,3,"#8fd8ff");
    R(g,3,10,6,2,"#3d5a80"); R(g,2,12,8,2,"#5a3520");
    return g.canvas;
  }

  /* ===== HỒN MA (10×14, 2 frames) ===== */
  function ghost(fr) {
    var g = C(10, 14);
    R(g,2,0,6,3,"rgba(180,170,220,0.75)");
    R(g,1,2,8,5,"rgba(180,170,220,0.8)");
    R(g,2,7,6,3,"rgba(180,170,220,0.7)");
    P(g,3,4,"#ff3b3b"); P(g,6,4,"#ff3b3b"); // red eyes
    R(g,4,6,2,1,"#1a1a2e");                  // mouth
    var wy = fr===0 ? [1,0,1,0] : [0,1,0,1];
    for (var i=0;i<4;i++) R(g,1+i*2,10+wy[i],2,2,"rgba(180,170,220,0.6)");
    return g.canvas;
  }

  /* ===== BÁNH KEM (14×12, 2 frames) ===== */
  function cake(fr) {
    var g = C(14, 12);
    R(g,4,0,1,3,"#ffd93d"); R(g,6,0,1,3,"#ffd93d");
    R(g,8,0,1,3,"#ffd93d"); R(g,10,0,1,3,"#ffd93d");
    var fd=fr===0?0:1;
    P(g,4+fd,0,"#ff6b3d"); P(g,6+fd,0,"#ff6b3d");
    P(g,9,0,"#ff6b3d"); P(g,11,0,"#ff6b3d");
    R(g,2,3,10,2,"#fff"); R(g,1,4,12,1,"#ffc4e3");
    R(g,2,5,10,4,"#e8893a"); R(g,3,6,8,2,"#f5c49a");
    R(g,1,9,12,1,"#d4d4d4"); R(g,0,10,14,2,"#aaa");
    return g.canvas;
  }

  /* ===== HEART (6×6) ===== */
  function heart(fr) {
    var g = C(6, 6);
    R(g,0,0,3,2,"#ff3b5c"); R(g,3,0,3,2,"#ff3b5c");
    R(g,0,1,6,2,"#ff3b5c"); R(g,1,3,4,1,"#ff3b5c"); R(g,2,4,2,1,"#ff3b5c");
    return g.canvas;
  }

  /* ===== MŨI TÊN (10×6) ===== */
  function arrow() {
    var g = C(10, 6);
    R(g,3,0,4,1,"#ffd93d"); R(g,2,1,6,1,"#ffd93d");
    R(g,1,2,8,2,"#ffd93d"); R(g,3,4,4,1,"#ffd93d");
    return g.canvas;
  }

  /* ===== MINI SPRITES ===== */
  function bush() { var g=C(10,6); R(g,1,0,8,2,"#3cc060"); R(g,0,2,10,2,"#2eaa4f"); R(g,1,4,8,2,"#1e7a35"); return g.canvas; }
  function tree() { var g=C(14,26); R(g,5,14,4,12,"#6b4226"); R(g,1,0,12,5,"#3cc060"); R(g,0,4,14,5,"#2eaa4f"); R(g,2,8,10,3,"#1e7a35"); return g.canvas; }
  function flower() { var g=C(4,5); P(g,1,0,"#ff6fb5"); P(g,2,0,"#ff6fb5"); P(g,0,1,"#ff6fb5"); P(g,3,1,"#ff6fb5"); P(g,1,2,"#ffd93d"); P(g,2,2,"#ffd93d"); R(g,1,3,2,2,"#2eaa4f"); return g.canvas; }
  function blood() { var g=C(14,5); R(g,1,0,12,1,"#cc2233"); R(g,0,1,14,2,"#aa1122"); R(g,2,3,10,1,"#881122"); return g.canvas; }

  /* ===== CỬA (8×14) ===== */
  function door(open) {
    var g = C(8, 14);
    R(g,0,0,8,14, open?"#2b2b2b":"#8a6a45");
    if (!open) { R(g,1,1,6,13,"#a07848"); R(g,2,2,4,4,"#c9d8ff"); R(g,2,7,4,6,"#a07848"); P(g,6,9,"#ffd93d"); }
    return g.canvas;
  }

  /* ===== BACKGROUNDS (480×270) ===== */
  function bgTitle() {
    var g=C(480,270);
    var gr=g.createLinearGradient(0,0,0,270);
    gr.addColorStop(0,"#4a9fff"); gr.addColorStop(0.5,"#7ec8ff"); gr.addColorStop(0.85,"#bfe6ff"); gr.addColorStop(1,"#e8f7ff");
    g.fillStyle=gr; g.fillRect(0,0,480,270);
    g.fillStyle="#ffe066"; g.beginPath(); g.arc(390,48,24,0,Math.PI*2); g.fill();
    g.fillStyle="#fff5cc"; g.beginPath(); g.arc(390,48,16,0,Math.PI*2); g.fill();
    cloud(g,60,50,1); cloud(g,200,30,0.8); cloud(g,350,70,1.1);
    R(g,0,200,480,70,"#6abe30"); R(g,0,210,480,60,"#58a828");
    for(var i=0;i<24;i++) R(g,i*20,202,10,2,"#7ed957");
    g.drawImage(tree(),20,174); g.drawImage(tree(),390,174);
    g.drawImage(bush(),100,204); g.drawImage(bush(),300,208);
    for(var f=0;f<8;f++) g.drawImage(flower(),60+f*42,212+(f%3)*8);
    return g.canvas;
  }
  function cloud(g,x,y,s) {
    g.fillStyle="#fff"; g.beginPath(); g.arc(x,y,14*s,0,Math.PI*2); g.fill();
    g.beginPath(); g.arc(x+14*s,y-4*s,10*s,0,Math.PI*2); g.fill();
    g.beginPath(); g.arc(x+26*s,y,12*s,0,Math.PI*2); g.fill();
    g.fillRect(x-4*s,y-2,34*s,8*s);
  }
  function bgGarden() {
    var g=C(480,270);
    var gr=g.createLinearGradient(0,0,0,270);
    gr.addColorStop(0,"#3a6fbf"); gr.addColorStop(0.35,"#e88a40"); gr.addColorStop(0.55,"#f5a855"); gr.addColorStop(0.7,"#c96d28"); gr.addColorStop(1,"#5a8a28");
    g.fillStyle=gr; g.fillRect(0,0,480,270);
    g.fillStyle="#ffe066"; g.beginPath(); g.arc(80,130,22,0,Math.PI*2); g.fill();
    cloud(g,50,40,1); cloud(g,160,60,0.8); cloud(g,300,45,1.1);
    R(g,0,190,480,80,"#6abe30"); for(var i=0;i<24;i++) R(g,i*20,192,10,2,"#7ed957");
    for(var fx=0;fx<480;fx+=28) { R(g,fx,176,4,14,"#a07848"); R(g,fx+4,180,24,3,"#a07848"); R(g,fx+4,186,24,3,"#a07848"); }
    R(g,320,110,160,80,"#c98a4b"); R(g,320,110,160,10,"#a06a35");
    g.fillStyle="#d4574e"; g.beginPath(); g.moveTo(310,114); g.lineTo(400,70); g.lineTo(490,114); g.fill();
    R(g,388,144,24,46,"#6b4226"); R(g,390,146,20,42,"#8a6a45"); P(g,407,170,"#ffd93d");
    R(g,340,130,28,22,"#c9d8ff"); R(g,341,131,12,10,"#7ec8ff"); R(g,354,131,12,10,"#7ec8ff");
    g.drawImage(bush(),260,196); g.drawImage(bush(),340,198);
    for(var f=0;f<6;f++) g.drawImage(flower(),180+f*30,214+(f%2)*8);
    g.drawImage(tree(),40,164);
    return g.canvas;
  }
  function bgKitchen() {
    var g=C(480,270);
    R(g,0,0,480,270,"#e0d4bc"); R(g,0,180,480,90,"#c4b494");
    for(var i=0;i<16;i++) R(g,i*30,182,28,86,i%2?"#b8a888":"#c4b494");
    R(g,0,176,480,4,"#a09070");
    R(g,360,100,120,80,"#7d6242"); R(g,362,102,56,36,"#5a3e28"); R(g,424,102,54,36,"#5a3e28"); R(g,362,144,116,32,"#5a3e28");
    R(g,380,70,50,30,"#4a4a5a"); R(g,384,74,18,12,"#1a1a2e"); R(g,408,74,18,12,"#1a1a2e");
    R(g,440,70,30,30,"#b8c4cc"); R(g,444,74,22,20,"#8aa0aa");
    g.fillStyle="rgba(10,10,20,0.8)"; g.fillRect(0,0,80,100);
    R(g,140,150,100,30,"#8a6a45"); R(g,142,152,96,6,"#a07848");
    g.drawImage(blood(),175,235);
    R(g,10,120,28,60,"#6b4226"); R(g,12,122,24,56,"#8a6a45");
    return g.canvas;
  }
  function bgLiving() {
    var g=C(480,270);
    R(g,0,0,480,270,"#e8d8b8"); R(g,0,190,480,80,"#c9b48a");
    for(var i=0;i<16;i++) R(g,i*30,192,28,76,i%2?"#b8a888":"#c9b48a");
    R(g,0,186,480,4,"#a09070");
    R(g,60,36,48,40,"#c9d8ff"); R(g,62,38,20,36,"#7ec8ff"); R(g,86,38,20,36,"#7ec8ff");
    R(g,56,32,6,48,"#d4574e"); R(g,108,32,6,48,"#d4574e");
    R(g,20,148,90,42,"#7a5c8a"); R(g,22,150,86,14,"#9b7bff"); R(g,20,148,90,4,"#5a4570");
    R(g,140,180,60,12,"#a07848");
    R(g,350,60,60,45,"#1a1a2e"); R(g,354,64,52,37,"#101018"); R(g,376,105,8,10,"#3a3a4a");
    R(g,10,100,28,80,"#6b4226"); R(g,12,102,24,76,"#8a6a45");
    R(g,438,100,32,80,"#6b4226"); R(g,440,102,28,76,"#8a6a45"); P(g,464,145,"#ffd93d");
    return g.canvas;
  }
  function bgHaunted() {
    var g=C(480,270);
    R(g,0,0,480,270,"#1e1523"); R(g,0,190,480,80,"#16101a");
    for(var i=0;i<16;i++) R(g,i*30,192,28,76,i%2?"#120d16":"#16101a");
    R(g,0,186,480,4,"#0a0810");
    R(g,60,36,48,40,"#0d0a12"); R(g,56,32,6,48,"#3a2040"); R(g,108,32,6,48,"#3a2040");
    R(g,20,148,90,42,"#3a2f45"); R(g,22,150,86,14,"#4a3f55");
    R(g,350,60,60,45,"#0a0810"); R(g,354,64,52,37,"#050408");
    R(g,10,100,28,80,"#3a2040"); R(g,12,102,24,76,"#2a1830");
    R(g,438,100,32,80,"#3a2040"); R(g,440,102,28,76,"#2a1830");
    R(g,210,10,50,30,"#3a2040"); R(g,212,12,46,26,"#2a1830");
    candle(g,180,170); candle(g,280,170);
    g.fillStyle="rgba(140,130,170,0.06)"; g.fillRect(0,50,480,30); g.fillRect(0,130,480,25);
    return g.canvas;
  }
  function candle(g,x,y) {
    R(g,x,y,6,10,"#8a6a45"); R(g,x+1,y-4,4,4,"#ffd93d");
    g.fillStyle="rgba(255,200,80,0.3)"; g.beginPath(); g.arc(x+3,y-6,10,0,Math.PI*2); g.fill();
  }
  function bgHallway() {
    var g=C(480,270);
    R(g,0,0,480,80,"#2a2036"); R(g,0,80,480,110,"#241d30"); R(g,0,190,480,80,"#2a2036");
    for(var i=0;i<16;i++) R(g,i*30,82,28,106,i%2?"#1e1726":"#241d30");
    R(g,0,78,480,2,"#0e0b14");
    R(g,0,100,18,60,"#3a2040"); R(g,450,100,30,60,"#3a2040");
    for(var c=0;c<5;c++) { var cx=80+c*80; candle(g,cx,70); g.fillStyle="rgba(255,200,80,0.15)"; g.beginPath(); g.arc(cx+3,68,30,0,Math.PI*2); g.fill(); }
    return g.canvas;
  }
  function bgDining() {
    var g=C(480,270);
    var gr=g.createLinearGradient(0,0,0,270);
    gr.addColorStop(0,"#3a2a1e"); gr.addColorStop(1,"#2a1d14");
    g.fillStyle=gr; g.fillRect(0,0,480,270);
    R(g,0,200,480,70,"#4a3524"); for(var i=0;i<16;i++) R(g,i*30,202,28,66,i%2?"#3e2d1c":"#4a3524");
    R(g,0,196,480,4,"#3a2818");
    candle(g,80,60); candle(g,200,60); candle(g,320,60); candle(g,400,60);
    R(g,130,130,220,50,"#7d5a38"); R(g,130,130,220,8,"#8f6a44");
    R(g,150,180,10,14,"#6b4226"); R(g,320,180,10,14,"#6b4226");
    R(g,130,178,220,2,"#ffc4e3");
    R(g,180,30,120,80,"#1a1218"); R(g,184,34,112,72,"#2a1a12");
    return g.canvas;
  }

  var BG={};
  function getBG(n) {
    if (!BG[n]) {
      switch(n) {
        case "title":BG[n]=bgTitle();break;
        case "garden":BG[n]=bgGarden();break;
        case "kitchen":BG[n]=bgKitchen();break;
        case "living":BG[n]=bgLiving();break;
        case "haunted":BG[n]=bgHaunted();break;
        case "hallway":BG[n]=bgHallway();break;
        case "dining":BG[n]=bgDining();break;
      }
    }
    return BG[n];
  }

  root.Sprites = {
    cat: cat, butterfly: butterfly, owner: owner, ownerSit: ownerSit,
    ghost: ghost, cake: cake, heart: heart, arrow: arrow,
    door: door, bush: bush, tree: tree, flower: flower, blood: blood,
    getBG: getBG
  };
})(typeof window !== "undefined" ? window : this);
