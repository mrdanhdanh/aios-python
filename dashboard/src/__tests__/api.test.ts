import { describe, expect, it } from "vitest";
import { get, post } from "../api";

function mockFetchOnce(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
    )
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("api client (C1-02 — 3 error envelopes)", () => {
  it("parses {data} on success", async () => {
    mockFetchOnce(200, { data: { ok: true } });
    await expect(get("/health")).resolves.toEqual({ ok: true });
  });

  it("throws on 200 + {error} (chat no_intent)", async () => {
    mockFetchOnce(200, { error: { code: "no_intent", message: "could not determine intent" } });
    await expect(get("/x")).rejects.toThrow("could not determine intent");
  });

  it("throws on 400 + {detail} (HTTPException)", async () => {
    mockFetchOnce(400, { detail: "goal not found" });
    await expect(get("/goals/nope")).rejects.toThrow("goal not found");
  });

  it("throws on 500 + {error}", async () => {
    mockFetchOnce(500, { error: { code: "internal_error", message: "boom" } });
    await expect(get("/x")).rejects.toThrow("boom");
  });

  it("throws on malformed success body", async () => {
    mockFetchOnce(200, { nope: 1 });
    await expect(get("/x")).rejects.toThrow("malformed response");
  });

  it("posts JSON body", async () => {
    mockFetchOnce(200, { data: { response: "hi", intent: "chat", status: "ok" } });
    await expect(post("/chat", { text: "hi" })).resolves.toMatchObject({ intent: "chat" });
  });
});
