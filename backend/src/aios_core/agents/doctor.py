"""Doctor assistant — 6-step pipeline + Safety Layer invariants (TASK-013).

Demo knowledge base only — NOT real medical diagnosis. Safety invariants:
(a) every ok response carries DISCLAIMER; (b) never prescribes medication
(checked BEFORE (d), applies to every response); (c) risk=high -> emergency;
(d) no symptom AND no danger keyword -> refuse + ask for more info.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .base import Assistant, AssistantRequest, AssistantResponse, EventSink

DISCLAIMER = (
    "Thông tin này chỉ mang tính tham khảo demo, KHÔNG phải chẩn đoán y tế. "
    "Vui lòng hỏi bác sĩ hoặc cơ sở y tế chuyên môn."
)

DOCTOR_KNOWLEDGE: dict[str, dict] = {
    "đau đầu": {"condition": "headache (demo)", "severity": "low"},
    "sốt": {"condition": "fever (demo)", "severity": "medium"},
    "sốt cao": {"condition": "high fever (demo)", "severity": "high"},
    "ho": {"condition": "cough (demo)", "severity": "low"},
    "đau bụng": {"condition": "abdominal pain (demo)", "severity": "medium"},
    "khó thở": {"condition": "breathing difficulty (demo)", "severity": "high"},
    "đau ngực": {"condition": "chest pain (demo)", "severity": "high"},
    "buồn nôn": {"condition": "nausea (demo)", "severity": "low"},
}

DANGER_KEYWORDS = ("sốt cao", "khó thở", "đau ngực", "bất tỉnh", "co giật")

MEDICATION_REQUEST_PATTERNS = ("thuốc", "liều", "mg", "kê đơn", "uống gì")

MEDICATION_REFUSAL = "Tôi không kê đơn hoặc gợi ý liều thuốc. Hãy hỏi bác sĩ/dược sĩ."
MORE_INFO_TEXT = "Tôi chưa nhận diện được triệu chứng cụ thể. Bạn có thể mô tả thêm..."

_VALID_SEVERITIES = {"low", "medium", "high"}


class DoctorAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symptoms: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    risk: Literal["low", "medium", "high"] = "low"
    recommendation: str = ""  # self_care | see_doctor | emergency; empty on (d)
    need_more_info: bool = False
    disclaimer: str = DISCLAIMER


def _validate_knowledge(knowledge: dict[str, dict]) -> None:
    for keyword, entry in knowledge.items():
        if not keyword or not keyword.strip():
            raise ValueError("knowledge keyword must not be empty")
        if not isinstance(entry, dict) or "condition" not in entry:
            raise ValueError(f"knowledge entry for {keyword!r} must have condition")
        severity = entry.get("severity")
        if severity not in _VALID_SEVERITIES:
            raise ValueError(f"knowledge entry for {keyword!r} has invalid severity: {severity!r}")


class DoctorAssistant(Assistant):
    name = "doctor"
    intent = "medical"
    description = "Medical demo assistant: symptom → knowledge → risk → recommendation (offline, safety-layered)"

    def __init__(self, knowledge: dict | None = None, event_sink: EventSink | None = None) -> None:
        super().__init__(event_sink=event_sink)
        active = dict(DOCTOR_KNOWLEDGE if knowledge is None else knowledge)
        _validate_knowledge(active)
        self._knowledge = active
        # Extractor keyword source = union(default KB keys, active KB keys, danger) (R1.1).
        self._keywords = sorted(
            set(DOCTOR_KNOWLEDGE) | set(active) | set(DANGER_KEYWORDS),
            key=len,
            reverse=True,  # longest-match-first
        )

    def _process(self, request: AssistantRequest) -> AssistantResponse:
        text = request.text.strip()
        medication_requested = any(p in text for p in MEDICATION_REQUEST_PATTERNS)
        danger_found = [kw for kw in DANGER_KEYWORDS if kw in text]
        symptoms = self._extract_symptoms(text)

        # (d) gate: no symptom AND no danger keyword (C2-01).
        if not symptoms and not danger_found:
            meta: dict = {"need_more_info": True}
            reply = MORE_INFO_TEXT
            if medication_requested:
                reply = MEDICATION_REFUSAL + " " + MORE_INFO_TEXT
                meta["medication_refused"] = True
            return AssistantResponse(
                text=reply + "\n\n" + DISCLAIMER,
                intent=self.intent,
                metadata=meta,
            )

        assessment = self._assess(symptoms, danger_found)
        # (c): risk=high -> emergency override.
        if assessment.risk == "high":
            assessment.recommendation = "emergency"
            recommendation_text = "Đến cơ sở y tế/cấp cứu gần nhất ngay, gọi cấp cứu nếu cần."
        elif assessment.recommendation == "see_doctor":
            recommendation_text = "Nên đi khám bác sĩ."
        else:
            recommendation_text = "Nghỉ ngơi, uống nước, theo dõi. Không tự ý dùng thuốc."

        parts = [
            f"Triệu chứng: {', '.join(assessment.symptoms)}.",
            f"Có thể liên quan: {', '.join(assessment.conditions) or 'không xác định'}.",
            f"Mức rủi ro: {assessment.risk}.",
            f"Khuyến nghị: {recommendation_text}",
        ]
        if medication_requested:
            parts.append(MEDICATION_REFUSAL)  # (b) applies to every response
        reply = " ".join(parts)

        meta = {
            "symptoms": assessment.symptoms,
            "conditions": assessment.conditions,
            "risk": assessment.risk,
            "recommendation": assessment.recommendation,
            "disclaimer": True,
            "medication_refused": medication_requested,
            "need_more_info": assessment.need_more_info,
        }
        return AssistantResponse(
            text=reply + "\n\n" + DISCLAIMER,
            intent=self.intent,
            metadata=meta,
        )

    def _extract_symptoms(self, text: str) -> list[str]:
        lowered = text.lower()
        found: list[str] = []
        for keyword in self._keywords:
            if keyword in lowered and keyword not in found:
                found.append(keyword)
        # Loại keyword là substring của keyword dài hơn đã match ("sốt" ⊂ "sốt cao").
        return [k for k in found if not any(k != other and k in other for other in found)]

    def _assess(self, symptoms: list[str], danger_found: list[str]) -> DoctorAssessment:
        conditions: list[str] = []
        max_severity = 0
        for symptom in symptoms:
            entry = self._knowledge.get(symptom)
            if entry is None:
                continue  # KB-miss (R1.1): keyword matched but not in active KB
            conditions.append(entry["condition"])
            max_severity = max(max_severity, {"low": 1, "medium": 2, "high": 3}[entry["severity"]])

        # danger keyword in text -> high regardless (bước 3).
        risk = "high" if danger_found else ("medium" if max_severity == 2 else
                                            ("high" if max_severity == 3 else "low"))

        assessment = DoctorAssessment(symptoms=symptoms, conditions=conditions, risk=risk)
        if not conditions and not danger_found:
            # KB-miss with symptoms (no danger): be cautious (C1-06).
            assessment.recommendation = "see_doctor"
            assessment.need_more_info = True
        elif risk == "high":
            assessment.recommendation = "emergency"
        elif risk == "medium":
            assessment.recommendation = "see_doctor"
        else:
            assessment.recommendation = "self_care"
        return assessment
