/* audio.js — WebAudio SFX tự sinh (không cần file) — meow/scare/chime
 * Browser only. Autoplay policy: khởi tạo sau gesture đầu tiên.
 * WebAudio không khả dụng → mute hoàn toàn, game vẫn chơi (C2-22).
 */
(function (root) {
  "use strict";

  var AudioFX = function () {
    var ctx = null;
    var enabled = false;
    var master = null;

    function init() {
      if (ctx) {
        if (ctx.state === "suspended") ctx.resume();
        return;
      }
      try {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) { enabled = false; return; }
        ctx = new AC();
        master = ctx.createGain();
        master.gain.value = 0.35;
        master.connect(ctx.destination);
        enabled = true;
        if (ctx.state === "suspended") ctx.resume();
      } catch (e) {
        enabled = false;
      }
    }

    function tone(freq, start, dur, type, vol, glideTo) {
      if (!enabled || !ctx) return;
      var t0 = ctx.currentTime + (start || 0);
      var osc = ctx.createOscillator();
      var g = ctx.createGain();
      osc.type = type || "sine";
      osc.frequency.setValueAtTime(freq, t0);
      if (glideTo) osc.frequency.exponentialRampToValueAtTime(glideTo, t0 + dur);
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(vol || 0.2, t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      osc.connect(g);
      g.connect(master);
      osc.start(t0);
      osc.stop(t0 + dur + 0.05);
    }

    function noise(start, dur, vol) {
      if (!enabled || !ctx) return;
      var t0 = ctx.currentTime + (start || 0);
      var len = Math.floor(ctx.sampleRate * dur);
      var buf = ctx.createBuffer(1, len, ctx.sampleRate);
      var data = buf.getChannelData(0);
      for (var i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / len);
      var src = ctx.createBufferSource();
      src.buffer = buf;
      var g = ctx.createGain();
      g.gain.value = vol || 0.3;
      var filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = 900;
      src.connect(filter);
      filter.connect(g);
      g.connect(master);
      src.start(t0);
    }

    return {
      init: init,
      isEnabled: function () { return enabled; },
      // Meo meo: 2 tone trượt lên
      meow: function () {
        tone(520, 0, 0.16, "sine", 0.25, 780);
        tone(620, 0.18, 0.22, "sine", 0.2, 940);
      },
      // Scare: noise + boom trầm
      scare: function () {
        noise(0, 0.5, 0.5);
        tone(160, 0, 0.6, "sawtooth", 0.3, 50);
        tone(90, 0.1, 0.7, "sine", 0.4, 40);
      },
      // Chime: 3 nốt vui
      chime: function () {
        tone(880, 0, 0.25, "triangle", 0.25);
        tone(1108, 0.12, 0.25, "triangle", 0.25);
        tone(1318, 0.24, 0.45, "triangle", 0.3);
      },
      // Gọi mèo (thì thầm) — 2 tone trầm ngắn
      whisper: function () {
        tone(220, 0, 0.3, "sine", 0.12, 180);
        tone(200, 0.4, 0.4, "sine", 0.1, 160);
      }
    };
  };

  root.AudioFX = AudioFX;
})(typeof window !== "undefined" ? window : this);
