import { afterEach, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { buildPrompt, editorText } from "../context";
import { activate } from "../extension";

const ALL_COMMAND_IDS = [
  "aios.chat",
  "aios.explain",
  "aios.fixSelection",
  "aios.generateTest",
  "aios.reviewPr",
  "aios.refactor",
  "aios.rename",
  "aios.askWorkspace",
  "aios.chatRepo",
];

/** Backend intents per spec §4 (chat = no intent field). */
const EXPECTED_INTENTS: Record<string, string | undefined> = {
  "aios.chat": undefined,
  "aios.explain": "coding",
  "aios.fixSelection": "coding",
  "aios.generateTest": "coding",
  "aios.reviewPr": "coding",
  "aios.refactor": "coding",
  "aios.rename": "coding",
  "aios.askWorkspace": "system",
  "aios.chatRepo": "coding",
};

afterEach(() => vi.unstubAllGlobals());

describe("editorText", () => {
  it("returns text when selection present", () => {
    const editor = {
      document: { getText: () => "const x = 1" },
      selection: {},
    };
    expect(editorText(editor as never)).toBe("const x = 1");
  });
  it("returns null when empty or no editor", () => {
    const editor = { document: { getText: () => "" }, selection: {} };
    expect(editorText(editor as never)).toBeNull();
    expect(editorText(undefined)).toBeNull();
  });
});

describe("buildPrompt", () => {
  it("builds explain prompt", () => {
    expect(buildPrompt("explain", "def f(): pass")).toContain("def f(): pass");
  });
  it("builds fix prompt", () => {
    expect(buildPrompt("fix", "x =")).toContain("Fix lỗi");
  });
  it("builds review_pr prompt from git diff extra", () => {
    expect(buildPrompt("review_pr", null, "diff --git a/x.py")).toContain("diff --git a/x.py");
  });
});

describe("extension activation (9 commands)", () => {
  interface VscodeStub {
    commands: { registerCommand: (id: string, fn: () => void) => void };
    window: {
      activeTextEditor: unknown;
      showInformationMessage: (m: string) => void;
      showWarningMessage: (m: string) => void;
      showErrorMessage: (m: string) => void;
      showInputBox: () => Promise<string | undefined>;
    };
    workspace: { getConfiguration: () => { get: <T>(_k: string, d: T) => T } };
  }

  function makeVscode() {
    const handlers = new Map<string, () => void>();
    const messages: string[] = [];
    const vscode: VscodeStub = {
      commands: {
        registerCommand: (id, fn) => {
          handlers.set(id, fn);
        },
      },
      window: {
        activeTextEditor: undefined,
        showInformationMessage: (m) => messages.push(m),
        showWarningMessage: (m) => messages.push(m),
        showErrorMessage: (m) => messages.push(m),
        showInputBox: async () => undefined,
      },
      workspace: { getConfiguration: () => ({ get: <T>(_k: string, d: T) => d }) },
    };
    (activate as unknown as (v: unknown) => void)(vscode);
    return { vscode, handlers, messages };
  }

  it("registers all 9 commands", () => {
    const { handlers } = makeVscode();
    expect([...handlers.keys()]).toEqual(ALL_COMMAND_IDS);
  });

  it("warns when selection-based command runs without selection", async () => {
    const { handlers, messages } = makeVscode();
    await handlers.get("aios.explain")!();
    expect(messages.some((m) => m.includes("không có selection"))).toBe(true);
  });

  it("AC6: does not call the API when selection is missing", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const { handlers } = makeVscode();
    await handlers.get("aios.explain")!();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("AC4: sends correct intent hint per command (9 cases)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ data: { response: "r", intent: "coding", status: "ok" } }),
        { status: 200 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);
    for (const id of ALL_COMMAND_IDS) {
      const editor = {
        document: { getText: () => "const x = 1" },
        selection: {},
      };
      const { vscode, handlers } = makeVscode();
      vscode.window.activeTextEditor = editor as never;
      vscode.window.showInputBox = async () => "const x = 1";
      await handlers.get(id)!();
      const calls = fetchMock.mock.calls;
      const body = JSON.parse(calls[calls.length - 1][1].body as string);
      if (EXPECTED_INTENTS[id] === undefined) {
        expect(body, `command ${id}`).not.toHaveProperty("intent");
      } else {
        expect(body.intent, `command ${id}`).toBe(EXPECTED_INTENTS[id]);
      }
    }
  });

  it("AC4 fix: replaces selection in editor via editor.edit", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ data: { response: "FIXED CODE", intent: "coding", status: "ok" } }),
        { status: 200 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);
    const replaced: Array<{ range: unknown; text: string }> = [];
    const { vscode, handlers } = makeVscode();
    vscode.window.activeTextEditor = {
      document: { getText: () => "buggy code" },
      selection: { sel: 1 },
      edit: async (cb: (b: { replace: (r: unknown, t: string) => void }) => void) => {
        cb({ replace: (r, t) => replaced.push({ range: r, text: t }) });
      },
    } as never;
    await handlers.get("aios.fixSelection")!();
    expect(replaced).toHaveLength(1);
    expect(replaced[0].text).toBe("FIXED CODE");
    expect(replaced[0].range).toEqual({ sel: 1 });
  });

  it("AC1: package.json contributes.commands matches registered IDs", () => {
    const pkg = JSON.parse(readFileSync(join(__dirname, "..", "..", "package.json"), "utf8"));
    const contributed = pkg.contributes.commands.map((c: { command: string }) => c.command);
    expect(contributed).toEqual(ALL_COMMAND_IDS);
    expect(pkg.activationEvents).toEqual(ALL_COMMAND_IDS.map((id) => `onCommand:${id}`));
  });
});

