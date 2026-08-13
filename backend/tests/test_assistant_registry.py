"""AssistantRegistry tests (AC11, AC12)."""

import threading

import pytest

from aios_core.agents import (
    AssistantRegistry,
    CoderAssistant,
    DoctorAssistant,
    GeneralAssistant,
    SystemDoctor,
)


def _registry(selector=None):
    reg = AssistantRegistry(selector=selector)
    reg.register(GeneralAssistant())
    reg.register(CoderAssistant())
    reg.register(DoctorAssistant())
    reg.register(SystemDoctor())
    return reg


def test_register_get_list():
    reg = _registry()
    assert reg.get("coder").name == "coder"
    names = [a.name for a in reg.list()]
    assert names == ["general", "coder", "doctor", "system_doctor"]


def test_register_duplicate_raises():
    reg = AssistantRegistry()
    reg.register(GeneralAssistant())
    with pytest.raises(ValueError, match="already registered"):
        reg.register(GeneralAssistant())


def test_get_unknown_none():
    reg = _registry()
    assert reg.get("nope") is None


def test_resolve_by_intent_with_selector():
    selector = {"coding": "coder", "medical": "doctor", "system": "system_doctor", "chat": "general"}.get
    reg = _registry(selector=selector)
    assert reg.resolve_by_intent("coding").name == "coder"
    assert reg.resolve_by_intent("medical").name == "doctor"


def test_resolve_selector_none():
    reg = _registry()
    assert reg.resolve_by_intent("coding") is None


def test_resolve_unknown_intent_none():
    reg = _registry(selector=lambda intent: None)
    assert reg.resolve_by_intent("nonsense") is None


def test_concurrent_register_list():
    # Bài học STATS #23: mỗi thread dùng prefix riêng — tránh trùng name.
    reg = AssistantRegistry()
    errors = []

    def _worker(prefix):
        try:
            for i in range(25):
                reg.register(GeneralAssistant() if False else _Fake(name=f"{prefix}-{i}"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(f"worker-{c}",)) for c in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(reg.list()) == 50


class _Fake:
    """Minimal Assistant stand-in for concurrency test."""

    def __init__(self, name):
        self.name = name


def test_integration_with_agent_selector():
    from aios_core.orchestrator.agent_selector import AgentSelector

    reg = _registry(selector=AgentSelector().select)
    assert reg.resolve_by_intent("coding").name == "coder"
    assert reg.resolve_by_intent("medical").name == "doctor"
    assert reg.resolve_by_intent("system").name == "system_doctor"
    assert reg.resolve_by_intent("chat").name == "general"
