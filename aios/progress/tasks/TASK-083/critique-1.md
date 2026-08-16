# TASK-083 — Critique vòng 1 (spec)

> **Critic**: AIOS Orchestrator | **Ngày**: 2026-08-16 | **Trạng thái**: resolved

## P1 — Phải sửa

### C1-01. `GitHubFetchStub` — deterministic từ URL nhưng tree trả về thế nào?
Nếu mọi URL trả cùng tree thì không phân biệt được skill khác nhau. Nếu hash URL → tree khác nhau.
→ **Resolve**: stub hash URL (sha256 → seed) → sinh tree mẫu (SKILL.md, src/, tests/, manifest.json với id từ seed, capability keywords chọn theo seed mod) — cùng URL → cùng tree; khác URL → khác skill. Deterministic + meaningful.

### C1-02. SkillManifest.validate_manifest yêu cầu gì (id/name/version/source/description...)?
Nếu synthesis sinh manifest thiếu field bắt buộc → AC4 fail. Phải đọc contract trước.
→ **Resolve**: đọc `skills/base.py::SkillManifest` fields — synthesis phải sinh đủ: id, name, version, description, source (SkillSource), dependencies=[]. Ghi vào tasks.md bước đọc contract.

### C1-03. R7 `deploy --apply` tạo deploy.json marker ở đâu? Không đụng code user?
→ **Resolve**: marker tạo trong dir target `.aios/deploy.json` (hidden) — không đụng file user; nếu `.aios/` tồn tại → merge (không ghi đè). Dry-run → không tạo gì.

## P2 — Nên sửa

### C2-01. SkillDistillReport schema (extra=forbid) — fields rõ ràng
→ **Resolve**: `distilled_files: list[str]`, `capabilities: list[str]`, `warnings: list[str]`, `manifest_path: str`, `license_status: str` (ok/warn). Pydantic.

### C2-02. CLI `skill distill` — skill subcommand đã có `list`; thêm `distill` sub-subcommand
→ **Resolve**: `skill_sub.add_parser("distill")` + arg `url` + `--out` — không xung đột.

### C2-03. R7 DeployReport — fields + status
→ **Resolve**: `dir: str`, `status: str` (ok/blocked), `files: int`, `total_bytes: int`, `total_sha256: str`, `marker: str = ""`. Pydantic extra=forbid.

## P3 — Ghi nhận

### C3-01. R5 "contract validation" = validate_manifest pass; không cần critque×2 trong distiller
→ Resolve: ghi nhận — distiller sinh manifest rồi validate qua SkillManifest; không chạy hard-gate bên trong.

## Kết luận
Spec khả thi sau resolve C1-01..03 + C2-01..03 → vòng 2.
