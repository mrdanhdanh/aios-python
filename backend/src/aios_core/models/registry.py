"""Model registry: named model lookup (no singleton hardcode)."""

from __future__ import annotations

import logging
import threading

from .base import ModelContract
from .errors import ModelError

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Register and look up models by name.

    Duplicate registration overwrites (with a warning). The registry does NOT
    auto-register any model — RuntimeKernel pre-registers the mock.
    """

    def __init__(self, default_name: str = "mock") -> None:
        self._default_name = default_name
        self._models: dict[str, ModelContract] = {}
        self._lock = threading.RLock()

    def register(self, name: str, model: ModelContract) -> None:
        with self._lock:
            if name in self._models:
                logger.warning("Overwriting model registration %s", name)
            self._models[name] = model

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
