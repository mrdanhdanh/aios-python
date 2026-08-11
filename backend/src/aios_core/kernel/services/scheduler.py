"""Scheduler service: one-shot and interval jobs in background threads."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

from ...logging import get_logger

logger = get_logger("aios.kernel.services.scheduler")


class SchedulerService:
    """Schedule one-shot (after delay) and interval jobs.

    Callbacks run in daemon threads; interval ticks are skipped while a
    previous callback is still running; callback errors only log (the job
    keeps ticking); stop/cancel do NOT kill a running callback.
    """

    def __init__(self, poll_interval_s: float = 0.05) -> None:
        self._poll_interval_s = poll_interval_s
        self._jobs: dict[str, dict[str, Any]] = {}
        self._running_flags: dict[str, threading.Event] = {}
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._started = False

    # -- lifecycle ------------------------------------------------------------

    def on_startup(self) -> None:
        self.start()

    def on_shutdown(self) -> None:
        self.stop()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True, name="aios-scheduler")
            self._thread.start()
            self._started = True

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=1.0)
            self._started = False

    # -- jobs -----------------------------------------------------------------

    def schedule_one_shot(self, name: str, delay_s: float, callback: Callable[[], Any]) -> None:
        with self._lock:
            if name in self._jobs:
                logger.warning("Replacing existing job %s", name)
            self._jobs[name] = {
                "kind": "one_shot",
                "delay_s": delay_s,
                "interval_s": 0.0,
                "callback": callback,
                "run_at": time.monotonic() + delay_s,
                "next_run": time.monotonic() + delay_s,
            }
            self._running_flags[name] = threading.Event()

    def schedule_interval(self, name: str, interval_s: float, callback: Callable[[], Any]) -> None:
        with self._lock:
            if name in self._jobs:
                logger.warning("Replacing existing job %s", name)
            self._jobs[name] = {
                "kind": "interval",
                "delay_s": 0.0,
                "interval_s": interval_s,
                "callback": callback,
                "next_run": time.monotonic() + interval_s,
            }
            self._running_flags[name] = threading.Event()

    def cancel(self, name: str) -> None:
        with self._lock:
            job = self._jobs.pop(name, None)
            if job is None:
                logger.warning("cancel: unknown job %s (no-op)", name)
                return
            self._running_flags.pop(name, None)
            logger.debug("Cancelled job %s", name)

    def list_jobs(self) -> list[tuple[str, str, bool]]:
        with self._lock:
            return [
                (name, job["kind"], self._running_flags[name].is_set())
                for name, job in self._jobs.items()
            ]

    # -- internals ------------------------------------------------------------

    def _loop(self) -> None:
        while not self._stop.is_set():
            now = time.monotonic()
            with self._lock:
                due = [
                    (name, job)
                    for name, job in self._jobs.items()
                    if job["next_run"] <= now and not self._running_flags[name].is_set()
                ]
            for name, job in due:
                self._running_flags[name].set()
                threading.Thread(
                    target=self._run_callback,
                    args=(name, job),
                    daemon=True,
                    name=f"aios-job-{name}",
                ).start()
            self._stop.wait(self._poll_interval_s)

    def _run_callback(self, name: str, job: dict[str, Any]) -> None:
        try:
            job["callback"]()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Job %s callback failed: %s", name, exc)
        finally:
            flag = self._running_flags.get(name)
            if flag is not None:
                flag.clear()
            if job["kind"] == "interval":
                job["next_run"] = time.monotonic() + job["interval_s"]
            else:
                with self._lock:
                    self._jobs.pop(name, None)
