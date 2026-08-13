import { afterEach, describe, expect, it } from "vitest";
import { AiosClient } from "../client";

function mockFetchOnce(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
    )
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("AiosClient.callChat", () => {
  it("posts text and parses data", async () => {
    mockFetchOnce(200, { data: { response: "ok", intent: "coding", status: "ok" } });
    const client = new AiosClient("http://x");
    const data = await client.callChat("hello");
    expect(data.intent).toBe("coding");
  });

  it("sends intent hint when provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: { response: "r", intent: "medical", status: "ok" } }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new AiosClient("http://x");
    await client.callChat("tôi đau đầu", "medical");
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body).toEqual({ text: "tôi đau đầu", intent: "medical" });
  });

  it("throws on 200 + {error} envelope", async () => {
    mockFetchOnce(200, { error: { message: "no intent" } });
    await expect(new AiosClient("http://x").callChat("x")).rejects.toThrow("no intent");
  });

  it("throws on 400 + {detail}", async () => {
    mockFetchOnce(400, { detail: "bad" });
    await expect(new AiosClient("http://x").callChat("x")).rejects.toThrow("bad");
  });

  it("throws on 422 + {detail: [...]} (array — FastAPI validation)", async () => {
    mockFetchOnce(422, { detail: [{ loc: ["body", "text"], msg: "field required" }] });
    await expect(new AiosClient("http://x").callChat("x")).rejects.toThrow("field required");
  });

  it("throws on network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("ECONNREFUSED")));
    await expect(new AiosClient("http://x").callChat("x")).rejects.toThrow("network error");
  });

  it("normalizes trailing slash in serverUrl", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: { response: "r", intent: "coding", status: "ok" } }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);
    await new AiosClient("http://x:8000/").callChat("hello");
    expect(String(fetchMock.mock.calls[0][0])).toBe("http://x:8000/api/v1/chat");
  });

  it("throws on malformed body", async () => {
    mockFetchOnce(200, { nope: 1 });
    await expect(new AiosClient("http://x").callChat("x")).rejects.toThrow("malformed");
  });
});
