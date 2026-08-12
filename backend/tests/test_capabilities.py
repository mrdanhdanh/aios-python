"""Capability registry tests."""

import threading

import pytest

from aios_core.capabilities import CapabilityError, CapabilityRegistry


def make_registry():
    reg = CapabilityRegistry()
    reg.register_capability("execute_code", "run code")
    reg.register_capability("read_file")
    return reg


def test_register_get_list():
    reg = make_registry()
    assert reg.get("execute_code").description == "run code"
    assert reg.list() == ["execute_code", "read_file"]


def test_unknown_get_raises():
    reg = make_registry()
    with pytest.raises(CapabilityError, match="Unknown capability"):
        reg.get("nope")


def test_bind_unbind_tool():
    reg = make_registry()
    reg.bind_tool("execute_code", "docker-tool")
    reg.bind_tool("execute_code", "docker-tool")  # idempotent
    assert reg.tools_for("execute_code") == ["docker-tool"]
    reg.unbind_tool("execute_code", "docker-tool")
    assert reg.tools_for("execute_code") == []


def test_bind_unknown_raises():
    reg = make_registry()
    with pytest.raises(CapabilityError):
        reg.bind_tool("ghost", "t1")
    with pytest.raises(CapabilityError):
        reg.tools_for("ghost")
    with pytest.raises(CapabilityError):
        reg.unbind_tool("ghost", "t1")
    with pytest.raises(CapabilityError):
        reg.agents_using("ghost")


def test_register_agent_use():
    reg = make_registry()
    reg.register_agent_use("coder", "execute_code")
    reg.register_agent_use("coder", "execute_code")  # idempotent set
    reg.register_agent_use("tester", "execute_code")
    assert reg.agents_using("execute_code") == ["coder", "tester"]


def test_register_agent_use_empty_or_unknown():
    reg = make_registry()
    with pytest.raises(ValueError, match="agent_id"):
        reg.register_agent_use("", "execute_code")
    with pytest.raises(CapabilityError):
        reg.register_agent_use("a", "ghost")


def test_duplicate_register_overwrite():
    reg = make_registry()
    reg.register_capability("execute_code", "updated desc")
    assert reg.get("execute_code").description == "updated desc"


def test_empty_name_raises():
    reg = make_registry()
    with pytest.raises(ValueError, match="capability name"):
        reg.register_capability("   ")


def test_thread_safe():
    reg = make_registry()
    errors: list[Exception] = []

    def worker(thread_id: int):
        try:
            for i in range(50):
                reg.bind_tool("execute_code", f"tool-{thread_id}-{i}")
                reg.register_agent_use(f"agent-{thread_id}-{i}", "read_file")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(reg.agents_using("read_file")) == 100
