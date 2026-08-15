# Skills (SKILLS_DIR)

Thư mục này là `SKILLS_DIR` chuẩn của AIOS (theo `backend/tests/test_architecture.py`).
Chứa các **skill package** ở dạng file-based (agent-skill / meta-skill), mỗi skill là
một thư mục có `SKILL.md` + `manifest.json` + (tùy chọn) `references/`, `scripts/`,
`agents/`.

## Danh sách skill

### `agent-sprite-forge/` — Agent skill (sinh asset pixel-art)
- Cô đọng từ [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) (MIT).
- `$generate2dsprite` (nhân vật, quái, spell, FX) + `$generate2dmap` (map lớp, prop-pack, collision).
- Script `scripts/generate2dsprite.py` (Pillow): chroma-key `#FF00FF`, cắt frame lưới,
  export PNG trong suốt + GIF + `pipeline-meta.json`.
- `manifest.json` tuân thủ `SkillManifest` (backend/src/aios_core/skills/base.py):
  `source=git`, `capabilities`/`permissions` không rỗng.

### `pixel-game-dev/` — Meta-skill (tự học cô đọng)
- Tài liệu cô đọng làm web game / pixel game: Phaser 4 (filter pixel-art Blocky/Pixelate/
  GradientMap/Quantize), KAPLAY, PixiJS, công cụ vẽ (Piskel/Pixelorama/Aseprite),
  palette (LOSPEC/mulfok32).
- Ánh xạ sẵn vào dự án **Yuniebel's Cat**.
- `references/phaser-pixel-filters.md`, `references/engine-comparison.md`.

## Catalog
Metadata của mỗi skill được nhân đôi vào `catalog/<id>.json` (CatalogEntry:
`kind="skill"`, `id`, `metadata`) để `SystemCatalog` có thể index. Lưu ý: root `catalog/`
là **artifact registry JSON**; code module catalog nằm ở
`backend/src/aios_core/catalog/`.

## Đăng ký vào runtime (sau này)
Khi AIOS Runtime sẵn sàng, đăng ký skill vào `skills.db` qua SkillManager
(`backend/src/aios_core/skills/manager.py`), ví dụ CLI: `aiagent skill register
--manifest skills/<id>/manifest.json`. (Ngoài phạm vi TASK-080.)
