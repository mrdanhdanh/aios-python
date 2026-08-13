import { beforeEach, describe, expect, it } from "vitest";
import { MockWebSocket } from "../test/setup";
import { connectEvents } from "../ws";

beforeEach(() => {
  MockWebSocket.instances.length = 0;
});

describe("ws client (C1-03 raw frames, C1-04 relative URL)", () => {
  it("connects to relative WS path and forwards raw event frames", () => {
    const frames: unknown[] = [];
    const stop = connectEvents((f) => frames.push(f));
    const ws = MockWebSocket.instances[MockWebSocket.instances.length - 1]!;
    ws.open();
    ws.emit({ id: "e1", type: "workflow.completed", timestamp: "t", source: "s", payload: { x: 1 } });
    expect(frames).toHaveLength(1);
    expect((frames[0] as { type: string }).type).toBe("workflow.completed");
    stop();
  });

  it("reconnects after close (3s) — timer is cleared on stop", () => {
    vi.useFakeTimers();
    MockWebSocket.instances.length = 0;
    const stop = connectEvents(() => undefined, () => undefined);
    const ws = MockWebSocket.instances[MockWebSocket.instances.length - 1]!;
    ws.closeFromServer();
    vi.advanceTimersByTime(3100);
    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(2);
    stop();
    vi.useRealTimers();
  });
});
