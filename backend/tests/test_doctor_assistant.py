"""Doctor assistant + Safety Layer invariant tests (AC7, AC8, AC9)."""

import pytest

from aios_core.agents import (
    DISCLAIMER,
    DOCTOR_KNOWLEDGE,
    DoctorAssistant,
)


def _resp(text):
    return DoctorAssistant().handle(__import__("aios_core.agents.base", fromlist=["AssistantRequest"]).AssistantRequest(text=text))


def test_happy_path_low_risk():
    response = _resp("tôi bị đau đầu")
    assert response.status == "ok"
    assert response.metadata["symptoms"] == ["đau đầu"]
    assert response.metadata["conditions"] == ["headache (demo)"]
    assert response.metadata["risk"] == "low"
    assert response.metadata["recommendation"] == "self_care"


def test_medium_risk_see_doctor():
    response = _resp("tôi bị sốt và đau bụng")
    assert response.metadata["risk"] == "medium"
    assert response.metadata["recommendation"] == "see_doctor"


def test_longest_match_wins():
    response = _resp("tôi sốt cao")
    assert response.metadata["symptoms"] == ["sốt cao"]  # not ["sốt"]
    assert response.metadata["risk"] == "high"


def test_safety_layer_invariants():
    # (a) every ok response carries DISCLAIMER
    for text in ("tôi đau đầu", "tôi đau ngực", "hôm nay trời đẹp", "tôi đau đầu, nên uống thuốc gì"):
        response = _resp(text)
        assert response.status == "ok"
        assert DISCLAIMER in response.text

    # (b) medication request with symptom -> refusal + no drug name/liều
    response = _resp("tôi đau đầu, nên uống thuốc gì")
    assert response.metadata["medication_refused"] is True
    assert "không kê đơn" in response.text
    assert "paracetamol" not in response.text
    assert "500mg" not in response.text and "mg" not in response.text.split("(")[0]

    # (b)∩(d): medication without symptom -> refusal + more info
    response = _resp("uống thuốc gì")
    assert response.metadata["need_more_info"] is True
    assert response.metadata["medication_refused"] is True

    # (c) risk=high -> emergency (incl. danger-only "bất tỉnh" — C2-01)
    for text in ("tôi đau ngực", "tôi khó thở", "tôi bất tỉnh"):
        response = _resp(text)
        assert response.metadata["risk"] == "high"
        assert response.metadata["recommendation"] == "emergency"

    # (d) no symptom/danger/medication -> refuse + ask more info
    response = _resp("hôm nay trời đẹp")
    assert response.metadata["need_more_info"] is True
    # assert on response text + metadata keys (R2), not assessment.risk
    assert "chưa nhận diện" in response.text
    assert "risk" not in response.metadata
    assert "conditions" not in response.metadata
    assert "recommendation" not in response.metadata


def test_danger_only_not_refused():
    # "bất tỉnh" is danger keyword but NOT in KB -> still emergency (C2-01)
    response = _resp("tôi bất tỉnh rồi")
    assert response.status == "ok"
    assert response.metadata["need_more_info"] is False
    assert response.metadata["risk"] == "high"
    assert response.metadata["recommendation"] == "emergency"
    assert "bất tỉnh" in response.metadata["symptoms"]


def test_inject_knowledge():
    assistant = DoctorAssistant(knowledge={"ho": {"condition": "cough (demo)", "severity": "low"}})
    response = assistant.handle(
        __import__("aios_core.agents.base", fromlist=["AssistantRequest"]).AssistantRequest(text="tôi bị ho")
    )
    assert response.metadata["conditions"] == ["cough (demo)"]


def test_kb_miss_cautious():
    # R1.1: "đau đầu" matches (default KB keyword) but not in injected KB -> cautious
    assistant = DoctorAssistant(knowledge={"ho": {"condition": "cough (demo)", "severity": "low"}})
    response = assistant.handle(
        __import__("aios_core.agents.base", fromlist=["AssistantRequest"]).AssistantRequest(text="tôi bị đau đầu")
    )
    assert response.metadata["conditions"] == []
    assert response.metadata["risk"] == "low"
    assert response.metadata["recommendation"] == "see_doctor"
    assert response.metadata["need_more_info"] is True


def test_invalid_knowledge_raises():
    with pytest.raises(ValueError, match="severity"):
        DoctorAssistant(knowledge={"ho": {"condition": "c", "severity": "extreme"}})
    with pytest.raises(ValueError, match="condition"):
        DoctorAssistant(knowledge={"ho": {"severity": "low"}})
    with pytest.raises(ValueError, match="keyword"):
        DoctorAssistant(knowledge={"": {"condition": "c", "severity": "low"}})


def test_doctor_deterministic():
    assistant = DoctorAssistant()
    r1 = assistant.handle(
        __import__("aios_core.agents.base", fromlist=["AssistantRequest"]).AssistantRequest(text="tôi đau đầu và sốt")
    )
    r2 = assistant.handle(
        __import__("aios_core.agents.base", fromlist=["AssistantRequest"]).AssistantRequest(text="tôi đau đầu và sốt")
    )
    assert r1.text == r2.text
    assert r1.metadata == r2.metadata


def test_default_knowledge_has_expected_keys():
    assert "đau đầu" in DOCTOR_KNOWLEDGE
    assert "sốt cao" in DOCTOR_KNOWLEDGE
