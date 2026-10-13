"""Single-owner serial transport with a deterministic mock for tests."""

from __future__ import annotations

from collections import deque
import threading
import time
from typing import Protocol

from transport.protocol import Command, Frame, Status


class TransportError(ConnectionError):
    pass


class BytePort(Protocol):
    def write(self, data: bytes) -> int: ...
    def read(self, size: int) -> bytes: ...
    def close(self) -> None: ...


class SerialTransport:
    """Synchronous request/response transport; GUI callers should use a worker."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.port_name, self.baudrate, self.timeout = port, baudrate, timeout
        self._serial: BytePort | None = None
        self._sequence = 0
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self._serial is not None

    def open(self) -> None:
        if self._serial is not None:
            return
        try:
            import serial  # type: ignore
            self._serial = serial.Serial(self.port_name, self.baudrate, timeout=self.timeout)
        except Exception as exc:
            raise TransportError(f"Unable to open {self.port_name!r}: {exc}") from exc

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def request(self, command: int | Command, payload: bytes = b"", timeout: float | None = None) -> Frame:
        with self._lock:
            if self._serial is None:
                raise TransportError("transport is not connected")
            self._sequence = (self._sequence + 1) & 0xFFFF
            request = Frame(self._sequence, int(command), payload)
            self._serial.write(request.encode())
            deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
            from transport.protocol import FrameParser
            parser = FrameParser()
            while time.monotonic() < deadline:
                chunk = self._serial.read(256)
                for response in parser.feed(chunk):
                    if response.sequence == request.sequence:
                        return response
            raise TransportError("timed out waiting for firmware response")


class MockTransport:
    """Hardware-independent transport; it reports capability, never target success."""

    def __init__(self, capabilities: set[str] | None = None):
        self.capabilities = capabilities or {"gpio", "protocol-discovery"}
        self.connected = False
        self.requests: list[Frame] = []

    def open(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def request(self, command: int | Command, payload: bytes = b"", timeout: float | None = None) -> Frame:
        if not self.connected:
            raise TransportError("mock transport is not connected")
        sequence = len(self.requests) + 1
        request = Frame(sequence, int(command), payload)
        self.requests.append(request)
        if int(command) == Command.GET_INFO:
            body = b"firmware=mock;board=Teensy 4.1;capabilities=" + ",".join(sorted(self.capabilities)).encode()
            return Frame(sequence, int(command), body, Status.OK)
        return Frame(sequence, int(command), b"", Status.OK)
