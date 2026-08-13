# Critique ×1 — TASK-019 (critic subagent, độc lập)

> 2026-08-13 | critic (subagent) phản biện spec + code extension. Xem chi tiết báo cáo critic.

## Vấn đề phát hiện

### Spec
- **P2**: §4 Output mơ hồ — không xác định lệnh nào chèn editor, lệnh nào show message → code chọn 1 chiều "hợp lệ" theo đọc nghĩa hẹp → **Resolve**: spec §4 tách rõ từng lệnh (fix/generateTest → replace selection; còn lại showInformationMessage) + thêm AC6.
- **P2**: AC5 chỉ test `tsc --noEmit` — `main: ./out/extension.js` không bao giờ được tạo → **Resolve**: thêm script `build` (tsc emit), AC5 yêu cầu `npm run build` tạo `out/extension.js`; exclude `src/__tests__` khỏi emit.
- **P2**: thiếu guard selection — code im lặng gửi text rỗng → **Resolve**: guard `showWarningMessage` khi không selection (AC6).
- **P3**: §6 liệt kê `context.test.ts` không tồn tại (logic context nằm trong extension.test.ts) → **Resolve**: cập nhật §6 theo file thật.
- **P3**: spec không dẫn contract TASK-017 → **Resolve**: §4 ghi rõ request/response + 3 envelope.

### Code
- **P1**: `editor.selection.text` KHÔNG tồn tại trong @types/vscode (Selection chỉ có anchor/active/isReversed — verified index.d.ts:523-604) → `getSelection()` luôn null → 5 lệnh selection-based gửi prompt rỗng → **Resolve**: dùng `editor.document.getText(editor.selection)` (context.ts `editorText`), test stub theo shape thật.
- **P2**: intent hint sai 2/9 lệnh — hard-code `intent === "chat" ? undefined : "coding"` → askWorkspace gửi `coding` (spec: system), chatRepo gửi undefined (spec: coding) → **Resolve**: INTENTS map đúng bảng §4 (ask_workspace→system, chat_repo→coding).
- **P2**: `askInput` luôn gọi `run("chat", ...)` → case `ask_workspace`/`chat_repo` trong buildPrompt là dead code → **Resolve**: askInput nhận intent, gọi đúng prompt template.
- **P2**: `aios.reviewPr` input sai (spec: git diff; code: selection thường null) → **Resolve**: `gitDiff()` (child_process execSync, timeout 5s, try/catch → null), fallback selection.
- **P2**: output không đạt spec — fix/generateTest không replace selection → **Resolve**: `editor.edit(builder.replace(selection, response))`.
- **P2**: thiếu test network-error → **Resolve**: thêm test fetch rejects → "network error".
- **P3**: 422 FastAPI trả `{detail: [...]}` (array) → ném array → **Resolve**: `typeof detail === "string" ? detail : JSON.stringify(detail)`.
- **P3**: URL concat không trim trailing slash → **Resolve**: `serverUrl.replace(/\/+$/, "")` + test.
- **P3**: extension.test.ts chỉ assert 2/9 ID → **Resolve**: assert đủ 9 ID khớp contributes.commands.

## Trạng thái: RESOLVED 13/13 (1 P1, 7 P2, 5 P3) — xác nhận bằng vitest 15/15 + tsc clean + build emit OK.
