"""Creative workflows mặc định — R6 (M11-P3b, TASK-082).

Hai workflow creative v1 (definition đơn giản, MockCompiler compile được):
  - creative/game_scaffold    — scaffold webgame (Phaser/canvas)
  - creative/sprite_generate  — generate sprite/pixel art asset
"""

from __future__ import annotations

from typing import Any

from ..workflow.definition import WorkflowDefinition

_GAME_SCAFFOLD: dict[str, Any] = {
    "name": "creative/game_scaffold",
    "version": "1.0.0",
    "description": "Scaffold a creative/game project (Phaser/canvas) — R6 M11",
    "nodes": [
        {
            "id": "scaffold",
            "type": "task",
            "name": "Scaffold game project",
            "agent": "general",
            "capabilities": ["asset:sprite"],
            "timeout_s": 120.0,
        },
    ],
    "retries": 0,
    "timeout_s": 300.0,
    "permissions": ["filesystem"],
    "metadata": {"domain": "creative", "m11": "R6"},
}

_SPRITE_GENERATE: dict[str, Any] = {
    "name": "creative/sprite_generate",
    "version": "1.0.0",
    "description": "Generate a sprite/pixel-art asset via asset capability — R6 M11",
    "nodes": [
        {
            "id": "generate",
            "type": "task",
            "name": "Generate sprite asset",
            "agent": "general",
            "capabilities": ["asset:sprite"],
            "timeout_s": 120.0,
        },
    ],
    "retries": 1,
    "timeout_s": 300.0,
    "permissions": ["filesystem"],
    "metadata": {"domain": "creative", "m11": "R6"},
}


def creative_workflow_definitions() -> list[WorkflowDefinition]:
    """Hai definition creative mặc định (deterministic)."""
    return [
        WorkflowDefinition.from_dict(_GAME_SCAFFOLD),
        WorkflowDefinition.from_dict(_SPRITE_GENERATE),
    ]


def register_creative_workflows(library: Any) -> int:
    """Register creative workflows vào WorkflowLibrary — trả số lượng đã thêm."""
    added = 0
    for definition in creative_workflow_definitions():
        if definition.name not in library.list():
            library.register(definition)
            added += 1
    return added
