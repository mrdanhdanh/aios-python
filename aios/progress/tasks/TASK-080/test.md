# TASK-080 — Test

## Mục tiêu
Xác thực các artifact tạo ra đáp ứng AC1–AC6 của spec.

## Môi trường
- Python: `backend/.venv/Scripts/python.exe` (đã cài `Pillow`, `numpy`).
- Chạy từ gốc repo `AIAGENT`.

## Kịch bản test

### AC1 — manifest.json tuân thủ SkillManifest
`test_validate_artifacts.py` parse `skills/*/manifest.json`:
- `source ∈ {zip, git, pip}` → dùng `git` ✅
- `version` semver (3 số) ✅
- `capabilities`, `permissions` là list không rỗng ✅
- không có key lạ (extra=forbid) ✅
- `description` không rỗng ✅

Kết quả thực tế (chạy 2026-08-15):
```
manifest OK: manifest.json (id=agent-sprite-forge, v=1.0.0)
manifest OK: manifest.json (id=pixel-game-dev, v=1.0.0)
ALL PASS
```

### AC2 — SKILL.md có frontmatter + nội dung cô đọng
- `skills/agent-sprite-forge/SKILL.md`: frontmatter `name`/`description`, nội dung
  cô đọng `$generate2dsprite` + `$generate2dmap`, hard rules (nền #FF00FF, không
  strip 1xN, lưới nhiều dòng, tách lớp).
- `skills/pixel-game-dev/SKILL.md`: bảng chọn engine, Phaser 4 filter, công cụ vẽ,
  palette, ánh xạ Yuniebel's Cat.
Kiểm tra thủ công: file tồn tại, frontmatter hợp lệ YAML, có mục "HARD RULES".

### AC3 — script generate2dsprite.py chạy được
Tạo ảnh synthetic nền #FF00FF 256×256, 4 ô màu → chạy:
```
python skills/agent-sprite-forge/scripts/generate2dsprite.py process \
  --input sample_raw.png --rows 2 --cols 2 --output-dir out \
  --cell-size 64 --align feet --strict-qc
```
Output sinh ra:
- `sheet-transparent.png` (128×128, RGBA, **0 pixel magenta còn lại**) ✅
- `frame-00..03.png` (4 frame) ✅
- `animation.gif` ✅
- `pipeline-meta.json` (có `qc_summary`) ✅
Chroma-key đúng: magenta bị xoá, alpha trong suốt.

### AC4 — catalog JSON đúng CatalogEntry
`test_validate_artifacts.py` parse `catalog/skill-*.json`:
```
catalog OK: skill-agent-sprite-forge.json (id=agent-sprite-forge)
catalog OK: skill-pixel-game-dev.json (id=pixel-game-dev)
```
`kind=="skill"`, `id` không rỗng, `metadata` là dict ✅

### AC5 — tự động hoá validation
Script `test_validate_artifacts.py` xuất nhật ký "manifest OK / catalog OK" và
`ALL PASS`, exit code 0 khi hợp lệ, 1 khi lỗi. ✅

### AC6 — tài liệu ánh xạ vào Yuniebel's Cat
`skills/pixel-game-dev/SKILL.md` có mục "Ánh xạ vào Yuniebel's Cat" + mục tiêu
nâng cấp pixel-art cho game. ✅

## Kết luận
Tất cả AC1–AC6 PASS. Không có lỗi.
