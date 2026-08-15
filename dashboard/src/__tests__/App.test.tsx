import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { App } from "../App";

function mockFetchOnce(status: number, body: unknown) {
  // Response mới MỖI lần gọi (body JSON chỉ consume 1 lần)
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
      )
    )
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("App tabs (M10-F7 — 11 tabs)", () => {
  it("renders 11 tab labels", () => {
    mockFetchOnce(200, { data: [] });
    render(<App />);
    for (const name of ["overview", "operations", "autonomy", "agents", "workflows", "knowledge", "memory", "harness", "enterprise", "ecosystem", "system"]) {
      expect(screen.getByTestId(`tab-${name}`)).toBeInTheDocument();
    }
  });

  it("Overview + ExecutionTimeline render from mocked data", async () => {
    mockFetchOnce(200, {
      data: {
        health_score: 94,
        slo_release_ready: true,
        security_blocking: false,
        contract_breaking: 0,
        contract_warnings: 2,
      },
    });
    render(<App />);
    fireEvent.click(screen.getByTestId("tab-overview"));
    await waitFor(() => expect(screen.getByTestId("overview")).toBeInTheDocument());
    expect(screen.getByTestId("overview-slo")).toHaveTextContent("READY");
    expect(screen.getByTestId("overview-contract")).toHaveTextContent("clean");

    mockFetchOnce(200, {
      data: [
        { seq: 0, type: "plan", label: "plan:p1", execution_id: "e1", ts: "" },
        { seq: 1, type: "tool", label: "tool:python", execution_id: "e1", ts: "" },
      ],
    });
    fireEvent.click(screen.getByTestId("tab-autonomy"));
    await waitFor(() => expect(screen.getByTestId("execution-timeline")).toBeInTheDocument());
    expect(screen.getAllByTestId("timeline-step")).toHaveLength(2);
  });
});

describe("ChatView (AC5)", () => {
  it("sends text and shows response", async () => {
    mockFetchOnce(200, { data: { response: "generated code", intent: "coding", status: "ok" } });
    render(<App />);
    fireEvent.click(screen.getByTestId("tab-agents"));
    fireEvent.change(screen.getByTestId("chat-input"), { target: { value: "generate api" } });
    fireEvent.click(screen.getByTestId("chat-send"));
    await waitFor(() => expect(screen.getByTestId("chat-result")).toHaveTextContent("generated code"));
  });
});

describe("HealthView (AC7)", () => {
  it("renders score + components", async () => {
    mockFetchOnce(200, {
      data: {
        health_score: 0.75,
        components: [
          { name: "kernel", ok: true, status: "healthy", detail: "ok" },
          { name: "models", ok: false, status: "unhealthy", detail: "down" },
        ],
      },
    });
    render(<App />);
    fireEvent.click(screen.getByTestId("tab-harness"));
    await waitFor(() => expect(screen.getAllByTestId("health-component")).toHaveLength(2));
    expect(screen.getByText(/0.75/)).toBeInTheDocument();
  });
});

describe("no-data states (AC8)", () => {
  it("shows empty states for workflows/skills/models", async () => {
    mockFetchOnce(200, { data: [] });
    render(<App />);
    fireEvent.click(screen.getByTestId("tab-workflows"));
    await waitFor(() => expect(screen.getByTestId("workflow-empty")).toBeInTheDocument());
    fireEvent.click(screen.getByTestId("tab-ecosystem"));
    await waitFor(() => expect(screen.getByTestId("skills-empty")).toBeInTheDocument());
  });
});
