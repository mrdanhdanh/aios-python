# TASK-080 Implementation

Các artifact thực tế của TASK-080 nằm **ngoài** thư mục này (theo thiết kế
file-based skill của AIOS). Danh sách:

## Artifacts chính
- `skills/agent-sprite-forge/` — agent skill sinh asset pixel-art
  - `manifest.json` (SkillManifest)
  - `SKILL.md` (cô đọng $generate2dsprite / $generate2dmap)
  - `references/modes.md`, `references/prompt-rules.md`
  - `agents/openai.yaml`
  - `scripts/generate2dsprite.py` (post-processor deterministic)
- `skills/pixel-game-dev/` — meta-skill tự học cô đọng
  - `manifest.json`, `SKILL.md`
  - `references/phaser-pixel-filters.md`, `references/engine-comparison.md`
- `catalog/skill-agent-sprite-forge.json` — CatalogEntry
- `catalog/skill-pixel-game-dev.json` — CatalogEntry
- `skills/README.md` — giải thích SKILLS_DIR + catalog

## Test/Validation (trong thư mục này)
- `test_validate_artifacts.py` — validate manifest + catalog (AC1/AC4/AC5)
- `make_sample.py` — sinh ảnh test nền magenta
- `sample_raw.png`, `out/` — kết quả chạy script (AC3)

## Cách chạy lại test
```powershell
backend/.venv/Scripts/python.exe aios/progress/tasks/TASK-080/test_validate_artifacts.py
backend/.venv/Scripts/python.exe aios/progress/tasks/TASK-080/make_sample.py
backend/.venv/Scripts/python.exe skills/agent-sprite-forge/scripts/generate2dsprite.py process --input sample_raw.png --rows 2 --cols 2 --output-dir out --cell-size 64 --align feet --strict-qc
```
