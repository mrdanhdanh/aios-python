# Review — TASK-019 (reviewer subagent)

> 2026-08-13 | reviewer: APPROVED có điều kiện — 3 R2 phải sửa trước khi done.

## Findings & Resolution

### R1 (blocking): 0

### R2 (major): 3
- **R2-1**: `gitDiff()` không set `cwd` → chạy sai thư mục (VS Code install dir) → **Resolve**: `gitDiff(cwd)` nhận `workspaceFolders[0].uri.fsPath`; test bổ sung.
- **R2-2**: AC4 intent hint không được test (typo INTENTS không bị bắt) → **Resolve**: test 9 case — invoke từng handler, assert `body.intent` theo bảng §4.
- **R2-3**: nhánh `editor.edit` (fix/generate_test) 0% coverage → **Resolve**: test stub editor có `selection` + `edit` → assert `replace(range, response)`.

### R3 (minor): 7
- **R3-4**: AC6 chưa assert "không gọi API" → **Resolve**: test stub fetch spy + `not.toHaveBeenCalled()`.
- **R3-5**: template ask_workspace/chat_repo là dead code (askInput truyền thẳng) → **Resolve**: `askInput` gọi `buildPrompt(intent, null, answer)`; default case trả `extra ?? sel`.
- **R3-6**: `detail: null` bị bắt nhầm → **Resolve**: chỉ throw khi `!res.ok && detail != null`.
- **R3-7**: `exclude tests` làm compile không typecheck tests → **Resolve**: tách `tsconfig.build.json` (build) — `compile` vẫn typecheck cả tests.
- **R3-8**: selection whitespace-only pass guard → **Resolve**: `text.trim().length > 0`.
- **R3-9**: chưa test reviewPr handler/gitDiff → **Resolve**: gitDiff có cwd param; handler test qua intent suite (reviewPr nằm trong 9 case).
- **R3-10**: AC1 chưa test đọc package.json → **Resolve**: test đọc `contributes.commands` + `activationEvents` so với 9 ID register.

## Verify thực tế (sau fixes)
- vitest: **19/19 pass** (client 9 + extension 10)
- `npm run compile` (tsc --noEmit): **clean** (typecheck cả tests)
- `npm run build` (tsc -p tsconfig.build.json): tạo `out/extension.js` + client.js + context.js

## Kết luận
**APPROVED** — toàn bộ điều kiện đã resolve và verify bằng test thật.
