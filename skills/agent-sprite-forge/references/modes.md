# generate2dsprite — Modes (cô đọng)

## asset_type
`player` | `npc` | `creature` | `character` | `spell` | `projectile` |
`impact` | `prop` | `summon` | `fx`

## action
`single` | `idle` | `cast` | `attack` | `shoot` | `jump` | `hurt` | `combat` |
`walk` | `run` | `hover` | `charge` | `projectile` | `impact` | `explode` | `death`

## view
`topdown` | `side` | `3/4`

## sheet (grid)
`auto` | `2x2` | `2x3` | `2x4` | `3x3` | `3x4` | `4x4` | `5x5` |
`custom_grid` | `strip_1x3` | `strip_1x4`

Quy tắc: animated body → multi-row grid (4f→2x2, 6f→2x3, 8f→2x4, 9f→3x3,
12f→3x4, 16f→4x4). 4-hướng walk topdown → 4x4 (canonical directional).

## bundle
`single_asset` | `unit_bundle` | `spell_bundle` | `combat_bundle` |
`line_bundle` | `hero_action_bundle` | `engine_atlas`

- `hero_action_bundle`: mỗi action = 1 raw grid sheet; xử lý QC riêng; mới assemble
  atlas sau cùng (deterministic).
- spell_bundle: caster cast + projectile loop + impact burst (3 sheet riêng).

## art_style
`pixel_art` | `retro_pixel` (16-bit/JRPG) | `clean_hd` (hand-painted HD) |
`pixel_inspired` (pixel gần, không chunky) | `map_style` | `project-native`

## anchor / scale
- `anchor`: `center` | `bottom` | `feet`
- `scale_strategy`: `fit` (compact body/FX) | `preserve` (giữ nguyên raw-cell scale,
  translate đến shared anchor — dùng cho hero melee tích hợp vũ khí dài)
- `margin`: `tight` | `normal` | `safe`
- `component_mode`: `largest` (hero body) | `all` (FX/projectile/impact tách rời)

## Examples
- hero 4 hướng → `player` + `player_sheet` (4x4)
- hero side idle/run/shoot/jump → `player` + `hero_action_bundle`
- boss idle loop → `creature` + `idle` + `3x3`
- wizard orb → `spell_bundle` (cast + projectile + impact)
