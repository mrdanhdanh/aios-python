"""Upgrade pipeline (M4-P7, TASK-020)."""

from .backup import BackupRecord, BackupStore
from .dependency import ComponentSpec, Dependency, DependencyResolver, Resolution
from .errors import UpgradeError
from .migrator import DictMigrator, Migrator, SkillMigrator
from .pipeline import UpgradePipeline, UpgradeResult

__all__ = [
    "BackupRecord",
    "BackupStore",
    "ComponentSpec",
    "Dependency",
    "DependencyResolver",
    "DictMigrator",
    "Migrator",
    "Resolution",
    "SkillMigrator",
    "UpgradeError",
    "UpgradePipeline",
    "UpgradeResult",
]
