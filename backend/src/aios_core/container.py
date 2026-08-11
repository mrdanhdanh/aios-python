"""Dependency injection container (Runtime -> Container -> Agent)."""

from __future__ import annotations

import inspect
import logging
import threading
import types
from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints

logger = logging.getLogger(__name__)


class ContainerError(Exception):
    """Raised for container misuse: unknown interface, circular deps, etc."""


class Scope(str, Enum):
    SINGLETON = "singleton"
    SCOPED = "scoped"  # v1: per-container (equivalent to singleton)
    TRANSIENT = "transient"


def _is_optional(hint: Any) -> bool:
    return get_origin(hint) in (types.UnionType, getattr(__import__("typing"), "Union")) and type(None) in get_args(hint)


def _unwrap_optional(hint: Any) -> Any:
    args = [a for a in get_args(hint) if a is not type(None)]
    return args[0] if len(args) == 1 else hint


class _Registration:
    __slots__ = ("impl", "scope", "instance")

    def __init__(self, impl: type, scope: Scope):
        self.impl = impl
        self.scope = scope
        self.instance: Any = None


class Container:
    """Thread-safe DI container with constructor injection.

    Rules:
    - ``register`` with an impl that is not a subclass of the interface raises
      ``TypeError`` immediately.
    - Re-registering the same interface **overwrites** the previous impl
      (allows test mocks), with a warning logged.
    - Constructor injection: **registration always wins over defaults**;
      ``Optional[X]`` resolves to ``None`` when unregistered; unsupported
      hints (Union without None, untyped params) raise ``ContainerError``.
    """

    def __init__(self) -> None:
        self._registrations: dict[type, _Registration] = {}
        self._lock = threading.RLock()
        self._started = False
        self._started_instances: set[int] = set()

    # -- registration ---------------------------------------------------------

    def register(self, interface: type, impl: type, scope: Scope = Scope.SINGLETON) -> None:
        if not inspect.isclass(impl) or not issubclass(impl, interface):
            raise TypeError(f"{impl!r} is not a subclass of interface {interface!r}")
        with self._lock:
            if interface in self._registrations:
                logger.warning("Overwriting registration for %s (old impl: %s)", interface, self._registrations[interface].impl)
            self._registrations[interface] = _Registration(impl, scope)

    def register_instance(self, interface: type, instance: Any) -> None:
        if not isinstance(instance, interface):
            raise TypeError(f"{instance!r} is not an instance of interface {interface!r}")
        with self._lock:
            reg = _Registration(type(instance), Scope.SINGLETON)
            reg.instance = instance
            self._registrations[interface] = reg

    def has(self, interface: type) -> bool:
        with self._lock:
            return interface in self._registrations

    def clear(self) -> None:
        with self._lock:
            self._registrations.clear()
            self._started_instances.clear()

    # -- resolution -----------------------------------------------------------

    def resolve_all(self, interface: type) -> list[Any]:
        return [self.resolve(interface)]

    def resolve(self, interface: type) -> Any:
        with self._lock:
            reg = self._registrations.get(interface)
            if reg is None:
                raise ContainerError(f"No registration for interface {interface!r}")
            if reg.scope == Scope.TRANSIENT:
                return self._instantiate(reg.impl, (), set())
            if reg.instance is None:
                reg.instance = self._instantiate(reg.impl, (), set())
            return reg.instance

    def _instantiate(self, impl: type, args: tuple, resolving: set[type]) -> Any:
        if impl in resolving:
            chain = " -> ".join(t.__name__ for t in resolving) + f" -> {impl.__name__}"
            raise ContainerError(f"Circular dependency detected: {chain}")
        resolving.add(impl)
        try:
            init = impl.__init__
            # Classes inheriting object.__init__ accept no injectable params.
            if init is object.__init__:
                return impl(*args)
            try:
                # Resolve string annotations (from __future__ import annotations).
                hints = get_type_hints(init)
            except Exception:  # noqa: BLE001 — unresolvable hints fall back to raw
                hints = {}
            params = inspect.signature(init).parameters
            kwargs: dict[str, Any] = {}
            for name, param in list(params.items())[1:]:  # skip self
                if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                    raise ContainerError(
                        f"Unsupported parameter {name!r} in {impl.__name__} (varargs not supported in v1)"
                    )
                hint = hints.get(name, inspect.Parameter.empty)
                if hint is inspect.Parameter.empty:
                    raise ContainerError(
                        f"Parameter {name!r} of {impl.__name__} has no type hint (v1 requires hints)"
                    )
                kwargs[name] = self._resolve_param(hint, param.default, name, impl, resolving)
            return impl(*args, **kwargs)
        finally:
            resolving.discard(impl)

    def _resolve_param(self, hint: Any, default: Any, name: str, impl: type, resolving: set[type]) -> Any:
        # Optional[X] / X | None — resolve if registered, else None (never errors).
        if _is_optional(hint):
            inner = _unwrap_optional(hint)
            if isinstance(inner, type) and inner in self._registrations:
                return self._resolve_registration(inner, resolving)
            return None

        if isinstance(hint, type):
            if hint in self._registrations:
                # Registration always wins over defaults.
                return self._resolve_registration(hint, resolving)
            if default is not inspect.Parameter.empty:
                return default  # unregistered hint with default → use default
            raise ContainerError(
                f"No registration for {hint.__name__!r} and no default for {name!r} in {impl.__name__}"
            )

        raise ContainerError(
            f"Unsupported parameter type {hint!r} for {name!r} in {impl.__name__} (Union/non-type unsupported in v1)"
        )

    def _resolve_registration(self, interface: type, resolving: set[type]) -> Any:
        reg = self._registrations[interface]
        if reg.scope == Scope.TRANSIENT:
            return self._instantiate(reg.impl, (), resolving)
        if reg.instance is None:
            reg.instance = self._instantiate(reg.impl, (), resolving)
        return reg.instance

    # -- lifecycle ------------------------------------------------------------

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            for interface in list(self._registrations):
                try:
                    instance = self.resolve(interface)
                except ContainerError:
                    continue
                self._invoke_hook(instance, "on_startup")
            self._started = True

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            for reg in list(self._registrations.values()):
                if reg.instance is not None:
                    self._invoke_hook(reg.instance, "on_shutdown")
            self._started = False

    @staticmethod
    def _invoke_hook(instance: Any, hook: str) -> None:
        method = getattr(instance, hook, None)
        if callable(method):
            method()
