from pathlib import Path
import gc
from threading import Barrier, Event
from time import monotonic

from validata.core.events import EventDispatcher
from validata.services.jobs import JobController
from validata.services.logging_setup import initialize_logging
from validata.services.paths import StoragePaths


def _drain_until_finished(controller, dispatcher, timeout=10):
    deadline = monotonic() + timeout
    events = []
    while not any(event.kind == "job_finished" for event in events) and monotonic() < deadline:
        events.extend(dispatcher.drain(500))
        for thread in controller._threads:
            thread.join(0.001)
    events.extend(dispatcher.drain(5000))
    for thread in controller._threads:
        thread.join(1)
    assert not controller.active
    return events


def _controller(tmp_path, dispatcher, **kwargs):
    logging = initialize_logging(StoragePaths(tmp_path.parent / f"{tmp_path.name}-logs", "development"))
    return JobController(dispatcher, logging.logger, **kwargs)


def test_job_fifo_accounting_errors_and_sequential_jobs(tmp_path: Path) -> None:
    files = [tmp_path / f"{index}.txt" for index in range(6)]
    for path in files:
        path.write_text("fixture", encoding="utf-8")
    completed_order = []

    def handler(task):
        completed_order.append(task.file.path)
        if task.file.path == files[2]:
            raise RuntimeError("synthetic worker error")
        return "Not Validated"

    dispatcher = EventDispatcher(max_events=8)
    controller = _controller(tmp_path, dispatcher, worker_count=1, queue_capacity=2,
                             task_handler=handler)
    job_id = controller.start(tuple(files))
    events = _drain_until_finished(controller, dispatcher)
    discovered = [event for event in events if event.kind == "file_discovered"]
    finished = [event for event in events if event.kind == "job_finished"][-1]
    discovered_order = [Path(event.payload["path"]) for event in discovered]
    assert set(discovered_order) == set(files)
    assert completed_order == discovered_order
    assert finished.payload["job_id"] == job_id
    assert finished.payload["state"] == "Completed"
    counts = finished.payload["counts"]
    assert counts["discovered"] == 6
    assert counts["queued"] == counts["running"] == counts["admitting"] == 0
    assert counts["completed"] == 5
    assert counts["processing_errors"] == 1
    assert counts["cancelled"] == 0
    assert not any(event.payload.get("status") in {"Valid", "Corrupted"}
                   for event in events if event.kind == "file_status")

    second_id = controller.start((files[0],))
    second_events = _drain_until_finished(controller, dispatcher)
    second_finished = [event for event in second_events if event.kind == "job_finished"][-1]
    assert second_id != job_id
    assert second_finished.payload["job_id"] == second_id
    assert second_finished.payload["counts"]["discovered"] == 1


def test_cancellation_interrupts_full_queue_and_reconciles(tmp_path: Path) -> None:
    files = [tmp_path / f"{index}.txt" for index in range(20)]
    for path in files:
        path.write_text("fixture", encoding="utf-8")
    entered = Event()
    release = Event()

    def blocked_handler(_task):
        entered.set()
        assert release.wait(5)
        return "Not Validated"

    dispatcher = EventDispatcher(max_events=4)
    controller = _controller(tmp_path, dispatcher, worker_count=1, queue_capacity=1,
                             task_handler=blocked_handler)
    controller.start(tuple(files))
    assert entered.wait(5)
    discovered_count = 0
    deadline = monotonic() + 5
    while monotonic() < deadline and discovered_count < 3:
        events = dispatcher.drain(10)
        discovered_count += sum(event.kind == "file_discovered" for event in events)
    assert discovered_count >= 3
    controller.cancel()
    release.set()
    events = _drain_until_finished(controller, dispatcher)
    finished = [event for event in events if event.kind == "job_finished"][-1]
    counts = finished.payload["counts"]
    assert finished.payload["state"] == "Cancelled"
    assert counts["discovered"] == (counts["completed"] + counts["cancelled"] +
                                      counts["processing_errors"] + counts["queued"] +
                                      counts["running"] + counts["admitting"])
    assert counts["cancelled"] > 0
    assert counts["queued"] == counts["running"] == counts["admitting"] == 0


def test_multiple_workers_can_finish_out_of_order(tmp_path: Path) -> None:
    files = [tmp_path / "first.txt", tmp_path / "second.txt"]
    for path in files:
        path.touch()
    both_started = Barrier(2)
    release_first = Event()
    finished_order = []

    def handler(task):
        both_started.wait(timeout=5)
        if task.file.path == files[0]:
            assert release_first.wait(5)
        else:
            release_first.set()
        finished_order.append(task.file.path)
        return "Deferred"

    dispatcher = EventDispatcher()
    controller = _controller(tmp_path, dispatcher, worker_count=2, queue_capacity=2,
                             task_handler=handler)
    controller.start(tuple(files))
    events = _drain_until_finished(controller, dispatcher)
    assert finished_order == [files[1], files[0]]
    finished = [event for event in events if event.kind == "job_finished"][-1]
    assert finished.payload["counts"]["completed"] == 2


def test_unexpected_discovery_failure_reconciles_and_releases_job(tmp_path: Path, monkeypatch) -> None:
    def fail_discovery(_sources, _cancel):
        raise RuntimeError("synthetic controller failure")

    monkeypatch.setattr("validata.services.jobs.discover", fail_discovery)
    dispatcher = EventDispatcher()
    controller = _controller(tmp_path, dispatcher, worker_count=2, queue_capacity=1)
    controller.start((tmp_path,))
    events = _drain_until_finished(controller, dispatcher)
    finished = [event for event in events if event.kind == "job_finished"][-1]
    assert finished.payload["state"] == "Failed"
    assert not controller.active
    assert sum(event.kind == "job_error" for event in events) == 1


def test_discovery_errors_are_operational_rows_not_tasks(tmp_path: Path) -> None:
    dispatcher = EventDispatcher()
    controller = _controller(tmp_path, dispatcher, worker_count=1, queue_capacity=1)
    controller.start((tmp_path / "missing.txt",))
    events = _drain_until_finished(controller, dispatcher)
    error = next(event for event in events if event.kind == "discovery_error")
    finished = [event for event in events if event.kind == "job_finished"][-1]
    assert error.payload["path"] == str(tmp_path / "missing.txt")
    assert error.payload["error_id"]
    assert finished.payload["counts"]["discovery_errors"] == 1
    assert finished.payload["counts"]["discovered"] == 0


def test_large_synthetic_tree_is_streamed_and_reconciled(tmp_path: Path) -> None:
    # Synthetic Windows 11 / Python 3.13 acceptance workload: 1,000 tiny files, no media.
    gc.collect()  # Tk resources from the earlier GUI smoke test must finalize on this thread.
    for index in range(1000):
        folder = tmp_path / f"d{index // 100}"
        folder.mkdir(exist_ok=True)
        (folder / f"f{index:04}.txt").touch()
    dispatcher = EventDispatcher(max_events=128)
    controller = _controller(tmp_path, dispatcher, worker_count=2, queue_capacity=16)
    started = monotonic()
    controller.start((tmp_path,))
    events = _drain_until_finished(controller, dispatcher, timeout=20)
    elapsed = monotonic() - started
    found = sum(event.kind == "file_discovered" for event in events)
    finished = [event for event in events if event.kind == "job_finished"][-1]
    assert found == 1000
    assert finished.payload["counts"]["completed"] == 1000
    assert finished.payload["state"] == "Completed"
    assert elapsed < 20
