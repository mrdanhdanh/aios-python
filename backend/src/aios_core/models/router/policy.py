"""Routing policy helpers (TASK-025): parse settings dict -> RoutingPolicy."""

from __future__ import annotations

from .contracts import PolicyRule, RoutingPolicy

__all__ = ["PolicyRule", "RoutingPolicy", "policy_from_settings"]


def policy_from_settings(data: dict) -> RoutingPolicy:
    """Alias for ``RoutingPolicy.from_settings`` (kept for DI clarity)."""
    return RoutingPolicy.from_settings(data)
