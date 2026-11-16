"""Thread-safe event handoff to the Tk main thread."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import get_ident
from queue import Empty, Queue
from types import MappingProxyType
from typing import Any


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    if value is None or isinstance(value, (str, bytes, int, float, bool)):
        return value
    raise TypeError(f"event payload value is not immutable or a supported container: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class UiEvent:
    """A named event with a read-only, recursively frozen payload."""

    kind: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str) or not self.kind:
            raise ValueError("event kind must be a non-empty string")
        if not isinstance(self.payload, Mapping):
            raise TypeError("event payload must be a mapping")
        object.__setattr__(self, "payload", _freeze(self.payload))


class EventDispatcher:
    """Accept events from any thread and drain them only on the owner thread."""

    def __init__(self, max_events: int = 2048) -> None:
        if max_events < 1:
            raise ValueError("max_events must be positive")
        self._queue: Queue[UiEvent] = Queue(maxsize=max_events)
        self._owner_thread = get_ident()

    def publish(self, event: UiEvent) -> None:
        if not isinstance(event, UiEvent):
            raise TypeError("event must be a UiEvent")
        self._queue.put(event)

    def drain(self, limit: int = 100) -> tuple[UiEvent, ...]:
        if get_ident() != self._owner_thread:
            raise RuntimeError("UI events may only be drained on the owner thread")
        if limit < 1:
            raise ValueError("limit must be positive")
        events = []
        for _ in range(limit):
            try:
                events.append(self._queue.get_nowait())
            except Empty:
                break
        return tuple(events)


class EventPump:
    """Poll an event dispatcher using a Tk-compatible ``after`` scheduler."""

    def __init__(
        self,
        scheduler: Any,
        dispatcher: EventDispatcher,
        handler: Callable[[UiEvent], None],
        *,
        interval_ms: int = 40,
        batch_size: int = 100,
    ) -> None:
        if interval_ms < 1 or batch_size < 1:
            raise ValueError("interval_ms and batch_size must be positive")
        self._scheduler = scheduler
        self._dispatcher = dispatcher
        self._handler = handler
        self._interval_ms = interval_ms
        self._batch_size = batch_size
        self._owner_thread = get_ident()
        self._running = False
        self._after_id: Any = None

    def start(self) -> None:
        self._assert_owner()
        if not self._running:
            self._running = True
            self._schedule()

    def stop(self) -> None:
        self._assert_owner()
        self._running = False
        if self._after_id is not None:
            self._scheduler.after_cancel(self._after_id)
            self._after_id = None

    def _schedule(self) -> None:
        self._after_id = self._scheduler.after(self._interval_ms, self._tick)

    def _tick(self) -> None:
        self._after_id = None
        if not self._running:
            return
        for event in self._dispatcher.drain(self._batch_size):
            self._handler(event)
        if self._running:
            self._schedule()

    def _assert_owner(self) -> None:
        if get_ident() != self._owner_thread:
            raise RuntimeError("event pump must be controlled on its owner thread")
