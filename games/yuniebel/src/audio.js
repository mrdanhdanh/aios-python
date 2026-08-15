/* audio.js — Yuniebel's Cat (TASK-078) — WebAudio synth, 0 dependency
 * Sequencer nhạc nền theo AUDIO CLOCK (ctx.currentTime lookahead — C1-16).
 * 10 mood (§6.3) + 21 SFX (AC-4). getStats() đếm TẦNG REQUEST (R2) — counter tăng
 * ngay đầu hàm trước mọi check ctx/mute → headless vẫn đếm được.
 */
(function (root) {
  "use strict";

  var SFX_NAMES = [
    "ting", "flutter", "meow", "happyMeow", "scaredMeow", "painMeow",
    "footstepGrass", "footstepEcho", "wind", "bird", "clockTick", "drip",
    "whisper", "whisperFar", "rush", "swoosh", "whoosh", "creak",
    "jumpscare", "candle", "bell", "sparkle", "uiClick", "intro", "darkStart", "warm", "gameOver"
  ];

  function AudioFX() {
    var ctx = null;
    var master = null;
    var musicGain = null;
    var sfxGain = null;
    var muted = false;
    var mood = "calm-happy";
    var stats = {};
    var schedulerTimer = null;
    var nextNoteTime = 0;
    var noteIndex = 0;
    var started = false;

    for (var i = 0; i < SFX_NAMES.length; i++) stats[SFX_NAMES[i]] = 0;

    function ensureCtx() {
      if (ctx) return true;
      try {
        var AC = root.AudioContext || root.webkitAudioContext;
        if (!AC) return false;
        ctx = new AC();
        master = ctx.createGain();
        master.gain.value = muted ? 0 : 0.5;
        master.connect(ctx.destination);
        musicGain = ctx.createGain();
        musicGain.gain.value = 0.32;
        musicGain.connect(master);
        sfxGain = ctx.createGain();
        sfxGain.gain.value = 0.55;
        sfxGain.connect(master);
      } catch (e) { return false; } // R11: jsdom/không WebAudio → mute hoàn toàn
      return true;
    }

    function resume() { // C2-15: gesture đầu
      if (ctx && ctx.state === "suspended") { try { ctx.resume(); } catch (e) {} }
    }

    function resetStats() { // C2-16: reset theo màn chơi hiện tại
      for (var k in stats) stats[k] = 0;
    }

    // ===== SFX — counter tăng TRƯỚC mọi check (R2) =====
    function sfx(name) { stats[name] = (stats[name] || 0) + 1; }

    function tone(freq, dur, type, vol, when, dest) {
      if (!ctx) return;
      var t = when || ctx.currentTime;
      var o = ctx.createOscillator();
      var g = ctx.createGain();
      o.type = type || "square";
      o.frequency.value = freq;
      g.gain.setValueAtTime(vol || 0.15, t);
      g.gain.exponentialRampToValueAtTime(0.001, t + (dur || 0.15));
      o.connect(g); g.connect(dest || sfxGain);
      o.start(t); o.stop(t + (dur || 0.15) + 0.02);
    }

    function noise(dur, vol, when, dest, fType) {
      if (!ctx) return;
      var t = when || ctx.currentTime;
      var len = Math.max(1, Math.floor(ctx.sampleRate * (dur || 0.2)));
      var buf = ctx.createBuffer(1, len, ctx.sampleRate);
      var d = buf.getChannelData(0);
      for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      var src = ctx.createBufferSource();
      src.buffer = buf;
      var g = ctx.createGain();
      g.gain.setValueAtTime(vol || 0.2, t);
      g.gain.exponentialRampToValueAtTime(0.001, t + (dur || 0.2));
      var f = ctx.createBiquadFilter();
      f.type = fType || "lowpass";
      f.frequency.value = 800;
      src.connect(f); f.connect(g); g.connect(dest || sfxGain);
      src.start(t); src.stop(t + (dur || 0.2) + 0.02);
    }

    function meow(kind) {
      if (!ctx) return;
      var base = kind === "pain" ? 500 : kind === "happy" ? 700 : 620;
      var t = ctx.currentTime;
      for (var i = 0; i < 3; i++) {
        var f0 = base * (1 + i * 0.08);
        tone(f0, 0.09, "sine", 0.18, t + i * 0.07);
        tone(f0 * 1.5, 0.09, "sine", 0.1, t + i * 0.07);
      }
      if (kind === "pain") noise(0.4, 0.12, t);
    }

    // ===== SFX API =====
    var api = {
      init: function () {
        if (!ensureCtx()) return;
        resume();
        // R-03: khởi động sequencer sau gesture đầu nếu chưa chạy
        if (!started) { started = true; this._startMusic(); }
      },
      setMuted: function (m) { muted = m; if (master) master.gain.value = m ? 0 : 0.5; },
      isMuted: function () { return muted; },
      getMood: function () { return mood; },
      getStats: function () { return JSON.parse(JSON.stringify(stats)); },
      resetStats: resetStats,
      sfxCount: function (name) { return stats[name] || 0; },

      // ===== 21+ SFX =====
      ting: function () { sfx("ting"); if (ctx) tone(1318, 0.12, "sine", 0.12); },
      flutter: function () { sfx("flutter"); if (ctx) noise(0.08, 0.05, null, null, "highpass"); },
      meow: function () { sfx("meow"); meow("normal"); },
      happyMeow: function () { sfx("happyMeow"); meow("happy"); },
      scaredMeow: function () { sfx("scaredMeow"); meow("scared"); tone(880, 0.1, "sawtooth", 0.1); },
      painMeow: function () { sfx("painMeow"); meow("pain"); },
      footstepGrass: function () { sfx("footstepGrass"); if (ctx) noise(0.05, 0.05, null, null, "highpass"); },
      footstepEcho: function () { sfx("footstepEcho"); if (ctx) { noise(0.08, 0.06, null, null, "highpass"); noise(0.12, 0.04, ctx.currentTime + 0.09, null, "highpass"); } },
      wind: function () { sfx("wind"); if (ctx) noise(1.2, 0.05, null, null, "bandpass"); },
      bird: function () { sfx("bird"); if (ctx) { tone(2200, 0.06, "sine", 0.06); tone(2600, 0.05, "sine", 0.05, ctx.currentTime + 0.1); } },
      clockTick: function () { sfx("clockTick"); if (ctx) tone(1200, 0.03, "square", 0.06); },
      drip: function () { sfx("drip"); if (ctx) { tone(300, 0.06, "sine", 0.1); tone(180, 0.1, "sine", 0.08, ctx.currentTime + 0.05); } },
      whisper: function () { sfx("whisper"); if (ctx) noise(0.8, 0.1, null, null, "bandpass"); },
      whisperFar: function () { sfx("whisperFar"); if (ctx) { noise(1.0, 0.06, null, null, "bandpass"); noise(1.2, 0.04, ctx.currentTime + 0.3, null, "bandpass"); } },
      rush: function () { sfx("rush"); if (ctx) { noise(0.8, 0.12, null, null, "highpass"); noise(0.8, 0.1, ctx.currentTime + 0.15, null, "highpass"); } },
      swoosh: function () { sfx("swoosh"); if (ctx) { var t = ctx.currentTime; noise(0.5, 0.2, t, null, "bandpass"); tone(200, 0.4, "sine", 0.15, t); } },
      whoosh: function () { sfx("whoosh"); if (ctx) { var t = ctx.currentTime; noise(0.6, 0.22, t, null, "bandpass"); tone(120, 0.5, "sawtooth", 0.08, t); } },
      creak: function () { sfx("creak"); if (ctx) { var t = ctx.currentTime; for (var i = 0; i < 4; i++) tone(140 + i * 30, 0.15, "sawtooth", 0.05, t + i * 0.14); } },
      jumpscare: function () { sfx("jumpscare"); if (ctx) { var t = ctx.currentTime; noise(0.5, 0.3, t); tone(70, 0.5, "sawtooth", 0.25, t); tone(1800, 0.25, "square", 0.1, t + 0.05); noise(0.3, 0.25, t + 0.1, null, "highpass"); } },
      candle: function () { sfx("candle"); if (ctx) noise(0.5, 0.03, null, null, "bandpass"); },
      bell: function () { sfx("bell"); if (ctx) { var t = ctx.currentTime; tone(2093, 0.4, "sine", 0.1, t); tone(2637, 0.4, "sine", 0.07, t + 0.02); tone(3136, 0.5, "sine", 0.05, t + 0.05); } },
      sparkle: function () { sfx("sparkle"); if (ctx) { var t = ctx.currentTime; for (var i = 0; i < 5; i++) tone(1500 + i * 300, 0.08, "sine", 0.06, t + i * 0.06); } },
      uiClick: function () { sfx("uiClick"); if (ctx) tone(700, 0.05, "square", 0.06); },

      // ===== Music: mood sequencer (audio clock lookahead) =====
      setMood: function (m) {
        if (m === mood) return;
        mood = m;
        if (ctx) { musicGain.gain.cancelScheduledValues(ctx.currentTime); musicGain.gain.setValueAtTime(musicGain.gain.value, ctx.currentTime); musicGain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.6); }
        var self = this;
        setTimeout(function () { self._startMusic(); }, 620);
      },

      _startMusic: function () {
        if (!ctx || muted) return;
        musicGain.gain.cancelScheduledValues(ctx.currentTime);
        musicGain.gain.setValueAtTime(0.001, ctx.currentTime);
        musicGain.gain.linearRampToValueAtTime(0.32, ctx.currentTime + 0.8);
        nextNoteTime = ctx.currentTime + 0.1;
        noteIndex = 0;
        if (schedulerTimer) clearInterval(schedulerTimer);
        var self = this;
        schedulerTimer = setInterval(function () { self._scheduler(); }, 25);
      },

      _scheduler: function () {
        if (!ctx || !musicGain || muted) return;
        var self = this;
        while (nextNoteTime < ctx.currentTime + 0.12) {
          self._scheduleNote(nextNoteTime);
          nextNoteTime += self._noteDur();
          noteIndex++;
        }
      },

      _noteDur: function () {
        switch (mood) {
          case "calm-happy": case "garden-calm": case "celebration": return 0.25;
          case "dusk-sad": return 0.5;
          case "mystery": case "kitchen-mystery": case "tense": return 0.35;
          case "suspense": return 0.2;
          case "warm": return 0.45;
          default: return 0.3;
        }
      },

      _scheduleNote: function (t) {
        var self = this;
        // scales per mood (§6.3)
        var seqs = {
          "calm-happy": [523, 659, 784, 659, 523, 587, 698, 587],
          "garden-calm": [392, 523, 659, 523, 440, 587, 784, 587],
          "dusk-sad": [392, 370, 349, 370, 392, 349, 311, 349],
          "mystery": [311, 370, 311, 370, 311, 370, 415, 370],
          "kitchen-mystery": [220, 220, 233, 220, 220, 233, 262, 233],
          "tense": [196, 208, 196, 208, 185, 196, 185, 208],
          "suspense": [233, 233, 233, 262, 233, 233, 220, 233],
          "warm": [523, 587, 659, 587, 523, 587, 659, 784],
          "celebration": [523, 659, 784, 1047, 784, 659, 784, 523],
          "gameOver": [392, 370, 349, 311]
        };
        var seq = seqs[mood] || seqs["calm-happy"];
        var f = seq[noteIndex % seq.length];
        // bass drone cho mood tối
        if (mood === "tense" || mood === "suspense" || mood === "kitchen-mystery") {
          tone(f / 2, this._noteDur() * 2, "triangle", 0.06, t, musicGain);
        }
        tone(f, this._noteDur() * 0.9, "triangle", 0.12, t, musicGain);
        // sparkle arp cho celebration
        if (mood === "celebration") {
          tone(f * 2, 0.15, "sine", 0.05, t, musicGain);
        }
      },

      stopMusic: function () { if (schedulerTimer) { clearInterval(schedulerTimer); schedulerTimer = null; } if (musicGain && ctx) musicGain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.3); }
    };
    return api;
  }

  root.AudioFX = AudioFX;
})(typeof self !== "undefined" ? self : this);
