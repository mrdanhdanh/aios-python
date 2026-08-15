"""Autonomous layer errors (M9)."""

from __future__ import annotations


class AutonomousError(Exception):
    """Base error cho toàn bộ autonomous/ package."""


class GoalLifecycleError(AutonomousError):
    """Transition hoặc thao tác goal không hợp lệ."""


class PlanError(AutonomousError):
    """Không thể sinh plan."""


class GovernorError(AutonomousError):
    """Lỗi governor."""


class RecoveryError(AutonomousError):
    """Lỗi autonomous recovery."""


class LongHorizonError(AutonomousError):
    """Lỗi long-horizon execution."""


class MemoryPromotionError(AutonomousError):
    """Lỗi promote memory (INV-034)."""


class ExperimentError(AutonomousError):
    """Lỗi experimentation."""


class DelegationError(AutonomousError):
    """Lỗi multi-agent delegation."""


class StuckError(AutonomousError):
    """Lỗi stuck detection."""


class ScheduleError(AutonomousError):
    """Lỗi autonomous scheduler."""
