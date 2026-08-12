"""Prompt registry tests."""

import threading

import pytest
from pydantic import ValidationError

from aios_core.prompts import PromptError, PromptRegistry, PromptTemplate


def prompt(**over):
    data = dict(
        id="coder",
        name="code-gen",
        version="1.0.0",
        template="Write {lang} code for {task}",
    )
    data.update(over)
    return PromptTemplate(**data)


def test_variables_extracted_and_deduped():
    p = PromptTemplate(id="x", name="x", version="1.0.0", template="Hi {name} {name} {task}")
    assert p.variables == ["name", "task"]


def test_extract_edges():
    # {{name}} is an escape → NOT extracted
    p = PromptTemplate(id="x", name="x", version="1.0.0", template="Use {{name}} here")
    assert p.variables == []
    # format spec → PromptError at construction
    with pytest.raises(PromptError):
        PromptTemplate(id="x", name="x", version="1.0.0", template="Score {score:.2f}")
    # positional → PromptError
    with pytest.raises(PromptError):
        PromptTemplate(id="x", name="x", version="1.0.0", template="Hello {}")
    # trailing brace → PromptError
    with pytest.raises(PromptError):
        PromptTemplate(id="x", name="x", version="1.0.0", template="{name}}")
    # triple braces → PromptError
    with pytest.raises(PromptError):
        PromptTemplate(id="x", name="x", version="1.0.0", template="{{{name}}}")


def test_version_invalid():
    with pytest.raises(ValidationError):
        prompt(version="nope")


def test_register_get_latest_by_semver():
    reg = PromptRegistry()
    reg.register(prompt())
    reg.register(prompt(version="2.0.0"))
    reg.register(prompt(version="1.5.0"))  # older than 2.0.0
    assert reg.get("coder").version == "2.0.0"
    assert reg.get("coder", "1.5.0").version == "1.5.0"
    assert reg.list() == ["coder"]


def test_register_same_id_version_overwrites():
    reg = PromptRegistry()
    reg.register(prompt())
    reg.register(prompt(template="New template {lang}"))
    assert reg.get("coder").template == "New template {lang}"


def test_unknown_id_or_version():
    reg = PromptRegistry()
    reg.register(prompt())
    with pytest.raises(PromptError, match="Unknown prompt id"):
        reg.get("ghost")
    with pytest.raises(PromptError, match="version"):
        reg.get("coder", "9.9.9")


def test_render():
    reg = PromptRegistry()
    reg.register(prompt())
    assert reg.render("coder", {"lang": "python", "task": "api"}) == "Write python code for api"


def test_render_missing_variable():
    reg = PromptRegistry()
    reg.register(prompt())
    with pytest.raises(PromptError, match="missing variable"):
        reg.render("coder", {"lang": "python"})  # task omitted


def test_evaluate_and_evaluations():
    reg = PromptRegistry()
    reg.register(prompt(version="1.0.0"))
    reg.register(prompt(version="2.0.0"))
    reg.evaluate("coder", 0.8, "good")
    reg.evaluate("coder", 0.9, "better")
    # latest version (2.0.0) is recorded
    all_eval = reg.evaluations("coder")
    assert len(all_eval) == 2
    assert all(e.version == "2.0.0" for e in all_eval)
    # filter by version
    v1 = reg.evaluations("coder", version="1.0.0")
    assert v1 == []
    v2 = reg.evaluations("coder", version="2.0.0")
    assert len(v2) == 2
    # average sanity
    assert sum(e.score for e in all_eval) / len(all_eval) == pytest.approx(0.85)


def test_evaluations_unknown_id():
    reg = PromptRegistry()
    with pytest.raises(PromptError, match="Unknown prompt id"):
        reg.evaluations("ghost")


def test_render_escape_literal():
    reg = PromptRegistry()
    reg.register(PromptTemplate(id="t", name="t", version="1.0.0", template="Literal {{x}} and {v}"))
    assert reg.render("t", {"v": "ok"}) == "Literal {x} and ok"


def test_render_missing_variable():
    reg = PromptRegistry()
    reg.register(prompt())
    with pytest.raises(PromptError, match="missing variable"):
        reg.render("coder", {"lang": "python"})


def test_render_extra_variable_ignored():
    reg = PromptRegistry()
    reg.register(prompt())
    assert reg.render("coder", {"lang": "py", "task": "t", "extra": 1}) == "Write py code for t"


def test_render_none_value():
    reg = PromptRegistry()
    reg.register(prompt())
    assert reg.render("coder", {"lang": None, "task": "t"}) == "Write None code for t"


def test_evaluate_and_evaluations():
    reg = PromptRegistry()
    reg.register(prompt())
    reg.evaluate("coder", 0.9, note="good")
    reg.evaluate("coder", 0.7)
    history = reg.evaluations("coder")
    assert len(history) == 2  # history append
    assert history[0].score == 0.9
    assert history[0].version == "1.0.0"
    assert history[0].timestamp
    assert len(reg.evaluations("coder", version="1.0.0")) == 2
    assert reg.evaluations("coder", version="9.9.9") == []


def test_evaluate_unknown_id():
    reg = PromptRegistry()
    with pytest.raises(PromptError):
        reg.evaluate("ghost", 1.0)
    with pytest.raises(PromptError):
        reg.evaluations("ghost")


def test_thread_safe():
    reg = PromptRegistry()
    reg.register(prompt())
    errors: list[Exception] = []

    def worker():
        try:
            for i in range(50):
                reg.render("coder", {"lang": "py", "task": f"t{i}"})
                reg.evaluate("coder", 1.0)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(reg.evaluations("coder")) == 100
