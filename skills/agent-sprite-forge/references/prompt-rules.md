# generate2dsprite — Prompt Rules (cô đọng)

## Nguyên tắc chung
- Agent **tự viết prompt** thủ công. KHÔNG dùng script sinh prompt sáng tạo.
- Mọi raw image dùng built-in `image_gen`. Nền **solid `#FF00FF`**.
- CHỈ dùng code/PIL để: layout guide, postprocess, runtime display. KHÔNG vẽ art gốc.

## Containment (bắt buộc trong mỗi cell)
- Subject centered; body chiếm vùng an toàn 60–70% giữa.
- Cùng identity/scale/camera distance xuyên suốt các frame.
- Feet/bottom anchor trên cùng 1 hàng y (khi áp dụng).
- KHÔNG để limb/vũ khí/cape/dust/muzzle/FX vượt mép cell.
- Wide melee (slash arc, weapon trail) → sheet FX riêng, hoặc
  `--scale-strategy preserve --align feet` cho body tích hợp vũ khí.

## Reference handling
- Nếu có reference: make visible trước (`view_image` cho local, hoặc đã hiện trong
  context). Nêu rõ role: preserve identity/style, hay tạo animation/evolution.
- Giữ identity markers: silhouette, palette, face/eye, costume marks, accessories.
- Chỉ thay đổi action/evolution được yêu cầu; không redesign subject.

## Mixed-action guardrail
- KHÔNG yêu cầu `image_gen` sinh row hỗn tạp (row1 idle, row2 run...).
- Nếu engine cần atlas 4x4/5x5: gen grid riêng → QC riêng → assemble sau.

## Map prop pack guardrail
- Square 2x2/3x3/4x4 chỉ cho compact props (rock, shrub, barrel, crate, lamp,
  small sign, pot, debris, ornament).
- Wide/collision object (floor, platform, wall, ladder, gate, door, building,
  large tree, checkpoint, exit) → one-by-one / `1x3`/`1x4` strip / custom wide cell.
- Nếu square pack fail do edge touch → reclassify, regenerate, không nới lỏng QC.

## Layout guide (optional)
`python scripts/make_layout_guide.py --rows R --cols C --cell-width 384 --cell-height 384 --output guide.png`
Chỉ để slot count/spacing/centering; output KHÔNG vẽ box/label/border.
