/** Extension entry — registers 9 commands talking to the AIOS backend.
 * vscode namespace is injected (tests stub it). */

import { AiosClient } from "./client";
import { buildPrompt, editorText, gitDiff } from "./context";

/** Subset of the vscode namespace used by the extension (matches real API shapes). */
export interface VscodeLike {
  commands: {
    registerCommand(id: string, fn: (...args: unknown[]) => unknown): unknown;
  };
  window: {
    activeTextEditor?: {
      document: { getText(range?: unknown): string };
      selection: unknown;
      edit(cb: (builder: { replace(range: unknown, text: string): void }) => unknown): Promise<unknown>;
    };
    showInformationMessage(msg: string): void;
    showWarningMessage(msg: string): void;
    showErrorMessage(msg: string): void;
    showInputBox(opts?: { prompt?: string }): Promise<string | undefined>;
  };
  workspace: {
    getConfiguration(section: string): { get<T>(key: string, def: T): T };
    workspaceFolders?: { uri: { fsPath: string } }[];
  };
}

/** Backend intents (contract TASK-017): coding | medical | system | chat(none). */
const INTENTS: Record<string, string | undefined> = {
  explain: "coding",
  fix: "coding",
  generate_test: "coding",
  review_pr: "coding",
  refactor: "coding",
  rename: "coding",
  ask_workspace: "system",
  chat_repo: "coding",
  chat: undefined,
};

export function activate(vscode: VscodeLike): void {
  const serverUrl = vscode.workspace
    .getConfiguration("aios")
    .get<string>("serverUrl", "http://127.0.0.1:8000");
  const client = new AiosClient(serverUrl);

  const getSelection = (): string | null => editorText(vscode.window.activeTextEditor);

  const run = async (intent: string, prompt?: string) => {
    try {
      const text = prompt ?? buildPrompt(intent, getSelection());
      const data = await client.callChat(text, INTENTS[intent]);
      if (intent === "fix" || intent === "generate_test") {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
          const selection = editor.selection;
          await editor.edit((builder) => builder.replace(selection, data.response));
          vscode.window.showInformationMessage(`[${data.intent}] Đã chèn kết quả vào editor`);
          return;
        }
      }
      vscode.window.showInformationMessage(`[${data.intent}] ${data.response.slice(0, 300)}`);
    } catch (err) {
      vscode.window.showErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  const runSelection = async (intent: string) => {
    if (!getSelection()) {
      vscode.window.showWarningMessage("AIOS: không có selection — hãy chọn code trước.");
      return;
    }
    await run(intent);
  };

  const askInput = async (intent: string, label: string): Promise<void> => {
    const answer = await vscode.window.showInputBox({ prompt: label });
    if (answer) await run(intent, buildPrompt(intent, null, answer));
  };

  vscode.commands.registerCommand("aios.chat", () => askInput("chat", "Chat với AIOS:"));
  vscode.commands.registerCommand("aios.explain", () => runSelection("explain"));
  vscode.commands.registerCommand("aios.fixSelection", () => runSelection("fix"));
  vscode.commands.registerCommand("aios.generateTest", () => runSelection("generate_test"));
  vscode.commands.registerCommand("aios.reviewPr", () => {
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const diff = gitDiff(cwd);
    if (diff) {
      void run("review_pr", buildPrompt("review_pr", null, diff));
    } else {
      void runSelection("review_pr");
    }
  });
  vscode.commands.registerCommand("aios.refactor", () => runSelection("refactor"));
  vscode.commands.registerCommand("aios.rename", () => runSelection("rename"));
  vscode.commands.registerCommand("aios.askWorkspace", () =>
    askInput("ask_workspace", "Hỏi về workspace:")
  );
  vscode.commands.registerCommand("aios.chatRepo", () => askInput("chat_repo", "Hỏi về repo:"));
}
