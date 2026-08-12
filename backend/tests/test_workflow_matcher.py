"""Workflow matcher tests."""

from aios_core.orchestrator import WorkflowMatcher
from aios_core.workflow import WorkflowDefinition, WorkflowLibrary


def make_library():
    lib = WorkflowLibrary()
    lib.register(
        WorkflowDefinition(
            name="crud_generator",
            version="1.0.0",
            description="CRUD API generator with tests",
            nodes=[{"id": "a", "type": "task", "name": "A"}],
        )
    )
    lib.register(
        WorkflowDefinition(
            name="review_pr",
            version="1.0.0",
            description="Review pull requests",
            nodes=[{"id": "a", "type": "task", "name": "A"}],
        )
    )
    return lib


def test_template_macro():
    matcher = WorkflowMatcher(make_library())
    match = matcher.match("crud generator")
    assert match is not None
    assert match.workflow_name == "crud_generator"
    assert match.confidence == 0.9


def test_full_search():
    matcher = WorkflowMatcher(make_library())
    match = matcher.match("crud api generator with tests")
    assert match is not None
    assert match.workflow_name == "crud_generator"
    assert match.confidence in (0.6, 0.8)


def test_token_search():
    matcher = WorkflowMatcher(make_library())
    match = matcher.match("i need a crud please")
    assert match is not None
    assert match.workflow_name == "crud_generator"  # token "crud" (stopword "please" filtered)
    assert match.matched_by == "token"


def test_token_stopword_filter():
    matcher = WorkflowMatcher(make_library())
    # tokens: ["hello", "world"] — no match; stopwords filtered out
    assert matcher.match("hello world the a please") is None


def test_no_match():
    matcher = WorkflowMatcher(make_library())
    assert matcher.match("quantum physics research lab") is None


def test_confidence_recheck():
    matcher = WorkflowMatcher(make_library())
    match = matcher.match("review_pr please")
    assert match is not None
    assert match.workflow_name == "review_pr"
