import { useEffect, useState } from "react";
import { get } from "../api";
import { connectEvents, type EventFrame } from "../ws";

export function EventTimeline() {
  const [events, setEvents] = useState<EventFrame[]>([]);
  const [live, setLive] = useState(false);

  useEffect(() => {
    get<EventFrame[]>("/events").then(setEvents).catch(() => undefined);
    const stop = connectEvents((frame) => {
      setEvents((prev) => [frame, ...prev].slice(0, 100));
    }, setLive);
    return stop;
  }, []);

  return (
    <div>
      <p>
        Live: <strong className={live ? "ok" : "fail"}>{live ? "connected" : "disconnected"}</strong>
      </p>
      {events.length === 0 && <p data-testid="events-empty">No events</p>}
      {events.map((e) => (
        <div key={e.id} className="card" data-testid="event-row">
          <code>{e.type}</code> — {e.timestamp} <small>({e.source})</small>
          <pre>{JSON.stringify(e.payload)}</pre>
        </div>
      ))}
    </div>
  );
}
