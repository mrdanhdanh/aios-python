# Critique v├▓ng 1 ΓÇö TASK-077 (bß╗ƒi critic agent, 2026-08-15)

## ─É├ính gi├í chung
Spec r├╡ vß╗ü c├óu chuyß╗çn, cß║Ñu tr├║c file, r├áng buß╗Öc kß╗╣ thuß║¡t v├á c├│ 15 AC. NH╞»NG ch╞░a ─æß╗º ─æß╗â implement an to├án: (1) state machine chß╗ë liß╗çt k├¬ state cß║Ñp cß║únh, thiß║┐u sub-state/phase trong tß╗½ng cß║únh ΓÇö nguß╗ôn ch├¡nh cß╗ºa "kß║╣t trigger"; (2) kh├┤ng quy ─æß╗ïnh ─æ╞░ß╗¥ng dß║½n t├ái nguy├¬n ΓåÆ rß╗ºi ro vß╗í asset khi deploy sub-path (AC1 file:// vs URL `/aios-python/games/yuniebel/`); (3) AC visual (AC2ΓÇôAC12) kh├┤ng c├│ ph╞░╞íng thß╗⌐c kiß╗âm chß╗⌐ng; (4) nhiß╗üu case bi├¬n ch╞░a ─æ╞░ß╗úc quyß║┐t ─æß╗ïnh (bß║Ñm X giß╗»a chß╗½ng, spam ph├¡m, m├¿o kß║╣t trigger, ─æß╗òi ├╜ sau chß╗ìn).
**Mß╗⌐c sß║╡n s├áng: 3/5 ΓÇö cß║ºn sß╗¡a tr╞░ß╗¢c khi implement.**

## Phß║ún biß╗çn

### P1 ΓÇö Bß║»t buß╗Öc sß╗¡a

**C1-01 ΓÇö ─É╞░ß╗¥ng dß║½n t├ái nguy├¬n: AC1 (file://) xung ─æß╗Öt tiß╗üm ß║⌐n vß╗¢i deploy sub-path (P1)**
- Vß║Ñn ─æß╗ü: Game deploy tß║íi sub-path `/aios-python/games/yuniebel/`, c├▓n AC1 y├¬u cß║ºu mß╗ƒ bß║▒ng file:// vß║½n ch╞íi ─æ╞░ß╗úc. Hai m├┤i tr╞░ß╗¥ng chß╗ë c├╣ng hoß║ít ─æß╗Öng nß║┐u Mß╗îI ─æ╞░ß╗¥ng dß║½n l├á relative v├á d├╣ng script tag **classic** (`<script type="module">` bß╗ï CORS chß║╖n tr├¬n file://).
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ spec bß╗ò sung r├áng buß╗Öc: script classic + relative path + cß║Ñm absolute/fetch/module. test.md th├¬m b╞░ß╗¢c kiß╗âm tra Network chß╗ë c├│ request local.

**C1-02 ΓÇö State machine thiß║┐u sub-state trong cß║únh (P1)**
- Vß║Ñn ─æß╗ü: Chuß╗ùi `TITLE ΓåÆ GARDEN ΓåÆ ...` chß╗ë l├á state cß║Ñp cß║únh; c├íc chuß╗ùi b├¬n trong cß║únh (b╞░ß╗¢m, m├íu, cutscene) cß║ºn sub-state k├¿m ─æiß╗üu kiß╗çn chuyß╗ân.
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ spec bß╗ò sung bß║úng phase ─æß║ºy ─æß╗º: `GARDEN: G_INIT ΓåÆ G_BUTTERFLY ΓåÆ G_CHASE ΓåÆ G_DARK ΓåÆ G_DOOR`; `KITCHEN: K_BLOOD ΓåÆ K_VOICE ΓåÆ K_CHOICE ΓåÆ (K_RUN ΓåÆ HAUNTED | K_OBEY ΓåÆ GAMEOVER)`; `DINING: D_APPROACH ΓåÆ D_JUMP ΓåÆ D_HUG ΓåÆ D_CAKE ΓåÆ D_END`; mß╗ùi transition ghi ─æiß╗üu kiß╗çn.

**C1-03 ΓÇö Cß╗¡a cß║únh 1 phß║úi kh├│a tß╗¢i khi chß║ím b╞░ß╗¢m (P1)**
- Vß║Ñn ─æß╗ü: Nß║┐u cß╗¡a vß║½n mß╗ƒ, ng╞░ß╗¥i ch╞íi ─æi thß║│ng v├áo cß╗¡a ΓåÆ bß╗Å lß╗í chuß╗ùi b╞░ß╗¢m/trß╗¥i tß╗æi.
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ cß╗¡a bß╗ï chß║╖n (invisible wall) tß╗¢i khi chß║ím b╞░ß╗¢m; chß║ím b╞░ß╗¢m 1 lß║ºn ΓåÆ despawn; b╞░ß╗¢m bay giß╗¢i hß║ín trong bi├¬n bß║ún ─æß╗ô.

**C1-04 ΓÇö AC visual (AC2ΓÇôAC12) thiß║┐u ph╞░╞íng thß╗⌐c kiß╗âm chß╗⌐ng (P1)**
- Vß║Ñn ─æß╗ü: `node test/core.test.js` chß╗ë test logic thuß║ºn; AC visual kh├┤ng Node-test ─æ╞░ß╗úc ΓåÆ trß║íng th├íi done m╞í hß╗ô.
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ test.md quy ─æß╗ïnh: (1) manual checklist ~15 b╞░ß╗¢c ─æi hß║┐t mß╗ìi nh├ính (2 lß╗▒a chß╗ìn, Game Over, X giß╗»a chß╗½ng, START lß║íi, resize, tab background); (2) danh s├ích node test case tß╗æi thiß╗âu (C2-10); (3) mß╗ùi AC ghi r├╡ verify bß║▒ng node test hay manual.

### P2 ΓÇö N├¬n sß╗¡a

**C2-01 ΓÇö C╞í chß║┐ nß║íp module cho Node test ch╞░a quy ─æß╗ïnh (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ core.js = logic + dß╗» liß╗çu thuß║ºn (kh├┤ng window/document/rAF), export k├¿m UMD guard (`typeof module !== 'undefined'`); game.js/audio.js/sprites.js kh├┤ng nß║▒m trong test.

**C2-02 ΓÇö ─Éiß╗üu khiß╗ân mobile/touch ch╞░a quyß║┐t ─æß╗ïnh (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ th├¬m d-pad ß║úo (4 n├║t) hiß╗ân thß╗ï khi ph├ít hiß╗çn `ontouchstart`, set key state t╞░╞íng ─æ╞░╞íng WASD.

**C2-03 ΓÇö Input: spam ph├¡m, key repeat, focus loss (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ key state set (keydown/keyup), bß╗Å qua `e.repeat`, `preventDefault` WASD/arrows, clear key state khi `blur`/`visibilitychange`; hß╗Öp lß╗▒a chß╗ìn one-shot (kh├│a tß╗¢i khi transition xong).

**C2-04 ΓÇö Knockback cß╗¡a tr╞░ß╗¢c cß║únh 4 (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ knockback 40px ng╞░ß╗úc h╞░ß╗¢ng + cooldown 1.5s; mß╗ùi lß║ºn chß║ím: ─æß║⌐y 1 lß║ºn + cß║únh b├ío "B├│ng tß╗æi chß║╖n cß╗¡a! Hß╗ôn ma ─æß║⌐y m├¿o l├╣i lß║íi!"; hß╗ôn ma canh cß╗¡a tr╞░ß╗¢c (vß║╜ sprite), cß╗¡a h├ánh lang ß╗ƒ vß╗ï tr├¡ kh├íc r├╡ r├áng (m┼⌐i t├¬n chß╗ë).

**C2-05 ΓÇö Cß║únh 5: c╞í chß║┐ "5 lß║ºn h├╣" (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ 5 scare zone cß╗æ ─æß╗ïnh theo ─æß╗Ö s├óu, fire-once; h├ánh lang one-way (cß╗¡a v├áo ─æ├│ng sau l╞░ng); counter "Bß╗ï h├╣: x/5" g├│c d╞░ß╗¢i m├án h├¼nh; sau scare thß╗⌐ 5 ΓåÆ mß╗ƒ cß╗¡a ph├▓ng ─ân + m┼⌐i t├¬n chß╗ë.

**C2-06 ΓÇö Cß║únh 6: cutscene (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ script cutscene: v├áo trigger cß║ính b├án ΓåÆ kh├│a input ΓåÆ m├¿o tß╗▒ di chuyß╗ân tß╗¢i m├⌐p b├án ΓåÆ nhß║úy (nß╗Öi suy 0.5s) ΓåÆ chß╗º ├┤m (2 sprite chß╗ông nhau + heart) ΓåÆ bubble "Happy Birthday Yuniebel!" + chime ΓåÆ b├ính kem hiß╗çn + text g├╡ tß╗½ng chß╗» ΓåÆ 2.5s ΓåÆ n├║t Ch╞íi lß║íi.

**C2-07 ΓÇö Reset trß║íng th├íi: X / Ch╞íi lß║íi / Game Over (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ h├ám `resetGame()` duy nhß║Ñt reset to├án bß╗Ö (scene, trigger flags, scare counter, darkness, audio, hß╗Öp thoß║íi); X v├á mß╗ìi n├║t Ch╞íi lß║íi gß╗ìi h├ám n├áy; X kh├┤ng cß║ºn x├íc nhß║¡n (game ngß║»n).

**C2-08 ΓÇö Delta time kh├┤ng clamp (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ clamp dt max 50ms; trigger check d├╣ng vß╗ï tr├¡ mß╗¢i mß╗ùi frame (─æß╗º vß╗¢i bß║ún ─æß╗ô nhß╗Å + clamp).

**C2-09 ΓÇö pages.yml thiß║┐u chi tiß║┐t (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ chß╗æt workflow trong spec: `actions/checkout@v4` + `actions/configure-pages@v5` + `actions/upload-pages-artifact@v3` (path `games`) + `actions/deploy-pages@v4`; permissions `contents: read / pages: write / id-token: write`; trigger `push master` + `workflow_dispatch`; AC13 ─æß╗òi th├ánh "pages.yml tß╗ôn tß║íi + syntax hß╗úp lß╗ç + deploy thß╗¡ (cß║ºn user bß║¡t Pages tß║íi Settings ΓåÆ Pages ΓåÆ GitHub Actions)"; b╞░ß╗¢c thß╗º c├┤ng ghi trong test.md.

**C2-10 ΓÇö AC14 thiß║┐u danh s├ích test case tß╗æi thiß╗âu (P2)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ spec liß╗çt k├¬: (1) di chuyß╗ân 4 h╞░ß╗¢ng + bi├¬n; (2) collision vß║¡t cß║ún; (3) chuß╗ùi trigger cß║únh 1 (4 phase) + cß║únh 3 (2 nh├ính) + cß║únh 4 (knockback) + cß║únh 5 (5 lß║ºn, kh├┤ng fire lß║╖p) + cß║únh 6; (4) mß╗ìi transition kß╗â cß║ú GAMEOVER + reset; (5) light radius.

### P3 ΓÇö Nhß║╣

- **C3-01 ΓÇö V├╣ng tß╗æi cß║únh 3 ─æi v├áo tr╞░ß╗¢c khi chß╗ìn** ΓåÆ RESOLUTION: tr╞░ß╗¢c phase K_CHOICE, v├╣ng tß╗æi l├á t╞░ß╗¥ng v├┤ h├¼nh; tß╗½ K_CHOICE trß╗ƒ ─æi, m├¿o ─æi v├áo v├╣ng tß╗æi = GAMEOVER (t╞░╞íng ─æ╞░╞íng chß╗ìn [2]).
- **C3-02 ΓÇö "Kiß╗âm tra vß║┐t m├íu" ch╞░a r├╡ c╞í chß║┐** ΓåÆ RESOLUTION: vß║┐t m├íu = trigger zone, chß║ím = ho├án th├ánh nhiß╗çm vß╗Ñ ΓåÆ phase K_VOICE.
- **C3-03 ΓÇö Nß╗Öi dung hß╗Öi thoß║íi ch╞░a chß╗æt** ΓåÆ RESOLUTION: chß╗æt to├án bß╗Ö text trong spec (mß╗Ñc "Nß╗Öi dung hß╗Öi thoß║íi").
- **C3-04 ΓÇö B╞░ß╗¢m AI** ΓåÆ RESOLUTION: b╞░ß╗¢m bay pattern sin (hover), khi m├¿o c├ích < 60px th├¼ bay tr├ính xa (tß╗æc ─æß╗Ö 85 px/s < m├¿o 120 px/s ΓÇö ─æuß╗òi kß╗ïp sau ~3ΓÇô5s), giß╗¢i hß║ín bi├¬n bß║ún ─æß╗ô, despawn khi chß║ím.
- **C3-05 ΓÇö Audio "footstep" kh├┤ng khß╗¢p scope** ΓåÆ RESOLUTION: bß╗Å footstep khß╗Åi scope ΓÇö chß╗ë meow/scare/chime.
- **C3-06 ΓÇö Input lock khi fade** ΓåÆ RESOLUTION: kh├│a input trong l├║c fade (transition timer).
- **C3-07 ΓÇö localStorage/─æiß╗âm sß╗æ m├óu thuß║½n hß╗ô s╞í** ΓåÆ RESOLUTION: ghi r├╡ "kh├┤ng c├│ ─æiß╗âm sß╗æ/localStorage ΓÇö ngo├ái scope" trong spec.
- **C3-08 ΓÇö Resolution/scale** ΓåÆ RESOLUTION: canvas nß╗Öi ph├ón giß║úi 480├ù270 (16:9), CSS scale giß╗» tß╗╖ lß╗ç vß╗¢i window (letterbox), `image-rendering: pixelated`.

## Kß║┐t luß║¡n
- [x] Cß║ºn sß╗¡a tr╞░ß╗¢c khi implement: C1-01..04 + C2-01..10 + C3-01..08 ΓÇö **Tß║ñT Cß║ó ─É├â RESOLVE** (xem mß╗Ñc RESOLUTION ß╗ƒ tr├¬n, spec.md ─æ├ú cß║¡p nhß║¡t).
