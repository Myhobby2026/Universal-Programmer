"""Serialized operation queue with cancellation and observable progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import threading
import time
from typing import Callable


class OperationState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Operation:
    name: str
    action: Callable[[threading.Event, Callable[[float, str], None]], object]
    state: OperationState = OperationState.QUEUED
    progress: float = 0.0
    message: str = ""
    result: object = None
    error: str = ""
    started_at: float | None = None
    finished_at: float | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)


class OperationEngine:
    """One worker at a time prevents conflicting access to shared pins."""

    def __init__(self):
        self._queue: list[Operation] = []
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None

    def submit(self, operation: Operation) -> Operation:
        with self._lock:
            self._queue.append(operation)
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(target=self._run, name="programmer-operation", daemon=True)
                self._worker.start()
        return operation

    def cancel(self, operation: Operation) -> None:
        operation.cancel_event.set()
        if operation.state == OperationState.QUEUED:
            operation.state = OperationState.CANCELLED

    def wait(self, timeout: float | None = None) -> None:
        worker = self._worker
        if worker:
            worker.join(timeout)

    def _run(self) -> None:
        while True:
            with self._lock:
                if not self._queue:
                    return
                operation = self._queue.pop(0)
            if operation.state == OperationState.CANCELLED:
                continue
            operation.state = OperationState.RUNNING
            operation.started_at = time.monotonic()
            try:
                operation.result = operation.action(operation.cancel_event, self._progress(operation))
                operation.state = OperationState.CANCELLED if operation.cancel_event.is_set() else OperationState.SUCCEEDED
            except Exception as exc:
                operation.error = str(exc)
                operation.state = OperationState.FAILED
            finally:
                operation.finished_at = time.monotonic()

    @staticmethod
    def _progress(operation: Operation) -> Callable[[float, str], None]:
        def update(value: float, message: str = "") -> None:
            operation.progress = max(0.0, min(1.0, value))
            operation.message = message
        return update
