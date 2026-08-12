"""Rule engine tests."""

from aios_core.orchestrator import RuleEngine, default_rules


def test_seven_intents():
    rules = default_rules()
    cases = {
        "generate api for users": ("coding", "coder"),
        "medical question about pain": ("medical", "doctor"),
        "system status please": ("system", "system_doctor"),
        "install skill python": ("skill", None),
        "upgrade the system": ("upgrade", None),
        "diagnose this error": ("diagnose", None),
        "hello there": ("chat", None),
    }
    for text, (intent, agent) in cases.items():
        match = rules.match(text)
        assert match is not None, text
        assert match.intent == intent, f"{text}: got {match.intent}"
        assert match.agent == agent, f"{text}: got {match.agent}"


def test_word_boundary_no_false_positive():
    rules = default_rules()
    # "system" is not a standalone pattern; "file system" must NOT match system rule
    match = rules.match("explain the file system to me")
    assert match is None or match.intent != "system"


def test_priority_over_longest():
    rules = default_rules()
    # "generate api generator" matches "generate api" (pri 10, len 12) and
    # "api generator" (pri 4, len 13) → priority wins → coding
    match = rules.match("generate api generator")
    assert match.intent == "coding"


def test_priority_tie_insertion():
    rules = default_rules()
    # "update system status" matches "system status" (8) and "update system" (8),
    # same length → insertion order (system status registered first)
    match = rules.match("update system status")
    assert match.matched_pattern == "system status"


def test_no_match_returns_none():
    rules = default_rules()
    assert rules.match("quantum physics research") is None


def test_custom_rule_added():
    rules = RuleEngine()
    rules.add_rule(["deploy"], "deploy", agent="ops", priority=20)
    match = rules.match("please deploy now")
    assert match.intent == "deploy"
    assert match.agent == "ops"


def test_case_insensitive():
    rules = default_rules()
    assert rules.match("GENERATE API").intent == "coding"
