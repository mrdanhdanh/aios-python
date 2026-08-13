import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { App } from "../App";

function mockFetchOnce(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
    )
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("App tabs (AC2)", () => {
  it("renders 10 tab labels", () => {
    mockFetchOnce(200, { data: [] });
    render(<App />);
    for (const name of ["chat", "workflow", "events", "tools", "memory", "artifacts", "skills", "models", "prompts", "health"]) {
      expect(screen.getByTestId(`tab-${name}`)).toBeInTheDocument();
    }
  });
});

describe("ChatView (AC5)", () => {
  it("sends text and shows response", async () => {
    mockFetchOnce(200, { data: { response: "generated code", intent: "coding", status: "ok" } });
    render(<App />);
    fireEvent.click(screen.getByTestId("tab-chat"));
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
    fireEvent.click(screen.getByTestId("tab-health"));
    await waitFor(() => expect(screen.getAllByTestId("health-component")).toHaveLength(2));
    expect(screen.getByText(/0.75/)).toBeInTheDocument();
  });
});

describe("no-data states (AC8)", () => {
  it("shows empty states for workflows/skills/models", async () => {
    mockFetchOnce(200, { data: [] });
    render(<App />);
    fireEvent.click(screen.getByTestId("tab-workflow"));
    await waitFor(() => expect(screen.getByTestId("workflow-empty")).toBeInTheDocument());
    fireEvent.click(screen.getByTestId("tab-skills"));
    await waitFor(() => expect(screen.getByTestId("skills-empty")).toBeInTheDocument());
  });
});
