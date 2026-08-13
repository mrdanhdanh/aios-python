"""AIOS Worker Plane agents (TASK-013): General, Coder, Doctor, System Doctor.

Hard isolation (INV-001/002): this package imports only model contracts +
pydantic + stdlib; all runtime interactions go through injectable callables.
"""

from .base import (
    EVENT_AGENT_FINISHED,
    EVENT_AGENT_STARTED,
    Assistant,
    AssistantRequest,
    AssistantResponse,
    EventSink,
)
from .coder import CoderAssistant, CoderResult, DEFAULT_STEPS
from .doctor import (
    DISCLAIMER,
    DANGER_KEYWORDS,
    DOCTOR_KNOWLEDGE,
    MEDICATION_REQUEST_PATTERNS,
    DoctorAssessment,
    DoctorAssistant,
)
from .general import GeneralAssistant
from .registry import AssistantRegistry
from .system_doctor import FIX_HINTS, GENERIC_HINT, SystemDoctor

__all__ = [
    "EVENT_AGENT_FINISHED",
    "EVENT_AGENT_STARTED",
    "Assistant",
    "AssistantRequest",
    "AssistantResponse",
    "EventSink",
    "CoderAssistant",
    "CoderResult",
    "DEFAULT_STEPS",
    "DISCLAIMER",
    "DANGER_KEYWORDS",
    "DOCTOR_KNOWLEDGE",
    "MEDICATION_REQUEST_PATTERNS",
    "DoctorAssessment",
    "DoctorAssistant",
    "GeneralAssistant",
    "AssistantRegistry",
    "FIX_HINTS",
    "GENERIC_HINT",
    "SystemDoctor",
]
