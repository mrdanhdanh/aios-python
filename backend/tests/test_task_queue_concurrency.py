"""TaskQueue concurrent dequeue test (M2 review correction — V11 / brief mục 6).

Proves that under >=2 worker threads, each claiming from the SAME shared
goals.db (separate connections, single-writer-single-process model with
UPDATE..RETURNING), exactly one worker claims each item: no double-claim,
no lost update. This is the mandatory concurrency test required by the
M2 review brief (mục 6).
"""

import threading

from aios_core.kernel.events import EventBus
from aios_core.kernel.services import EventService
from aios_core.orchestrator.goals import QueueItemStatus, TaskQueue


def _make_queue(db_path, audit_dir):
    bus = EventBus()
    svc = EventService(bus, audit_dir / "audit.db")
    return TaskQueue(event_service=svc, db_path=db_path)


def test_concurrent_dequeue_single_claim(tmp_path):
    db_path = tmp_path / "goals.db"
    # Seed with one writer (does not participate in the dequeue race).
    seed = _make_queue(db_path, tmp_path / "seed_audit")
    n = 50
    for i in range(n):
        seed.enqueue(f"wf-{i}", priority=(i % 5))

    claimed: list[str] = []
    claimed_lock = threading.Lock()
    stop = False

    def worker():
        # Each worker owns its own connection/EventService -> no shared-state race.
        q = _make_queue(db_path, tmp_path / f"audit_{threading.current_thread().name}")
        while True:
            item = q.dequeue()
            if item is None:
                break
            with claimed_lock:
                claimed.append(item.id)
            # simulate work, then mark completed so it is not reclaimed
            q.complete(item.id)

    threads = [threading.Thread(target=worker, name=f"w{i}") for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    # Exactly N items claimed, each by exactly one worker.
    assert len(claimed) == n, f"lost/missing claims: {len(claimed)} != {n}"
    assert len(set(claimed)) == n, f"double-claim detected: {len(claimed) - len(set(claimed))} dupes"
    # No item left queued/running after all workers drained the queue.
    leftover = _make_queue(db_path, tmp_path / "verify_audit")
    assert leftover.dequeue() is None
