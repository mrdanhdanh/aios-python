"""Normalizer tests (6 case từ AC1)."""

from aios_core.orchestrator import Normalizer
from aios_core.workflow import WorkflowDefinition, WorkflowLibrary


def library():
    lib = WorkflowLibrary()
    lib.register(
        WorkflowDefinition(
            name="crud_generator",
            version="1.0.0",
            description="CRUD API generator",
            nodes=[{"id": "a", "type": "task", "name": "A"}],
        )
    )
    return lib


def test_cli_params():
    n = Normalizer()
    req = n.normalize("generate api lang=python framework=fastapi")
    assert req.params == {"lang": "python", "framework": "fastapi"}
    assert req.source == "cli"
    assert req.confidence == 0.5


def test_alias_merge_custom():
    n = Normalizer(alias={"make app": "generate api"})
    req = n.normalize("make app")
    assert req.confidence == 1.0  # alias matched
    # custom overrides default
    n2 = Normalizer(alias={"create api": "something else"})
    req2 = n2.normalize("create api")
    assert req2.confidence == 1.0


def test_workflow_macro():
    n = Normalizer(library=library())
    req = n.normalize("@crud_generator")
    assert req.confidence == 1.0
    assert req.intent is None  # matcher decides


def test_hash_chat_direct():
    n = Normalizer()
    req = n.normalize("#hello world")
    assert req.intent == "chat"
    assert req.params == {"content": "hello world"}


def test_lowercase_strip():
    n = Normalizer()
    req = n.normalize("  GENERATE API  ")
    assert req.raw == "  GENERATE API  "
    assert req.confidence == 0.5  # no alias/macro hit


def test_dict_input():
    n = Normalizer()
    req = n.normalize("hello", source="api")
    assert req.source == "api"
