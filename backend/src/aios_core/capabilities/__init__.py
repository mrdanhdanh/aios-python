"""Capability layer: agents request capabilities, not tools."""

from .errors import CapabilityError
from .registry import Capability, CapabilityRegistry

__all__ = ["Capability", "CapabilityError", "CapabilityRegistry"]
