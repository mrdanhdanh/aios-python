"""System Doctor — deterministic health reporting (TASK-013).

Probe contract: ``Callable[[], dict]`` returning ``{component: {"ok": bool,
"detail": str}}``. Entries missing ``ok`` count as failed (worst-wins).
"""

from __future__ import annotations

from collections.abc import Callable

from .base import Assistant, AssistantRequest, AssistantResponse, EventSink

FIX_HINTS: dict[str, str] = {
    "models": "check model config and connectivity",
    "docker": "start docker daemon",
    "sandbox": "check sandbox pool status",
    "database": "check disk space and db connection",
}
GENERIC_HINT = "check component logs and configuration"

Probe = Callable[[], dict]


def _default_probe() -> dict:
    return {"aios_core": {"ok": True, "detail": "default probe"}}


class SystemDoctor(Assistant):
    name = "system_doctor"
    intent = "system"
    description = "System status reporter: health probe → score → suggestions (deterministic)"

    def __init__(self, health_probe: Probe | None = None, event_sink: EventSink | None = None) -> None:
        super().__init__(event_sink=event_sink)
        self._probe = health_probe or _default_probe

    def _process(self, request: AssistantRequest) -> AssistantResponse:
        raw = self._probe()
        ok_components: list[str] = []
        failed: list[dict] = []  # {"name", "detail"}
        for name, entry in raw.items():
            if not isinstance(entry, dict) or "ok" not in entry:
                failed.append({"name": name, "detail": "invalid probe entry"})
                continue
            if entry["ok"]:
                ok_components.append(name)
            else:
                failed.append({"name": name, "detail": str(entry.get("detail", ""))})

        total = len(raw)
        ok_count = len(ok_components)
        score = (ok_count / total) if total else 0.0

        suggestions = [
            f"{f['name']}: {FIX_HINTS.get(f['name'], GENERIC_HINT)}"
            for f in failed
        ]

        text = f"Health: {ok_count}/{total} healthy ({score * 100:.0f}%)"
        if ok_components:
            text += f"\nOK: {', '.join(ok_components)}"
        if failed:
            text += "\nFAILED: " + "; ".join(
                f"{f['name']} ({f['detail'] or 'no detail'})" for f in failed
            )
            text += "\nSuggestions: " + "; ".join(suggestions)

        return AssistantResponse(
            text=text,
            intent=self.intent,
            metadata={
                "health_score": score,
                "ok_components": ok_components,
                "failed_components": [f["name"] for f in failed],
                "suggestions": suggestions,
            },
        )
