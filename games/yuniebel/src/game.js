/* game.js — Game loop + render + input + UI (browser only)
 * Sprites mới: canvas primitives, backgrounds pre-rendered.
 */
(function () {
  "use strict";
  var core = window.AiosCore;
  var S = window.Sprites;
  var audio = window.AudioFX();
  var CW = 480, CH = 270;
  var canvas = document.getElementById("game");
  var ctx = canvas.getContext("2d");
  canvas.width = CW; canvas.height = CH;

  function resize() {
    var w = window.innerWidth, h = window.innerHeight;
    var s = Math.min(w / CW, h / CH);
    canvas.style.width = Math.floor(CW * s) + "px";
    canvas.style.height = Math.floor(CH * s) + "px";
  }
  window.addEventListener("resize", resize); resize();

  var lightC = document.createElement("canvas");
  lightC.width = CW; lightC.height = CH;
  var lightX = lightC.getContext("2d");

  var state = core.resetGame();
  var lastScene = state.scene;
  var fadeT = 0, time = 0;

  // ===== INPUT =====
  var keys = {}, dpad = { up:false, down:false, left:false, right:false };
  var isTouch = ("ontouchstart" in window) || navigator.maxTouchPoints > 0;
  var oneShot = { start:false, choice1:0, choice2:0 };

  function kN(e) { return e.key.toLowerCase(); }
  window.addEventListener("keydown", function (e) {
    var k = kN(e);
    if (["w","a","s","d","arrowup","arrowdown","arrowleft","arrowright"," "].indexOf(k)!==-1) e.preventDefault();
    if (e.repeat) return;
    keys[k] = true;
    if (k==="1"||k==="2") { if (state.phase==="K_CHOICE") { oneShot["choice"+k]=parseInt(k); audio.init(); } }
    if (k==="enter"||k===" ") { if (state.scene==="TITLE"||state.scene==="GAMEOVER"||state.scene==="END") { oneShot.start=true; audio.init(); } }
  });
  window.addEventListener("keyup", function (e) { keys[kN(e)]=false; });
  window.addEventListener("blur", clearKeys);
  document.addEventListener("visibilitychange", function () { if (document.hidden) clearKeys(); else audio.init(); });
  function clearKeys() { for (var k in keys) keys[k]=false; }

  // ===== D-PAD (mobile) =====
  function bPad(id, dir) {
    var el = document.getElementById(id); if (!el) return;
    el.addEventListener("touchstart", function(e){e.preventDefault();dpad[dir]=true;audio.init();});
    el.addEventListener("touchend", function(e){e.preventDefault();dpad[dir]=false;});
    el.addEventListener("touchcancel", function(){dpad[dir]=false;});
  }
  bPad("pad-up","up"); bPad("pad-down","down"); bPad("pad-left","left"); bPad("pad-right","right");
  if (isTouch) { document.getElementById("dpad").classList.remove("hidden"); document.getElementById("hint").classList.add("hidden"); }

  // ===== UI =====
  var uiTask=document.getElementById("task-box"), taskText=document.getElementById("task-text");
  var uiBtn=document.getElementById("ui-toggle"), diagEl=document.getElementById("dialogue");
  var choiceEl=document.getElementById("choice-box"), choice1=document.getElementById("choice-1"), choice2=document.getElementById("choice-2");
  var scareC=document.getElementById("scare-counter");
  var titleEl=document.getElementById("title-screen"), overEl=document.getElementById("gameover-screen"), endEl=document.getElementById("end-screen");
  var hintEl=document.getElementById("hint");
  var uiHidden = false;

  uiBtn.addEventListener("click", function(){uiHidden=!uiHidden;uiTask.classList.toggle("hidden",uiHidden);hintEl.classList.toggle("hidden",uiHidden);});
  document.getElementById("task-close").addEventListener("click", function(){state=core.resetGame();lastScene="TITLE";fadeT=0;syncUI();});
  document.getElementById("btn-start").addEventListener("click",function(){oneShot.start=true;audio.init();});
  document.getElementById("btn-replay-1").addEventListener("click",function(){oneShot.start=true;audio.init();});
  document.getElementById("btn-replay-2").addEventListener("click",function(){oneShot.start=true;audio.init();});
  choice1.addEventListener("click",function(){oneShot.choice1=1;audio.init();});
  choice2.addEventListener("click",function(){oneShot.choice2=2;audio.init();});

  function syncUI() {
    var inTitle=state.scene==="TITLE", inOver=state.scene==="GAMEOVER", inEnd=state.scene==="END";
    titleEl.classList.toggle("hidden",!inTitle); overEl.classList.toggle("hidden",!inOver); endEl.classList.toggle("hidden",!inEnd);
    uiTask.classList.toggle("hidden",uiHidden||inTitle||inOver||inEnd);
    if (!inTitle&&!inOver&&!inEnd) { var info=core.PHASES[state.phase]; taskText.textContent=info?info.task:""; }
  }

  var lastFlashT=-1, chimeSeen=false;

  // ===== CAMERA =====
  function camX() { var sc=core.SCENES[state.scene]; if (!sc||sc.w<=CW) return 0; return Math.max(0,Math.min(state.player.x-CW/2+8,sc.w-CW)); }

  // ===== DRAW HELPERS =====
  function drawPlayer(cx) {
    var p=state.player, fr=0;
    if (p.moving) fr=(Math.floor(time*8)%2)+1;
    var cv=S.cat(fr, p.dir);
    ctx.drawImage(cv, Math.round(p.x-cx), Math.round(p.y), cv.width*3, cv.height*3);
  }
  function drawSprite(cv, x, y, scale) { scale=scale||3; ctx.drawImage(cv, Math.round(x), Math.round(y), cv.width*scale, cv.height*scale); }

  // ===== SCENE RENDERERS =====
  function renderTitle() {
    ctx.drawImage(S.getBG("title"), 0, 0);
    drawSprite(S.cat(0,1), CW/2-21, CH-80);
  }

  function renderGarden(cx) {
    ctx.drawImage(S.getBG("garden"), -cx, 0);
    var doorOpen = state.phase==="G_DARK"||state.phase==="G_DOOR";
    drawSprite(S.door(doorOpen), 388-cx, 144);
    drawSprite(S.owner(0), 392-cx, 126);
    if (state.butterfly&&state.butterfly.alive) drawSprite(S.butterfly(Math.floor(time*8)%2), state.butterfly.x*1.5-cx, state.butterfly.y*1.5);
    drawPlayer(cx);
  }

  function renderLiving(cx, haunted) {
    ctx.drawImage(S.getBG(haunted?"haunted":"living"), 0, 0);
    drawSprite(S.door(false), 10, 100); // kitchen door
    if (!haunted) {
      drawSprite(S.arrow(), 26, 90);
      drawSprite(S.door(false), 438, 100);
    } else {
      drawSprite(S.door(false), 438, 100);
      drawSprite(S.ghost(Math.floor(time*4)%2), 420, 106);
      drawSprite(S.door(false), 210, 10);
      drawSprite(S.arrow(), 225, 12);
      ctx.fillStyle="#ffd93d"; ctx.font="8px monospace"; ctx.fillText("DI TIẾP",216,24);
    }
    drawPlayer(cx);
  }

  function renderKitchen() {
    ctx.drawImage(S.getBG("kitchen"), 0, 0);
    drawSprite(S.blood(), 175, 235);
    drawSprite(S.door(false), 10, 120);
    if (state.phase==="K_VOICE"||state.phase==="K_CHOICE"||state.phase==="K_OBEY") {
      if (Math.floor(time*2)%2===0) { ctx.fillStyle="#ff3b3b"; ctx.fillRect(58,62,5,4); ctx.fillRect(76,62,5,4); }
    }
    drawPlayer(0);
  }

  function renderHallway() {
    ctx.drawImage(S.getBG("hallway"), 0, 0);
    drawSprite(S.door(true), 0, 100);
    if (state.phase==="W_DONE") { ctx.fillStyle="#0a0a12"; ctx.fillRect(450,100,30,60); drawSprite(S.arrow(), 454,90); }
    else drawSprite(S.door(false), 450, 100);
    if (state.scareCount<5) {
      var gx=80+state.scareCount*80-((time*40)%80);
      drawSprite(S.ghost(Math.floor(time*4)%2), gx, 56);
    }
    drawPlayer(0);
  }

  function renderDining() {
    ctx.drawImage(S.getBG("dining"), 0, 0);
    drawSprite(S.ownerSit(), 220, 106);
    if (state.phase==="D_CAKE"||state.phase==="END") drawSprite(S.cake(Math.floor(time*3)%2), 222, 124);
    if (state.phase==="D_HUG"||state.phase==="D_CAKE") {
      drawSprite(S.heart(Math.floor(time*5)%2), 150+Math.sin(time*5)*12, 60);
      drawSprite(S.heart(Math.floor(time*5+1)%2), 270+Math.sin(time*5)*12, 56);
    }
    drawPlayer(0);
  }

  function renderEnd() {
    var gr=ctx.createLinearGradient(0,0,0,CH);
    gr.addColorStop(0,"#ffd9e8"); gr.addColorStop(1,"#ffb3d1");
    ctx.fillStyle=gr; ctx.fillRect(0,0,CW,CH);
    drawSprite(S.cake(Math.floor(time*3)%2), CW/2-21, 80);
    drawSprite(S.cat(0,1), CW/2-21, 120);
    drawSprite(S.heart(Math.floor(time*5)%2), CW/2-60, 50);
    drawSprite(S.heart(Math.floor(time*5+1)%2), CW/2+48, 46);
  }

  // ===== DARKNESS / LIGHT =====
  function drawDark() {
    var a=0;
    if (state.scene==="HAUNTED") a=0.82;
    else if (state.scene==="HALLWAY") a=0.78;
    else if (state.scene==="KITCHEN"&&state.phase==="K_OBEY") a=state.darkness*0.95;
    else if (state.scene==="GARDEN"&&(state.phase==="G_DARK"||state.phase==="G_DOOR")) a=state.darkness*0.4;
    if (a<=0) return;
    lightX.clearRect(0,0,CW,CH);
    lightX.fillStyle="rgba(0,0,10,"+a+")"; lightX.fillRect(0,0,CW,CH);
    var lx=state.player.x-camX(), ly=state.player.y+8;
    var rg=lightX.createRadialGradient(lx,ly,10,lx,ly,92);
    rg.addColorStop(0,"rgba(0,0,0,1)"); rg.addColorStop(0.7,"rgba(0,0,0,0.6)"); rg.addColorStop(1,"rgba(0,0,0,0)");
    lightX.globalCompositeOperation="destination-out";
    lightX.fillStyle=rg; lightX.fillRect(lx-92,ly-92,184,184);
    lightX.globalCompositeOperation="source-over";
    ctx.drawImage(lightC,0,0);
  }

  function drawFade() {
    if (fadeT>0) { var a=Math.min(1,fadeT/0.5)*0.85; ctx.fillStyle="rgba(5,5,15,"+a+")"; ctx.fillRect(0,0,CW,CH); }
  }

  function drawScare() {
    var f=state.scareFlash; if (!f) return;
    var rem=f.until-state.time; if (rem<=0) return;
    var a=Math.min(0.9,rem*2.2);
    ctx.fillStyle="rgba(255,60,60,"+a*0.6+")"; ctx.fillRect(0,0,CW,CH);
    drawSprite(S.ghost(Math.floor(state.time*6)%2), CW/2-15, CH/2-21);
    ctx.fillStyle="#fff"; ctx.font="bold 12px monospace"; ctx.fillText("!",CW/2+18,CH/2-16);
  }

  // ===== MAIN LOOP =====
  var last=0;
  function loop(t) {
    var dt=Math.min((t-last)/1000,0.05); last=t; time+=dt;
    var input={
      up:keys.w||keys.arrowup||dpad.up, down:keys.s||keys.arrowdown||dpad.down,
      left:keys.a||keys.arrowleft||dpad.left, right:keys.d||keys.arrowright||dpad.right,
      start:oneShot.start, choice1:oneShot.choice1, choice2:oneShot.choice2
    };
    core.updateGame(state,dt,input);
    oneShot.start=false; oneShot.choice1=0; oneShot.choice2=0;
    if (state.scene!==lastScene) { lastScene=state.scene; fadeT=0.5; audio.init(); }
    if (fadeT>0) fadeT-=dt;

    ctx.imageSmoothingEnabled=false;
    ctx.save();
    var cx=camX(), sc=state.scene;
    if (sc==="TITLE") renderTitle();
    else if (sc==="GARDEN") renderGarden(cx);
    else if (sc==="LIVING") renderLiving(cx,false);
    else if (sc==="KITCHEN") renderKitchen();
    else if (sc==="HAUNTED") renderLiving(cx,true);
    else if (sc==="HALLWAY") renderHallway();
    else if (sc==="DINING") renderDining();
    else if (sc==="GAMEOVER") { ctx.fillStyle="#0a0508"; ctx.fillRect(0,0,CW,CH); }
    else if (sc==="END") renderEnd();
    drawDark(); drawScare(); drawFade();
    ctx.restore();

    // UI updates
    syncUI();
    if (state.message&&state.message.text) { diagEl.textContent=state.message.text; diagEl.classList.remove("hidden"); }
    else diagEl.classList.add("hidden");
    if (state.phase==="K_CHOICE") choiceEl.classList.remove("hidden"); else choiceEl.classList.add("hidden");
    if (state.scene==="HALLWAY") { scareC.textContent="Bị hù: "+state.scareCount+"/5"; scareC.classList.remove("hidden"); }
    else scareC.classList.add("hidden");
    if (state.scareFlash&&state.scareFlash.until!==lastFlashT) { lastFlashT=state.scareFlash.until; audio.scare(); }
    if (state.chimeFlag&&!chimeSeen) { chimeSeen=true; audio.chime(); }
    if (!state.chimeFlag) chimeSeen=false;

    window.requestAnimationFrame(loop);
  }

  syncUI();
  window.requestAnimationFrame(function(t){last=t;window.requestAnimationFrame(loop);});
  window.__yuniebel={getState:function(){return state;},core:core};
})();
