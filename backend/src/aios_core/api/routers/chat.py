"""Chat router (AC11) — orchestrator → intent → assistant (C1-03/C2-03)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from ...agents import AssistantRequest

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    intent: str | None = None  # optional hint — resolves directly (C2-03)


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response: str
    intent: str
    status: str


@router.post("/chat")
def chat(body: ChatRequest, request: Request) -> dict:
    regs = request.app.state.registries
    text = body.text.strip()
    if not text:
        return {"error": {"code": "invalid_request", "message": "text must not be empty"}}

    intent = body.intent
    if intent is None:
        # Step 1: orchestrator decision pipeline → intent (offline-first).
        result = regs["orchestrator"].handle(text)
        intent = result.intent if hasattr(result, "intent") else None
        if not intent:
            return {"error": {"code": "no_intent", "message": "could not determine intent"}}

    # Step 2: resolve assistant via registry (Control Plane mapping).
    assistant = regs["assistants"].resolve_by_intent(intent)
    if assistant is None:
        return {"error": {"code": "no_assistant", "message": f"no assistant for intent {intent!r}"}}

    response = assistant.handle(AssistantRequest(text=text, session_id="api"))
    if response.status == "error":
        return {"error": {"code": "assistant_error", "message": response.text}}
    return {"data": ChatResponse(response=response.text, intent=response.intent, status="ok")}
