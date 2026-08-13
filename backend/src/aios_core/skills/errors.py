"""Skill errors (TASK-015)."""


class SkillError(Exception):
    """Raised for skill lifecycle misuse (not found, already exists, broken dep)."""


class SkillStateError(SkillError):
    """Raised on invalid state transitions / missing history."""
