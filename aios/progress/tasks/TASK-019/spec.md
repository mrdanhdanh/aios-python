# TASK-019 — M3-P6: VS Code Extension (TypeScript, 9 lệnh)

**Metadata**: TASK-019 | M3/P6 | 2026-08-13 | draft | AIOS Orchestrator
**Module đích**: `extension/` (VS Code extension TS)

## 1. Mục tiêu
Extension VS Code 9 lệnh theo PLAN P6: Chat, Explain, Fix selection, Generate test, Review PR, Refactor, Rename, Ask Workspace, Chat với repo. Mọi lệnh gọi backend AIOS qua `POST /api/v1/chat` (TASK-017) — offline-first với mock model; server URL configurable (`aios.serverUrl` default `http://127.0.0.1:8000`).

## 2. Phạm vi
**In**: `extension/` — package.json (vscode:^1.85, activationEvents commands, contributes.commands 9 lệnh), src/extension.ts (activate + register 9 commands), src/client.ts (aiosClient: callChat(text, intentHint) → fetch POST /api/v1/chat), src/context.ts (lấy selection/workspace context), test (vitest — client + context logic; extension host không test trong CI).
**Out**: publish/VSIX, settings UI phức tạp, auth, tree views, webview.

## 3. Kiến trúc
```
extension/
├── package.json          # contributes 9 commands, activationEvents
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── extension.ts      # activate(): register 9 commands
│   ├── client.ts         # callChat(text, intent?) → {response, intent, status} — fetch, error handling (3 envelope)
│   ├── context.ts        # selectionText(editor), workspaceSummary()
│   └── __tests__/client.test.ts, context.test.ts
```

## 4. 9 lệnh (mỗi lệnh: thu thập input → callChat với intent hint → output)
| Command | Input | intent hint | Output |
|---|---|---|---|
| aios.chat | prompt (inputBox) | none (orchestrator) | showInformationMessage |
| aios.explain | selection | coding | showInformationMessage |
| aios.fixSelection | selection | coding | **replace selection trong editor** (editor.edit) |
| aios.generateTest | selection | coding | **replace selection trong editor** (editor.edit) |
| aios.reviewPr | git diff (child_process) → fallback selection | coding | showInformationMessage |
| aios.refactor | selection | coding | showInformationMessage |
| aios.rename | selection | coding | showInformationMessage |
| aios.askWorkspace | prompt (inputBox) | system | showInformationMessage |
| aios.chatRepo | prompt (inputBox) | coding | showInformationMessage |

Quy tắc bổ sung:
- **Guard selection**: lệnh selection-based (explain/fix/generateTest/refactor/rename) khi KHÔNG có selection → `showWarningMessage`, KHÔNG gọi API.
- **Lấy selection đúng API thật**: `editor.document.getText(editor.selection)` — `Selection` trong @types/vscode KHÔNG có property `.text`.
- **Contract kế thừa TASK-017**: request `{text, intent?}` → response `{data: {response, intent, status}}`; 3 envelope lỗi: `200+{error.message}`, `4xx+{detail}`, network.

## 5. AC
- AC1: package.json có 9 commands + activationEvents + contributes.commands khớp nhau
- AC2: client.ts callChat — POST đúng URL (trim trailing slash)/body; parse {data}; xử lý 3 envelope lỗi (200+error, 4xx+detail **kể cả detail là array 422**, network)
- AC3: context.ts editorText — editor có selection → text (qua document.getText); không → null
- AC4: 9 commands đều register (mock vscode namespace — test activate với stub) + intent hint đúng bảng §4 (ask_workspace→system, chat_repo→coding, chat→none)
- AC5: vitest pass + `npm run compile` (tsc --noEmit) pass + `npm run build` (tsc emit) tạo `out/extension.js` (main trong package.json)
- AC6: guard selection — lệnh selection-based không selection → warning, không gọi API

## 6. Test
- client.test.ts: mock fetch — success + 200+error + 400+detail + 422 array + network fail + trim slash
- extension.test.ts: stub vscode (registerCommand capture handlers) → activate → đúng 9 ID + guard warning; editorText; buildPrompt (gồm review_pr extra)
- Không test extension host (cần VS Code thật) — ngoài phạm vi CI
