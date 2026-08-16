# TASK-083 — M11-P4a/b: R5 SkillDistiller + R7 Static Deploy

> **Milestone**: M11-P4a/b (Issue #4)
> **Ngày**: 2026-08-16 | **Owner**: AIOS Orchestrator
> **Tham chiếu**: proposal M11 §R5 + §R7 + §7 (P4a/b), PLAN.md §M11

## 1. Mục tiêu

- **R5 SkillDistiller** (Ecosystem Extension, KHÔNG core): `aiagent skill distill <url>`
  — distill skill package từ repo ngoài → structure → capability extraction → synthesis →
  manifest → contract validation → registry. Phiên bản P4 thực dụng, deterministic,
  offline-first (fetch mock injectable), tránh phình scope Meta-Evolution Engine.
- **R7 Static Deploy** (optional): `aiagent deploy --static <dir>` — deploy static
  site/artifact: verify → build manifest (SHA256) → dry-run → optional push.
  Bằng chứng: `pages.yml` sửa tay (Node 20 + build + dọn node_modules) — R7 tự động hóa.

## 2. Phạm vi (IN)

### R5 — SkillDistiller (P4a)
1. `ecosystem/distiller.py`:
   - `SkillDistiller.distill(url: str, out_dir: Path, fetcher: FetchFn | None = None) -> SkillDistillReport`
   - `FetchFn` injectable — default `GitHubFetchStub` (deterministic stub trả file tree mẫu
     từ URL dạng `https://github.com/<owner>/<repo>`; không network)
   - Pipeline 7 bước deterministic: fetch tree → license check (MIT/Apache-2.0 → ok;
     thiếu license → WARN không block) → structure scan (SKILL.md, src/, tests/, manifest.json)
     → capability extraction (keywords từ file: sprite/pixel/game/canvas...) → synthesis
     (sinh `SKILL.md` + `manifest.json` — deterministic, không LLM) → contract validation
     (SkillManifest.validate_manifest) → report (distilled files, capabilities, warnings)
   - Fail-closed (INV-035): fetch fail / tree rỗng → `SkillDistillError` (không tạo file một phần)
2. CLI: `aiagent skill distill <url> [--out DIR]`
3. Registry: report có `manifest` — KHÔNG tự install (user chạy skill resolve/install sau)

### R7 — Static Deploy (P4b)
4. `ecosystem/deploy.py`:
   - `StaticDeploy.verify(dir: str) -> DeployReport` — dir tồn tại + không rỗng + index.html
     (static site) hoặc artifact non-empty; fail-closed: thiếu → BLOCKED
   - `StaticDeploy.manifest(dir: str) -> dict` — SHA256 từng file + tổng (byte-identical)
   - `StaticDeploy.deploy(dir: str, dry_run: bool = True) -> DeployReport` — dry-run mặc định:
     verify → manifest → summary; dry_run=False → publish stub (ghi deploy.json marker,
     không thật push GitHub Pages — R7 optional, deterministic)
5. CLI: `aiagent deploy --static <dir> [--apply]`

## 3. OUT of scope

- Fetch thật (git clone/network) — fetcher injectable, default stub
- LLM synthesis — deterministic template
- Auto-install skill vào SkillManager — user tự resolve/install
- Push thật GitHub Pages/S3/Netlify — marker stub + manifest (R7 optional)
- Sửa game code / CI workflow thật

## 4. Input / Output

- **Input**: skill repo URL (R5), static dir path (R7)
- **Output**: `ecosystem/distiller.py` + `ecosystem/deploy.py` + CLI 2 lệnh + tests

## 5. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm tra |
|---|----|---------------|
| AC1 | R5: `distill(github-url)` → report đủ distilled files (SKILL.md + manifest.json) + capabilities | unit test |
| AC2 | R5: license thiếu → WARN không block; MIT/Apache → OK | unit test |
| AC3 | R5: fetch fail / tree rỗng → SkillDistillError (fail-closed, không file một phần) | unit test |
| AC4 | R5: manifest sinh hợp lệ (SkillManifest.validate_manifest pass) | unit test |
| AC5 | R5: capability extraction deterministic (cùng URL → cùng capabilities) | unit test |
| AC6 | R5: CLI `aiagent skill distill <url> --out <dir>` chạy thật (stub fetch) | chạy CLI |
| AC7 | R7: `verify` — dir hợp lệ → PASS; thiếu index.html → FAIL/BLOCKED (fail-closed) | unit test |
| AC8 | R7: `manifest` — SHA256 deterministic + đủ file | unit test |
| AC9 | R7: `deploy` dry_run → không tạo file; `--apply` → tạo deploy marker | unit test |
| AC10 | R7: CLI `aiagent deploy --static <dir> [--apply]` chạy thật | chạy CLI |
| AC11 | Full suite xanh (không regression) | pytest |

## 6. Nguồn tham khảo

- Proposal M11 §R5 (SkillDistiller — Ecosystem Extension P4) + §R7 (Static Deploy optional P4)
- M8 `ecosystem/devkit.py` (template scaffold pattern), `skills/base.py` (SkillManifest)
- M10 security vendor hash pattern (TASK-082 R8)
