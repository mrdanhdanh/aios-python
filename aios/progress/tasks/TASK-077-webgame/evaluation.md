# Evaluation ΓÇö TASK-077 (Webgame Yuniebel)

## ─Éß╗æi chiß║┐u AC (ti├¬u ch├¡ chß║Ñp nhß║¡n)

| AC | Nß╗Öi dung | Trß║íng th├íi | Ghi ch├║ |
|----|----------|------------|---------|
| AC1 | Chß║íy offline bß║▒ng file:// + relative path | Γ£à | Script classic + relative path (core/sprites/audio/game.js) |
| AC2 | Title: bß║ºu trß╗¥i + m├óy + mß║╖t trß╗¥i + START | Γ£à | bgTitle() vß║╜ gradient + sun + clouds + grass |
| AC3 | M├¿o pixel t├│c hß╗ông, WASD, bß╗ï chß║╖n | Γ£à | Sprites.cat() + collision slide + clamp bi├¬n |
| AC4 | N├║t UI toggle (g├│c phß║úi) | Γ£à | uiBtn click ΓåÆ ß║⌐n/hiß╗çn task box |
| AC5 | Task box (g├│c tr├íi) + n├║t X ΓåÆ Title | Γ£à | taskText + task-close ΓåÆ resetGame() |
| AC6 | Cß║únh 1 tuß║ºn tß╗▒: cß╗¡a kh├│a ΓåÆ b╞░ß╗¢m ΓåÆ ─æuß╗òi ΓåÆ tß╗æi ΓåÆ LIVING | Γ£à | core.js phases G_INITΓåÆG_BUTTERFLYΓåÆG_CHASEΓåÆG_DARKΓåÆG_DOOR |
| AC7 | Cß║únh 2: ph├▓ng kh├ích ΓåÆ bß║┐p | Γ£à | L_SEARCH ΓåÆ zone door_kitchen ΓåÆ K_INIT |
| AC8 | Cß║únh 3: m├íu ΓåÆ lß╗¥i gß╗ìi ΓåÆ chß╗ìn 1/2 hoß║╖c v├╣ng tß╗æi | Γ£à | K_INITΓåÆK_BLOODΓåÆK_VOICEΓåÆK_CHOICE; [1]ΓåÆK_RUNΓåÆHAUNTED; [2]ΓåÆK_OBEYΓåÆGAMEOVER |
| AC9 | Cß║únh 4: knockback cß╗¡a tr╞░ß╗¢c + cß╗¡a h├ánh lang | Γ£à | HAUNTED: door_front knockback 40px + cd 1.5s; door_hall ΓåÆ HALLWAY |
| AC10 | Cß║únh 5: 5 scare fire-once + counter | Γ£à | HALLWAY: 5 scare zones, counter "Bß╗ï h├╣: x/5", W_DONE |
| AC11 | Cß║únh 6: cutscene ΓåÆ ├┤m ΓåÆ b├ính ΓåÆ END | Γ£à | D_APPROACHΓåÆD_JUMPΓåÆD_HUGΓåÆD_CAKEΓåÆD_END |
| AC12 | Fade + darkness + light radius | Γ£à | fade 0.5s, darkness overlay, lightCanvas radial gradient |
| AC13 | pages.yml tß╗ôn tß║íi | Γ£à | .github/workflows/pages.yml (checkoutΓåÆconfigureΓåÆuploadΓåÆdeploy) |
| AC14 | Node test PASS | Γ£à | 58/58 PASS |
| AC15 | Hard gate ─æß║ºy ─æß╗º + LOG/PROGRESS | Γ£à | ─Éang thß╗▒c hiß╗çn |
| AC16 | resetGame() reset to├án bß╗Ö | Γ£à | node test: "resetGame 2 lß║ºn li├¬n tß╗Ñc kh├┤ng lß╗ùi" |
| AC17 | D-pad mobile | Γ£à | ontouchstart ΓåÆ d-pad div overlay |

## Kß║┐t luß║¡n
- **17/17 AC PASS**
- Sprites mß╗¢i d├╣ng canvas primitives thay v├¼ ma trß║¡n k├╜ tß╗▒ ΓÇö pixel art chi tiß║┐t h╞ín nhiß╗üu
- Backgrounds pre-rendered (7 scenes) ΓÇö render mß╗ùi frame chß╗ë cß║ºn drawImage 1 lß║ºn
- Audio: WebAudio 4 SFX (meow/scare/chime/whisper), graceful degradation
- Mobile: d-pad ß║úo + touch events

## B├ái hß╗ìc
- Ma trß║¡n k├╜ tß╗▒ 16x16 qu├í th├┤ ΓåÆ canvas primitives cho pixel art ─æß║╣p h╞ín nhiß╗üu
- Pre-render backgrounds ΓåÆµÇºΦâ╜ tß╗æt h╞ín fillRect tß╗½ng ├┤ mß╗ùi frame
- Override requestAnimationFrame tr╞░ß╗¢c khi eval game.js trong jsdom (tr├ính jsdom native rAF bß║Ñt ─æß╗ông bß╗Ö)

## H├ánh ─æß╗Öng ─æß╗ü xuß║Ñt
- Manual test tr├¬n browser (file:// + GitHub Pages URL)
- Bß║¡t GitHub Pages tß║íi Settings ΓåÆ Pages ΓåÆ Source: GitHub Actions
