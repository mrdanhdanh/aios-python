/** Editor/workspace context helpers (vscode-agnostic where possible). */

/** Shape of the vscode.TextEditor subset we need (matches real API). */
export interface EditorLike {
  document: { getText(range?: unknown): string };
  selection: unknown;
}

/** Returns selected text or null (uses document.getText — real VS Code Selection has no `.text`). */
export function editorText(editor: EditorLike | undefined): string | null {
  if (!editor) return null;
  const text = editor.document.getText(editor.selection);
  return text && text.trim().length > 0 ? text : null;
}

/** Best-effort `git diff` of the workspace (returns null when not a git repo / no diff).
 * cwd = workspace folder path (git diff must run inside the repo). */
export function gitDiff(cwd?: string): string | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const cp = require("child_process") as {
      execSync(cmd: string, opts: { timeout: number; encoding: string; cwd?: string }): string;
    };
    const out = cp.execSync("git diff", { timeout: 5000, encoding: "utf8", cwd });
    return out.trim() ? out : null;
  } catch {
    return null;
  }
}

export function buildPrompt(intent: string, selection: string | null, extra?: string): string {
  const sel = selection ?? "";
  switch (intent) {
    case "explain":
      return `Giải thích code sau:\n${sel}`;
    case "fix":
      return `Fix lỗi trong code sau (chỉ trả code đã sửa):\n${sel}`;
    case "generate_test":
      return `Sinh unit test cho code sau (chỉ trả code test):\n${sel}`;
    case "review_pr":
      return `Review thay đổi sau, liệt kê vấn đề:\n${extra ?? sel}`;
    case "refactor":
      return `Refactor code sau (giữ nguyên hành vi):\n${sel}`;
    case "rename":
      return `Đề xuất tên định danh tốt hơn cho code sau:\n${sel}`;
    case "ask_workspace":
      return `Trả lời về workspace:\n${extra ?? sel}`;
    case "chat_repo":
      return `Phân tích repo dựa trên:\n${extra ?? sel}`;
    default:
      return extra ?? sel;
  }
}
