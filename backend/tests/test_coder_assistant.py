"""Coder assistant tests (AC4, AC5, AC6)."""

import ast

import pytest

from aios_core.agents import AssistantRequest, CoderAssistant, CoderResult


def _req(text):
    return AssistantRequest(text=text)


def test_coder_happy_path_default_steps():
    assistant = CoderAssistant()
    response = assistant.handle(_req("tính tổng 2 số"))
    assert response.status == "ok"
    result = CoderResult(**response.metadata["result"])
    assert result.passed is True
    assert result.iterations == 1
    ast.parse(result.code)  # generated code parses
    assert "unit" in result.test_reports and "integration" in result.test_reports
    assert result.history == [
        "requirement", "planner", "generator", "static_analysis", "formatter",
        "unit_test", "integration_test",
    ]
    assert "generated code" in response.text


def test_coder_escapes_requirement_quotes():
    # C1-04: quotes/backslashes in requirement must not break generated code.
    assistant = CoderAssistant()
    response = assistant.handle(_req('viết hàm "hello" \\ test'))
    assert response.status == "ok"
    ast.parse(response.metadata["result"]["code"])


def test_coder_self_fix_rounds():
    calls = {"n": 0}

    def flaky_unit(state, request):
        calls["n"] += 1
        return {"passed": calls["n"] >= 2, "detail": f"try {calls['n']}"}

    assistant = CoderAssistant(steps={"unit_test": flaky_unit}, max_fix_rounds=2)
    response = assistant.handle(_req("tính tổng"))
    result = CoderResult(**response.metadata["result"])
    assert result.passed is True
    assert result.iterations == 2
    assert "fix_round:1" in result.history


def test_coder_feedback_passed_to_generator():
    seen = {}

    def recording_generator(state, request):
        seen["feedback"] = state.get("feedback")
        return {"code": "def main():\n    return 1\n"}

    def failing_unit(state, request):
        return {"passed": False, "detail": "assert fail"}

    assistant = CoderAssistant(
        steps={"generator": recording_generator, "unit_test": failing_unit},
        max_fix_rounds=1,
    )
    response = assistant.handle(_req("tính tổng"))
    result = CoderResult(**response.metadata["result"])
    assert result.passed is False
    # generator ran at least once with feedback from the first failed round
    assert seen["feedback"] is not None
    assert seen["feedback"]["unit"]["passed"] is False
    assert result.iterations == 2  # 1 + max_fix_rounds


def test_coder_max_rounds_zero():
    def always_fail(state, request):
        return {"passed": False, "detail": "nope"}

    assistant = CoderAssistant(steps={"unit_test": always_fail}, max_fix_rounds=0)
    response = assistant.handle(_req("tính tổng"))
    result = CoderResult(**response.metadata["result"])
    assert result.passed is False
    assert result.iterations == 1


def test_coder_invalid_max_rounds():
    with pytest.raises(ValueError, match="max_fix_rounds"):
        CoderAssistant(max_fix_rounds=-1)


def test_coder_unknown_step_key():
    with pytest.raises(ValueError, match="unknown step"):
        CoderAssistant(steps={"nonsense": lambda s, r: {}})


def test_coder_static_issues_recorded():
    # static_analysis reports missing main -> issues recorded (advisory, not blocking)
    def bad_generator(state, request):
        return {"code": "x = 1\n"}

    def passing_unit(state, request):
        ns = {}
        exec(state["code"], ns)  # noqa: S102 — test stub
        return {"passed": True, "detail": "ok"}

    assistant = CoderAssistant(steps={"generator": bad_generator, "unit_test": passing_unit})
    response = assistant.handle(_req("anything"))
    result = CoderResult(**response.metadata["result"])
    assert result.passed is True  # issues advisory (C1-09)
    assert "missing def main" in result.issues


def test_coder_step_raises_error_status():
    def exploding(state, request):
        raise RuntimeError("pipeline broke")

    assistant = CoderAssistant(steps={"generator": exploding})
    response = assistant.handle(_req("tính tổng"))
    assert response.status == "error"
    assert "pipeline broke" in response.metadata["error"]


def test_coder_history_has_fix_round():
    calls = {"n": 0}

    def flaky_unit(state, request):
        calls["n"] += 1
        return {"passed": calls["n"] >= 2, "detail": f"try {calls['n']}"}

    assistant = CoderAssistant(steps={"unit_test": flaky_unit}, max_fix_rounds=1)
    response = assistant.handle(_req("anything"))
    result = CoderResult(**response.metadata["result"])
    assert result.passed is True
    assert result.iterations == 2
    assert "fix_round:1" in result.history
