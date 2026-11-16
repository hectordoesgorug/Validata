from threading import Thread

import pytest

from validata.core.events import EventDispatcher, EventPump, UiEvent


def test_event_payload_is_recursively_immutable() -> None:
    event = UiEvent("result", {"items": [1, {"status": "Valid"}]})
    assert event.payload["items"][1]["status"] == "Valid"
    with pytest.raises(TypeError):
        event.payload["status"] = "Corrupted"
    with pytest.raises(TypeError):
        event.payload["items"][1]["status"] = "Corrupted"
    with pytest.raises(TypeError, match="not immutable"):
        UiEvent("invalid", {"buffer": bytearray(b"mutable")})


def test_dispatcher_preserves_fifo_order_and_accepts_worker_publish() -> None:
    dispatcher = EventDispatcher(max_events=3)
    worker = Thread(target=lambda: [dispatcher.publish(UiEvent("item", {"n": n})) for n in range(3)])
    worker.start()
    worker.join(timeout=2)
    assert not worker.is_alive()
    assert [event.payload["n"] for event in dispatcher.drain(3)] == [0, 1, 2]


def test_dispatcher_rejects_main_thread_drain_from_worker() -> None:
    dispatcher = EventDispatcher()
    errors = []

    def drain() -> None:
        try:
            dispatcher.drain()
        except RuntimeError as exc:
            errors.append(str(exc))

    worker = Thread(target=drain)
    worker.start()
    worker.join(timeout=2)
    assert errors == ["UI events may only be drained on the owner thread"]


class FakeScheduler:
    def __init__(self) -> None:
        self.callbacks = {}
        self.next_id = 0

    def after(self, _delay, callback):
        self.next_id += 1
        self.callbacks[self.next_id] = callback
        return self.next_id

    def after_cancel(self, identifier):
        self.callbacks.pop(identifier, None)

    def run_one(self):
        identifier, callback = next(iter(self.callbacks.items()))
        self.callbacks.pop(identifier)
        callback()


def test_event_pump_dispatches_in_batches_and_stops_cleanly() -> None:
    dispatcher = EventDispatcher()
    scheduler = FakeScheduler()
    received = []
    pump = EventPump(scheduler, dispatcher, received.append, interval_ms=25, batch_size=2)
    dispatcher.publish(UiEvent("one"))
    dispatcher.publish(UiEvent("two"))
    dispatcher.publish(UiEvent("three"))

    pump.start()
    scheduler.run_one()
    assert [event.kind for event in received] == ["one", "two"]
    assert len(scheduler.callbacks) == 1
    pump.stop()
    assert scheduler.callbacks == {}
