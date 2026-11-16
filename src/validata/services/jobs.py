"""Bounded Validator job orchestration; no file contents are read."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from queue import Full, Queue
from threading import Event, Lock, Thread
from uuid import uuid4

from validata.core.events import EventDispatcher, UiEvent

from .discovery import DiscoveredFile, DiscoveryError, discover


@dataclass(frozen=True, slots=True)
class FileTask:
    file_id: str
    file: DiscoveredFile


class JobController:
    """One streaming producer and a fixed, bounded pool of infrastructure workers."""

    def __init__(
        self,
        dispatcher: EventDispatcher,
        logger: logging.Logger,
        *,
        worker_count: int = 2,
        queue_capacity: int = 64,
        task_handler=None,
    ) -> None:
        if worker_count < 1 or queue_capacity < 1:
            raise ValueError("worker_count and queue_capacity must be positive")
        self.dispatcher = dispatcher
        self.logger = logger
        self.worker_count = worker_count
        self.queue_capacity = queue_capacity
        self.task_handler = task_handler or (lambda _task: "Not Validated")
        self._lock = Lock()
        self._active = False
        self._cancel = Event()
        self._job_id: str | None = None
        self._counts: dict[str, int] = {}
        self._state = "Idle"
        self._threads: tuple[Thread, ...] = ()

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    def start(self, sources: tuple[Path, ...]) -> str:
        with self._lock:
            if self._active:
                raise RuntimeError("a Validator job is already active")
            self._active = True
            self._cancel = Event()
            self._job_id = uuid4().hex
            self._state = "Discovering"
            self._counts = dict(discovered=0, admitting=0, queued=0, running=0,
                                completed=0, cancelled=0, discovery_errors=0,
                                processing_errors=0)
            job_id = self._job_id
            work: Queue[FileTask | None] = Queue(self.queue_capacity)
            workers = tuple(Thread(target=self._worker, args=(job_id, work),
                                   name=f"validata-worker-{i + 1}")
                            for i in range(self.worker_count))
            producer = Thread(target=self._produce, args=(job_id, tuple(sources), work, workers),
                               name="validata-discovery")
            self._threads = (*workers, producer)
        for worker in workers:
            worker.start()
        producer.start()
        return job_id

    def cancel(self) -> None:
        with self._lock:
            if self._active and not self._cancel.is_set():
                self._cancel.set()
                self._state = "Cancelling"
            else:
                return

    def _produce(self, job_id: str, sources: tuple[Path, ...],
                 work: Queue[FileTask | None], workers: tuple[Thread, ...]) -> None:
        failed = False
        try:
            self._publish("job_state", job_id=job_id, state="Discovering")
            for result in discover(sources, self._cancel):
                if self._cancel.is_set():
                    break
                if isinstance(result, DiscoveryError):
                    with self._lock:
                        self._counts["discovery_errors"] += 1
                        snapshot = dict(self._counts)
                    self._publish("discovery_error", job_id=job_id,
                                  error_id=uuid4().hex, path=str(result.path),
                                  message=result.message, counts=snapshot)
                    continue
                file_id = uuid4().hex
                task = FileTask(file_id, result)
                with self._lock:
                    self._counts["discovered"] += 1
                    self._counts["admitting"] += 1
                    snapshot = dict(self._counts)
                # This blocking publish is bounded by UI capacity, and always precedes task admission.
                self._publish("file_discovered", job_id=job_id, file_id=file_id,
                              path=str(result.path), size=result.size,
                              symlink=result.is_symlink, counts=snapshot)
                while True:
                    with self._lock:
                        if self._cancel.is_set():
                            self._counts["admitting"] -= 1
                            self._counts["cancelled"] += 1
                            snapshot = dict(self._counts)
                            cancelled = True
                        else:
                            cancelled = False
                    if cancelled:
                        self._publish("file_status", job_id=job_id, file_id=file_id,
                                      status="Cancelled", detail="Not started", counts=snapshot)
                        break
                    with self._lock:
                        try:
                            # Queue.put frees promptly when a worker dequeues, without polling delay.
                            work.put(task, timeout=0.05)
                        except Full:
                            continue
                        self._counts["admitting"] -= 1
                        self._counts["queued"] += 1
                        snapshot = dict(self._counts)
                        break
        except Exception as exc:
            failed = True
            self.logger.exception("Validator discovery controller failed")
            self._publish("job_error", job_id=job_id, message=f"Discovery controller error: {exc}")
            self._cancel.set()
        finally:
            if not self._cancel.is_set():
                with self._lock:
                    self._state = "Running"
                self._publish("job_state", job_id=job_id, state="Running")
            for _ in workers:
                while True:
                    try:
                        work.put(None, timeout=0.05)
                        break
                    except Full:
                        continue
            for worker in workers:
                worker.join()
            with self._lock:
                state = "Failed" if failed else "Cancelled" if self._cancel.is_set() else "Completed"
                self._state = state
                counts = dict(self._counts)
            self._publish("job_finished", job_id=job_id, state=state, counts=counts)
            with self._lock:
                self._active = False

    def _worker(self, job_id: str, work: Queue[FileTask | None]) -> None:
        while True:
            task = work.get()
            if task is None:
                return
            with self._lock:
                self._counts["queued"] -= 1
                if self._cancel.is_set():
                    self._counts["cancelled"] += 1
                    status, detail = "Cancelled", "Not started"
                    counts = dict(self._counts)
                    run = False
                else:
                    self._counts["running"] += 1
                    counts = dict(self._counts)
                    run = True
            if not run:
                self._publish("file_status", job_id=job_id, file_id=task.file_id,
                              status=status, detail=detail, counts=counts)
                continue
            try:
                status = self.task_handler(task)
                if status not in {"Not Validated", "Processing Unavailable", "Deferred"}:
                    raise ValueError("infrastructure task handler returned a non-neutral status")
                detail = "Integrity checks are not implemented"
                key = "completed"
            except Exception as exc:
                self.logger.exception("Validator task failed: %s", task.file.path)
                status, detail, key = "Processing Error", str(exc), "processing_errors"
            with self._lock:
                self._counts["running"] -= 1
                self._counts[key] += 1
                counts = dict(self._counts)
            self._publish("file_status", job_id=job_id, file_id=task.file_id,
                          status=status, detail=detail, counts=counts)

    def _publish(self, kind: str, **payload) -> None:
        self.dispatcher.publish(UiEvent(kind, payload))
