# Critique v├▓ng 2 ΓÇö TASK-077 (bß╗ƒi critic agent, 2026-08-15)

## ─É├ính gi├í chung
Spec sau resolve v├▓ng 1 ─æ├ú cß║úi thiß╗çn r├╡: state machine c├│ bß║úng sub-state, AC gß║»n ph╞░╞íng thß╗⌐c kiß╗âm chß╗⌐ng, r├áng buß╗Öc path/deploy/input/audio chß╗æt, pages.yml chi tiß║┐t. Mß╗⌐c sß║╡n s├áng 3.5/5 ΓÇö c├▓n thiß║┐u dß╗» liß╗çu cß╗Ñ thß╗â: k├¡ch th╞░ß╗¢c bß║ún ─æß╗ô, danh s├ích sprite, quy tß║»c trigger, input lock per phase.

## 1. R├á so├ít resolution v├▓ng 1 ΓåÆ spec
16/20 ─æ├ú phß║ún ├ính ─æ├║ng. **Thiß║┐u/kh├┤ng ─æß║ºy ─æß╗º (4)**: C3-04 (b╞░ß╗¢m AI) ΓÇö KH├öNG c├│ trong spec; C3-01 (t╞░ß╗¥ng v├┤ h├¼nh v├╣ng tß╗æi tr╞░ß╗¢c K_CHOICE) ΓÇö chß╗ë c├│ nß╗¡a sau; C2-05 (cß╗¡a v├áo ─æ├│ng sau l╞░ng h├ánh lang) ΓÇö kh├┤ng m├┤ tß║ú c╞í chß║┐; C2-04 (m┼⌐i t├¬n cß╗¡a h├ánh lang cß║únh 4 + heart D_HUG) ΓÇö kh├┤ng c├│. M├óu thuß║½n nhß╗Å: AC16 thiß║┐u "audio" so vß╗¢i C2-07.

## 2. Vß║Ñn ─æß╗ü mß╗¢i

### P1 ΓÇö Bß║»t buß╗Öc sß╗¡a

**C2-11 ΓÇö Thiß║┐u k├¡ch th╞░ß╗¢c bß║ún ─æß╗ô tß╗½ng cß║únh + policy camera**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ chß╗æt: GARDEN 960├ù270 (scroll ngang, camera follow), HALLWAY 960├ù270, LIVING/KITCHEN/HAUNTED/DINING 480├ù270 (vß╗½a canvas, kh├┤ng camera). Policy: map > canvas ΓåÆ camera follow m├¿o + clamp bi├¬n map; map Γëñ canvas ΓåÆ kh├┤ng camera. Test: clamp tß╗ìa ─æß╗Ö + camera clamp.

**C2-12 ΓÇö Thiß║┐u quy tß║»c trigger zone (fire-once/re-activate/╞░u ti├¬n overlap)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ (a) mß╗ùi phase khai b├ío danh s├ích zone active ri├¬ng, fire-once trong phase, tß╗▒ re-activate khi phase quay lß║íi; (b) ╞░u ti├¬n xß╗¡ l├╜: knockback/cß║únh b├ío TR╞»ß╗ÜC chuyß╗ân cß║únh (kh├┤ng chuyß╗ân cß║únh c├╣ng frame bß╗ï knockback); (c) zone tß╗æi thiß╗âu ΓëÑ 16px mß╗ùi chiß╗üu; (d) trigger check sau di chuyß╗ân + clamp.

### P2 ΓÇö N├¬n sß╗¡a

**C2-13 ΓÇö Thiß║┐u danh s├ích sprite + l╞░ß╗¢i + frame animation**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ bß║úng sprite tß╗æi thiß╗âu trong spec (16├ù16 l╞░ß╗¢i, scale 3x, Γëñ 16 m├áu/palette): m├¿o (idle + walk 2 frame, 2 h╞░ß╗¢ng + mirror), b╞░ß╗¢m (2 frame vß╗ù c├ính), chß╗º (idle + ├┤m), hß╗ôn ma (float 2 frame), b├ính kem (nß║┐n ch├íy 2 frame), cß╗¡a (kh├│a/mß╗ƒ), b├án, vß║┐t m├íu, m├óy, mß║╖t trß╗¥i, c├óy, hoa, heart, m┼⌐i t├¬n chß╗ë ─æ╞░ß╗¥ng.

**C2-14 ΓÇö Ch╞░a quy ─æß╗ïnh input trong hß╗Öp thoß║íi/cutscene**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ mß╗ùi phase c├│ cß╗¥ `inputLocked` (bß║úng phase th├¬m cß╗Öt); khi lock: WASD/click bß╗Å qua NH╞»NG key state vß║½n cß║¡p nhß║¡t (tr├ính d├¡nh ph├¡m); ph├¡m 1/2 chß╗ë xß╗¡ l├╜ khi phase = K_CHOICE; n├║t X lu├┤n hoß║ít ─æß╗Öng ß╗ƒ Mß╗îI state (gß╗ìi resetGame ΓÇö kh├┤ng bao giß╗¥ kß║╣t); bubble KH├öNG chß║╖n di chuyß╗ân (chß╗ë cutscene cß║únh 6 + fade mß╗¢i lock ho├án to├án).

**C2-15 ΓÇö Game timer theo dt (tab ß║⌐n nhß║úy phase)**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ Mß╗îI timing logic d├╣ng dt t├¡ch l┼⌐y tß╗½ rAF (game-time accumulator), cß║Ñm setTimeout/setInterval cho logic game; tab ß║⌐n ΓåÆ rAF dß╗½ng ΓåÆ pause tß╗▒ nhi├¬n, quay lß║íi tiß║┐p tß╗Ñc ─æ├║ng trß║íng th├íi; test node: kh├┤ng dt ΓåÆ kh├┤ng transition.

**C2-16 ΓÇö B╞░ß╗¢m AI ch╞░a v├áo spec**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ bß╗ò sung ─æ├║ng C3-04: bay pattern sin, m├¿o c├ích < 60px ΓåÆ bay tr├ính (85 px/s < m├¿o 120 px/s, ─æuß╗òi kß╗ïp 3ΓÇô5s), giß╗¢i hß║ín bi├¬n bß║ún ─æß╗ô, chß║ím = despawn 1 lß║ºn.

**C2-17 ΓÇö V├╣ng tß╗æi cß║únh 3 + light radius ch╞░a ─æß╗ïnh ngh─⌐a**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ tr╞░ß╗¢c K_CHOICE: v├╣ng tß╗æi = t╞░ß╗¥ng v├┤ h├¼nh; tß╗½ K_CHOICE: ─æi v├áo = K_OBEY. Light radius 90px quanh m├¿o, ├íp dß╗Ñng cß║únh 4 & 5; cß║únh 3 s├íng (chß╗ë v├╣ng tß╗æi cß╗Ñc bß╗Ö tß╗æi); cß║únh 1 G_DARK: darkness 0ΓåÆ1 trong 5s l├á overlay nß╗ün (KH├öNG light radius ΓÇö vß║½n dß╗à ─æi, chß╗ë tß╗æi bß║ºu trß╗¥i/khung). Test: darkness t─âng ─æ├║ng 0ΓåÆ1 trong 5s.

**C2-18 ΓÇö Collision resolution ch╞░a quy ─æß╗ïnh**
- **RESOLUTION: CHß║ñP NHß║¼N** ΓåÆ collision kiß╗âu slide (t├ích X/Y, tr╞░ß╗út dß╗ìc bß╗ü mß║╖t); vß║¡t cß║ún/bi├¬n/t╞░ß╗¥ng v├┤ h├¼nh ΓëÑ 8px (an to├án vß╗¢i b╞░ß╗¢c 6px/frame); knockback c┼⌐ng ├íp dß╗Ñng collision (─æß║⌐y tß╗¢i khi chß║ím t╞░ß╗¥ng, kh├┤ng xuy├¬n).

### P3 ΓÇö Nhß║╣

- **C2-19 ΓÇö AC16/AC17**: RESOLUTION: AC16 th├¬m "audio" v├áo reset; AC17: d-pad = div overlay 4 n├║t, touchstart/touchend (giß╗» = di chuyß╗ân li├¬n tß╗Ñc), c├│ touch ΓåÆ ß║⌐n hint b├án ph├¡m.
- **C2-20 ΓÇö pages.yml nh├ính**: RESOLUTION: trigger cß║ú 2 nh├ính `[master, main]` (kh├┤ng biß║┐t chß║»c nh├ính ch├¡nh).
- **C2-21 ΓÇö Fade + visual thiß║┐u**: RESOLUTION: fade 0.5s; D_HUG th├¬m heart; HAUNTED th├¬m m┼⌐i t├¬n chß╗ë cß╗¡a h├ánh lang; bubble chß╗º cß║únh 1 c├│ thß╗â bß╗ï cß║»t khi m├¿o chß║ím cß╗¡a sß╗¢m (CHß║ñP NHß║¼N).
- **C2-22 ΓÇö Audio degradation**: RESOLUTION: WebAudio kh├┤ng khß║ú dß╗Ñng ΓåÆ mute ho├án to├án, game vß║½n ch╞íi; `ctx.resume()` khi gesture/tab quay lß║íi.

## 3. ─É├ính gi├í AC16/AC17 + bß║úng sub-state
─Éß╗º vß╗ü ├╜ t╞░ß╗ƒng. Cß║ºn th├¬m 3 cß╗Öt cho bß║úng phase: `inputLocked`, zone active, timer duration ΓÇö sß║╜ bß╗ò sung v├áo tasks.md khi implement. AC16 cß║ºn case test "gß╗ìi resetGame 2 lß║ºn li├¬n tß╗Ñc kh├┤ng lß╗ùi".

## Kß║┐t luß║¡n
- [x] Cß║ºn sß╗¡a tr╞░ß╗¢c khi implement: C2-11..C2-18 (P1+P2) + C2-19..C2-22 (P3) ΓÇö **Tß║ñT Cß║ó ─É├â RESOLVE** (spec.md ─æ├ú cß║¡p nhß║¡t). Mß╗⌐c sß║╡n s├áng sau sß╗¡a: 4.5/5 ΓÇö ─æß╗º ─æiß╗üu kiß╗çn sang tasks.md.
