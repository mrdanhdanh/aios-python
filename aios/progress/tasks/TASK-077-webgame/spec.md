# TASK-077 ΓÇö Webgame 2D Pixel "Yuniebel" (GitHub Pages)

## Mß╗Ñc ti├¬u

Tß║ío mß╗Öt webgame 2D pixel art ho├án to├án static (0 dependency, chß║íy offline), kß╗â c├óu chuyß╗çn m├¿o "Yuniebel" ─æi t├¼m chß╗º nh├ón trong mß╗Öt ng├┤i nh├á b├¡ ß║⌐n, kß║┐t th├║c bß║▒ng m├án ch├║c mß╗½ng sinh nhß║¡t. Game deploy ─æ╞░ß╗úc qua GitHub Pages, ─æß║╖t trong th╞░ mß╗Ñc ri├¬ng `games/yuniebel/`, t├ích hß║│n khß╗Åi backend AIOS.

## Phß║ím vi

- **Trong phß║ím vi**:
  - Th╞░ mß╗Ñc mß╗¢i `games/yuniebel/` (HTML + CSS + JS thuß║ºn, canvas 2D, pixel art vß║╜ bß║▒ng code ΓÇö kh├┤ng d├╣ng file ß║únh/audio ngo├ái)
  - 6 cß║únh ch╞íi + m├án h├¼nh ch├¡nh (title) + m├án h├¼nh Game Over + m├án h├¼nh Kß║┐t th├║c
  - ─Éiß╗üu khiß╗ân WASD, n├║t bß║¡t/tß║»t UI, khung nhiß╗çm vß╗Ñ + n├║t X vß╗ü m├án h├¼nh ch├¡nh
  - Lß╗▒a chß╗ìn 1/2 tß║íi cß║únh bß║┐p, knockback hß╗ôn ma, 5 lß║ºn h├╣ dß╗ìa h├ánh lang
  - Hiß╗çu ß╗⌐ng: trß╗¥i tß╗æi dß║ºn, fade chuyß╗ân cß║únh, m├án tß╗æi quanh m├¿o (darkness), jumpscare flash, ├óm thanh WebAudio tß╗▒ sinh (meow, scare, chime ΓÇö kh├┤ng cß║ºn file)
  - Workflow `.github/workflows/pages.yml` deploy folder `games/` ΓåÆ GitHub Pages
  - Test logic thuß║ºn bß║▒ng Node (`node test/core.test.js`)
- **Ngo├ái phß║ím vi**: kh├┤ng ─æß╗Ñng code backend AIOS, kh├┤ng d├╣ng MCP/API (game static kh├┤ng cß║ºn), kh├┤ng d├╣ng framework/build tool, kh├┤ng phß╗Ñ thuß╗Öc CDN/font ngo├ái (chß╗ë monospace system font).

## Input / Output

- **Input**: b├án ph├¡m WASD (di chuyß╗ân), ph├¡m bß║Ñm/click cho lß╗▒a chß╗ìn, click n├║t START / n├║t X / n├║t toggle UI.
- **Output**: canvas 2D hiß╗ân thß╗ï game, UI overlay (khung nhiß╗çm vß╗Ñ, n├║t toggle, hß╗Öp lß╗▒a chß╗ìn, hß╗Öp thoß║íi).

## Luß╗ông tr├▓ ch╞íi (story beats ΓÇö theo y├¬u cß║ºu ng╞░ß╗¥i d├╣ng)

1. **Title**: bß║ºu trß╗¥i xanh, m├óy bay, mß║╖t trß╗¥i, n├║t START.
2. **Cß║únh 1 ΓÇö S├ón v╞░ß╗¥n**: m├¿o ch╞íi ngo├ái v╞░ß╗¥n; chß╗º gß╗ìi tß╗½ trong nh├á ΓåÆ nhiß╗çm vß╗Ñ "V├áo nh├á". Khi m├¿o tß╗¢i gß║ºn cß╗¡a ΓåÆ b╞░ß╗¢m xuß║Ñt hiß╗çn ΓåÆ nhiß╗çm vß╗Ñ "─Éuß╗òi theo con b╞░ß╗¢m". Chß║ím b╞░ß╗¢m ΓåÆ trß╗¥i dß║ºn tß╗æi ΓåÆ nhiß╗çm vß╗Ñ "Trß╗¥i tß╗æi ΓÇö h├úy v├áo nh├á" ΓåÆ v├áo cß╗¡a ΓåÆ Cß║únh 2.
3. **Cß║únh 2 ΓÇö Ph├▓ng kh├ích**: kh├┤ng thß║Ñy chß╗º ΓåÆ nhiß╗çm vß╗Ñ "T├¼m chß╗º nh├ón ΓÇö ─æß║┐n nh├á bß║┐p" ΓåÆ v├áo bß║┐p ΓåÆ Cß║únh 3.
4. **Cß║únh 3 ΓÇö Nh├á bß║┐p**: thß║Ñy vß║┐t m├íu d╞░ß╗¢i s├án ΓåÆ nhiß╗çm vß╗Ñ "Kiß╗âm tra vß║┐t m├íu". Kiß╗âm tra xong ΓåÆ v├╣ng tß╗æi ph├ít ra lß╗¥i gß╗ìi ΓåÆ hß╗Öp lß╗▒a chß╗ìn:
   - **[1] Bß╗Å chß║íy** ΓåÆ m├¿o chß║íy vß╗ü ph├▓ng kh├ích ΓåÆ Cß║únh 4.
   - **[2] Nghe theo lß╗¥i gß╗ìi** ΓåÆ m├¿o b╞░ß╗¢c v├áo v├╣ng tß╗æi ΓåÆ m├án h├¼nh tß╗æi dß║ºn ΓåÆ **GAME OVER** (n├║t Ch╞íi lß║íi ΓåÆ Title).
5. **Cß║únh 4 ΓÇö Ph├▓ng kh├ích ma ├ím**: c─ân ph├▓ng quß╗╖ dß╗ï (tß╗æi, s╞░╞íng m├╣, hß╗ôn ma). Nhiß╗çm vß╗Ñ "T├¼m ng╞░ß╗¥i chß╗º". ─Éi ra cß╗¡a tr╞░ß╗¢c ΓåÆ bß╗ï hß╗ôn ma **─æß║⌐y l├╣i** (knockback + flash + cß║únh b├ío). Phß║úi ─æi qua cß╗¡a ph├▓ng tiß║┐p theo (h├ánh lang) ΓåÆ Cß║únh 5.
6. **Cß║únh 5 ΓÇö H├ánh lang d├ái**: ─æi c├áng s├óu c├áng bß╗ï h├╣ dß╗ìa; **5 sß╗▒ kiß╗çn h├╣** (scare flash + shake + ├óm thanh). ─Éß╗º 5 lß║ºn ΓåÆ ─æß║┐n cß╗¡a ph├▓ng ─ân ΓåÆ Cß║únh 6.
7. **Cß║únh 6 ΓÇö Ph├▓ng ─ân / Sinh nhß║¡t**: chß╗º ngß╗ôi b├án chß╗¥; m├¿o lß║íi gß║ºn ΓåÆ nhß║úy l├¬n b├án ΓåÆ chß╗º ├┤m m├¿o ΓåÆ bong b├│ng "Happy Birthday Yuniebel!" ΓåÆ b├ính kem hiß╗çn ra + d├▓ng chß╗» ch├║c mß╗½ng sinh nhß║¡t ΓåÆ m├án h├¼nh Kß║┐t th├║c (n├║t Ch╞íi lß║íi).

## State machine ΓÇö phase/sub-state (chi tiß║┐t, theo C1-02)

State cß║Ñp cß║únh: `TITLE ΓåÆ GARDEN ΓåÆ LIVING ΓåÆ KITCHEN ΓåÆ HAUNTED ΓåÆ HALLWAY ΓåÆ DINING ΓåÆ END`, nh├ính `KITCHEN ΓåÆ GAMEOVER`, nh├ính `any ΓåÆ TITLE` (n├║t X / reset).

Sub-state (phase) mß╗ùi cß║únh + ─æiß╗üu kiß╗çn chuyß╗ân:

| Cß║únh | Phase | ─Éiß╗üu kiß╗çn v├áo | Trigger chuyß╗ân tiß║┐p |
|------|-------|---------------|---------------------|
| GARDEN | `G_INIT` | v├áo cß║únh | chß╗º gß╗ìi (auto 2s), m├¿o chß║ím v├╣ng cß╗¡a (door zone, cß╗¡a bß╗ï kh├│a) |
| GARDEN | `G_BUTTERFLY` | m├¿o v├áo door zone (lß║ºn ─æß║ºu) | b╞░ß╗¢m spawn gß║ºn cß╗¡a, bay ra v╞░ß╗¥n |
| GARDEN | `G_CHASE` | b╞░ß╗¢m spawn xong | m├¿o chß║ím b╞░ß╗¢m (AABB, 1 lß║ºn ΓåÆ despawn b╞░ß╗¢m) |
| GARDEN | `G_DARK` | chß║ím b╞░ß╗¢m | darkness 0ΓåÆ1 trong 5s, mß╗ƒ kh├│a cß╗¡a |
| GARDEN | `G_DOOR` | darkness >= 1 | m├¿o chß║ím v├╣ng cß╗¡a ΓåÆ v├áo LIVING |
| LIVING | `L_SEARCH` | v├áo cß║únh | m├¿o chß║ím v├╣ng cß╗¡a bß║┐p ΓåÆ KITCHEN |
| KITCHEN | `K_INIT` | v├áo cß║únh | m├¿o chß║ím v├╣ng vß║┐t m├íu |
| KITCHEN | `K_BLOOD` | chß║ím m├íu | hß╗Öp thoß║íi "vß║┐t m├íu..." (1.5s) ΓåÆ `K_VOICE` |
| KITCHEN | `K_VOICE` | xong K_BLOOD | lß╗¥i gß╗ìi tß╗½ v├╣ng tß╗æi (2s) ΓåÆ hiß╗çn hß╗Öp lß╗▒a chß╗ìn ΓåÆ `K_CHOICE` |
| KITCHEN | `K_CHOICE` | hß╗Öp chß╗ìn hiß╗çn | **[1] Bß╗Å chß║íy** ΓåÆ `K_RUN`; **[2] Nghe theo** ΓåÆ `K_OBEY`; m├¿o ─æi v├áo v├╣ng tß╗æi = `K_OBEY` |
| KITCHEN | `K_RUN` | chß╗ìn 1 | m├¿o chß║íy vß╗ü ph├¡a cß╗¡a ph├▓ng kh├ích (auto, 1.5s) ΓåÆ HAUNTED |
| KITCHEN | `K_OBEY` | chß╗ìn 2 | m├¿o ─æi v├áo v├╣ng tß╗æi (auto) ΓåÆ m├án tß╗æi dß║ºn ΓåÆ GAMEOVER |
| HAUNTED | `H_SEARCH` | v├áo cß║únh | chß║ím cß╗¡a tr╞░ß╗¢c ΓåÆ knockback + cß║únh b├ío (cooldown 1.5s, kh├┤ng chuyß╗ân cß║únh); chß║ím cß╗¡a h├ánh lang ΓåÆ HALLWAY |
| HALLWAY | `W_WALK` | v├áo cß║únh | mß╗ùi scare zone (5 zone cß╗æ ─æß╗ïnh, fire-once) ΓåÆ scare event + counter |
| HALLWAY | `W_DONE` | scare count = 5 | mß╗ƒ cß╗¡a ph├▓ng ─ân + m┼⌐i t├¬n chß╗ë ΓåÆ chß║ím cß╗¡a ΓåÆ DINING |
| DINING | `D_APPROACH` | v├áo cß║únh | m├¿o chß║ím v├╣ng cß║ính b├án ΓåÆ kh├│a input |
| DINING | `D_JUMP` | cutscene | m├¿o tß╗▒ di chuyß╗ân tß╗¢i m├⌐p b├án ΓåÆ nhß║úy l├¬n b├án (nß╗Öi suy 0.5s) |
| DINING | `D_HUG` | nhß║úy xong | chß╗º ├┤m m├¿o + bubble "Happy Birthday Yuniebel!" + chime |
| DINING | `D_CAKE` | 1.5s sau D_HUG | b├ính kem hiß╗çn + text ch├║c mß╗½ng g├╡ tß╗½ng chß╗» |
| DINING | `D_END` | text xong + 2.5s | m├án Kß║┐t th├║c (END) + n├║t Ch╞íi lß║íi |

Mß╗ìi transition ─æß╗üu c├│ fade; input bß╗ï kh├│a trong l├║c fade (C3-06).

## Kiß║┐n tr├║c file

```
games/yuniebel/
Γö£ΓöÇΓöÇ index.html          # Canvas + UI overlay, script tag CLASSIC (kh├┤ng module), relative path
Γö£ΓöÇΓöÇ style.css           # Pixel style (image-rendering: pixelated), UI layout, letterbox
Γö£ΓöÇΓöÇ src/
Γöé   Γö£ΓöÇΓöÇ core.js         # Logic THUß║ªN (test bß║▒ng Node): scenes, phases, tasks, collision, trigger, state machine, light radius, resetGame. KH├öNG window/document/rAF; UMD guard (typeof module !== 'undefined' ΓåÆ module.exports)
Γöé   Γö£ΓöÇΓöÇ sprites.js      # Pixel art maps (m├¿o hß╗ông, b╞░ß╗¢m, chß╗º, ma, b├ính kem...) + render helper (browser only)
Γöé   Γö£ΓöÇΓöÇ audio.js        # WebAudio SFX tß╗▒ sinh (meow/scare/chime)
Γöé   ΓööΓöÇΓöÇ game.js         # Game loop (rAF), input, scene rendering, UI wiring (browser only)
ΓööΓöÇΓöÇ test/
    ΓööΓöÇΓöÇ core.test.js    # Node test cho core.js (assert thß╗º c├┤ng, exit code)
.github/workflows/pages.yml  # Deploy games/ ΓåÆ GitHub Pages
```

## R├áng buß╗Öc ─æ╞░ß╗¥ng dß║½n & m├┤i tr╞░ß╗¥ng (C1-01)

- Mß╗îI ─æ╞░ß╗¥ng dß║½n t├ái nguy├¬n l├á **relative** (`src/core.js`, `style.css`); **cß║Ñm** URL tuyß╗çt ─æß╗æi (bß║»t ─æß║ºu `/`), **cß║Ñm** `fetch`, **cß║Ñm** `<script type="module">` (CORS chß║╖n tr├¬n file://).
- Game chß║íy ─æ╞░ß╗úc cß║ú khi mß╗ƒ bß║▒ng `file://` lß║½n deploy tß║íi `/aios-python/games/yuniebel/`.
- Kh├┤ng d├╣ng ─æiß╗âm sß╗æ/localStorage (ngo├ái scope ΓÇö C3-07).

## Ti├¬u ch├¡ chß║Ñp nhß║¡n (Acceptance Criteria)

Ph╞░╞íng thß╗⌐c kiß╗âm chß╗⌐ng: **[node]** = `node test/core.test.js`; **[manual]** = manual checklist trong test.md; **[visual]** = xem bß║▒ng mß║»t khi chß║íy game.

- **AC1** [manual+visual] Mß╗ƒ `games/yuniebel/index.html` bß║▒ng file:// l├á ch╞íi ─æ╞░ß╗úc; DevTools ΓåÆ Network chß╗ë c├│ request local (C1-01).
- **AC2** [visual] Title: bß║ºu trß╗¥i xanh + m├óy bay + mß║╖t trß╗¥i + n├║t START ΓåÆ v├áo Cß║únh 1.
- **AC3** [node+manual] M├¿o pixel t├│c hß╗ông, di chuyß╗ân WASD 4 h╞░ß╗¢ng, bß╗ï chß║╖n bß╗ƒi bi├¬n bß║ún ─æß╗ô v├á vß║¡t cß║ún.
- **AC4** [manual] N├║t bß║¡t/tß║»t UI g├│c tr├¬n phß║úi: ß║⌐n/hiß╗çn khung nhiß╗çm vß╗Ñ + h╞░ß╗¢ng dß║½n ─æiß╗üu khiß╗ân.
- **AC5** [manual] Khung nhiß╗çm vß╗Ñ g├│c tr├¬n tr├íi hiß╗ân thß╗ï nhiß╗çm vß╗Ñ hiß╗çn tß║íi; n├║t X ΓåÆ vß╗ü Title (gß╗ìi `resetGame()` ΓÇö AC16).
- **AC6** [node+manual] Cß║únh 1 ─æ├║ng chuß╗ùi: V├áo nh├á ΓåÆ gß║ºn cß╗¡a (cß╗¡a KH├ôA tß╗¢i khi chß║ím b╞░ß╗¢m ΓÇö C1-03) ΓåÆ b╞░ß╗¢m xuß║Ñt hiß╗çn ΓåÆ ─æuß╗òi b╞░ß╗¢m ΓåÆ chß║ím b╞░ß╗¢m (despawn) ΓåÆ trß╗¥i tß╗æi dß║ºn 5s ΓåÆ nhiß╗çm vß╗Ñ vß╗ü nh├á ΓåÆ v├áo cß╗¡a ΓåÆ Cß║únh 2.
- **AC7** [node+manual] Cß║únh 2: ph├▓ng kh├ích, kh├┤ng c├│ chß╗º, nhiß╗çm vß╗Ñ t├¼m chß╗º ß╗ƒ bß║┐p; v├áo bß║┐p ΓåÆ Cß║únh 3.
- **AC8** [node+manual] Cß║únh 3: chß║ím vß║┐t m├íu ΓåÆ kiß╗âm tra (K_BLOOD) ΓåÆ lß╗¥i gß╗ìi ΓåÆ lß╗▒a chß╗ìn; [1] ΓåÆ Cß║únh 4; [2] hoß║╖c ─æi v├áo v├╣ng tß╗æi ΓåÆ Game Over (m├án RIP + Ch╞íi lß║íi).
- **AC9** [node+manual] Cß║únh 4: ma ├ím (tß╗æi + s╞░╞íng + hß╗ôn ma canh cß╗¡a tr╞░ß╗¢c), ra cß╗¡a tr╞░ß╗¢c ΓåÆ knockback 40px + cooldown 1.5s + cß║únh b├ío; cß╗¡a h├ánh lang ΓåÆ Cß║únh 5.
- **AC10** [node+manual] Cß║únh 5: h├ánh lang one-way, 5 scare zone fire-once (counter "Bß╗ï h├╣: x/5"), sau 5 lß║ºn ΓåÆ mß╗ƒ cß╗¡a + m┼⌐i t├¬n ΓåÆ Cß║únh 6.
- **AC11** [node+manual] Cß║únh 6: cutscene ─æ├║ng thß╗⌐ tß╗▒ (lß║íi gß║ºn ΓåÆ nhß║úy ΓåÆ ├┤m ΓåÆ "Happy Birthday Yuniebel!" ΓåÆ b├ính kem + text g├╡ chß╗» ΓåÆ END + Ch╞íi lß║íi).
- **AC12** [visual] Fade chuyß╗ân cß║únh; cß║únh 1 tß╗æi dß║ºn sau khi chß║ím b╞░ß╗¢m; v├╣ng s├íng quanh m├¿o ß╗ƒ cß║únh tß╗æi (4, 5); input kh├│a khi fade.
- **AC13** [manual] `pages.yml` tß╗ôn tß║íi + syntax hß╗úp lß╗ç (validate YAML); deploy thß╗¡ khi user bß║¡t Pages (Settings ΓåÆ Pages ΓåÆ GitHub Actions) ΓåÆ URL `/aios-python/games/yuniebel/` hoß║ít ─æß╗Öng. B╞░ß╗¢c thß╗º c├┤ng ghi trong test.md.
- **AC14** [node] `node test/core.test.js` PASS ΓÇö tß╗æi thiß╗âu c├íc case (C2-10): (1) di chuyß╗ân 4 h╞░ß╗¢ng + bi├¬n; (2) collision vß║¡t cß║ún kh├┤ng xuy├¬n; (3) chuß╗ùi trigger cß║únh 1 (4 phase); (4) cß║únh 3 2 nh├ính + ─æi v├áo v├╣ng tß╗æi; (5) cß║únh 4 knockback + kh├┤ng chuyß╗ân cß║únh; (6) cß║únh 5 5 lß║ºn fire-once + mß╗ƒ cß╗¡a; (7) cß║únh 6 chuß╗ùi cutscene; (8) mß╗ìi transition + GAMEOVER; (9) `resetGame()` reset to├án bß╗Ö; (10) light radius.
- **AC15** [manual] Hard gate ─æß║ºy ─æß╗º 8 file + cß║¡p nhß║¡t LOG.md/PROGRESS.md + commit.
- **AC16** [node] `resetGame()` l├á h├ám duy nhß║Ñt reset to├án bß╗Ö state (scene, phases, trigger flags, scare counter, darkness, hß╗Öp thoß║íi, audio, timers); n├║t X v├á mß╗ìi n├║t Ch╞íi lß║íi ─æß╗üu gß╗ìi n├│ (C2-07); gß╗ìi resetGame 2 lß║ºn li├¬n tß╗Ñc kh├┤ng lß╗ùi (C2-19).
- **AC17** [manual] Mobile: d-pad ß║úo (div overlay 4 n├║t) hiß╗çn khi `ontouchstart` ΓÇö `touchstart/touchend` giß╗» ng├│n = di chuyß╗ân li├¬n tß╗Ñc (t╞░╞íng ─æ╞░╞íng keydown/keyup); khi c├│ touch ΓåÆ ß║⌐n hint b├án ph├¡m (C2-02/C2-19).

## R├áng buß╗Öc kß╗╣ thuß║¡t

- Canvas 2D nß╗Öi ph├ón giß║úi **480├ù270** (16:9, C3-08), CSS scale giß╗» tß╗╖ lß╗ç vß╗¢i window (letterbox), `image-rendering: pixelated`, scale sprite 3x.
- Pixel art ─æß╗ïnh ngh─⌐a bß║▒ng ma trß║¡n k├╜ tß╗▒ (string array), mß╗ùi k├╜ tß╗▒ = 1 m├áu ΓÇö vß║╜ l├¬n offscreen canvas, kh├┤ng d├╣ng file ß║únh.
- V├▓ng lß║╖p `requestAnimationFrame` + delta time **clamp dt Γëñ 50ms** (C2-08); physics ─æ╞ín giß║ún (AABB, velocity, walk speed 120 px/s); trigger check theo vß╗ï tr├¡ mß╗¢i mß╗ùi frame.
- Trigger zone: AABB t─⌐nh theo scene; mß╗ùi scene c├│ mß║úng phase/trigger/story events (theo bß║úng sub-state ß╗ƒ tr├¬n).
- Input: key state Set (keydown/keyup), bß╗Å qua `e.repeat`, `preventDefault` WASD/arrows, clear key state khi `blur`/`visibilitychange` (C2-03); hß╗Öp lß╗▒a chß╗ìn one-shot (kh├│a tß╗¢i khi transition xong); d-pad ß║úo khi `ontouchstart` (C2-02).
- UI overlay: div HTML (kh├┤ng vß║╜ l├¬n canvas) ΓÇö khung nhiß╗çm vß╗Ñ, hß╗Öp thoß║íi, hß╗Öp lß╗▒a chß╗ìn, counter h├╣.
- To├án bß╗Ö text tiß║┐ng Viß╗çt c├│ dß║Ñu (canvas fillText hß╗ù trß╗ú unicode; font system monospace).
- ├ém thanh: WebAudio tß╗▒ sinh, khß╗ƒi tß║ío context sau gesture ─æß║ºu ti├¬n (autoplay policy) ΓÇö meow/scare/chime (C3-05). WebAudio kh├┤ng khß║ú dß╗Ñng ΓåÆ mute ho├án to├án, game vß║½n ch╞íi b├¼nh th╞░ß╗¥ng; `ctx.resume()` khi c├│ gesture mß╗¢i / quay lß║íi tab (C2-22).
- Fade chuyß╗ân cß║únh: 0.5s (C2-21).
- `resetGame()`: duy nhß║Ñt reset to├án bß╗Ö state, gß╗ìi tß╗½ n├║t X / Ch╞íi lß║íi (C2-07).

## Bß║ún ─æß╗ô & camera (C2-11)

| Cß║únh | K├¡ch th╞░ß╗¢c map (px) | Camera | Ghi ch├║ |
|------|--------------------|--------|---------|
| GARDEN | 960├ù270 | follow m├¿o (clamp bi├¬n) | v╞░ß╗¥n rß╗Öng scroll ngang |
| LIVING | 480├ù270 | kh├┤ng | vß╗½a canvas |
| KITCHEN | 480├ù270 | kh├┤ng | |
| HAUNTED | 480├ù270 | kh├┤ng | layout giß╗æng LIVING, tß╗æi + ma |
| HALLWAY | 960├ù270 | follow m├¿o | 5 scare zone theo ─æß╗Ö s├óu |
| DINING | 480├ù270 | kh├┤ng | |

Camera: map > canvas ΓåÆ follow m├¿o, clamp kh├┤ng lß╗Ö bi├¬n; map Γëñ canvas ΓåÆ t─⌐nh.

## Quy tß║»c trigger zone (C2-12)

- Mß╗ùi phase khai b├ío danh s├ích zone **active ri├¬ng**; zone fire-once trong phase; tß╗▒ re-activate khi phase quay lß║íi (door zone GARDEN d├╣ng 2 phase).
- Tr├╣ng zone trong 1 frame ΓåÆ ╞░u ti├¬n: knockback/cß║únh b├ío xß╗¡ l├╜ TR╞»ß╗ÜC, kh├┤ng chuyß╗ân cß║únh c├╣ng frame.
- Zone tß╗æi thiß╗âu ΓëÑ 16px mß╗ùi chiß╗üu (m├¿o b╞░ß╗¢c tß╗æi ─æa 6px/frame ΓÇö kh├┤ng lß╗ìt zone).
- Trigger check sau khi di chuyß╗ân + clamp.

## Sprite list (tß╗æi thiß╗âu ΓÇö C2-13)

L╞░ß╗¢i 16├ù16 (scale 3x = 48px hiß╗ân thß╗ï), palette Γëñ 16 m├áu, vß║╜ bß║▒ng ma trß║¡n k├╜ tß╗▒:

| Sprite | Frame | H╞░ß╗¢ng | D├╣ng ß╗ƒ |
|--------|-------|-------|--------|
| M├¿o (t├│c hß╗ông) | idle + walk 2 frame | tr├íi/phß║úi (mirror) | mß╗ìi cß║únh |
| B╞░ß╗¢m | 2 frame vß╗ù c├ính | ΓÇö | GARDEN |
| Chß╗º | idle + ├┤m | phß║úi | GARDEN (gß╗ìi), DINING (ngß╗ôi b├án) |
| Hß╗ôn ma | float 2 frame | ΓÇö | HAUNTED, HALLWAY (scare) |
| B├ính kem | 2 frame nß║┐n ch├íy | ΓÇö | DINING |
| Cß╗¡a | kh├│a / mß╗ƒ | ΓÇö | GARDEN, LIVING, KITCHEN, HAUNTED, HALLWAY, DINING |
| B├án | 1 frame | ΓÇö | DINING, KITCHEN |
| Vß║┐t m├íu | 1 frame | ΓÇö | KITCHEN |
| M├óy, mß║╖t trß╗¥i | m├óy 2 frame drift | ΓÇö | TITLE, GARDEN |
| C├óy, bß╗Ñi, hoa | 1 frame | ΓÇö | GARDEN |
| Heart | 2 frame phß╗ông | ΓÇö | D_HUG |
| M┼⌐i t├¬n chß╗ë ─æ╞░ß╗¥ng | 1 frame | ΓÇö | HAUNTED (cß╗¡a h├ánh lang), HALLWAY W_DONE |
| V├╣ng tß╗æi (b├│ng) | 1 frame | ΓÇö | KITCHEN |

## Input trong hß╗Öp thoß║íi/cutscene (C2-14)

- Mß╗ùi phase c├│ cß╗¥ `inputLocked` (bß║úng phase): khi lock, WASD/click di chuyß╗ân bß╗ï bß╗Å qua NH╞»NG key state vß║½n ─æ╞░ß╗úc cß║¡p nhß║¡t (tr├ính d├¡nh ph├¡m).
- Ph├¡m 1/2 chß╗ë xß╗¡ l├╜ khi phase = K_CHOICE.
- N├║t X **lu├┤n hoß║ít ─æß╗Öng ß╗ƒ Mß╗îI state** (kß╗â cß║ú fade/cutscene/GAMEOVER ΓÇö gß╗ìi resetGame).
- Bubble/hß╗Öp thoß║íi KH├öNG chß║╖n di chuyß╗ân; chß╗ë cutscene cß║únh 6 + fade mß╗¢i lock ho├án to├án.

## Timer (C2-15)

- Mß╗îI timing logic d├╣ng **dt t├¡ch l┼⌐y tß╗½ rAF** (game-time accumulator); cß║Ñm setTimeout/setInterval cho logic game (chß╗ë UI kh├┤ng critical).
- Tab ß║⌐n ΓåÆ rAF dß╗½ng ΓåÆ game pause tß╗▒ nhi├¬n, quay lß║íi tiß║┐p tß╗Ñc ─æ├║ng trß║íng th├íi (kh├┤ng cß║ºn pause menu).
- Test: kh├┤ng c├│ dt ΓåÆ kh├┤ng transition.

## B╞░ß╗¢m AI (C2-16 / C3-04)

- Bay pattern sin (hover l├¬n xuß╗æng, ┬▒8px, tß║ºn sß╗æ 2Hz).
- M├¿o c├ích < 60px ΓåÆ bay tr├ính xa, tß╗æc ─æß╗Ö 85 px/s (m├¿o 120 px/s ΓåÆ ─æuß╗òi kß╗ïp sau ~3ΓÇô5s).
- Giß╗¢i hß║ín trong bi├¬n bß║ún ─æß╗ô; chß║ím (AABB) = despawn 1 lß║ºn ΓåÆ G_DARK.

## V├╣ng tß╗æi cß║únh 3 & light radius (C2-17 / C3-01)

- KITCHEN: tr╞░ß╗¢c phase K_CHOICE, v├╣ng tß╗æi l├á **t╞░ß╗¥ng v├┤ h├¼nh** (chß║╖n ─æi v├áo); tß╗½ K_CHOICE trß╗ƒ ─æi, m├¿o ─æi v├áo v├╣ng tß╗æi = K_OBEY (GAMEOVER). Ph├▓ng s├íng ΓÇö chß╗ë v├╣ng tß╗æi cß╗Ñc bß╗Ö tß╗æi.
- Light radius: b├ín k├¡nh **90px** quanh m├¿o, ├íp dß╗Ñng cß║únh HAUNTED v├á HALLWAY (tß╗æi to├án cß║únh, ngo├ái b├ín k├¡nh chß╗ë thß║Ñy silhouette).
- GARDEN G_DARK: darkness 0ΓåÆ1 trong 5s l├á overlay nß╗ün (bß║ºu trß╗¥i tß╗æi dß║ºn, KH├öNG ├íp dß╗Ñng light radius ΓÇö m├¿o vß║½n thß║Ñy).

## Collision (C2-18)

- Collision resolution kiß╗âu **slide**: t├ích trß╗Ñc X/Y ΓÇö va chß║ím theo trß╗Ñc n├áo th├¼ giß╗» nguy├¬n tß╗ìa ─æß╗Ö trß╗Ñc ─æ├│, vß║½n di chuyß╗ân trß╗Ñc kia (tr╞░ß╗út dß╗ìc t╞░ß╗¥ng).
- Mß╗ìi vß║¡t cß║ún/bi├¬n/t╞░ß╗¥ng v├┤ h├¼nh ΓëÑ 8px bß╗ü d├áy (an to├án vß╗¢i b╞░ß╗¢c 6px/frame).
- Knockback c┼⌐ng ├íp dß╗Ñng collision: ─æß║⌐y tß╗¢i khi chß║ím t╞░ß╗¥ng, kh├┤ng xuy├¬n.

## Nß╗Öi dung hß╗Öi thoß║íi & nhiß╗çm vß╗Ñ (chß╗æt ΓÇö C3-03)

| N╞íi | Text |
|-----|------|
| Title | Ti├¬u ─æß╗ü "YUNIEBEL" + phß╗Ñ ─æß╗ü "Mß╗Öt c├óu chuyß╗çn m├¿o con" + n├║t START + hint "WASD ─æß╗â di chuyß╗ân" |
| Cß║únh 1 ΓÇö G_INIT | Bong b├│ng chß╗º (tß╗½ cß╗¡a): "M├¿o ╞íi, v├áo nh├á ─æi!" | Nhiß╗çm vß╗Ñ: "Nghe lß╗¥i chß╗º ΓÇö v├áo nh├á" |
| Cß║únh 1 ΓÇö G_BUTTERFLY | "B╞░ß╗¢m k├¼a!" | Nhiß╗çm vß╗Ñ: "─Éuß╗òi theo con b╞░ß╗¢m!" |
| Cß║únh 1 ΓÇö G_CHASE xong | "M├¿o bß║»t ─æ╞░ß╗úc b╞░ß╗¢m!" | Nhiß╗çm vß╗Ñ: "Trß╗¥i tß╗æi rß╗ôi ΓÇö nhanh v├áo nh├á!" |
| Cß║únh 2 | Nhiß╗çm vß╗Ñ: "Chß╗º ─æ├óu rß╗ôi nhß╗ë? ΓÇö T├¼m ß╗ƒ nh├á bß║┐p" |
| Cß║únh 3 ΓÇö K_BLOOD | "Vß║┐t m├íu d╞░ß╗¢i s├án... phß║úi kiß╗âm tra!" | Nhiß╗çm vß╗Ñ: "Kiß╗âm tra vß║┐t m├íu" |
| Cß║únh 3 ΓÇö K_VOICE | Lß╗¥i gß╗ìi tß╗½ v├╣ng tß╗æi: "M├¿o ╞íi... lß║íi ─æ├óy..." | Nhiß╗çm vß╗Ñ: "C├│ tiß║┐ng gß╗ìi tß╗½ v├╣ng tß╗æi..." |
| Cß║únh 3 ΓÇö K_CHOICE | Hß╗Öp chß╗ìn: "[1] Bß╗Å chß║íy" / "[2] Nghe theo lß╗¥i gß╗ìi" |
| Game Over | "M├¿o Yuniebel ─æ├ú ─æi v├áo b├│ng tß╗æi..." + "GAME OVER" + n├║t "Ch╞íi lß║íi" |
| Cß║únh 4 | Nhiß╗çm vß╗Ñ: "T├¼m ng╞░ß╗¥i chß╗º... c─ân ph├▓ng sao lß║í thß║┐ n├áy" ; cß║únh b├ío cß╗¡a tr╞░ß╗¢c: "B├│ng tß╗æi chß║╖n cß╗¡a! Hß╗ôn ma ─æß║⌐y m├¿o l├╣i lß║íi!" |
| Cß║únh 5 | Nhiß╗çm vß╗Ñ: "─Éi qua h├ánh lang... ─æß╗½ng sß╗ú" + counter "Bß╗ï h├╣: x/5" |
| Cß║únh 6 | Nhiß╗çm vß╗Ñ: "Chß╗º ß╗ƒ ─æ├óy rß╗ôi!" ΓåÆ cutscene: "Happy Birthday Yuniebel!" + "≡ƒÄé Ch├║c mß╗½ng sinh nhß║¡t Yuniebel! ≡ƒÄé" |
| END | "Hß║┐t game ΓÇö Cß║úm ╞ín ─æ├ú ch╞íi!" + n├║t "Ch╞íi lß║íi" |

## Workflow GitHub Pages (chß╗æt ΓÇö C2-09)

`.github/workflows/pages.yml`:
- Trigger: `push` nh├ính `[master, main]` (paths: `games/**`, `.github/workflows/pages.yml`) + `workflow_dispatch` (C2-20).
- Permissions: `contents: read`, `pages: write`, `id-token: write`; `concurrency: { group: pages, cancel-in-progress: true }`.
- Steps: `actions/checkout@v4` ΓåÆ `actions/configure-pages@v5` ΓåÆ `actions/upload-pages-artifact@v3` (path: `games`) ΓåÆ `actions/deploy-pages@v4`.
- Kß║┐t quß║ú URL: `https://mrdanhdanh.github.io/aios-python/games/yuniebel/` (cß║ºn user bß║¡t Pages ΓåÆ Source: GitHub Actions).
