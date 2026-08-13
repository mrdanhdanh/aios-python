"""AIOS Skills (TASK-015) — lifecycle 10 states + manager + registry + sources."""

from .base import (
    Skill,
    SkillManifest,
    SkillSource,
    SkillState,
    assert_transition,
    is_installed_state,
)
from .errors import SkillError, SkillStateError
from .manager import SkillManager
from .registry import SkillRegistry
from .sources import GitSource, PipSource, ZipSource, build_default_sources

__all__ = [
    "Skill",
    "SkillManifest",
    "SkillSource",
    "SkillState",
    "assert_transition",
    "is_installed_state",
    "SkillError",
    "SkillStateError",
    "SkillManager",
    "SkillRegistry",
    "GitSource",
    "PipSource",
    "ZipSource",
    "build_default_sources",
    "build_skill_manager",
]


def build_skill_manager(db_path: str, event_sink=None):
    """Factory — db_path BẮT BUỘC (C1-16: không default path phụ thuộc cwd)."""
    return SkillManager(db_path=db_path, event_sink=event_sink)
