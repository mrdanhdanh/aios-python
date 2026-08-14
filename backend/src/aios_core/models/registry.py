"""Model registry: named model lookup (no singleton hardcode)."""

from __future__ import annotations

import logging
import threading

from .base import ModelContract
from .capability import ModelCapability
from .errors import ModelError

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Register and look up models by name.

    Duplicate registration overwrites (with a warning). The registry does NOT
    auto-register any model — RuntimeKernel pre-registers the mock.

    TASK-025 (additive): capability metadata per model. Resolution when
    ``register(name, model)`` without capability: provider ``capability()``
    duck-typed method -> ``ModelCapability.default()``. ``is_available()`` is
    NEVER called here (C2-05 v1 — Ollama does HTTP; offline determinism).
    """

    def __init__(self, default_name: str = "mock") -> None:
        self._default_name = default_name
        self._models: dict[str, ModelContract] = {}
        self._capabilities: dict[str, ModelCapability] = {}
        self._lock = threading.RLock()

    def register(
        self,
        name: str,
        model: ModelContract,
        capability: ModelCapability | None = None,
    ) -> None:
        with self._lock:
            if name in self._models:
                logger.warning("Overwriting model registration %s", name)
            self._models[name] = model
            if capability is not None:
                self._capabilities[name] = capability
            elif callable(getattr(model, "capability", None)):
                self._capabilities[name] = model.capability()  # duck-typed
            else:
                self._capabilities[name] = ModelCapability.default(
                    model_id=name, availability=True
                )

    def register_capability(self, name: str, capability: ModelCapability) -> None:
        """Attach/overwrite capability metadata (caller keeps model in sync)."""
        with self._lock:
            if name in self._capabilities:
                logger.warning("Overwriting capability %s", name)
            self._capabilities[name] = capability

    def capability(self, name: str) -> ModelCapability:
        with self._lock:
            capability = self._capabilities.get(name)
            if capability is None:
                raise ModelError(f"Unknown model capability: {name!r}")
            return capability

    def capabilities(self) -> dict[str, ModelCapability]:
        with self._lock:
            return {name: self._capabilities[name] for name in sorted(self._capabilities)}

    def get(self, name: str) -> ModelContract:
        with self._lock:
            model = self._models.get(name)
            if model is None:
                raise ModelError(f"Unknown model: {name!r}")
            return model

    def list(self) -> list[str]:
        with self._lock:
            return sorted(self._models.keys())

    def default(self, name: str | None = None) -> ModelContract:
        return self.get(name or self._default_name)
