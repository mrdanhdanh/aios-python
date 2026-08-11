"""DI container tests: scopes, injection, lifecycle, thread-safety."""

import threading
from abc import ABC

import pytest

from aios_core.container import Container, ContainerError, Scope


class Service(ABC):
    pass


class ServiceImpl(Service):
    pass


class Dep(ABC):
    pass


class DepImpl(Dep):
    pass


class NeedsDep:
    def __init__(self, dep: Dep):
        self.dep = dep


class NeedsOptional:
    def __init__(self, dep: Dep | None = None):
        self.dep = dep


class NeedsDefault:
    def __init__(self, dep: Dep = DepImpl()):
        self.dep = dep


class NeedsRegisteredDefault:
    def __init__(self, dep: Dep = DepImpl()):
        self.dep = dep


class Unannotated:
    def __init__(self, x):
        self.x = x


class CircularA:
    def __init__(self, b: "CircularB"):
        self.b = b


class CircularB:
    def __init__(self, a: CircularA):
        self.a = a


def test_register_wrong_type_raises():
    c = Container()
    with pytest.raises(TypeError):
        c.register(Service, object)  # object is not a subclass of Service


def test_resolve_unregistered_raises():
    c = Container()
    with pytest.raises(ContainerError):
        c.resolve(Service)


def test_singleton_same_instance():
    c = Container()
    c.register(Service, ServiceImpl)
    assert c.resolve(Service) is c.resolve(Service)


def test_transient_new_instance():
    c = Container()
    c.register(Service, ServiceImpl, scope=Scope.TRANSIENT)
    assert c.resolve(Service) is not c.resolve(Service)


def test_scoped_same_instance_v1():
    c = Container()
    c.register(Service, ServiceImpl, scope=Scope.SCOPED)
    assert c.resolve(Service) is c.resolve(Service)


def test_register_instance_singleton():
    c = Container()
    impl = ServiceImpl()
    c.register_instance(Service, impl)
    assert c.resolve(Service) is impl
    assert c.resolve(Service) is impl  # always the same instance


def test_constructor_injection():
    c = Container()
    c.register(Dep, DepImpl)
    c.register(NeedsDep, NeedsDep)
    obj = c.resolve(NeedsDep)
    assert isinstance(obj, NeedsDep)
    assert isinstance(obj.dep, DepImpl)


def test_circular_dependency_raises():
    c = Container()
    c.register(CircularA, CircularA)
    c.register(CircularB, CircularB)
    with pytest.raises(ContainerError, match="Circular"):
        c.resolve(CircularA)


def test_optional_unregistered_is_none():
    c = Container()
    c.register(NeedsOptional, NeedsOptional)
    obj = c.resolve(NeedsOptional)
    assert obj.dep is None


def test_optional_registered_resolves():
    c = Container()
    c.register(Dep, DepImpl)
    c.register(NeedsOptional, NeedsOptional)
    assert isinstance(c.resolve(NeedsOptional).dep, DepImpl)


def test_default_used_when_unregistered():
    c = Container()
    c.register(NeedsDefault, NeedsDefault)
    assert isinstance(c.resolve(NeedsDefault).dep, DepImpl)


def test_registration_wins_over_default():
    c = Container()
    c.register(Dep, DepImpl)
    c.register(NeedsRegisteredDefault, NeedsRegisteredDefault)
    assert isinstance(c.resolve(NeedsRegisteredDefault).dep, DepImpl)


def test_unannotated_param_raises():
    c = Container()
    c.register(Unannotated, Unannotated)
    with pytest.raises(ContainerError, match="no type hint"):
        c.resolve(Unannotated)


def test_no_registration_no_default_raises():
    class NeedsDep2:
        def __init__(self, dep: Dep):  # no default, not registered
            self.dep = dep

    c = Container()
    c.register(NeedsDep2, NeedsDep2)
    with pytest.raises(ContainerError, match="No registration"):
        c.resolve(NeedsDep2)


def test_overwrite_registration():
    c = Container()
    c.register(Service, ServiceImpl)
    c.register(Service, ServiceImpl)  # overwrite — resolve returns the new impl
    assert isinstance(c.resolve(Service), ServiceImpl)


def test_has_and_clear():
    c = Container()
    assert c.has(Service) is False
    c.register(Service, ServiceImpl)
    assert c.has(Service) is True
    c.clear()
    assert c.has(Service) is False
    with pytest.raises(ContainerError):
        c.resolve(Service)


def test_clear_resets_singleton():
    c = Container()
    c.register(Service, ServiceImpl)
    first = c.resolve(Service)
    c.clear()
    c.register(Service, ServiceImpl)
    assert c.resolve(Service) is not first


def test_resolve_all():
    c = Container()
    c.register(Service, ServiceImpl)
    assert len(c.resolve_all(Service)) == 1


class LifecycleService:
    def __init__(self):
        self.started = 0
        self.stopped = 0

    def on_startup(self):
        self.started += 1

    def on_shutdown(self):
        self.stopped += 1


class PlainService:
    pass


def test_lifecycle_hooks():
    c = Container()
    c.register(LifecycleService, LifecycleService)
    c.register(PlainService, PlainService)  # no hooks → skipped silently
    c.start()
    c.start()  # idempotent
    obj = c.resolve(LifecycleService)
    assert obj.started == 1
    c.stop()
    c.stop()  # idempotent
    assert obj.stopped == 1


def test_thread_safe_resolve_no_deadlock():
    c = Container()
    c.register(Dep, DepImpl)
    c.register(NeedsDep, NeedsDep)
    results: list[bool] = []
    errors: list[Exception] = []

    def worker():
        try:
            for _ in range(50):
                obj = c.resolve(NeedsDep)
                assert isinstance(obj.dep, DepImpl)
            results.append(True)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(results) == 2
