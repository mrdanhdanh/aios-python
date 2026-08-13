# TASK-019 — tasks.md (breakdown checklist)

> Chuỗi hard gate: spec → critique ×2 → tasks → review → implement → test → evaluate → commit

## Checklist

| # | Bước | Trạng thái | Ghi chú |
|---|------|-----------|---------|
| 1 | Spec (spec.md) | done | 6 AC ban đầu → mở rộng 6 AC sau critique-1 |
| 2 | Critique ×1 (critic subagent) | done | 13 vấn đề (1 P1, 7 P2, 5 P3) — RESOLVED |
| 3 | Critique ×2 (critic/self) | done | 3 vấn đề (C1 vscode lazy, C2 fetch, C3 command IDs) — RESOLVED |
| 4 | tasks.md | done | file này |
| 5 | Review (reviewer subagent) | todo | — |
| 6 | Implement: scaffold extension/ | done | package.json, tsconfig, vitest.config, .gitignore |
| 7 | Implement: client.ts (AiosClient.callChat) | done | 3 envelope + trim slash + 422 array |
| 8 | Implement: context.ts (editorText, gitDiff, buildPrompt 8 template) | done | dùng document.getText theo API thật |
| 9 | Implement: extension.ts (activate, 9 commands, INTENTS map, guard selection, editor.edit cho fix/generate_test) | done | — |
| 10 | Test: vitest (client 9 + extension/context 6 = 15) | done | 15/15 pass |
| 11 | Test: tsc --noEmit + tsc emit (out/extension.js) | done | cả 2 pass, __tests__ excluded |
| 12 | Evaluation (evaluation.md) | todo | — |
| 13 | Cập nhật PROGRESS.md/LOG.md + commit | todo | — |

## Quyết định thiết kế
- `vscode` namespace INJECTED (VscodeLike) thay vì import — test stub được, phù hợp hard gate.
- `editorText` dùng `document.getText(selection)` — Selection thật không có `.text`.
- INTENTS map riêng — intent hint đúng từng lệnh (không hard-code).
- gitDiff best-effort: execSync timeout 5s, lỗi → null → fallback selection.
