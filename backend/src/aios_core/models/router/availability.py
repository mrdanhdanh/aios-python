"""Availability checker (TASK-025): STATIC flag only — never calls the model.

``model.is_available()`` may do network I/O (Ollama HTTP), which breaks
offline determinism. Dynamic state (runtime failures) belongs to ModelHealth.
"""

from __future__ import annotations

from ..capability import ModelCapability


class AvailabilityChecker:
    """Reads the static ``availability`` flag from capability metadata."""

    def is_available(self, cap: ModelCapability) -> bool:
        return cap.availability
