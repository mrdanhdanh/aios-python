# TASK-080 — Tự học & cô đọng skill/repo web game + pixel game, tạo skill manifest & catalog entry

> Ngày: 2026-08-15 | Owner: AIOS Orchestrator | Milestone: M2 (Tools/Skills) — bổ sung skills cho web game / pixel game

## 1. Mục tiêu
- **Tự học** nội dung thực tế của các repo/skill web game & pixel game đã khảo sát trên GitHub (Phaser 4, KAPLAY, PixiJS, `agent-sprite-forge`, Piskel/Pixelorama, LOSPEC palette).
- **Cô đọng lại** thành tài liệu kỹ thuật súc tích, tiếng Việt, đưa vào repo (không chỉ nằm trong chat).
- **Tạo skill manifest** cho `agent-sprite-forge` (bê SKILL.md + scripts + references + agents) vào `skills/` (SKILLS_DIR chuẩn của framework).
- **Tạo meta-skill** `pixel-game-dev` chứa bản cô đọng kiến thức các engine/tool (kết quả "tự học").
- **Viết `catalog/` entry** (CatalogEntry: kind=`skill`, id, metadata) cho mỗi skill để SystemCatalog có thể index.

## 2. Phạm vi (in-scope)
- Tạo `skills/agent-sprite-forge/` (SKILL.md cô đọng, manifest.json, references/, scripts/generate2dsprite.py, agents/openai.yaml).
- Tạo `skills/pixel-game-dev/` (SKILL.md cô đọng tổng hợp, manifest.json, references/).
- Tạo `catalog/skill-agent-sprite-forge.json`, `catalog/skill-pixel-game-dev.json`.
- Script Python hậu-xử lý sprite (chroma-key `#FF00FF` → transparent, cắt frame lưới, export PNG trong suốt + GIF + `pipeline-meta.json`), dependency: Pillow/numpy.
- Test validate manifest + catalog (parse JSON, kiểm tra schema).

## 3. Ngoài phạm vi (out-of-scope)
- Không migrate game `games/yuniebel/` sang Phaser/KAPLAY (đây là TASK khác).
- Không cài đặt/đăng ký vào `skills.db` qua SkillManager (chỉ chuẩn bị artifact file-based; đăng ký sau khi có runtime sẵn sàng).
- Không viết lại engine.

## 4. Input
- Nội dung gốc đã fetch: `agent-sprite-forge` SKILL.md (`$generate2dsprite`, `$generate2dmap`), Phaser 4 `filters-and-postfx` SKILL.md, mô tả repo Phaser/KAPLAY/PixiJS/Piskel/Pixelorama/LOSPEC.
- Schema chuẩn: `SkillManifest` (backend/src/aios_core/skills/base.py) + `CatalogEntry` (backend/src/aios_core/catalog/catalog.py).

## 5. Output (artifact)
- `skills/agent-sprite-forge/{SKILL.md,manifest.json,references/modes.md,references/prompt-rules.md,scripts/generate2dsprite.py,agents/openai.yaml}`
- `skills/pixel-game-dev/{SKILL.md,manifest.json,references/phaser-pixel-filters.md,references/engine-comparison.md}`
- `catalog/skill-agent-sprite-forge.json`, `catalog/skill-pixel-game-dev.json`
- `aios/progress/tasks/TASK-080/implementation/README.md` (pointer)

## 6. Tiêu chí chấp nhận (Acceptance Criteria)
- **AC1** — `manifest.json` của mỗi skill hợp lệ theo `SkillManifest`: có `id`, `name`, `version` (semver), `source` ∈ {zip,git,pip}, `description`, `dependencies`, `capabilities`, `permissions` (list không rỗng cho capabilities/permissions); `extra=forbid`.
- **AC2** — Mỗi skill có `SKILL.md` với frontmatter `--- name / description ---` và nội dung cô đọng (≤ ~200 dòng).
- **AC3** — `scripts/generate2dsprite.py process` chạy được với Pillow: nhận ảnh nền `#FF00FF`, cắt lưới `rows×cols`, xuất `sheet-transparent.png` + các frame PNG + `animation.gif` + `pipeline-meta.json`.
- **AC4** — `catalog/*.json` đúng shape `CatalogEntry`: `{ "kind": "skill", "id": "<id>", "metadata": { ... } }`.
- **AC5** — Test validate (parse JSON + schema) **PASS** (chạy bằng `backend/.venv/Scripts/python`).
- **AC6** — Commit toàn bộ artifact, working tree sạch khi kết thúc.

## 7. Rủi ro / ghi chú
- Script hậu-xử lý là bản cô đọng (deterministic processor), không thay thế bộ scripts gốc của upstream; đủ để minh họa pipeline và test AC3.
- `source=git` cho cả 2 skill (vendored locally; metadata.note ghi rõ nguồn gốc).
