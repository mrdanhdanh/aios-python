"""uvicorn runner for `aiagent serve` (C3-04 lazy import)."""

from __future__ import annotations


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    from .app import create_app

    uvicorn.run(create_app(), host=host, port=port, log_level="info")
