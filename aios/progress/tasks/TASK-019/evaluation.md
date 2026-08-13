# Evaluation — TASK-019 (VS Code Extension)

> 2026-08-13 | đối chiếu spec.md (6 AC) với kết quả thực tế.

## Kết quả kiểm chứng

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|----------|---------|------------|
| AC1 | 9 commands + activationEvents + contributes khớp | ✅ | test AC1 đọc package.json so với registered (9/9/9); `package.json` activationEvents onCommand ×9 |
| AC2 | callChat: POST đúng URL (trim slash) + 3 envelope + 422 array + network | ✅ | client.test.ts 9 test (success, intent body, 200+error, 400+detail, 422 array, network, trim slash, malformed, URL normalize) |
| AC3 | editorText qua document.getText (Selection thật không có .text) | ✅ | extension.test.ts 2 test (có text / rỗng + không editor) + trim whitespace |
| AC4 | 9 commands register + intent hint đúng bảng §4 | ✅ | test 9 case intent hint (chat không intent; ask_workspace→system; chat_repo→coding; còn lại→coding) + editor.edit replace cho fix |
| AC5 | vitest pass + compile pass + build emit out/extension.js | ✅ | **19/19 tests**, tsc --noEmit clean, `out/extension.js` tồn tại |
| AC6 | Guard selection: warning + không gọi API | ✅ | test: showWarningMessage + fetchMock `not.toHaveBeenCalled()` |

## Thống kê
- **Tests**: vitest 19/19 pass (client.test.ts 9 + extension.test.ts 10)
- **TypeScript**: `npm run compile` clean; `npm run build` emit 3 file (extension/client/context.js)
- **Phạm vi**: extension/ (package.json, tsconfig, tsconfig.build.json, vitest.config, src/ 4 file, tests 2 file, .gitignore, README)

## Critic ×2 & Review
- critique-1 (critic subagent): 13 vấn đề (1 P1 — Selection.text không tồn tại, 7 P2, 5 P3) — **RESOLVED 13/13**
- critique-2: 3 vấn đề (vscode lazy-inject, fetch global, command IDs) — **RESOLVED 3/3**
- review (reviewer subagent): APPROVED có điều kiện — 3 R2 + 7 R3 — **RESOLVED hết** (xem review.md)

## Khác biệt so với spec (đã cập nhật spec)
- spec §4: Output tách rõ từng lệnh; guard selection; contract TASK-017 tham chiếu
- spec §5: AC6 mới (guard) + AC5 thêm build emit
- Không test extension host (cần VS Code thật) — ngoài phạm vi CI, ghi chú trong spec §6

## Kết luận
**TASK-019 DONE** — 6/6 AC pass, hard gate đầy đủ (spec → critique ×2 → tasks → review → implement → test → evaluate), commit kèm.
