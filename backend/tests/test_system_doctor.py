"""SystemDoctor tests (AC10)."""

from aios_core.agents import AssistantRequest, SystemDoctor


def _resp(probe):
    return SystemDoctor(health_probe=probe).handle(AssistantRequest(text="system status"))


def test_health_score_and_lists():
    response = _resp(lambda: {"api": {"ok": True, "detail": "up"}, "models": {"ok": True, "detail": "ok"},
                              "docker": {"ok": False, "detail": "daemon down"}})
    assert response.status == "ok"
    assert response.metadata["health_score"] == 2 / 3
    assert response.metadata["ok_components"] == ["api", "models"]
    assert response.metadata["failed_components"] == ["docker"]
    assert any("docker daemon" in s for s in response.metadata["suggestions"])
    assert "2/3 healthy" in response.text


def test_invalid_probe_entry_fails():
    response = _resp(lambda: {"api": {"ok": True}, "weird": "not-a-dict", "no_ok": {"detail": "x"}})
    assert response.metadata["failed_components"] == ["weird", "no_ok"]
    assert response.metadata["health_score"] == 1 / 3


def test_probe_raise_error_status():
    def _boom():
        raise RuntimeError("probe failed")

    response = SystemDoctor(health_probe=_boom).handle(AssistantRequest(text="status"))
    assert response.status == "error"
    assert "probe failed" in response.metadata["error"]


def test_probe_none_default_ok():
    response = SystemDoctor().handle(AssistantRequest(text="status"))
    assert response.status == "ok"
    assert response.metadata["health_score"] == 1.0
    assert response.metadata["ok_components"] == ["aios_core"]


def test_generic_hint_for_unknown_component():
    response = _resp(lambda: {"mystery": {"ok": False, "detail": "x"}})
    assert any("check component logs" in s for s in response.metadata["suggestions"])


def test_deterministic():
    probe = lambda: {"a": {"ok": True}, "b": {"ok": False, "detail": "d"}}  # noqa: E731
    r1 = _resp(probe)
    r2 = _resp(probe)
    assert r1.text == r2.text
    assert r1.metadata == r2.metadata


def test_empty_probe_zero_score():
    response = _resp(lambda: {})
    assert response.metadata["health_score"] == 0.0
