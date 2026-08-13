"""AIOS API server (M3-P5) — FastAPI REST + WebSocket for Dashboard/Extension.

Infra layer (Tầng 1 — UI access): may import anything. Offline-first; chat
uses the orchestrator decision pipeline with mock model by default.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import Settings
from ..kernel.runtime_kernel import RuntimeKernel

from .routers import (
    catalog,
    chat,
    events,
    goals,
    health,
    memory,
    observability,
    prompts,
    skills,
    tools,
)

V1 = "/api/v1"


def create_app(
    settings: Settings | None = None,
    kernel: RuntimeKernel | None = None,
    registries: dict | None = None,
) -> FastAPI:
    """Build the FastAPI app. registries: {"orchestrator", "catalog",
    "assistants", "tools", "skills", "goals", "sandbox", "prompts", "models",
    "health", "conversations", "artifacts"} — None keys are auto-built."""
    settings = settings or Settings()
    kernel = kernel or RuntimeKernel.create(settings)
    regs: dict = dict(registries or {})
    from .wiring import build_registries

    regs = build_registries(settings, kernel, regs)

    app = FastAPI(title="AIOS API", version="0.1.0")
    app.state.settings = settings
    app.state.kernel = kernel
    app.state.registries = regs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=V1)
    app.include_router(events.router, prefix=V1)
    app.include_router(catalog.router, prefix=V1)
    app.include_router(goals.router, prefix=V1)
    app.include_router(skills.router, prefix=V1)
    app.include_router(tools.router, prefix=V1)
    app.include_router(memory.router, prefix=V1)
    app.include_router(prompts.router, prefix=V1)
    app.include_router(chat.router, prefix=V1)
    app.include_router(observability.router, prefix=V1)

    @app.exception_handler(ValueError)
    async def _value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "invalid_request", "message": str(exc)}},
        )

    @app.exception_handler(Exception)
    async def _generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": str(exc)}},
        )

    return app
