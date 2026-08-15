---
name: agent-sprite-forge
description: "Sinh sprite sheet & map pixel-art từ prompt. Dùng khi cần nhân vật, quái, props, spell, FX (generate2dsprite) hoặc map lớp/prop-pack/collision (generate2dmap). Script hậu-xử lý: chroma-key #FF00FF, cắt frame, export PNG trong suốt + GIF + metadata. Cô đọng từ 0x0funky/agent-sprite-forge (MIT)."
---

# Agent Sprite Forge (bản cô đọng)

Skill sinh asset 2D game-ready từ prompt. Agent lập kế hoạch → agent viết prompt →
host thực hiện `image_gen` → script Python xử lý deterministic (cleanup, cắt frame,
align, export). Không dùng script để vẽ nghệ thuật; script chỉ xử lý pixel cuối.

## Hai skill con

### `$generate2dsprite` — sprite / animation
Sinh asset tự lập: player, npc, creature, character, spell, projectile, impact,
prop, summon, fx.

**Quy tắc cốt lõi (phải nhớ):**
- Nền **solid `#FF00FF`** (magenta) cho mọi raw sheet. Script dùng màu này làm chroma-key.
- Mỗi raw sheet = MỘT action family / MỘT sequence / MỘT directional locomotion /
  MỘT prop-pack. KHÔNG gộp action không liên quan vào 1 sheet.
- **Không dùng `1x4`/`1x6`/row-strip** cho character/player/creature/npc/enemy/summon/
  animated prop (dễ drift ngang). Dùng grid đa hàng: 4 frame→`2x2`, 6→`2x3`,
  8→`2x4`, 9→`3x3`, 12→`3x4`/`4x3`, 16→`4x4`. Riêng 4-hướng walk-topdown dùng `4x4`.
- Giữ subject **centered** trong mỗi cell, body chiếm vùng an toàn 60–70% giữa,
  feet/bottom anchor cùng 1 hàng y, KHÔNG để limb/vũ khí/cape/FX vượt mép cell.
- Hero/player body attack: body-only mặc định. Slash arc, muzzle, projectile, impact
  → sheet FX riêng. Nếu vũ khí dài làm bbox thu nhỏ → `--scale-strategy preserve --align feet`.
- Wide/tall/collision-bearing object (platform, wall, gate, tree, tileset) →
  **KHÔNG** vào square prop pack; dùng one-by-one / `1x3`/`1x4` strip / custom wide cell.
- Ghi prompt đã dùng vào `<asset>.prompt.txt` (không để metadata rỗng).

**Sheet mặc định:** idle 2x2, cast 2x3, projectile 2x2, impact 2x2, walk side 2x2,
walk topdown 4x4, boss idle 3x3.

### `$generate2dmap` — map playable
Sinh map có gameplay geometry tách biệt (KHÔNG chỉ 1 ảnh baked).

**Quy tắc cốt lõi:**
- Chọn `map_mode` trước: `tile_mode`(RPG/tactical) | `scene_mode`(tower-defense/cozy) |
  `side_scroll_mode`(platformer/runner) | `grid_mode`(tactical/factory) |
  `room_chunk_mode`(roguelike) | `baked_scene_mode`(chỉ background phẳng).
- **Layer separation**: base/background chỉ chứa nền (ground, road, water, sky,
  distant scenery). KHÔNG bake props/tall-objects/doors/gates/pickups/actors vào base.
- Playable map luôn có runtime objects tách biệt: props, collision, zones, exits,
  camera bounds, scene hooks (player spawn, encounter zones).
- `side_scroll_mode`: dùng `parallax_layers` (sky/far/mid/near) + `platform_objects`
  + `precise_shapes`. Chọn 1 `stage_canvas` (vd 1536x864) và `stage_segment_count`
  (mặc định 2) TRƯỚC khi gen art. Background là scenery-only, không chứa platform.
- Visual reference handoff: make base image visible (`view_image`) rồi gen
  "dressed reference mockup" (tối đa 9 candidate object), sau đó mới gen props rời.
- Prop pack: chỉ `compact_prop` (rock, shrub, barrel, crate, lamp...) vào square
  2x2/3x3/4x4. Wide/tall/collision object → one-by-one hoặc strip.

## Workflow (sprite)
1. Infer plan (asset_type, action, view, sheet, frames, art_style).
2. Viết prompt thủ công; chọn `art_style` (pixel_art / retro_pixel / clean_hd / pixel_inspired).
3. `image_gen` raw sheet (nền #FF00FF).
4. Postprocess: `python scripts/generate2dsprite.py process --input raw.png --rows R --cols C --output-dir out --align feet [--scale-strategy preserve] [--strict-qc]`
5. QC: frame chạm mép? scale khác nhau? body height hero lệch >10–15% vs idle?
6. Trả về: `raw-sheet.png`, `raw-sheet-clean.png`, `sheet-transparent.png`, frame PNGs,
   `animation.gif`, `prompt-used.txt`, `pipeline-meta.json`.

## Workflow (map)
1. Inspect game (camera size, tile size, collision, zone format).
2. Chọn map_mode + visual_model + runtime_object_model + collision_model + engine_target.
3. Gen base foundation-only → visual reference handoff → gen props rời / tile layers.
4. Viết placement + collision + zones + scene-hooks metadata (JSON).
5. Compose flattened preview, validate.

## Script hậu-xử lý
`scripts/generate2dsprite.py` (Pillow + numpy):
- `process`: magenta cleanup → detect subject per cell → trim → align (feet/center) →
  export `sheet-transparent.png`, frame PNGs, `animation.gif`, `pipeline-meta.json`.
- Flag: `--rows --cols --cell-size --fit-scale --align {center,feet,bottom}
  --scale-strategy {fit,preserve} --component-mode {all,largest} --strict-qc`.

## Cấm (hard rules)
- KHÔNG vẽ nghệ thuật bằng code (PIL/Canvas/SVG) làm raw source.
- KHÔNG gộp action không liên quan vào 1 raw sheet.
- KHÔNG dùng square prop pack cho wide/tall/collision object.
- KHÔNG ship 1 ảnh baked làm playable map (trừ baked_scene_mode).

## Tham khảo
- Upstream: https://github.com/0x0funky/agent-sprite-forge (MIT)
- `references/modes.md`, `references/prompt-rules.md`, `scripts/generate2dsprite.py`
