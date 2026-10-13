"""Editable byte buffer used by the memory editor and file services."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True, slots=True)
class BufferChange:
    offset: int
    before: bytes
    after: bytes


class MemoryBuffer:
    def __init__(self, data: bytes = b"", *, base_address: int = 0):
        if base_address < 0:
            raise ValueError("base_address cannot be negative")
        self._data = bytearray(data)
        self.base_address = base_address
        self._undo: list[BufferChange] = []
        self._redo: list[BufferChange] = []

    def __len__(self) -> int:
        return len(self._data)

    def __bytes__(self) -> bytes:
        return bytes(self._data)

    def read(self, offset: int = 0, length: int | None = None) -> bytes:
        self._check_range(offset, 0 if length is None else length, allow_end=True)
        return bytes(self._data[offset:] if length is None else self._data[offset:offset + length])

    def edit(self, offset: int, data: bytes | bytearray) -> BufferChange:
        payload = bytes(data)
        self._check_range(offset, len(payload), allow_end=True)
        before = bytes(self._data[offset:offset + len(payload)])
        change = BufferChange(offset, before, payload)
        self._data[offset:offset + len(payload)] = payload
        if payload != before:
            self._undo.append(change)
            self._redo.clear()
        return change

    def fill(self, offset: int, length: int, value: int) -> BufferChange:
        if not 0 <= value <= 255:
            raise ValueError("fill value must be 0..255")
        return self.edit(offset, bytes([value]) * length)

    def undo(self) -> BufferChange | None:
        if not self._undo:
            return None
        change = self._undo.pop()
        self._data[change.offset:change.offset + len(change.after)] = change.before
        self._redo.append(change)
        return change

    def redo(self) -> BufferChange | None:
        if not self._redo:
            return None
        change = self._redo.pop()
        self._data[change.offset:change.offset + len(change.after)] = change.after
        self._undo.append(change)
        return change

    def find(self, needle: bytes, start: int = 0) -> int:
        if not needle:
            raise ValueError("needle cannot be empty")
        return bytes(self._data).find(needle, start)

    def sha256(self) -> str:
        return hashlib.sha256(self._data).hexdigest()

    def _check_range(self, offset: int, length: int, *, allow_end: bool = False) -> None:
        if offset < 0 or length < 0 or offset + length > len(self._data) or (not allow_end and offset == len(self._data)):
            raise IndexError("memory range is outside the buffer")


def compare_buffers(left: bytes, right: bytes) -> list[tuple[int, int | None, int | None]]:
    """Return (offset, left_byte, right_byte) for every differing byte."""
    differences = []
    for offset in range(max(len(left), len(right))):
        a = left[offset] if offset < len(left) else None
        b = right[offset] if offset < len(right) else None
        if a != b:
            differences.append((offset, a, b))
    return differences
