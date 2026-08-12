"""Goals, task queue, permission broker and failure recovery (M2-P3b).

Control Plane modules — pure deterministic, offline-first, SQLite-persisted.
All four modules share ONE database file (``goals.db``) with 3 tables; the DDL
is defined here so both GoalManager and TaskQueue initialize the same schema
idempotently (review R1/R2: ``cancel_goal`` cascade touches ``queue_items``
even when only GoalManager was constructed).
"""

from __future__ import annotations

from typing import Callable

from ...config import Settings
from ...kernel.services.events import EventService
from ...kernel.services.policy import PolicyService
from .errors import GoalError, QueueError
from .failure_recovery import FailureRecovery, RecoveryResult, RecoveryStatus
from .goal import Goal, GoalManager, GoalStatus, GoalTask, TaskStatus
from .permission_broker import PermissionBatch, PermissionBatchDecision, PermissionBroker
from .schema import SCHEMA_SQL
from .task_queue import QueueItem, QueueItemStatus, TaskQueue

__all__ = [
    "GoalError",
    "QueueError",
    "FailureRecovery",
    "RecoveryResult",
    "RecoveryStatus",
    "Goal",
    "GoalManager",
    "GoalStatus",
    "GoalTask",
    "TaskStatus",
    "PermissionBatch",
    "PermissionBatchDecision",
    "PermissionBroker",
    "QueueItem",
    "QueueItemStatus",
    "TaskQueue",
    "SCHEMA_SQL",
    "build_goal_modules",
]

def build_goal_modules(
    settings: Settings,
    event_service: EventService,
    policy_service: PolicyService,  # required (C2-03): EventService does not expose its bus
    approver: Callable[[PermissionBatch], PermissionBatchDecision] | None = None,
) -> tuple[GoalManager, TaskQueue, PermissionBroker, FailureRecovery]:
    """Assemble the four goal-plane modules on the shared ``goals.db``.

    GoalManager and TaskQueue MUST share the same ``db_path`` (review R1/C2-14):
    ``cancel_goal`` cascade relies on it. ``FailureRecovery`` needs no DB.
    """
    db_path = settings.goals.db_path
    goal_manager = GoalManager(event_service=event_service, db_path=db_path)
    task_queue = TaskQueue(event_service=event_service, db_path=db_path)
    broker = PermissionBroker(
        event_service=event_service,
        policy_service=policy_service,
        approver=approver,
    )
    recovery = FailureRecovery(event_service=event_service)
    return goal_manager, task_queue, broker, recovery
