# Test — TASK-019 (M3-P6: VS Code Extension)

> Ngày chạy: 2026-08-13 | Môi trường: Node, vitest 2.1.9

## Lệnh chạy

```powershell
cd extension; npm install; npm run test    # vitest run
npm run compile                           # tsc --noEmit
npm run build                             # tsc emit → out/extension.js
```

## Kết quả

```
Test Files  2 passed (2)
     Tests  19 passed (19)   (client.test.ts 9 + extension.test.ts 10)
tsc --noEmit: clean
build: out/extension.js (+ client.js, context.js) emitted
```

## Chi tiết AC test (6/6)

| AC | Test | Kết quả |
|----|------|---------|
| AC1 | `extension.test.ts` "registers all 9 commands" | ✅ 9/9 ID khớp package.json |
| AC2 | `client.test.ts` 9 cases | ✅ success, intent body, 200+error, 400+detail, 422 array, network, trim slash, malformed, URL normalize |
| AC3 | `extension.test.ts` editorText | ✅ document.getText (Selection thật không .text) |
| AC4 | `extension.test.ts` 9-case intent + editor.edit | ✅ ask_workspace→system, chat_repo→coding, fix→editor.edit replace |
| AC5 | `npm run test` + `compile` + `build` | ✅ 19 pass + tsc clean + out/extension.js |
| AC6 | `extension.test.ts` guard selection | ✅ showWarningMessage + fetchMock not called |

## Ghi chú

- Không test extension host (cần VS Code thật) — ngoài phạm vi CI.
- Tại M3: 19 vitest pass.
