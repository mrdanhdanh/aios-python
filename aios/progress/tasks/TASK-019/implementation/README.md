# Implementation — TASK-019 (M3-P6: VS Code Extension)

> Pointer tới code thật trong repo (git-tracked). Commit: `298e4bb`.

## Cấu trúc đã implement

```
extension/
├── package.json            # 9 commands + activationEvents + contributes.commands + config aios.serverUrl
├── tsconfig.json
├── tsconfig.build.json     # tách build emit
├── vitest.config.ts
├── src/
│   ├── extension.ts        # activate(vscode) — 9 commands + INTENTS map + selection guard + editor.edit
│   ├── client.ts           # AiosClient.callChat — 3 envelope + 422 array + trim slash
│   ├── context.ts          # editorText (document.getText), gitDiff(cwd), buildPrompt 8 template
│   └── __tests__/
│       ├── client.test.ts  # 9 tests
│       └── extension.test.ts # 10 tests
└── out/                    # build emit (extension.js, client.js, context.js)
```

## 9 lệnh (khớp PLAN P6)

| Command | intent hint | Output |
|---------|-------------|--------|
| aios.chat | none | showInformationMessage |
| aios.explain | coding | showInformationMessage |
| aios.fixSelection | coding | editor.edit replace |
| aios.generateTest | coding | editor.edit replace |
| aios.reviewPr | coding | showInformationMessage (git diff hoặc selection) |
| aios.refactor | coding | showInformationMessage |
| aios.rename | coding | showInformationMessage |
| aios.askWorkspace | system | showInformationMessage |
| aios.chatRepo | coding | showInformationMessage |

## Tiêu chí đạt

- vitest **19/19 pass**, `tsc --noEmit` clean, `out/extension.js` emitted.
- 6/6 AC (xem `evaluation.md`).
- Không vi phạm INV-006 (chỉ `fetch("/api/v1/chat")` qua HTTP).
