/** WebSocket wrapper — C1-03/C1-04: raw event dict frames, reconnect. */

export interface EventFrame {
  id: string;
  type: string;
  timestamp: string;
  source: string;
  payload: Record<string, unknown>;
}

export function connectEvents(onEvent: (frame: EventFrame) => void, onStatus?: (open: boolean) => void): () => void {
  let closed = false;
  let ws: WebSocket | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const open = () => {
    if (closed) return;
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${proto}//${location.host}/api/v1/events/ws`);
    ws.onopen = () => onStatus?.(true);
    ws.onmessage = (ev) => {
      try {
        onEvent(JSON.parse(String(ev.data)) as EventFrame);
      } catch {
        /* ignore malformed frame */
      }
    };
    ws.onclose = () => {
      onStatus?.(false);
      if (!closed) timer = setTimeout(open, 3000); // reconnect
    };
  };

  open();
  return () => {
    closed = true;
    if (timer) clearTimeout(timer);
    ws?.close();
  };
}
