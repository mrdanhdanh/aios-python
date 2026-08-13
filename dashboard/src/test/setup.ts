/** Test setup — C1-05: stub global WebSocket (jsdom has none). */

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  closed = false;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
  close() {
    this.closed = true;
  }
  emit(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }
  open() {
    this.onopen?.();
  }
  closeFromServer() {
    this.onclose?.();
  }
}

vi.stubGlobal("WebSocket", MockWebSocket);

export { MockWebSocket };
