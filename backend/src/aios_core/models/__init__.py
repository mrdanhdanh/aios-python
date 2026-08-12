"""AIOS model layer: contract, providers, registry."""

from .base import ChatMessage, ChatResponse, ModelContract
from .errors import ModelError, ModelNotAvailableError, ModelTimeoutError
from .mock import MockModel
from .ollama_provider import OllamaModel
from .openai_provider import OpenAIModel
from .registry import ModelRegistry

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "ModelContract",
    "ModelError",
    "ModelNotAvailableError",
    "ModelTimeoutError",
    "MockModel",
    "OllamaModel",
    "OpenAIModel",
    "ModelRegistry",
]
